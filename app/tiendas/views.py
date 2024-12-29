
from django.shortcuts import render, get_object_or_404,HttpResponse,redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.forms import User
from django.contrib.auth import authenticate,login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, request,HttpResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from ventas import settings
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from datetime import datetime, date
import os
import json

import ast
from app.tiendas.models import *
from app.tiendas.forms import *
from app.catalog.models import Product, Orden, Pedido, Like
from app.inicio.views import get_Dashboard
from app.catalog.views import *
# Create your views here.
def getTypes(request, id_type):
    if request.user.is_authenticated:
        companys = Company.objects.filter(user_id = int(request.user.id), status=True)
    else:
        companys = Company.objects.filter(category=int(id_type), status=True)
    count_productos = {}
    for c in companys:
        count_productos[c.name] = Product.objects.filter(company_id = int(c.id)).count()
    
    request.session['compra'] = []#inicializa el carrito vacio nuevamente
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
            menj = "La cuenta: "+"<span style='color:green;'>"+request.POST['email']+"</span>"+" ya existe "
            return JsonResponse({'error':menj})
        else:
            return JsonResponse({'valido':'valido'})

def login_user(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = authenticate(username=request.POST['username'],password=request.POST['password'])
            if user is not None:
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
        #print(datos)#como dict
        #print(type(datos))#como string
        
        user = User()
        user.username = datos['user_data']['user']
        user.email = datos['user_data']['email']
        
        user.password1 = datos['user_data']['pass1']
        user.password2 = datos['user_data']['pass2']

        print("User:",datos['user_data']['user'])
        print("email:",datos['user_data']['email'])
        print("pass:", datos['user_data']['pass1'])
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

        #user_login = authenticate(username=datos['user_data']['user'],password=datos['user_data']['pass1'])
        login(request, user)

        return JsonResponse({'user_id':user.id})
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

def add_huvicacion(request, id_company):
    company = Company.objects.get(id=id_company)
    try:  
        if request.method == 'POST':
            form = FormHuvicacion(request.POST, instance=company)
            ubicacion = Sucursal()
            ubicacion.company_id = int(id_company)
            ubicacion.address = request.POST['address']
            ubicacion.latitud = request.POST['latitud']
            ubicacion.longitud = request.POST['longitud']
            ubicacion.save()
            return JsonResponse({'success':'Registro exitoso.'})
    except:
        return JsonResponse({'error':'Ys existe el registro.'})

def info_address_company(request, id_company):
    address = Sucursal.objects.get(company_id = int(id_company))
    return render(request,'notificaciones/info_address_company.html',{'address':address})

def del_address_comp(request, id_address):
    address = get_object_or_404(Sucursal, id = int(id_address))
    id_company = address.company_id
    if request.method == 'POST':
        address.delete()
        return JsonResponse({'success':"Se Borro el registro.",'id_company':id_company})
    return render(request, 'notificaciones/del_addres_company.html', {'address':address})

@login_required(login_url='/')
def configuraciones_company(request, id_company):
    pedidos = Orden.objects.filter(company_id=int(id_company)).values('client_id').order_by('-id').distinct()
    ped = []
    for p in pedidos:
        if not p in ped:
            ped.append(p)

    productos = Product.objects.filter(stock__gt=0, company_id=int(id_company)).order_by('-id')
    dic = {
        'form_huvicacion':FormHuvicacion(),
        'form_ban':FormBanco(),
        'form_precio':PrecioForm(),
        'form_avisos':Form_avisos(),
        'categorias':categorys_from_productos(productos),
        'company':get_company(id_company),
        'total_compra':len(request.session['compra']),
        'precios':Precio_envio.objects.filter(company_id=int(id_company))[:1],
        'avisos':Aviso.objects.filter(company_id = int(id_company))[:1],
        'banco':Banco.objects.filter(company_id = int(id_company))[:1],
        #'precio_env':determinarPrecioEnvio(id_company),distinct()
        #'ordens':Orden.objects.filter(company_id=int(id_company)).values('client_id').order_by('-id').distinct(),
        'ordens':ped,
        'clientes':Client.objects.all().order_by('-id'),
        'address':get_address(id_company)
    }
    return render(request,'configuraciones_company.html', dic)

def precio_envio(request, id_company):
    company = get_object_or_404(Company, id = int(id_company))
    if request.method == 'POST':
        form_precio = PrecioForm(request.POST, instance=company)
        if form_precio.is_valid():
            preci = Precio_envio()
            preci.precio = request.POST['precio']
            preci.company_id = company.id
            preci.save()
            return JsonResponse({'success':'Registro Exitoso.', 'precio':preci.precio, 'id_precio':preci.id})
        else:
            return JsonResponse({'error':'Error intente nuevamente.'})

def buscar_orden(request, id_company):
    precio_envio=determinarPrecioEnvio(id_company)
    if request.method == 'POST':
        pedidos = None
        cod = int(request.POST['codigo_orden'])
        if Orden.objects.filter(id=cod, company_id=int(id_company)).exists():
            orden = Orden.objects.get(id=cod)
            pedidos = Pedido.objects.filter(orden_id = orden.id)
        else:
            orden = None
        return render(request, 'reportes/buscar_orden.html', {'orden':orden, 'pedidos':pedidos, 'precio_envio':precio_envio})

def reportByRange(request, id_company):
    if request.method == 'POST':
        print(request.POST['startDate'], type(request.POST['startDate']))
        inicio = datetime.strptime(request.POST['startDate'], '%d-%m-%Y')
        #print(datetime.strftime(inicio, '%Y-%m-%d')) 
        final = datetime.strptime(request.POST['endDate'], '%d-%m-%Y')
        ordenes = Orden.objects.filter(company_id = int(id_company), date_joined__range=(datetime.strftime(inicio, '%Y-%m-%d'), datetime.strftime(final, '%Y-%m-%d')))
        return render(request, 'reportes/reportByRangeOrden.html', {'ordenes':ordenes})

def inventarioProductos(request, id_company):
    p = Product()
    if request.method == 'POST':
        if request.POST['criterio'] == "todos":
            productos = Product.objects.filter(company_id = int(id_company))
        elif request.POST['criterio'] == "con_stock":
            productos = Product.objects.filter(company_id = int(id_company), stock__gt = 0)
        else:
            productos = Product.objects.filter(company_id = int(id_company), stock__lte = 0)
    return render(request, 'reportes/inventarioProductos.html', {'productos':productos})

def add_avisos(request, id_company):
    company = get_object_or_404(Company, id = int(id_company))
    if request.method == 'POST':
        form_aviso = Form_avisos(request.POST, instance=company)
        if form_aviso.is_valid():
            a = Aviso()
            a.company_id = company.id
            a.Tiempo_entrega = request.POST['Tiempo_entrega']
            a.envios = request.POST['envios']
            a.pedidos = request.POST['pedidos']
            a.pide_ahora = request.POST['pide_ahora']
            a.save()
            return JsonResponse({'success':'Registro Exitoso.', 'avisos':a.toJSON()})
        else:
            return JsonResponse({'error':'Error intente nuevamente.'})

def get_opciones(request, id_company):
    avisos = Aviso.objects.filter(company_id = int(id_company))
    return render(request, 'notificaciones/get_opciones.html', {'avisos':avisos})

def del_precio(request, id_precio):
    precio = get_object_or_404(Precio_envio, id = int(id_precio))
    if request.method == 'POST':
        precio.delete()
        return JsonResponse({'success':"Se Borro el registro. "})
    return render(request, 'notificaciones/del_precio.html', {'precio':precio})

def banco_envio(request, id_company):
    company = get_object_or_404(Company, id = int(id_company))
    if request.method == 'POST':
        
        form_ban = FormBanco(request.POST, request.FILES)
        if form_ban.is_valid():
            formulario = form_ban.save(commit=False)
            formulario.company_id = company.id
            formulario.save()
            return JsonResponse({'success':'Registro Exitoso.'})
        else:
            return JsonResponse({'error':'Error intente nuevamente.'})

def infor_banco(request, id_company):
    banco = Banco.objects.filter(company_id = int(id_company))
    return render(request, 'notificaciones/infor_banco.html', {'banco':banco})

def del_infor_banco_by_company(request, id_banco):
    banco = get_object_or_404(Banco, id = int(id_banco))
    if request.method == 'POST':
        banco.delete()
        return JsonResponse({'success':"Se Borro el registro. "})
    return render(request, 'notificaciones/del_infor_banco_by_company.html', {'banco':banco})

def eliminar_opciones(request, id_aviso):
    aviso = get_object_or_404(Aviso, id = int(id_aviso))
    if request.method == 'POST':
        aviso.delete()
        return JsonResponse({'success':"Se Borro el registro. "})
    return render(request, 'notificaciones/eliminar_opciones.html', {'aviso':aviso})


def report_pdf(request, id_company, id_orden):
    precio_envio=determinarPrecioEnvio(id_company)
    company = None

    pedidos = None
    cod = int(id_orden)
    if Orden.objects.filter(id=cod, company_id=int(id_company)).exists():
        orden = Orden.objects.get(id=cod)
        company = Company.objects.get(id = int(id_company))
        pedidos = Pedido.objects.filter(orden_id = orden.id)
    else:
        orden = None

    dic = {'precio_envio':precio_envio, 'company':company, 'orden':orden, 'pedidos':pedidos}
    html = render_to_string("reportes/report_order_pdf.html", dic)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; reporte_orden.pdf"
    font_config = FontConfiguration()
    HTML(string=html).write_pdf(response)
    return response

def like_company(request, id_company, id_orden, id_cliente):
    if request.method == 'POST':
        lik = Like()
        lik.like = int(request.POST['like'])
        lik.company_id = int(id_company)
        lik.client_id = int(id_cliente)
        lik.orden_id = int(id_orden)
        lik.save()
        ruta = "/"+str(id_company)+"/catalogo" 
        print(ruta)
        return JsonResponse({'success':'Muchas gracias por su preserencia','ruta:':ruta})
    else:
        if Like.objects.filter(company_id=id_company, orden_id=id_orden, client_id=id_cliente).exists():
            ruta = str(id_company)+"/catalogo"
            dic = {
                'categorias':categorys_from_productos(productosDeCatalogo(request, id_company)),
                'total_compra':len(request.session['compra']),
                't_pago':calcular_pago(request),
                'company':get_company(id_company),
                'aviso':optener_avisos_by_company(id_company),
                'id_orden':id_orden,
                'id_cliente':id_cliente,
                'like':'Muchas gracias por su preferencia',
                'ruta:':ruta,
                'address':get_address(id_company)
            }
            return render(request, 'notificaciones/like_company.html', dic)

        else:

            dic = {
                'categorias':categorys_from_productos(productosDeCatalogo(request, id_company)),
                'productos':productosDeCatalogo(request, id_company),
                'total_compra':len(request.session['compra']),
                't_pago':calcular_pago(request),
                'company':get_company(id_company),
                'aviso':optener_avisos_by_company(id_company),
                'id_orden':id_orden,
                'id_cliente':id_cliente,
                'address':get_address(id_company)
            }
            return render(request, 'notificaciones/like_company.html', dic)


def productosDeCatalogo(request ,id_company):
    productos = Product.objects.filter(stock__gt=0, company_id=int(id_company)).order_by('-id')
    page = request.GET.get('page',1)
    try: 
        paginator = Paginator(productos, 10)
        productos = paginator.page(page)
    except:
        raise Http404
    return productos
