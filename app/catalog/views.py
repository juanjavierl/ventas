#encoding:utf-8
#import pywhatkit
from datetime import datetime, date, timedelta
from django.core.mail import EmailMultiAlternatives
import threading
from django.template.loader import get_template
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
from django.db.models import F, ExpressionWrapper, IntegerField
from django.db.models.functions import Coalesce
from decimal import Decimal
# Create your views here.
def CatalogView(request, id_company=None):
    template_name = "sitio.html"
    if request.method == 'GET':
        #productos = Product.objects.filter(company_id=int(id_company)).order_by('-id')
        if request.company: #si entramos por el dominio peronalizado
            company = request.company
            id_company = company.id
        elif id_company:#si entramos mediante /1/catalogo
            try:
                company = get_company(id_company)
            except:
               return redirect("/") 
        else:
            return redirect("/")
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
            'total_compra':sum(item['cantidad'] for item in request.session['compra']),
            't_pago':calcular_pago(request),
            'company':get_company(id_company),
            'aviso':optener_avisos_by_company(id_company),
            'dashboard':get_Dashboard(),
            'date_expiration':date_expiration,
            'address':get_address(id_company),
            'code':get_code_meta(id_company),
            'promocion':get_promacion(id_company)
        }
        return render(request,template_name, dic)

def get_promacion(id_company):
    try:
        promocion = Promocion.objects.get(company_id = int(id_company))
    except:
        promocion = False
    return promocion

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

def optenerProducto(request, id_company, id_producto):
    productos = Product.objects.filter(company_id = int(id_company))
    p = get_object_or_404(Product,id = id_producto)
    datos = {}
    dic = {}
    try:
        data_cli = request.session['compra']
    except:
        data_cli = request.session.get('compra', [])
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
        datos['imagen'] = p.image.url if p.image else ''
        tiene_nota = request.POST.get('is_nota',False) == 'on'#verificamos si su pedido tiene una nota
        if tiene_nota:
            datos['nota'] = request.POST['nota']
        else:
            datos['nota'] = ""

        if len(data_cli) == 0:#cuanoo el carrido esta vasio
            data_cli.append(datos)
            request.session['compra'] = data_cli
            dic = {
                'total_compra':sum(item['cantidad'] for item in data_cli),
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
                    dic['total_compra'] = sum(item['cantidad'] for item in data_cli)
                    dic['success'] = p.name.title()," agregado al Carrito."
                    return JsonResponse(dic)
            if not datos in data_cli:#verifica si el producto aun no esta en la sesion
                data_cli.append(datos)
                request.session['compra'] = data_cli
                dic['total_compra'] = sum(item['cantidad'] for item in data_cli)
                dic['success'] = p.name.title()," agregado al Carrito."
                return JsonResponse(dic)
    else:
        context = { 'p':p,
                    'total_compra':sum(item['cantidad'] for item in data_cli),
                    'company':get_company(id_company),
                    'categorias':categorys_from_productos(productos),
                    'aviso':optener_avisos_by_company(id_company),
                    'productos':productosMasVistos(id_company),
                    'address':get_address(id_company),
                    'code':get_code_meta(id_company),
                    'images_product':Imagen.objects.filter(items_id = int(id_producto))
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
        'cant_compras':sum(item['cantidad'] for item in request.session['compra']),
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
        'cant_compras':sum(item['cantidad'] for item in request.session['compra']),
        't_pago':calcular_pago(request)
    }
    return JsonResponse(data)

def shear_product(request, id_company):
    if request.method=="POST":
        texto=request.POST["search"]
        busqueda=(
            Q(name__icontains=texto) |
            Q(description__icontains=texto) |
            Q(category__name__icontains=texto)
        )
        productos=Product.objects.filter(busqueda,stock__gt=0, company_id=int(id_company)).distinct()
        return render(request,'catalog/card_productos.html',{'productos':productos,'company':get_company(id_company)})
    else:
        texto=request.GET["search"]
        busqueda=(
            Q(name__icontains=texto) |
            Q(description__icontains=texto) |
            Q(category__name__icontains=texto)
        )
        productos=Product.objects.filter(busqueda,stock__gt=0, company_id=int(id_company)).distinct()
        return render(request,'catalog/card_productos.html',{'productos':productos,'company':get_company(id_company)})

def mostrar_por_categoria(request, id_company, id_categoria):
    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return redirect(f'/{id_company}/catalogo')
    productos = Product.objects.filter(stock__gt=0, category_id = id_categoria, company_id= id_company).order_by('-id')
    return render(request, 'catalog/card_productos.html', {'productos':productos,'company':get_company(id_company)})

def create_mail_confirmar_venta(email_propietario, subject, template_name, context):
    template = get_template(template_name)
    content = template.render(context)
    message = EmailMultiAlternatives(
        subject=subject,
        body='',
        from_email=settings.EMAIL_HOST_USER,
        to=[email_propietario]
    )
    message.attach_alternative(content, 'text/html')
    return message

def send_confirmar_venta_mail(email_propietario, orden, company):
    mail = create_mail_confirmar_venta(
        email_propietario,
        'Tienes una venta en tu tienda online',
        'notificaciones/confirmar_venta_email.html',
        {
            'email': email_propietario,
            'orden': orden,
            'company': company
        }
    )
    mail.send(fail_silently=False)

def confirmar_compra(request, id_company):
    company = get_object_or_404(Company, id=id_company)
    t_pago = calcular_pago(request)
    compra = request.session.get('compra', [])
    total_compra = sum(item['cantidad'] for item in compra)
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        tipo_envio = request.POST.get('tipo_envio', '').strip()

        # Validaciones
        if not email:
            return JsonResponse({'error': "Por favor ingrese su email."})
        if not mobile:
            return JsonResponse({'error': "Por favor ingrese su número de celular."})
        if not tipo_envio:
            return JsonResponse({'error': "Por favor seleccione el tipo de envío."})

        forms = ClientFormOrder(request.POST)

        # --- Determinar tipo de envío ---
        lugar, precio_envio, ref = {}, 0, None

        if tipo_envio == 'tienda':
            ref = 'tienda'
            try:
                d = datetime.strptime(request.POST['date_time'] + ":00", '%Y-%m-%dT%H:%M:%S')
                if d < datetime.now():
                    return JsonResponse({'error': "Error: La fecha debe ser mayor o igual a hoy"})
            except Exception:
                return JsonResponse({'error': "Fecha inválida"})

            dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            dia = dias[d.weekday()]
            fecha = datetime.strftime(d, f"{dia} %d/%m/%y hora: %H:%M %p")
            lugar = {'fecha': fecha, 'tipo': 'tienda'}

        elif tipo_envio == 'domicilio':
            ref = 'domicilio'
            lugar = {'direccion': request.POST.get('address', ''), 'tipo': 'domicilio'}
            precio_envio = obtener_datos_envio(request, id_company)['precio_envio']

        elif tipo_envio == 'ciudad':
            ref = 'ciudad'
            lugar = {'destino': request.POST.get('destino', ''), 'tipo': 'ciudad'}
            precio_envio = obtener_datos_envio(request, id_company)['precio_envio']

        else:
            return JsonResponse({'error': "Por favor complete sus datos correctamente."})

        # --- Obtener o crear cliente ---
        # --- Buscar si el cliente ya existe ---
        cliente = Client.objects.filter(email=email).first()
        # ✅ Si NO existe → lo validamos y lo registramos
        if not cliente:
            if not forms.is_valid():
                return JsonResponse({'error': forms.errors})

            # Si es envío a otra ciudad, registrar el atributo ref en address del cliente antes de guardar
            if ref == 'ciudad':
                # Creamos una instancia, no la guardamos aún
                cliente = forms.save(commit=False)
                cliente.address =  request.POST.get('destino', '')
                cliente.save()
            else:
                cliente = forms.save()
   
        # ✅ Si YA existe → NO validamos, NO registramos, solo seguimos con la orden

        # --- Crear orden ---
        orden = crear_orden(request, cliente.id, id_company, ref)

        # --- Registrar pedidos ---
        for item in compra:
            producto_id = int(item['id_producto'])
            cantidad = int(item['cantidad'])
            precio = float(item['precio_uni'])
            total = cantidad * precio

            Pedido.objects.create(
                orden=orden,
                product_id=producto_id,
                cant=cantidad,
                price=precio,
                total=total,
                nota=item.get('nota', '')
            )
            """ producto = getProducto(producto_id)
            if not producto.is_service:
                Product.objects.filter(id=producto_id).update(
                    salida=producto.salida + cantidad
                ) """

        # --- Vaciar carrito ---
        lista_product = compra.copy()
        request.session['compra'] = []

        # --- Enviar correo al propietario ---
        email_propietario = company.user.email
        if email_propietario:
            threading.Thread(
                target=send_confirmar_venta_mail,
                args=(email_propietario, orden, company)
            ).start()

        return JsonResponse({
            'success': "Tu pedido fue registrado con éxito.",
            'cliente_object': cliente.toJSON(),
            'company_object': company.toJSON(),
            'orden': orden.toJSON(),
            'lugar': lugar,
            'lista': lista_product,
            't_pago': t_pago,
            'products': sum(item['cantidad'] for item in compra)
        })

    # --- Si no es POST, renderizar vista ---
    ahora = datetime.now() + timedelta(minutes=30)
    limite = datetime.now() + timedelta(days=15)
    dic = {
        'form': ClientFormOrder(),
        'total_compra': total_compra,
        'company': get_company(id_company),
        'categorias': categorys_from_productos(productosMasVistos(id_company)),
        'datos': compra,
        't_pago': t_pago,
        'productos': productosMasVistos(id_company),
        'aviso': optener_avisos_by_company(id_company),
        'address': get_address(id_company),
        'regla': get_rule_condicion(id_company),
        'code': get_code_meta(id_company),
        'ahora': ahora.strftime("%Y-%m-%dT%H:%M"),
        'limite': limite.strftime("%Y-%m-%dT%H:%M")
    }
    return render(request, 'catalog/confirmar_compra.html', dic)

def getProducto(id_producto):
    producto = Product.objects.get(id = id_producto)
    return producto

def productosMasVistos(id_company):
    #productos = Product.objects.filter(stock__gt=0, company_id=id_company, is_promotion=True)
    productos = Product.objects.annotate(
        stock_real=ExpressionWrapper(
            F('stock') - Coalesce(F('salida'), 0),
            output_field=IntegerField()
        )
    ).filter(
        stock_real__gt=0,
        company_id=id_company,
        is_promotion=True
    )
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

def crear_orden(request, id_cliente, id_company, ref='tienda'):
    """
    Registra la orden para el cliente, calcula envío y aplica promoción según el tipo de entrega.
    Reglas:
      - Si es recojo en tienda, el envío es 0.
      - Si es domicilio o ciudad, verifica si hay precio registrado, o si es "por pagar" (None o 0).
      - Calcula si aplica descuento dependiendo del monto total de la compra y las condiciones de la compañía.
    """
    
    # Obtiene la compañía y posibles reglas de descuento/promo
    company = get_company(id_company)
    subtotal = float(calcular_pago(request))

    # Determinar precio de envío según tipo (ref)
    pr_envio = 0
    tipo_envio = None   # Para guardar si es por pagar/por definir

    if ref == 'tienda':
        pr_envio = 0
        tipo_envio = 'tienda'
    elif ref == 'domicilio':
        precio_envio = determinarPrecioEnvio(id_company)
        if precio_envio and precio_envio > 0:
            pr_envio = float(precio_envio)
            tipo_envio = 'domicilio'
        else:
            # Envío por pagar o no disponible
            pr_envio = 0
            tipo_envio = 'domicilio_por_pagar'
    elif ref == 'ciudad':
        precio_envio_ciudad = determinarPrecioEnvioCiudad(id_company)
        if precio_envio_ciudad and precio_envio_ciudad > 0:
            pr_envio = float(precio_envio_ciudad)
            tipo_envio = 'ciudad'
        else:
            pr_envio = 0
            tipo_envio = 'ciudad_por_pagar'
    else:
        pr_envio = 0
        tipo_envio = 'otro'

    # Calcular el total preliminar
    subtotal_con_envio = subtotal + pr_envio

    # Buscar si la company tiene una promoción activa/configurada
    descuento = 0
    promocion = getattr(company, "promocion", None)

    if promocion and promocion.aplica(subtotal) :
        monto_minimo = getattr(promocion, "monto_minimo", 0) or 0
        porcentaje_descuento = getattr(promocion, "descuento", 0) or 0
        # Se aplica el descuento sólo si se supera el mínimo
        if subtotal_con_envio >= monto_minimo:
            descuento = subtotal_con_envio * (porcentaje_descuento / 100)
        else:
            descuento = 0
    else:
        descuento = 0

    # El total de la orden es subtotal+envio-descuento
    total = subtotal_con_envio - descuento

    # Registrar la orden
    orden = Orden()
    orden.client_id = int(id_cliente)
    orden.company_id = int(id_company)
    orden.subtotal = Decimal(str(subtotal_con_envio))
    orden.dscto = Decimal(str(descuento))
    orden.total = Decimal(str(total))
    orden.tipo_venta = ref
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
            if Imagen.objects.filter(items_id = int(id_producto)).count() >= 5:
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

def obtener_datos_envio(request, id_company):
    opcion = request.GET.get('opcion', 'domicilio')

    subtotal = calcular_pago(request)
    banco = getBanco(id_company)
    config = Precio_envio.objects.filter(company_id=id_company).first()
    desc_promocion = Promocion.objects.filter(company_id = id_company).first()

    # La lógica original tenía error porque 'total' estaba inicializado a 0 y nunca se usó subtotal para comparar.
    # Corregimos para comparar subtotal (que es el total real antes de descuento) con compra_mayores
    if desc_promocion and desc_promocion.aplica(subtotal):
        desc = subtotal * desc_promocion.descuento / 100
        total = subtotal - desc
    else:
        desc = 0
        total = subtotal

    datos = {
        'subtotal': subtotal,  # total sin descuento
        'desc': desc,          # descuento calculado
        'total': total,        # total menos el desc
        'qr': banco.toJSON() if banco else False,
        'precio_envio': 0,
        'tipo_envio': 'gratis',
    }

    # Si el cliente recoge en tienda
    if opcion == 'tienda':
        return datos

    # Existe configuración de envío
    if config:

        # Envío por pagar
        if config.por_pagar:
            datos['precio_envio'] = 'Por Pagar'
            datos['tipo_envio'] = 'por_pagar'

        # Precio fijo a domicilio
        elif opcion == 'domicilio' and config.precio is not None:
            datos['precio_envio'] = config.precio
            datos['tipo_envio'] = 'fijo'
            datos['total'] = total + config.precio
            datos['desc'] = desc

        # Precio fijo a otra ciudad
        elif opcion == 'ciudad' and config.precio_ciudad is not None:
            datos['precio_envio'] = config.precio_ciudad
            datos['tipo_envio'] = 'fijo'
            datos['total'] = total + config.precio_ciudad
            datos['desc'] = desc

    return datos

def getPrecioEnvio(request, id_company):
    datos = obtener_datos_envio(request, id_company)
    return JsonResponse({'datos': datos})

def form_sheart_product(request):
    company = Company.objects.get(id = int(request.GET['id_company']))
    return render(request, 'catalog/form_sheart_product.html', {'company':company})