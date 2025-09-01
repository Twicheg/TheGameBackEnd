from datetime import datetime
from players.models import Player, PlayerLevel, Boost, Level
from rest_framework import serializers
from adrf.serializers import Serializer, ModelSerializer

from players.services import LevelService


class PlayerCreateSerializer(ModelSerializer):
    class Meta:
        model = Player
        exclude = ['last_entry', 'last_boost_date']


class LevelSerializer(ModelSerializer):
    class Meta:
        model = Level
        fields = '__all__'


class PlayerLevelSerializer(ModelSerializer):
    current_level = serializers.SerializerMethodField()

    @staticmethod
    def get_current_level(instance) -> int:
        return LevelService.get_level(instance.level_id)

    class Meta:
        model = PlayerLevel
        exclude = ['player', "level", 'id']


class BoostSerializer(ModelSerializer):
    class Meta:
        model = Boost
        exclude = ['player', "id"]


class BoostsListSerializer(ModelSerializer):
    class Meta:
        model = Boost
        exclude = ['id', 'player']


class BoostCreateSerializer(Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    duration = serializers.IntegerField()


class PlayersListSerializer(ModelSerializer):
    boost = BoostSerializer(source="boosts", many=True, read_only=True)
    player_level = PlayerLevelSerializer(source='playerlevel_set', many=True, read_only=True)
    boost_required = serializers.SerializerMethodField()


    def get_boost_required(self, obj):
        """check if 1 day has passed"""
        now = datetime.now().date()
        last_boost = obj.last_boost_date
        try:
            return (now - last_boost).days >= 1
        except TypeError:
            return True

    class Meta:
        model = Player
        fields = '__all__'


class PlayerSerializer(ModelSerializer):
    """All about player"""
    boost = BoostSerializer(source="boosts", many=True, read_only=True)
    player_levels = PlayerLevelSerializer(source='playerlevel_set', many=True, read_only=True)
    boost_required = serializers.SerializerMethodField()

    def get_boost_required(self, obj):
        """check if 1 day has passed"""
        now = datetime.now().date()
        last_boost = obj.last_boost_date
        try:
            return (now - last_boost).days >= 1
        except TypeError:
            return True

    class Meta:
        model = Player
        fields = '__all__'
