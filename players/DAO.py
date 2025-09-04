import asyncio
import collections
import functools
import logging

from asyncio import AbstractEventLoop
from concurrent.futures.process import ProcessPoolExecutor
from functools import partial
from typing import Union, Optional, AsyncIterator, Callable, Any, List
from asgiref.sync import sync_to_async
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from concurrent.futures import ThreadPoolExecutor
from django.db.models.base import ModelBase, Model
from django.db.models import QuerySet
from players.meta import StaticMethodMaker

logger = logging.getLogger(__name__)


class AsyncDAO(metaclass=StaticMethodMaker):

    async def acreate(queryset: QuerySet, **data) -> Model:
        obj = await queryset.acreate(**data)
        return obj

    async def aget_one(queryset: QuerySet, search_field: Union[str, ModelBase], val: Union[str, bool],
                       ignore_logger: bool = False) -> Optional[Model]:

        if isinstance(search_field, str):
            key = dict([(search_field, val)], )
        elif isinstance(search_field, bool):
            key = dict([(search_field, val)], )

        elif isinstance(search_field, ModelBase):
            pks = search_field._meta.pk_fields
            assert len(pks) == 1, "More than one primary key field"
            key = dict([(search_field._meta.pk_fields[0].__dict__.get("name"), val)], )

        try:
            return await queryset.aget(**key)
        except (ObjectDoesNotExist, MultipleObjectsReturned) as e:
            if ignore_logger:
                return
            logger.error("Error players.DAO.AsyncDAO.get_one", exc_info=True)
            return

    def get_one(queryset: QuerySet, search_field: Union[str, ModelBase], val: Union[str, bool]) -> Optional[Model]:
        if isinstance(search_field, str):
            key = dict([(search_field, val)], )

        elif isinstance(search_field, ModelBase):
            pks = search_field._meta.pk_fields
            assert len(pks) == 1, "More than one primary key field"
            key = dict([(search_field._meta.pk_fields[0].__dict__.get("name"), val)], )

        try:
            return queryset.get(**key)
        except (ObjectDoesNotExist, MultipleObjectsReturned) as e:
            logger.error("Error players.DAO.AsyncDAO.get_one", exc_info=True)
            return

    def get_list(queryset: QuerySet) -> QuerySet:
        return queryset.all()

    async def aget_count(queryset: QuerySet) -> int:
        return await sync_to_async(queryset.count)()

    async def aget_list_iterator(queryset: QuerySet, chuck: int = 50) -> Union[list, AsyncIterator[QuerySet]]:
        return queryset.aiterator(chunk_size=chuck)

    async def aget_list(queryset: QuerySet) -> QuerySet:
        return await sync_to_async(queryset.all)()

    async def aget_filtered_list(queryset: QuerySet, search_field: Union[str, ModelBase] = None,
                                 val: str = None) -> QuerySet:
        if isinstance(search_field, str):
            key = dict([(search_field, val)], )

        elif isinstance(search_field, ModelBase):
            pks = search_field._meta.pk_fields
            assert len(pks) == 1, "More than one primary key field"
            key = dict([(search_field._meta.pk_fields[0].__dict__.get("name"), val)], )

        return await sync_to_async(queryset.filter)(**key)

    async def get_minimal(queryset: QuerySet, sort_field: str) -> QuerySet:
        obj = await queryset.order_by(sort_field).afirst()
        return obj

    async def aget_last(queryset: QuerySet,
                        search_field: Union[str, Model] = None,
                        val: str = None,
                        order: Optional[str] = None) -> ModelBase:
        if val and search_field:
            if isinstance(search_field, str):
                key = dict([(search_field, val)], )

            elif isinstance(search_field, ModelBase):
                key = dict([(search_field._meta.pk_fields[0].__dict__.get("name"), val)], )

            else:
                return
            if order:
                return await queryset.filter(**key).order_by(f"{order}").last()
            else:
                return await queryset.filter(**key).alast()
        else:
            return await queryset.order_by(order).alast()

    async def aget_sorted(queryset: QuerySet,
                          order: Optional[str] = None) -> QuerySet:
        return await sync_to_async(queryset.order_by, thread_sensitive=True)(order)

    def t_pool(func: Callable, *arg) -> Any:
        with ThreadPoolExecutor(max_workers=1) as executor:
            res = executor.submit(func, *arg)
            return res.result()

    async def async_processes_work(loop: AbstractEventLoop, partials: List[Callable]) -> List:
        task = []
        with ProcessPoolExecutor() as executor:
            for part in partials:
                task.append(loop.run_in_executor(executor, part))
            result = await asyncio.gather(*task)
        return result
