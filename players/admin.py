from django.contrib import admin
from players.models import Player, Boost, PlayerLevel, Level, Prize, LevelPrize


class BoostInline(admin.TabularInline):
    model = Boost


class LevelInline(admin.TabularInline):
    model = PlayerLevel


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ["player_id", "player_name", "last_entry"]
    search_fields = ["player_id", "player_name", "last_entry"]
    list_filter = ["player_id"]
    inlines = [BoostInline, LevelInline]


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    pass


@admin.register(Prize)
class PrizeAdmin(admin.ModelAdmin):
    pass


@admin.register(LevelPrize)
class LevelPrizeAdmin(admin.ModelAdmin):
    pass
