from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    name     = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    concerns = models.JSONField(default=list)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.username} — {self.location}"