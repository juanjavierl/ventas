from django.contrib import admin
from datetime import datetime, date
# Register your models here.
from app.tiendas.models import *

from import_export import resources
from import_export.admin import ImportExportModelAdmin

admin.site.register([Banco,Ciudad,Tipo_company,Plataforma, Sucursal,Precio_envio, Aviso])

""" class companias_expirados(admin.SimpleListFilter):
    #queryset = queryset.filter(expiration_date__lt=date.today())
    title = "Expirados"
    parameter_name = "Catalogos Expirados"
    
    def lookups(self, request, model_admin):
        return (
            (date.today(), 'Catalogos Expirados'),
        )
    
    def queryset(self, request, queryset):
        queryset = queryset.filter(expiration_date__gt=date.today())
        print(queryset)
        return queryset
 """
#companias_expirados.short_description = 'Catalogos Expirados'

class CompanyResource(resources.ModelResource):

    class Meta:
        model = Company

@admin.register(Company)
class CompanyAdmin(ImportExportModelAdmin):
    resource_class = CompanyResource
    list_display = (
        'id',
        'name',
        'date_joined',
        'plan',
        'status',
        'expiration_date',
        'ruc',
        'address',
        'mobile',
        'cuidad'
    )
    search_fields = ('name','ruc','id',)
    list_filter = ('plan',)
    #actions = [companias_expirados]
