from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import UserManager


class Tenant(AbstractBaseUser):
    username = models.CharField(max_length=20, blank=False, null=False, unique=True)
    password = models.CharField(max_length=128)

    REQUIRED_FIELDS = []
    USERNAME_FIELD = "username"

    objects = UserManager()

    class Meta:
        managed = True
        unique_together = (("username",),)
