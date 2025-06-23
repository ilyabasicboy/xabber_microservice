from django.contrib.auth.models import User
from django.db import models


class Account(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )
    jid = models.EmailField(
        unique=True
    )
    message_retention = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.jid