from django.urls import path
from players.apps import PlayerConfig
from players.views import PlayerView, BoostPlayerView, PlayerLevelUp, PlayerListView, PlayerCreateView, CSVApi

app_name = PlayerConfig.name

urlpatterns = [
    path('all', PlayerListView.as_view(), name='players'),
    path('csv', CSVApi.as_view(), name='players_csv'),
    path('player/create', PlayerCreateView.as_view(), name='player_create'),
    path('player/<uuid:pk>', PlayerView.as_view(), name='player'),
    path('player/<uuid:pk>/boost', BoostPlayerView.as_view(), name='boost_player'),
    path('player/<uuid:pk>/level_up', PlayerLevelUp.as_view(), name='level_up_player'),
]
