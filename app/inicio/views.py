from django.db.models import Avg, Max, Min, Count

from django.shortcuts import render
from app.inicio.models import *
from app.tiendas.models import *
# Create your views here.
def inicio(request):
    type_company = Tipo_company.objects.all().order_by('-id')
    #contar todas las conpanyas q pertenecen a cada categoria
    #conpanias = Company.objects.all().order_by('-id')
    count_comp = {}
    for t_companys in type_company:
        count_comp[t_companys.name] = Company.objects.filter(category_id = int(t_companys.id)).count()
    
    dic = {
        'dashboard':get_Dashboard(),
        'type_company':type_company,
        'count_comp':count_comp
    }
    return render(request,'index.html',dic)


def get_Dashboard():
    try:
        dashboard = Dashboard.objects.get(id=1)
    except:
        dashboard = {'name':"AMCEB"}
    return dashboard