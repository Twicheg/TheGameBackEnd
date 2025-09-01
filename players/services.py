import asyncio
import logging
import csv
from sys import exc_info

import pandas as pd
import aiohttp
from datetime import datetime
from io import StringIO
from typing import Optional, Dict, Union, AsyncIterator
from rest_framework.request import Request
from rest_framework.exceptions import NotFound
from rest_framework.reverse import reverse
from uuid import UUID
from players.models import Player, Boost, PlayerLevel, Level, Prize, LevelPrize
from django.db.models import QuerySet, Model
from players.DAO import AsyncDAO
from players.async_atomic import aatomic

logger = logging.getLogger(__name__)


class BaseService:
    _pl_queryset: QuerySet = Player.objects
    _boost_queryset: QuerySet = Boost.objects
    _pll_queryset: QuerySet = PlayerLevel.objects
    _lvl_queryset: QuerySet = Level.objects
    _prize_queryset: QuerySet = Prize.objects
    _lvl_prize_queryset: QuerySet = LevelPrize.objects
    dao: AsyncDAO = AsyncDAO


class PlayerService(BaseService):

    @classmethod
    def get_players_list(cls) -> QuerySet:
        return cls.dao.get_list(cls._pl_queryset)

    @classmethod
    async def get_player(cls, player_id: str) -> Player():
        player = await cls.dao.aget_one(cls._pl_queryset, Player, player_id)
        try:
            assert player, "Player not found"
            assert await player.check_boosts, "Player check-problem players.services.PlayerService.get_players"
            assert await player.remove_inactive, "Player remove-inactive problem players.services.PlayerService.get_players"
        except AssertionError as e:
            logger.error("problem players.services.PlayerService.get_players", exc_info=True)
            return
        return player

    @classmethod
    async def check_last_entry(cls, obj: Model) -> Model:
        try:
            if obj.last_entry is None:
                obj.last_entry = datetime.now().date()
                await obj.asave()
                return obj
            return obj
        except AttributeError as e:
            logger.error("problem players.services.PlayerService.check_last_entry", exc_info=True)


class BoostService(BaseService):

    @classmethod
    async def create_boost(cls, data: Dict[str, Union[str, int]], player_pk: str) -> Dict[str, str]:
        buff = await cls.dao.acreate(cls._boost_queryset,
                                     player_id=player_pk,
                                     title=data.get("title"),
                                     description=data.get("description"),
                                     get_time=datetime.now())

        player = await cls.dao.aget_one(cls._pl_queryset, Player, player_pk)
        player.last_boost_date = datetime.now().date()
        await buff.asave(delay_time=data.get("duration"))
        await player.asave()
        return {"ok": "%s player buffed by %s" % (player_pk, buff.title)}

    @classmethod
    async def get_boosts_list(cls, pk: str) -> QuerySet:
        player = await cls.dao.aget_one(cls._pl_queryset, Player, pk)
        return await cls.dao.aget_list(player.boosts)

    @classmethod
    async def boost_player(cls, request_kwarg: Dict[str, str], request: Request, **kwargs) -> Optional[bool]:
        """Boost with http request"""
        try:
            url = reverse("players:boost_player", kwargs=request_kwarg, request=request)
            async with aiohttp.ClientSession() as session:
                data = {**kwargs}
                await session.post(url=url, json=data)
                return True
        except aiohttp.client_exceptions.ClientResponseError as e:
            logger.error("Can't buff player", exc_info=True)


class PlayerLevelService(BaseService):

    @classmethod
    async def set_levels_to_fresh_player(cls, uuid: UUID) -> None:
        """Set first from order level to player"""
        try:
            minimal = await cls.dao.get_minimal(cls._lvl_queryset, "order")
            assert minimal, "Empty LeveL table"
        except AssertionError:
            logger.warning('The LeveL is empty', exc_info=True)
            minimal = await cls.dao.acreate(cls._lvl_queryset,
                                            title='The Zero Default Level',
                                            order=0)

        player_level = await cls.dao.acreate(cls._pll_queryset,
                                             player_id=uuid,
                                             level_id=minimal.id,
                                             completed=datetime.now().date(),
                                             is_completed=False,
                                             )
        await player_level.asave()

    @classmethod
    @aatomic()
    async def level_up(cls, player_id: str) -> Dict[str, Union[str, bool]]:
        """Try set new level to player"""

        async def find_new_level(level: int) -> Optional[Model]:
            """Try to find level.order > that"""
            levels_queryset = await cls.dao.aget_list(cls._lvl_queryset)
            levels = [i.order async for i in levels_queryset]
            assert any(filter(lambda x: x > level, levels)), "Player have max level"

            for lvl in sorted(levels):
                if lvl > level:
                    return await cls.dao.aget_one(cls._lvl_queryset, "order", lvl, ignore_logger=True)

        player = await cls.dao.aget_one(cls._pl_queryset, Player, player_id)
        if player is None:
            raise NotFound

        try:
            current_level = await cls.dao.aget_one(player.playerlevel_set, "is_completed", False)
            assert current_level, "the player has no unfinished levels"
            current_level.is_completed = True
            current_level.completed = datetime.now().date()
            finished_level_id = current_level.level_id
            await current_level.asave()
            player.player_score += current_level.score

            current_order = await cls.dao.aget_one(cls._lvl_queryset, "id", finished_level_id)

            new_level_model_or_None = await find_new_level(current_order.order)
        except AssertionError as e:
            return {"result": False, "description":
                f"{player.player_id} {player.player_name} {str(e)}"}

        new_level_rewards_queryset = await cls.dao.aget_list(new_level_model_or_None.levelprize_set)
        await cls.dao.acreate(cls._pll_queryset,
                              player=player,
                              level=new_level_model_or_None,
                              completed=datetime.now().date(),  # PlayerLevel.completed null = False
                              is_completed=False,
                              )
        rewards_list = []
        async for lp in new_level_rewards_queryset:
            prize = await cls.dao.aget_one(cls._prize_queryset, Prize, lp.prize_id)
            rewards_list += [prize.title]
            assert await player.set_rewards(prize.title), "Can't reward player"
            lp.received = datetime.now().date()
            await lp.asave()

        return {"result": True, "description":
            f"{player.player_id} {player.player_name} поднял уровень до {new_level_model_or_None.order}"
            f" и получил {rewards_list} в подарок"}


class LevelService(BaseService):
    @classmethod
    def get_level(cls, pk: str) -> int:
        """Получение данных в отдельном потоке, потому-что ADRF ... """
        return cls.dao.t_pool(cls.dao.get_one, cls._lvl_queryset, "id", pk).order


class CSVService(BaseService):

    @classmethod
    def csv_work(cls, players: list) -> StringIO:
        def map_player(player):
            _dict = dict()
            _dict["player_id"] = player.player_id
            _dict["player_name"] = player.player_name
            _dict["levels"] = []

            for pll in player.playerlevel_set.all():
                _dict.get("levels").append(
                    {"level_title": pll.level.title,
                     "player_level_is_completed": pll.is_completed,
                     "prize": [i.prize.title for i in pll.level.levelprize_set.all()]})

            return _dict

        cloud_file = StringIO()
        fieldnames = ["player_id", "player_name", "levels"]
        writer = csv.DictWriter(cloud_file, fieldnames=fieldnames)
        dict_players = map(map_player, players)
        writer.writeheader()
        for pl in dict_players:
            writer.writerow(pl)
        cloud_file.seek(0)
        return cloud_file

    @classmethod
    async def export_to_csv(cls):
        """ Экспорт данных игрока в CSV. """
        workers = []
        count = await cls.dao.aget_count(cls._pl_queryset)
        chunk = 500

        assert count > 0, "Empty player queryset"
        assert chunk > 50, "Chunk too small"

        iterator = await cls.dao.aget_list_iterator(cls._pl_queryset, chunk)

        assert isinstance(iterator, AsyncIterator), "returned not asyncio iterator"

        match count:
            case x if x > chunk:
                _list = []
                async for p in iterator:
                    _list.append(p)
                    if len(_list) == chunk:
                        workers.append(cls.dao.async_processes_work(asyncio.get_running_loop(),
                                                                    cls.csv_work, _list.copy()))
                        _list = []
                else:
                    workers.append(cls.dao.async_processes_work(asyncio.get_running_loop(),
                                                                cls.csv_work, _list))

            case x if x < chunk:
                _list = []
                async for p in iterator:
                    _list.append(p)
                else:
                    workers.append(cls.dao.async_processes_work(asyncio.get_running_loop(),
                                                                cls.csv_work, _list))

        result = await asyncio.gather(*workers)
        assert result, "empty result after asyncio processes"
        csv_pd_list = [pd.read_csv(i.result()) for i in result]
        return pd.concat(csv_pd_list, ignore_index=True)
