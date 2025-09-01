from adrf.views import APIView
from adrf.generics import ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework.exceptions import NotFound
from players.serializers import (PlayerSerializer, PlayersListSerializer,
                                 BoostCreateSerializer, BoostsListSerializer, PlayerCreateSerializer)
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_503_SERVICE_UNAVAILABLE
from players.services import PlayerService, BoostService, PlayerLevelService, CSVService, logger
from uuid import uuid4


class PlayerListView(ListAPIView):
    """List of players"""
    serializer_class = PlayersListSerializer
    queryset = PlayerService.get_players_list()


class PlayerCreateView(CreateAPIView):
    queryset = PlayerService.get_players_list()
    serializer_class = PlayerCreateSerializer

    async def post(self, request: Request, *args, **kwargs):
        uuid = uuid4()
        request.data.update([('player_id', uuid)])
        resp = await super().post(request, *args, **kwargs)
        try:
            await PlayerLevelService.set_levels_to_fresh_player(uuid)
        except AssertionError as e:
            logger.error('The LeveL is empty',exc_info=True)
        return resp


class PlayerView(RetrieveAPIView):
    """Get all about player"""
    serializer_class = PlayerSerializer

    async def aget_object(self, *args, **kwargs):
        obj = await PlayerService.get_player(self.kwargs.get('pk'))
        if not obj:
            raise NotFound
        await PlayerService.check_last_entry(obj)
        return obj


class BoostPlayerView(APIView):
    """Boost player"""
    http_method_names = ['post', 'get']

    async def post(self, request: Request, *args, **kwargs):
        req = BoostCreateSerializer(data=request.data)
        if await PlayerService.get_player(self.kwargs.get('pk')) is None:
            raise NotFound
        if req.is_valid():
            return Response(await BoostService.create_boost(req.data,
                                                            kwargs.get("pk"),
                                                            ), status=HTTP_201_CREATED)
        return Response(req.errors)

    async def get(self, request, *args, **kwargs):
        data = await BoostService.get_boosts_list(kwargs.get("pk"))
        ser = BoostsListSerializer(instance=data, many=True)
        return Response(data=await ser.adata, status=HTTP_200_OK)


class PlayerLevelUp(APIView):
    http_method_names = ["patch"]

    async def patch(self, request: Request, *args, **kwargs):
        result = await PlayerLevelService.level_up(kwargs.get("pk"))
        if result.get("result"):
            await BoostService.boost_player(kwargs, request,
                                            title="boost",
                                            description="new level boost",
                                            duration=1)
        return Response(result, status=HTTP_200_OK)


class CSVApi(APIView):
    http_method_names = ["get"]

    async def get(self, request: Request, *args, **kwargs) -> Response:
        try:
            ready_csv = await CSVService.export_to_csv()
            response = Response(ready_csv)
            response['Content-Type'] = 'text/csv'
            response['Content-Disposition'] = 'attachment; filename="players.csv"'
            return response
        except (AssertionError) as e:
            logger.error("Something goes wrong in CSVApi", exc_info=True)
            return Response({False: "Сервис временно недоступен"}
                            , status=HTTP_503_SERVICE_UNAVAILABLE)
