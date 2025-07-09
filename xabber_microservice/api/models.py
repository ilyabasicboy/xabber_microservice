from django.db import models


class Account(models.Model):

    jid = models.EmailField(
        unique=True
    )
    message_retention = models.IntegerField(
        default=0
    )
    unlimited = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.jid