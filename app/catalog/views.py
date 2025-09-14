#encoding:utf-8
#import pywhatkit
from datetime import datetime, date, timedelta

from django.shortcuts import render, HttpResponse,get_object_or_404, redirect
from django.http import JsonResponse, request
from django.core.paginator import Paginator
from django.http import Http404
from django.views.generic import DeleteView, CreateView, UpdateView, TemplateView,DetailView
from django.db.models import Q
from app.tiendas.models import *
from app.catalog.models import *
from app.catalog.forms import *
from app.inicio.views import get_Dashboard
# Create your views here.
def CatalogView(request, id_company):
    template_name = "sitio.html"
    if request.method == 'GET':
        #productos = Product.objects.filter(company_id=int(id_company)).order_by('-id')
        productos = Product.objects.filter(company_id=int(id_company)) \
            .select_related('category') \
            .order_by('category__name', '-id')
        page = request.GET.get('page',1)
        try:
            categorys = categorys_from_productos(productos)
            paginator = Paginator(productos, 10)
            productos = paginator.page(page)
        except:
            raise Http404
        try:
            request.session['compra']
        except:
            request.session['compra'] = []

        date_expiration = False
        try:
            if(get_company(id_company).expiration_date < datetime.now().date()):
                date_expiration = True
        except:
            return redirect("/")
        dic = {
            'categorias':categorys,
            'productos':productos,
            'paginator':paginator,
            'total_compra':len(request.session['compra']),
            't_pago':calcular_pago(request),
            'company':get_company(id_company),
            'aviso':optener_avisos_by_company(id_company),
            'dashboard':get_Dashboard(),
            'date_expiration':date_expiration,
            'address':get_address(id_company),
            'code':get_code_meta(id_company)
        }
        return render(request,template_name, dic)

def get_address(id_company):
    try:
        address = Sucursal.objects.get(company_id=int(id_company))
    except:
        address = False
    return address

def get_code_meta(id_company):
    try:
        address = PixelMeta.objects.get(company_id=int(id_company))
    except:
        address = False
    return address

def get_rule_condicion(id_company):
    try:
        reglas = Condicion.objects.get(company_id=int(id_company))
    except:
        reglas = False
    return reglas

def getBanco(id_company):
    try:
        banco = Banco.objects.get(company_id=int(id_company))
    except:
        banco = False
    return banco

def optener_avisos_by_company(id_company):
    try:
        aviso = Aviso.objects.get(company_id=int(id_company))
    except:
        aviso = False
    return aviso

def categorys_from_productos(productos):
    ct = []
    for p in productos:
        if not {'id':p.category.id, 'name':p.category.name} in ct:
            ct.append({'id':p.category.id, 'name':p.category.name})
    return ct

def get_company(id_company, user=None):
    company = get_object_or_404(Company, id=int(id_company))

    # Verificar que el usuario logueado sea el dueño
    if user is not None and company.user != user:
        raise Http404("Empresa no encontrada")

    return company

def optenerProducto(request, id_producto, id_company):
    productos = Product.objects.filter(company_id = int(id_company))
    p = get_object_or_404(Product,id = id_producto)
    datos = {}
    dic = {}
    try:
        data_cli = request.session['compra']
    except:
        request.session['compra'] = []
    if request.method == 'POST':
        if not request.POST['cantidad'].isdigit():
            return JsonResponse({'error': "La cantidad debe ser numerico."})
        #if int(request.POST['cantidad']) > p.stock:
        if p.stock_actual() <= 0:
            return JsonResponse({'error': 'Producto Agotado...!'})
        datos['id_producto'] = int(p.id)
        datos['name'] = p.name.title()
        datos['cantidad'] = int(request.POST['cantidad'])
        datos['precio_uni'] = float(p.price)
        datos['total'] = float(int(request.POST['cantidad']) * float(p.price))

        tiene_nota = request.POST.get('is_nota',False) == 'on'#verificamos si su pedido tiene una nota
        if tiene_nota:
            datos['nota'] = request.POST['nota']
        else:
            datos['nota'] = ""

        if len(data_cli) == 0:#cuanoo el carrido esta vasio
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
            dic['success'] = p.name.title()," agregado al Carrito."
            return JsonResponse(dic)
        elif len(data_cli) > 0:#cuando el carrito ya tiene compras
            for indice in range(len(data_cli)):   
                if data_cli[indice]['id_producto'] == datos['id_producto']:
                    data_cli[indice]['cantidad'] = int(data_cli[indice]['cantidad']) + int(request.POST['cantidad'])
                    data_cli[indice]['total'] = float(int(data_cli[indice]['cantidad']) * float(p.price))
                    data_cli[indice] = data_cli[indice]
                    request.session['compra'] = data_cli
                    dic['success'] = p.name.title()," agregado al Carrito."
                    return JsonResponse(dic)
            if not datos in data_cli:#verifica si el producto aun no esta en la sesion
                data_cli.append(datos)
                request.session['compra'] = data_cli
                dic['total_compra'] = len(request.session['compra'])
                dic['success'] = p.name.title()," agregado al Carrito."
                return JsonResponse(dic)
    else:
        context = { 'p':p,
                    'total_compra':len(request.session['compra']),
                    'company':get_company(id_company),
                    'categorias':categorys_from_productos(productos),
                    'aviso':optener_avisos_by_company(id_company),
                    'productos':productosMasVistos(id_company),
                    'address':get_address(id_company),
                    'images_product':Imagen.objects.filter(items_id = int(id_producto)),
                    'code':get_code_meta(id_company)
                }
    return render(request,'catalog/OptenerProducto.html',context)

def add_iten(request, id_producto):
    
    if request.method == 'POST':
        print(id_producto)
        print(request.POST['cantidad'])

        return JsonResponse({'p':id_producto})

def ver_carrito(request, id_company):
    company = get_object_or_404(Company, id=id_company)
    datos = request.session['compra']
    t_pago = calcular_pago(request)
    return render(request, 'catalog/ver_carrito.html',{'datos':datos,'t_pago':t_pago, 'company':company})

def show_productos_carrito(request, id_company):
    company = get_object_or_404(Company, id=id_company)
    datos = request.session['compra']
    t_pago = calcular_pago(request)
    regla = get_rule_condicion(id_company)
    return render(request, 'catalog/show_productos_carrito.html',{'datos':datos,'t_pago':t_pago, 'company':company, 'regla':regla})


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
    #calcular nuevamente
    data = {
        'cant_compras':len(request.session['compra']),
        't_pago':calcular_pago(request)
    }
    return JsonResponse(data)

def actualizarCantidad(request):
    cantidad = request.GET['cantidad']
    indice = request.GET['indice']
    productos = request.session['compra']
    productos[int(indice)]['cantidad'] =  int(productos[int(indice)]['cantidad']) + int(cantidad)
    productos[int(indice)]['total'] = int(productos[int(indice)]['precio_uni']) * int(productos[int(indice)]['cantidad'])
    #print(productos[int(indice)]['precio_uni'], " X ", productos[int(indice)]['cantidad'])
    request.session['compra'] = productos
    data = {
        'cant_compras':len(request.session['compra']),
        't_pago':calcular_pago(request)
    }
    return JsonResponse(data)

def shear_product(request, id_company):
    if request.method=="POST":
        texto=request.POST["search"]
        busqueda=(
            Q(name__icontains=texto) |
            Q(description__icontains=texto) |
            Q(code__icontains=texto)
        )
        productos=Product.objects.filter(busqueda,stock__gt=0, company_id=int(id_company)).distinct()
        return render(request,'catalog/card_productos.html',{'productos':productos,'company':get_company(id_company)})
    else:
        texto=request.GET["search"]
        busqueda=(
            Q(name__icontains=texto) |
            Q(description__icontains=texto) |
            Q(code__icontains=texto)
        )
        productos=Product.objects.filter(busqueda,stock__gt=0, company_id=int(id_company)).distinct()
        return render(request,'catalog/card_productos.html',{'productos':productos,'company':get_company(id_company)})

def mostrar_por_categoria(request, id_company, id_categoria):
    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return redirect(f'/{id_company}/catalogo')
    productos = Product.objects.filter(stock__gt=0, category_id = id_categoria, company_id= id_company).order_by('-id')
    return render(request, 'catalog/card_productos.html', {'productos':productos,'company':get_company(id_company)})

def confirmar_compra(request, id_company):
    company = get_object_or_404(Company, id = id_company)
    t_pago = calcular_pago(request)#total a pagar de todo el carrito
    try:
        total_compra = len(request.session['compra'])
        datos = request.session['compra']
    except:
        total_compra = 0
        datos = []
    if request.method == 'POST':
        if request.POST['email'] == " ":
            return JsonResponse({'error': "Por favor ingrese su email."})
        if not request.POST['mobile'].isdigit():
            return JsonResponse({'error': "El Nro de Celular debe ser numérico."})
        forms=ClientFormOrder(request.POST)

        if request.POST['tipo_envio'] == 'tienda':
            precio_envio = 0
            ref = 'tienda'
            valor = request.POST['date_time'].split("T")
            valor = " ".join(valor)#'2024,06,23 13:58'
            d = datetime.strptime(request.POST['date_time']+":00", '%Y-%m-%dT%H:%M:%S')
            if d < datetime.now():
                return JsonResponse({'error':"Error: La fecha debe ser mayor o igual a hoy"})
            else:
                dias={0:'Lunes',1:'Martes',2:'Miercoles',3:'Jueves',4:'Viernes',5:'Sabado',6:'Domingo'}
                dia = dias[d.weekday()]
                fecha = datetime.strftime(d, dia + ' %d/%m/%y hora: %H:%M %p')
                lugar = {'fecha':fecha,'date':'date'}
        elif request.POST['tipo_envio'] == 'domicilio':
            lugar = {'direccion':request.POST['address'],'dir':'dir'}
            precio_envio = determinarPrecioEnvio(id_company)
            ref = 'domicilio'

        elif request.POST['tipo_envio'] == 'ciudad':
            lugar = {'destino':request.POST['destino'],'cuidad':'cuidad'}
            precio_envio = determinarPrecioEnvioCiudad(id_company)
            ref = 'ciudad'
        else:
            return JsonResponse({'error': "Por favor complete sus datos."})
        #try:#si ya existe ese cliente
        if Client.objects.filter(email = request.POST['email']).exists():
            cliente = Client.objects.get(email = request.POST['email'])
            orden = crear_orden(request, cliente.id, id_company, ref)#se crea una orden
            for productos in request.session['compra']:#[{'id_producto':12,'cantidad':1},{'id_producto':10,'cantidad':2}]
                pedido = Pedido()
                pedido.orden_id = int(orden.id)
                pedido.product_id = int(productos['id_producto'])
                pedido.cant = int(productos['cantidad'])
                pedido.price = float(productos['precio_uni'])
                pedido.total = float(int(productos['cantidad']) * float(productos['precio_uni']))
                pedido.nota = productos['nota']
                pedido.save()

                if not getProducto(int(productos['id_producto'])).is_service:
                    cantProductos = getProducto(int(productos['id_producto'])).salida
                    Product.objects.filter(id=int(productos['id_producto'])).update(salida=int(cantProductos)+int(productos['cantidad']))
            
            lista_product = request.session['compra']
            request.session['compra'] = []#cuando al cliente confirma su pedido se resetea al carrito a 0
            return JsonResponse(
                        {
                            'cliente_object':cliente.toJSON(),
                            'company_object':company.toJSON(),
                            'orden':orden.toJSON(),
                            'lugar':lugar,
                            'products':len(request.session['compra']),
                            'success':"Bien, tu pedido a sido registrado.",
                            'lista':lista_product,#envio lasession en la variable lista_product
                            't_pago':t_pago,
                            'precio_envio':determinarPrecioEnvio(id_company),
                            'precio_envio_ciudad':determinarPrecioEnvioCiudad(id_company)
                        }
                    )
        #except Client.DoesNotExist:
        else:
            if forms.is_valid():
                cliente = forms.save(commit=False)
                cliente.save()
                orden = crear_orden(request, cliente.id, id_company, ref)
                for productos in request.session['compra']:#[{'id_producto':12,'cantidad':1},{'id_producto':10,'cantidad':2}]
                    pedido = Pedido()
                    pedido.orden_id = int(orden.id)
                    pedido.product_id = int(productos['id_producto'])
                    pedido.cant = int(productos['cantidad'])
                    pedido.price = float(productos['precio_uni'])
                    pedido.total = float(int(productos['cantidad']) * float(productos['precio_uni']))
                    pedido.nota = productos['nota']
                    pedido.save()
                    
                    if not getProducto(int(productos['id_producto'])).is_service:
                        cantProductos = getProducto(int(productos['id_producto'])).salida
                        Product.objects.filter(id=int(productos['id_producto'])).update(salida=int(cantProductos)+int(productos['cantidad']))

                lista_product = request.session['compra']
                request.session['compra'] = []#cuando al cliente confirma su pedido se resetea al carrito a 0
                return JsonResponse(
                            {
                                'company_object':company.toJSON(),
                                'cliente_object':cliente.toJSON(),
                                'orden':orden.toJSON(),
                                'lugar':lugar,
                                'products':len(request.session['compra']),
                                'success':"En hora buena realizaste tu pedido.",
                                'lista':lista_product,
                                't_pago':t_pago,
                                'precio_envio':determinarPrecioEnvio(id_company),
                                'precio_envio_ciudad':determinarPrecioEnvioCiudad(id_company)
                            }
                        )

    dic = {
        'form':ClientFormOrder(),
        'total_compra':total_compra,
        'company':get_company(id_company),
        'categorias':categorys_from_productos(productosMasVistos(id_company)),
        'datos':datos,
        't_pago':t_pago,
        'productos':productosMasVistos(id_company),
        'aviso':optener_avisos_by_company(id_company),
        'address':get_address(id_company),
        'regla':get_rule_condicion(id_company),
        'code':get_code_meta(id_company),
        'ahora':(datetime.now() + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M"),  # fecha y hora actual en tu zona
        'limite': (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%dT%H:%M")  # fecha dentro de 30 días
    }
    return render(request,'catalog/confirmar_compra.html',dic)

def confirmarCita(request, id_company, id_producto):
    p = get_object_or_404(Product,id = id_producto)
    company = get_object_or_404(Company, id = id_company)
    datos={}
    data_cli = []
    datos['id_producto'] = int(p.id)
    datos['name'] = p.name.title()
    datos['cantidad'] = 1
    datos['precio_uni'] = 0.0
    datos['total'] = 0.0
    data_cli.append(datos)

    if request.method == 'POST':
        if not request.POST['dni'].isdigit():
            return JsonResponse({'error': "El Nro de Nit/CI debe ser numérico."})
        if not request.POST['mobile'].isdigit():
            return JsonResponse({'error': "El Nro de Celular debe ser numérico."})

        d = datetime.strptime(request.POST['date_time']+":00", '%Y-%m-%dT%H:%M:%S')
        if d < datetime.now():
            return JsonResponse({'error':"Error: La fecha debe ser mayor o igual a hoy"})
        else:
            dias={0:'Lunes',1:'Martes',2:'Miercoles',3:'Jueves',4:'Viernes',5:'Sabado',6:'Domingo'}
            dia = dias[d.weekday()]
            fecha = datetime.strftime(d, dia + ' %d/%m/%y hora: %H:%M %p')
            lugar = {'fecha':fecha,'date':'date'}
        forms=ClientFormOrder(request.POST)
        if Client.objects.filter(dni = int(request.POST['dni'])).exists():
            cliente = Client.objects.get(dni = int(request.POST['dni']))
            orden = crear_orden(request, cliente.id, id_company)

            pedido = Pedido.objects.create(orden_id = int(orden.id),product_id=int(datos['id_producto']),cant=int(datos['cantidad']),price=float(datos['precio_uni']),total=float(int(datos['cantidad']) * float(datos['precio_uni'])))
            pedido.save()
        else:
            if forms.is_valid():
                cliente = forms.save(commit=False)
                cliente.save()
                orden = crear_orden(request, cliente.id, id_company)
                pedido = Pedido.objects.create(orden_id = int(orden.id),product_id=int(datos['id_producto']),cant=int(datos['cantidad']),price=float(datos['precio_uni']),total=float(int(datos['cantidad']) * float(datos['precio_uni'])))
                pedido.save()
        try:
            lugar = get_address(id_company).toJSON()
        except:
            lugar = False
        return JsonResponse(
                            {
                                'company':company.name,
                                'company_object':company.toJSON(),
                                'cel_company':company.mobile,
                                'cliente_object':cliente.toJSON(),
                                'orden':orden.id,
                                'lista':data_cli,
                                'lugar':lugar,
                                'success':"Tu cita se completo exitosamente gracias."
                            }
                        )
    dic = {
        'form':ClientFormOrder(),
        'company':get_company(id_company),
        'categorias':categorys_from_productos(productosMasVistos(id_company)),
        'datos':data_cli,
        'productos':productosMasVistos(id_company),
        'precio_envio':determinarPrecioEnvio(id_company),
        'aviso':optener_avisos_by_company(id_company),
        'address':get_address(id_company),
        'producto':p
    }
    return render(request,'catalog/confirmar_cita.html',dic)

def getProducto(id_producto):
    producto = Product.objects.get(id = id_producto)
    return producto

def productosMasVistos(id_company):
    productos = Product.objects.filter(stock__gt=0, company_id=id_company, is_promotion=True)
    return productos

def determinarPrecioEnvio(id_company):
    try:
        p_envio = Precio_envio.objects.get(company_id=int(id_company))
        return p_envio.precio
    except:
        p_envio = 0
        return p_envio#QUIERO ENVIAR SOLO EL PRECIO AL TEMPLATE

def determinarPrecioEnvioCiudad(id_company):
    try:
        p_envio = Precio_envio.objects.get(company_id=int(id_company))
        return p_envio.precio_ciudad
    except:
        p_envio = 0
        return p_envio#QUIERO ENVIAR SOLO EL PRECIO AL TEMPLATE

def crear_orden(request, id_cliente, id_company, ref = 'tienda'):
    if ref == 'tienda':
        pr_envio = 0
    elif ref == 'domicilio':
        pr_envio = determinarPrecioEnvio(id_company)
    elif ref == 'ciudad':
        pr_envio = determinarPrecioEnvioCiudad(id_company)
    else:
        pr_envio = 0
    orden = Orden()
    orden.client_id = int(id_cliente)
    orden.company_id = int(id_company)
    orden.subtotal = float(calcular_pago(request))
    orden.total = float(calcular_pago(request)) + pr_envio
    orden.save()
    return orden

def newProducto(request, id_company):
    company = get_object_or_404(Company,id = int(id_company))
    aviso = False
    date_expiration = False
    cantProductos = cantProductosByCompany(id_company)
    if request.method == 'POST':
        new = request.POST.get('is_new', False) == 'on'
        if new == 'on':
            new = True
        service = request.POST.get('is_service',False) == 'on'
        if service == 'on':
            service = True
        promotion = request.POST.get('is_promotion',False) == 'on'
        if promotion == 'on':
            promotion = True

        producto = Product()
        producto.name = request.POST['name']
        producto.code = request.POST['code']
        producto.description = request.POST['description']
        producto.category_id = int(request.POST['category'])
        producto.company_id = int(id_company)
        producto.price = float(request.POST['price'])
        producto.price_before = float(request.POST['price_before'])
        producto.stock = request.POST['stock']
        producto.image = request.FILES.get('image','')
        producto.is_service = service
        producto.is_new = new
        producto.is_promotion = promotion
        if  int(cantProductos) >= int(company.plan.cantidad) or (get_company(id_company).expiration_date < datetime.now().date()):
            aviso = True
            date_expiration = True
            return JsonResponse({'error':'Alcansaste el limite de registros para este plan. o la fecha ha caducado','aviso':aviso, 'date_expiration':date_expiration})
        else:
            producto.save()
            return JsonResponse({'success':'Producto registrado exitosamente.','aviso':aviso, 'date_expiration':date_expiration})
    form = formProducto()

    if int(cantProductos) >= int(company.plan.cantidad):
        aviso = True
    if get_company(id_company).expiration_date < datetime.now().date():
        date_expiration = True
    
    categorys = Category.objects.all().order_by('-id')
    return render(request, 'catalog/newProducto.html',{'form':form,'company':company,'categorys':categorys, 'aviso':aviso, 'date_expiration':date_expiration})

def cantProductosByCompany(id_company):
    cantidad = Product.objects.filter(company_id = int(id_company)).count()
    return cantidad

def newCategory(request):
    if request.method == 'POST':
        form = formCategory(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.save()
            return JsonResponse({'category_name':cat.name, 'category_id':cat.id})
        else:
            return JsonResponse({'error':'La Categoria ya Existe o Datos Invalidos.'})
    form = formCategory()
    return render(request, 'catalog/newCategory.html',{'form':form})

def updateProduct(request, id_product):
    product = Product.objects.get(id=id_product)
    if request.method=='POST':
        form=formUpdateProducto(request.POST, request.FILES,instance=product)
        if form.is_valid():
            form.save()
            return JsonResponse({'id_company':product.company.id})
    else:
        form=formUpdateProducto(instance=product)
        return render(request, 'catalog/updateProduct.html',{'form':form,'product':product})

def deleteProduct(request, id_product):
    product = get_object_or_404(Product, id=int(id_product))
    if request.method == 'POST':
        product.delete()
        return JsonResponse({'id_company':product.company.id})
    return render(request,'catalog/deleteProduct.html',{'product':product})

def updateStock(request, id_product):
    product = get_object_or_404(Product, id=int(id_product))
    if request.method=='POST':
        if int(request.POST['incremento']) > 0 and int(request.POST['decremento']) == 0:
            cant = int(request.POST['incremento'])

            Product.objects.filter(id=id_product).update(stock = int(product.stock) + cant)
            return JsonResponse({'success':'Bien Stock Actualizado'})
        elif int(request.POST['incremento']) == 0 and int(request.POST['decremento']) > 0:
            cant = int(request.POST['decremento'])
            Product.objects.filter(id=id_product).update(salida =  cant + int(abs(product.salida)))

            return JsonResponse({'success':'Bien Stock Actualizado'})
        else:
            return JsonResponse({'error':'Los datos estan en 0, ingrese una cantidad.'})
    else:
        return render(request, 'catalog/updateStock.html',{'p':product})

def imgs_products(request, id_producto):
    product = Product.objects.get(id=id_producto)
    if request.method=='POST':
        form=FormImgProducto(request.POST, request.FILES)
        if form.is_valid():
            imgsProducto = form.save(commit=False)
            imgsProducto.items_id = (int(id_producto))
            if Imagen.objects.filter(items_id = int(id_producto)).count() >= 2:
                return JsonResponse({'error':'Ya tiene registrado sus imagenes'})
            else:
                imgsProducto.save()
                return JsonResponse({'success':'Registro exitoso'})
        else:
            return JsonResponse({'error':'Error intente nuevamente'})
    else:
        form=FormImgProducto()
    return render(request, 'catalog/imgs_products.html',{'form':form,'product':product})

def remode_imgs_products(request, id_producto):
    imagenes = Imagen.objects.filter(items_id = int(id_producto))
    return render(request, 'catalog/remode_imgs_products.html',{'imagenes':imagenes})

def deleteImgProduct(request, id_img):
    image = get_object_or_404(Imagen, id=int(id_img))
    image.delete()
    return JsonResponse({'success':'Se Elimino la Imagen'})

def getPrecioEnvio(request, id_company):
    datos = {}
    opcion = request.GET.get('opcion', 'domicilio')
    datos['total'] = calcular_pago(request)#total a pagar de todo el carrito
    
    if getBanco(id_company):
        datos['qr'] = getBanco(id_company).toJSON()#estoy traendo toda la funcion toJSON del models
    else:
        datos['qr'] = False

    if opcion == "domicilio":
        if determinarPrecioEnvio(id_company):
            datos['precio_envio'] = determinarPrecioEnvio(id_company)
            datos['total_pagar'] = int(calcular_pago(request)) + int(determinarPrecioEnvio(id_company))
        else:
            datos['precio_envio'] = 0
            datos['total_pagar'] = calcular_pago(request)
    elif opcion == "ciudad":
        if determinarPrecioEnvioCiudad(id_company):
            datos['precio_envio'] = determinarPrecioEnvioCiudad(id_company)
            datos['total_pagar'] = int(calcular_pago(request)) + int(determinarPrecioEnvioCiudad(id_company))
        else:
            datos['precio_envio'] = 0
            datos['total_pagar'] = calcular_pago(request)
    else:
        datos['precio_envio'] = 0
        datos['total_pagar'] = calcular_pago(request)
    
    datos['importe'] = calcular_pago(request)
    return JsonResponse({'datos':datos})

def form_sheart_product(request):
    company = Company.objects.get(id = int(request.GET['id_company']))
    return render(request, 'catalog/form_sheart_product.html', {'company':company})