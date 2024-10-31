from django.contrib import admin

# Register your models here.
from app.catalog.models import *

admin.site.register([Category,Product, Pedido, Like])

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        'names',
        'dni',
        'mobile',
        'address',
        'date_joined',
    )
    search_fields = ('names','dni',)


@admin.register(Orden)
class OrdenAdmin(admin.ModelAdmin):
    list_display = (
        'company',
        'client',
        'subtotal',
        'dscto',
        'total',
        'date_joined',
    )
    search_fields = ('date_joined',)