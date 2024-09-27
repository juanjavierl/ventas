from django.contrib import admin

# Register your models here.
from app.catalog.models import *

admin.site.register([Category,Product, Client, Orden, Pedido, Like])