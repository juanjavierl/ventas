from django.contrib import admin
# Register your models here.
from app.tiendas.models import *

admin.site.register([Banco,Company,Ciudad,Tipo_company,Plataforma, Sucursal,Precio_envio, Aviso])