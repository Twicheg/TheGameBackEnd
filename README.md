## Задания раздельные, в первой таске нужно просто описать модели.

1. Приложение подразумевает ежедневный вход пользователя, начисление баллов за вход. Нужно отследить момент первого входа игрока для аналитики. Также у игрока имеются игровые бонусы в виде нескольких типов бустов. Нужно описать модели игрока и бустов с возможностью начислять игроку бусты за прохождение уровней или вручную. (Можно написать, применяя sqlachemy)

```python
from django.db import models

class Player(models.Model):
    pass
    

class Boost(models.Model):
    pass
```

1. Дано несколько моделей

```python
from django.db import models

class Player(models.Model):
    player_id = models.CharField(max_length=100)
    
    
class Level(models.Model):
    title = models.CharField(max_length=100)
    order = models.IntegerField(default=0)
    
    
    
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
     
     
```

Написать два метода:

1. Присвоение игроку приза за прохождение уровня.
2. Выгрузку в csv следующих данных: id игрока, название уровня, пройден ли уровень, полученный приз за уровень. Учесть, что записей может быть 100 000 и более.


## Стек
- python3.13
- drf
- adrf
- asyncio
- DjangoOrm
- gunicorn


### Инструкции для запуска
варианты запуска:

1. создать файл .env (пример в env_sample):\
запуск приложения через `docker-compose up -d`\


2. pip install -r requirements.txt  
pythom main.py



### Api Эндпоинты
* GET '/players/all name='players'
* GET '/players/csv name='players_csv'
* POST '/players/player/create name='player_create'
* GET '/players/player/<uuid:pk>' name='player'
* GET/POST '/players/player/<uuid:pk>/boost name='boost_player'
* PATCH '/players/player/<uuid:pk>/level_up name='level_up_player'
### админка:
 http://example.com/admin
\ логин: admin пароль: 12345
    
### host/admin

### Автор: https://t.me/MadbitSE