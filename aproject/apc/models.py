from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class Query(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    query = models.TextField(verbose_name="Запрос")
    time_create = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    time_update = models.DateTimeField(auto_now=True, verbose_name="Время изменения")

    def __str__(self):
        return str(self.user)+ ": " + self.query


    class Meta:
        verbose_name = 'Запрос'
        verbose_name_plural = 'Запросы'
