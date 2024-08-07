
from django.shortcuts import render, get_object_or_404,HttpResponse,redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.forms import User
from django.contrib.auth import authenticate,login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, request,HttpResponse
import json

import ast
from app.tiendas.models import *
from app.tiendas.forms import *
from app.catalog.models import Product
from app.inicio.views import get_Dashboard
# Create your views here.
def getTypes(request, id_type):
    if request.user.is_authenticated:
        companys = Company.objects.filter(user_id = int(request.user.id))
    else:
        companys = Company.objects.filter(category=int(id_type))
    count_productos = {}
    for c in companys:
        count_productos[c.name] = Product.objects.filter(company_id = int(c.id)).count()

    dic = {
        'category':getType(id_type),
        'companys':companys,
        'dashboard':get_Dashboard(),
        'count_productos':count_productos
    }
    return render(request, 'card_companys.html', dic)


def getType(id_type):
    try:
        companys = Tipo_company.objects.get(id=int(id_type))
    except:
        companys = {'name':"company"}
    return companys

def registro_company(request):
    form_user = RegisterForm()
    form_company = formCompany()
    planes = Plataforma.objects.all().order_by('-id')
    dic = {
        'form_user':form_user,
        'form_company':form_company,
        'planes':planes
        }
    return render(request, 'registro_company.html' , dic)

def validar_form(request):
    if request.method == "POST":
        formulario = formCompany(data=request.POST)
        if formulario.is_valid():
            return JsonResponse({'formulario':True})
        else:
            return JsonResponse({'error':'Los Datos con * son requeridos'})

def validar_username(request):
    if request.method == "POST":
        if User.objects.filter(email = request.POST['email']).exists():
            menj = "La cuenta: "+request.POST['email']+" ya existe " + " <a href='/login/'>Iniciar Sesion</a>"
            return JsonResponse({'error':menj})
        else:
            return JsonResponse({'valido':'valido'})

def login_user(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = authenticate(username=request.POST['username'],password=request.POST['password'])
            if user is not None:
                print("TE AUTENTICASTE EN EL SISTEMA")
                login(request, user)
                return JsonResponse({'user_id':int(user.id)})
            else:
                return JsonResponse({'error':'Contactese con el administrador para resolver el problema gracias.'})
        else:
            return JsonResponse({'error':'Datos incorrectos intente nuevamente gracias.'})
    
    form = AuthenticationForm()
    dic = {'form':form}
    return render(request, 'form_login.html', dic)

def salir(request):
    logout(request)
    return redirect('/')

def get_img_plan(request, id_plan):
    img = get_object_or_404(Plataforma, id = id_plan)
    #print(img.qr_img)retorna la ruta de la imagen como cadena
    return HttpResponse(json.dumps(str(img.qr_img)))


def datos_registro(request):
    if request.method == "POST":
        datos = request.POST['valores']
        """ print(datos)#{user_data: {…}, company_data: {…}, plan_data: {…}}
        print(type(datos))#como string
        print("*"*50)"""

        datos = ast.literal_eval(datos)
        print(datos)#como dict
        print(type(datos))#como string
        
        user = User()
        user.username = datos['user_data']['user']
        user.email = datos['user_data']['email']
        user.password1 = datos['user_data']['pass1']
        user.password2 = datos['user_data']['pass2']
        user.save()
        
        company = Company()
        company.name = datos['company_data']['name']
        company.description = datos['company_data']['description']
        company.ruc = datos['company_data']['ruc']
        company.address = datos['company_data']['address']
        company.mobile = datos['company_data']['mobile']
        company.category_id = datos['company_data']['category']
        company.cuidad_id = datos['company_data']['cuidad']
        company.user_id = int(user.id)
        #company.image =  datos['company_data']['image']#no se puedo guardar la imagen
        company.plan_id = datos['plan_data']['plan_name']
        company.save()
        print(datos['user_data']['user'])
        print(datos['user_data']['pass1'])
        print(company.id)
        user_login = authenticate(username=datos['user_data']['user'],password=datos['user_data']['pass1'])
        print(user_login)

        login(request, user_login)
        return JsonResponse({'company_id':company.id})
        #else:
            #return JsonResponse({'error': 'Up. algo salio mal intentalo nuevamente gracias.'})

def contar_productos(id_user):
    companys = Company.objects.filter(user_id = int(id_user))
    count_productos = {}
    for c in companys:
        count_productos[c.name] = Product.objects.filter(company_id = int(c.id)).count()
    return count_productos

def companys_from_user(request, user_id):
    companys = Company.objects.filter(user_id = int(user_id))
    dic = {
        'companys':companys,
        'dashboard':get_Dashboard(),
        'count_productos':contar_productos(int(user_id))
    }
    return render(request, 'card_companys.html', dic)

def updateCompany(request, id_company):
    company = Company.objects.get(id=id_company)
    if request.method=='POST':
        form=formCompanyImage(request.POST, request.FILES,instance=company)
        if form.is_valid():
            form.save()
            return JsonResponse({'companys_from_user':request.user.id})
    else:
        form=formCompanyImage(instance=company)
        return render(request,'updateCompany.html',{'form':form,'company':company})

def deleteCompany(request, id_company):
    company = get_object_or_404(Company, id=int(id_company))
    if request.method == 'POST':
        company.delete()
        return JsonResponse({'companys_from_user':request.user.id})
    return render(request,'deleteCompany.html',{'company':company})

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