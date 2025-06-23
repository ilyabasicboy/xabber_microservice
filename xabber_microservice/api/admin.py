from django.contrib import admin
from xabber_microservice.api.models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    model = Account
