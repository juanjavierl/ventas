from django.db.models import Avg, Max, Min, Count
from django.http import JsonResponse, request
from django.shortcuts import render, get_object_or_404,HttpResponse,redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.forms import User
from django.contrib.auth import authenticate,login, logout
from django.contrib.auth.decorators import login_required

from app.inicio.models import *
from app.tiendas.models import *
from .forms import *

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
        dashboard = {'name':"AMCEB",'mobile':79436914}
    return dashboard

def verPlanes(request):

    dic = {
        'celular':get_Dashboard(),
        'planes':Plataforma.objects.all()
    }
    return render(request, 'verPlanes.html',dic)

def update_perfil_user(request, user_id):
    user = get_object_or_404(User, id = int(user_id))
    if request.method == 'POST':
        form = UpdateUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return JsonResponse({'success':'Datos actualizados correctamente.'})
        else:
            return JsonResponse({'error':'Error intente nuevamente.'})
    form = UpdateUserForm(instance=user)
    return render(request,'update_perfil_user.html',{'form':form})

def changePassword(request, id_user):
    if request.method=='POST':
        form=ChangePasswordForm(request.POST)
        new_password = request.POST['new_password']
        confirmed = request.POST['confirm_password']
        user = request.user
        print(user.check_password(request.POST['old_password']))
        if new_password == confirmed and user.check_password(request.POST['old_password']):
            user.set_password(new_password)
            user.save()
            print('bien')
            return JsonResponse({"success":'Bien actualizaste tus credenciales, autentificate nuevamente gracias.'})
        else:
            return JsonResponse({"error":'Los dastos son incorrectos, intente nuevamente gracias.'})
    else:
        form=ChangePasswordForm()
    return render(request,'changePassword.html',{'form':form})