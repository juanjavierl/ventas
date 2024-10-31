from django.contrib import admin
# Register your models here.
from app.tiendas.models import *

from import_export import resources
from import_export.admin import ImportExportModelAdmin



admin.site.register([Banco,Ciudad,Tipo_company,Plataforma, Sucursal,Precio_envio, Aviso])


class CompanyResource(resources.ModelResource):

    class Meta:
        model = Company

@admin.register(Company)
class CompanyAdmin(ImportExportModelAdmin):
    resource_class = CompanyResource
    list_display = (
        'name',
        'category',
        'ruc',
        'address',
        'mobile',
        'cuidad',
        'date_joined',
        'plan',
    )
    search_fields = ('name','ruc',)
    list_filter = ('plan',)
