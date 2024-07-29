#encoding:utf-8
#import pywhatkit
from datetime import datetime, date

from django.shortcuts import render, HttpResponse,get_object_or_404
from django.http import JsonResponse, request
from django.core.paginator import Paginator
from django.http import Http404
from django.views.generic import DeleteView, CreateView, UpdateView, TemplateView,DetailView
from django.db.models import Q
from app.tiendas.models import *
from app.catalog.models import *
from app.catalog.forms import *
# Create your views here.
def CatalogView(request, id_company):
    template_name = "sitio.html"
    if request.method == 'GET':
        productos = Product.objects.filter(stock__gt=0, id=int(id_company)).order_by('-id')
        page = request.GET.get('page',1)
        try: 
            paginator = Paginator(productos, 10)
            productos = paginator.page(page)
        except:
            raise Http404

        try:
            request.session['compra']
        except:
            request.session['compra'] = []
        #formula  (ahora-antes)/ahora*100
        dic = {
            'categorias':Category.objects.all(),
            'productos':productos,
            'paginator':paginator,
            'total_compra':len(request.session['compra']),
            't_pago':calcular_pago(request),
            'company':get_company(id_company)
        }
        return render(request,template_name, dic)

def get_company(id_company):
    try:
        company = Company.objects.get(id=int(id_company))
    except:
        company = {'name':"company"}
    return company

def optenerProducto(request, id_producto):
    p = get_object_or_404(Product,id = id_producto)
    datos = {}
    dic = {}
    data_cli = request.session['compra']
    if request.method == 'POST':
        if not request.POST['cantidad'].isdigit():
            return JsonResponse({'error': "La cantidad debe ser numerico."})
        if int(request.POST['cantidad']) > p.stock:
            menj = "La cantidad disponible en tienda es: ",p.stock
            return JsonResponse({'error': menj})
        datos['id_producto'] = int(p.id)
        datos['name'] = p.name.title()
        datos['cantidad'] = int(request.POST['cantidad'])
        datos['precio_uni'] = float(p.price)
        datos['total'] = float(int(request.POST['cantidad']) * float(p.price))
        if len(data_cli) == 0:
            data_cli.append(datos)
            request.session['compra'] = data_cli
            dic = {
                'total_compra':len(request.session['compra']),
                'cantidad':int(request.POST['cantidad']),
                'producto':p.name.title(),
                'precio_uni':float(p.price),
                'total':float(int(request.POST['cantidad']) * float(p.price)),
                'datos': request.session['compra'],
                "t_pago":calcular_pago(request)
            }
            dic['success'] = p.name.title(),", agregado al Carrito."
            return JsonResponse(dic)
        elif len(data_cli) > 0:
            for indice in range(len(data_cli)):   
                if data_cli[indice]['id_producto'] == datos['id_producto']:
                    data_cli[indice]['cantidad'] = int(data_cli[indice]['cantidad']) + int(request.POST['cantidad'])
                    data_cli[indice]['total'] = float(int(data_cli[indice]['cantidad']) * float(p.price))
                    data_cli[indice] = data_cli[indice]
                    request.session['compra'] = data_cli
                    dic['success'] = p.name.title(),", agregado al Carrito."
                    return JsonResponse(dic)
            if not datos in data_cli:
                data_cli.append(datos)
                request.session['compra'] = data_cli
                dic['total_compra'] = len(request.session['compra'])
                dic['success'] = p.name.title(),", agregado al Carrito."
                return JsonResponse(dic)
    return render(request,'catalog/OptenerProducto.html',
                    {
                        'p':p,
                        'total_compra':len(request.session['compra']),
                        'company':get_company(id_company),
                        'categorias':Category.objects.all()
                    }
                )

def add_iten(request, id_producto):
    
    if request.method == 'POST':
        print(id_producto)
        print(request.POST['cantidad'])

        return JsonResponse({'p':id_producto})

def ver_carrito(request):
    datos = request.session['compra']
    t_pago = calcular_pago(request)
    return render(request, 'catalog/ver_carrito.html',{'datos':datos,'t_pago':t_pago})

def calcular_pago(request):
    total_pago = 0
    try:
        productos = request.session['compra']
        for producto in productos:
            total_pago += float(producto['total'])

        return round(total_pago,2)
    except:
        return round(total_pago,2)
    

def vaciar_carrito(request):
    request.session['compra'] = []
    return HttpResponse(len(request.session['compra']))

def eliminarProducto(request, id_producto):#el id_producto es el indicen 
    productos = request.session['compra']
    productos.pop(int(id_producto))
    request.session['compra'] = productos
    data = {
        'cant_compras':len(request.session['compra']),
        't_pago':calcular_pago(request)
    }
    return JsonResponse(data)

def shear_product(request):
    if request.method=="POST":
        texto=request.POST["search"]
        busqueda=(
            Q(name__icontains=texto) |
            Q(description__icontains=texto) |
            Q(code__icontains=texto)
        )
        productos=Product.objects.filter(busqueda).distinct()
        return render(request,'catalog/card_productos.html',{'productos':productos,'company':get_company(id_company)})
    else:
        texto=request.GET["search"]
        busqueda=(
            Q(name__icontains=texto) |
            Q(description__icontains=texto) |
            Q(code__icontains=texto)
        )
        productos=Product.objects.filter(busqueda).distinct()
        return render(request,'catalog/card_productos.html',{'productos':productos,'company':get_company(id_company)})

def mostrar_por_categoria(request, id_categoria):
    productos = Product.objects.filter(category = id_categoria)
    return render(request, 'catalog/card_productos.html', {'productos':productos,'company':get_company(id_company)})


def confirmar_compra(request):
    if request.method == 'POST':
        if not request.POST['dni'].isdigit():
            return JsonResponse({'error': "El Nro de Nit/CI debe ser numérico."})
        if not request.POST['mobile'].isdigit():
            return JsonResponse({'error': "El Nro de Celular debe ser numérico."})
        forms=ClientFormOrder(request.POST)

        if request.POST['tipo_envio'] == 'tienda':
            print(request.POST['date_time'])
            print(type(request.POST['date_time']))

            valor = request.POST['date_time'].split("T")
            valor = " ".join(valor)#'2024,06,23 13:58'

            d = datetime.strptime(request.POST['date_time']+":00", '%Y-%m-%dT%H:%M:%S')
            if d < datetime.now():
                return JsonResponse({'error':"Por favor, Ingrese una hora más adelantado"})
            else:
                fecha = datetime.strftime(d,'%A %d/%m/%y hora: %H:%M %p')
                print(type(d))
                lugar = {'fecha':fecha,'date':'date'}

        elif request.POST['tipo_envio'] == 'domicilio':
            lugar = {'direccion':request.POST['address'],'dir':'dir'}

        elif request.POST['tipo_envio'] == 'ciudad':
            lugar = {'destino':request.POST['destino'],'cuidad':'cuidad'}
        else:
            return JsonResponse({'error': "Por favor complete sus datos."})
        try:#si ya existe ese cliente
            print("ya existe ese cliente")
            cliente = Client.objects.get(dni = int(request.POST['dni']))
            orden = crear_orden(cliente.id)#se crea una orden
            for productos in request.session['compra']:#[{'id_producto':12,'cantidad':1},{'id_producto':10,'cantidad':2}]
                pedido = Pedido()
                pedido.orden_id = int(orden.id)
                pedido.product_id = int(productos['id_producto'])
                pedido.cant = int(productos['cantidad'])
                pedido.price = float(productos['precio_uni'])
                pedido.total = float(int(productos['cantidad']) * float(productos['precio_uni']))
                pedido.save()
            lista_product = request.session['compra']
            t_pago = calcular_pago(request)
            request.session['compra'] = []#cuando al cliente confirma su pedido se resetea al carrito a 0
            return JsonResponse(
                        {
                            'company':orden.company.name,
                            'cliente':orden.client.names,
                            'lugar':lugar,
                            'cel_company':orden.company.mobile,
                            'products':len(request.session['compra']),
                            'success':"Bien, tu pedido a sido registrado. <a href='/'> Ir al Inicio</a>",
                            'lista':lista_product,#envio lasession en la variable lista_product
                            't_pago':t_pago
                        }
                    )
        except Client.DoesNotExist:
            print("NO existe ese cliente")
            if forms.is_valid():
                cliente = forms.save(commit=False)
                cliente.save()
                orden = crear_orden(cliente.id)
                for productos in request.session['compra']:#[{'id_producto':12,'cantidad':1},{'id_producto':10,'cantidad':2}]
                    pedido = Pedido()
                    pedido.orden_id = int(orden.id)
                    pedido.product_id = int(productos['id_producto'])
                    pedido.cant = int(productos['cantidad'])
                    pedido.price = float(productos['precio_uni'])
                    pedido.total = float(int(productos['cantidad']) * float(productos['precio_uni']))
                    pedido.save()
                t_pago = calcular_pago(request)
                lista_product = request.session['compra']
                request.session['compra'] = []#cuando al cliente confirma su pedido se resetea al carrito a 0
                return JsonResponse(
                            {
                                'company':orden.company.name,
                                'cel_company':orden.company.mobile,
                                'cliente':orden.client.names,
                                'lugar':lugar,
                                'products':len(request.session['compra']),
                                'success':"En hora buena realizaste tu pedido.<a href='/'> Ir al Inicio</a>",
                                'lista':lista_product,
                                't_pago':t_pago
                            }
                        )
    dic = {
        'form':ClientFormOrder(),
        'total_compra':len(request.session['compra']),
        'company':get_company(id_company),
        'categorias':Category.objects.all(),
        'datos':request.session['compra'],
         "t_pago":calcular_pago(request)
    }
    return render(request,'catalog/confirmar_compra.html',dic)

def crear_orden(id_cliente):
    orden = Orden()
    orden.client_id = int(id_cliente)
    orden.company_id = int(get_company(id_company).id)
    orden.total = float(calcular_pago(request))
    orden.save()
    return orden

def newProducto(request):

    form = formProducto()
    
    return render(request, 'catalog/newProducto.html',{'form':form})
