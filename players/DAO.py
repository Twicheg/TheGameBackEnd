from asyncio import AbstractEventLoop
from concurrent.futures.process import ProcessPoolExecutor
from typing import Union, Optional, AsyncIterator, Callable, Any
from asgiref.sync import sync_to_async
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
import logging
from concurrent.futures import ThreadPoolExecutor
from django.db.models.base import ModelBase, Model
from django.db.models import QuerySet

logger = logging.getLogger(__name__)


class AsyncDAO:
    @staticmethod
    async def acreate(queryset: QuerySet, **data) -> Model:
        obj = await queryset.acreate(**data)
        return obj

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def get_list(queryset: QuerySet) -> QuerySet:
        return queryset.all()

    @staticmethod
    async def aget_count(queryset: QuerySet) -> int:
        return await sync_to_async(queryset.count)()

    @staticmethod
    async def aget_list_iterator(queryset: QuerySet, chuck: int = 50) -> Union[list, AsyncIterator[QuerySet]]:
        return queryset.aiterator(chunk_size=chuck)

    @staticmethod
    async def aget_list(queryset: QuerySet) -> QuerySet:
        return await sync_to_async(queryset.all)()

    @staticmethod
    async def aget_filtered_list(queryset: QuerySet, search_field: Union[str, ModelBase] = None,
                                 val: str = None) -> QuerySet:
        if isinstance(search_field, str):
            key = dict([(search_field, val)], )

        elif isinstance(search_field, ModelBase):
            pks = search_field._meta.pk_fields
            assert len(pks) == 1, "More than one primary key field"
            key = dict([(search_field._meta.pk_fields[0].__dict__.get("name"), val)], )

        return await sync_to_async(queryset.filter)(**key)

    @staticmethod
    async def get_minimal(queryset: QuerySet, sort_field: str) -> QuerySet:
        obj = await queryset.order_by(sort_field).afirst()
        return obj

    @staticmethod
    def get_last(queryset: QuerySet,
                 search_field: Union[str, Model],
                 pk: str,
                 order: Optional[str] = None) -> ModelBase:

        if isinstance(search_field, str):
            key = dict([(search_field, pk)], )

        elif isinstance(search_field, ModelBase):
            key = dict([(search_field._meta.pk_fields[0].__dict__.get("name"), pk)], )

        else:
            return
        if order:
            return queryset.filter(**key).order_by(f"{order}").last()
        else:
            return queryset.filter(**key).last()

    @staticmethod
    async def aget_sorted(queryset: QuerySet,
                          order: Optional[str] = None) -> QuerySet:
        return await sync_to_async(queryset.order_by, thread_sensitive=True)(order)

    @staticmethod
    def t_pool(func: Callable, *arg) -> Any:
        with ThreadPoolExecutor(max_workers=1) as executor:
            res = executor.submit(func, *arg)
            return res.result()


    @staticmethod
    async def async_processes_work(loop: AbstractEventLoop, func: Callable, *arg) -> Any:
        with ProcessPoolExecutor() as executor:
            if not arg:
                res = loop.run_in_executor(executor, func)
            else:
                res = loop.run_in_executor(executor, func, *arg)
            return res
