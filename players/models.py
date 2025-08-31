from datetime import timedelta, datetime

from asgiref.sync import sync_to_async
from django.db import models


class Player(models.Model):
    player_id = models.UUIDField(auto_created=True, max_length=100, primary_key=True, db_index=True)
    player_name = models.CharField(max_length=20, unique=True, verbose_name="Имя игрока", default="anonymous")
    last_entry = models.DateField(verbose_name="последний вход", auto_now_add=True, null=True)
    last_boost_date = models.DateField(verbose_name="последний буст", default=None, null=True)
    player_score = models.BigIntegerField(default=0)
    rewarded = models.JSONField(verbose_name="Награды", default=dict)

    @property
    async def check_boosts(self):
        boosts = await sync_to_async(self.boosts.all)()
        async for boost in boosts:
            if boost.end_time:
                if boost.end_time <= datetime.now():
                    boost.active = False
                    await boost.asave()
            else:
                await boost.adelete()
        return True

    @property
    async def remove_inactive(self):
        boosts = await sync_to_async(self.boosts.all)()
        async for boost in boosts:
            if boost.active is False:
                await boost.adelete()
        return True

    def __str__(self):
        return self.player_name

    async def set_rewards(self, rewards):
        self.rewarded["rewards"] = self.rewarded.get("rewards", []) + [rewards]
        await self.asave()
        return True

    class Meta:
        ordering = ['player_id']
        verbose_name = "Игрок"
        verbose_name_plural = "Игроки"


class Boost(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, verbose_name="усилитель", related_name="boosts",
                               null=True)
    title = models.CharField(max_length=30, verbose_name="Усиление", default=None)
    description = models.CharField(max_length=30, verbose_name="Усиление", default="None", null=True)
    active = models.BooleanField(default=True)
    get_time = models.DateTimeField(auto_now_add=False)
    end_time = models.DateTimeField(auto_now=False, null=True, default=None)

    async def asave(
            self,
            *args,
            delay_time=None,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None,
    ):
        if delay_time:
            self.end_time = self.get_time + timedelta(hours=delay_time)
        await super().asave(force_update, force_update, using, update_fields)

    def __str__(self):
        return self.title


class Level(models.Model):
    title = models.CharField(max_length=100)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title} {self.order}"


class Prize(models.Model):
    title = models.CharField()


class PlayerLevel(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    completed = models.DateField()
    is_completed = models.BooleanField(default=False)
    score = models.PositiveIntegerField(default=0)


class LevelPrize(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    prize = models.ForeignKey(Prize, on_delete=models.CASCADE)
    received = models.DateField()
