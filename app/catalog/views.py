#encoding:utf-8
#import pywhatkit
# 1. Biblioteca estándar de Python
from datetime import date, datetime, timedelta
from decimal import Decimal
import json
import threading

# 2. Librerías de terceros (Django)
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import ExpressionWrapper, F, IntegerField, Q
from django.db.models.functions import Coalesce
from django.db import transaction
from django.http import Http404, JsonResponse, request
from django.shortcuts import HttpResponse, get_object_or_404, redirect, render
from django.template.loader import get_template

# 3. Aplicaciones locales de tu proyecto
from app.catalog.forms import *
from app.catalog.models import *
from app.inicio.models import Proyecto
from app.inicio.views import get_Dashboard
from app.tiendas.models import *
from app.tiendas.utils import calcular_puntos_fidelidad
from app.catalog.pricing import calculate_product_price, normalize_attribute_values
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
        productos = productos_by_company(id_company)
        page = request.GET.get('page',1)
        try:
            categorys = categorys_from_productos(productos)
            paginator = Paginator(productos, 20)
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
            'promocion':get_promacion(id_company),
            'fidelidad':get_fidelidad(id_company)
        }
        return render(request,template_name, dic)

def productos_by_company(id_company):
    productos = Product.objects.filter(company_id=int(id_company)) \
                .select_related('category') \
                .prefetch_related('attributes') \
                .order_by('category__name', '-id')
    return productos

def get_promacion(id_company):
    try:
        promocion = Promocion.objects.get(company_id = int(id_company))
    except:
        promocion = False
    return promocion

def get_fidelidad(id_company):
    try:
        fidelidad = Fidelidad.objects.get(company_id = int(id_company))
    except:
        fidelidad = False
    return fidelidad

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
        if not {'id':p.category.id, 'name':p.category.name, 'get_slug':p.category.get_slug()} in ct:
            ct.append({'id':p.category.id, 'name':p.category.name, 'get_slug':p.category.get_slug()})
    return ct

def get_company(id_company, user=None):
    company = get_object_or_404(Company, id=int(id_company))

    # Verificar que el usuario logueado sea el dueño
    if user is not None and company.user != user:
        raise Http404("Empresa no encontrada")

    return company

def optenerProducto(request, id_company, id_producto, slug):
    productos = Product.objects.filter(company_id = int(id_company))
    p = get_object_or_404(Product, id=id_producto, company_id=id_company)
    atributos_producto = list(p.attributes.all())
    for attribute in atributos_producto:
        attribute.option_values = normalize_attribute_values(attribute.values)
    atributos_informativos = [attribute for attribute in atributos_producto if not attribute.is_selectable]
    if request.method != 'POST' and slug != p.get_slug():
        return redirect(
            'detail_product',
            id_company=p.company_id,
            id_producto=p.id,
            slug=p.get_slug(),
            permanent=True,
        )
    datos = {}
    dic = {}
    try:
        data_cli = request.session['compra']
    except:
        data_cli = request.session.get('compra', [])
    if request.method == 'POST':
        if not request.POST.get('cantidad', '').isdigit() or int(request.POST.get('cantidad', '0')) < 1:
            return JsonResponse({'error': "La cantidad debe ser numerico."})
        try:
            seleccionados = json.loads(request.POST.get('atributos', '{}'))
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Las opciones seleccionadas no son válidas.'}, status=400)
        if not isinstance(seleccionados, dict):
            return JsonResponse({'error': 'Las opciones seleccionadas no son válidas.'}, status=400)
        requeridos = {a.name: a for a in atributos_producto if a.is_selectable}
        faltantes = [name for name in requeridos if not seleccionados.get(name)]
        if faltantes:
            return JsonResponse({'error': 'Seleccione: ' + ', '.join(faltantes) + '.'}, status=400)
        try:
            precio_final, snapshot = calculate_product_price(p, seleccionados)
        except ValidationError:
            return JsonResponse({'error': 'Una o más opciones seleccionadas no pertenecen al producto.'}, status=400)
        #if int(request.POST['cantidad']) > p.stock:
        if p.stock_actual() <= 0:
            return JsonResponse({'error': 'Producto Agotado...!'})
        datos['id_producto'] = int(p.id)
        datos['name'] = p.name.title()
        datos['cantidad'] = int(request.POST['cantidad'])
        datos['precio_base'] = str(p.price)
        datos['precio_uni'] = str(precio_final)
        datos['incrementos'] = snapshot
        datos['total'] = str(int(request.POST['cantidad']) * precio_final)
        datos['atributos'] = {name: option['value'] for name, option in snapshot.items()}
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
                'precio_uni':str(precio_final),
                'total':str(int(request.POST['cantidad']) * precio_final),
                'datos': request.session['compra'],
                "t_pago":calcular_pago(request)
            }
            dic['success'] = p.name.title()," agregado al Carrito."
            return JsonResponse(dic)
        elif len(data_cli) > 0:#cuando el carrito ya tiene compras
            for indice in range(len(data_cli)):   
                if data_cli[indice]['id_producto'] == datos['id_producto'] and data_cli[indice].get('atributos', {}) == seleccionados:
                    data_cli[indice]['cantidad'] = int(data_cli[indice]['cantidad']) + int(request.POST['cantidad'])
                    data_cli[indice]['total'] = str(int(data_cli[indice]['cantidad']) * Decimal(data_cli[indice]['precio_uni']))
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
        company = get_company(id_company)
        fidelidad = get_fidelidad(id_company)
        if not fidelidad or not fidelidad.vigente:
            fidelidad = None

        promocion = get_promacion(id_company)
        if not promocion or not promocion.promocion_vigente:
            promocion = None
        context = { 'p':p,
                    'total_compra':sum(item['cantidad'] for item in data_cli),
                    'company':company,
                    'fidelidad':fidelidad,
                    'promocion':promocion,
                    'categorias':categorys_from_productos(productos),
                    'aviso':optener_avisos_by_company(id_company),
                    'productos':productosMasVistos(id_company),
                    'address':get_address(id_company),
                    'code':get_code_meta(id_company),
                    'images_product':Imagen.objects.filter(items_id = int(id_producto)),
                    'attributes_producto':atributos_producto,
                    'atributos_informativos':atributos_informativos
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
    fidelidad = getattr(company, 'fidelidad', None)# verificamos si la compañia tiene fidelidad activa para calcular los puntos que genera la compra
    puntos = calcular_puntos_fidelidad(t_pago, fidelidad) if fidelidad and fidelidad.vigente else 0
    return render(request, 'catalog/show_productos_carrito.html',{'datos':datos,'t_pago':t_pago, 'company':company, 'regla':regla, 'puntos':puntos})


def calcular_pago(request):
    total_pago = Decimal('0')
    try:
        productos = request.session['compra']
        for producto in productos:
            total_pago += Decimal(str(producto['total']))

        return total_pago.quantize(Decimal('0.01'))
    except:
        return total_pago.quantize(Decimal('0.01'))
    

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
    productos[int(indice)]['total'] = str(Decimal(str(productos[int(indice)]['precio_uni'])) * int(productos[int(indice)]['cantidad']))
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
        productos=Product.objects.filter(busqueda,stock__gt=0, company_id=int(id_company)).prefetch_related('attributes').distinct()
        return render(request,'catalog/card_productos.html',{'productos':productos,'company':get_company(id_company)})
    else:
        texto=request.GET["search"]
        busqueda=(
            Q(name__icontains=texto) |
            Q(description__icontains=texto) |
            Q(category__name__icontains=texto)
        )
        productos=Product.objects.filter(busqueda,stock__gt=0, company_id=int(id_company)).prefetch_related('attributes').distinct()
        return render(request,'catalog/card_productos.html',{'productos':productos,'company':get_company(id_company)})

def mostrar_por_categoria(request, id_company, id_categoria):
    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return redirect(f'/{id_company}/catalogo')
    productos = Product.objects.filter(stock__gt=0, category_id = id_categoria, company_id= id_company).prefetch_related('attributes').order_by('-id')
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
    compra = request.session.get('compra', [])
    if request.method == 'POST':
        # Reprice session lines from current DB data before totals or order creation.
        for item in compra:
            producto = Product.objects.filter(id=item.get('id_producto'), company_id=id_company).first()
            if not producto:
                return JsonResponse({'error': 'El carrito contiene un producto no disponible.'}, status=400)
            try:
                price, snapshot = calculate_product_price(producto, item.get('atributos', {}))
            except ValidationError:
                return JsonResponse({'error': 'El carrito contiene opciones inválidas. Vuelva al producto y seleccione sus opciones.'}, status=400)
            try:
                cantidad = int(item.get('cantidad', 0))
            except (TypeError, ValueError):
                cantidad = 0
            if cantidad < 1:
                return JsonResponse({'error': 'La cantidad del carrito no es válida.'}, status=400)
            item.update({
                'precio_base': str(producto.price), 'precio_uni': str(price),
                'incrementos': snapshot,
                'total': str(price * cantidad),
                'atributos': {name: option['value'] for name, option in snapshot.items()},
            })
        request.session['compra'] = compra
    t_pago = calcular_pago(request)
    total_compra = sum(item['cantidad'] for item in compra)
    fidelidad = getattr(company, 'fidelidad', None)# verificamos si la compañia tiene fidelidad activa para calcular los puntos que genera la compra
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

        for item in compra:
            producto = Product.objects.filter(id=item.get('id_producto'), company_id=id_company).first()
            if not producto:
                return JsonResponse({'error': 'El carrito contiene un producto no disponible.'}, status=400)
            seleccionados = item.get('atributos', {})
            try:
                calculate_product_price(producto, seleccionados)
            except ValidationError:
                return JsonResponse({'error': 'El carrito contiene opciones inválidas. Vuelva al producto y seleccione sus opciones.'}, status=400)

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

        # --- Crear orden y líneas como una sola operación ---
        with transaction.atomic():
            orden = crear_orden(request, cliente.id, id_company, ref)
            for item in compra:
                producto = Product.objects.get(id=int(item['id_producto']), company_id=id_company)
                seleccionados = item.get('atributos', {})
                cantidad = int(item['cantidad'])
                precio, snapshot = calculate_product_price(producto, seleccionados)
                Pedido.objects.create(
                    orden=orden, product=producto, cant=cantidad, price=precio,
                    total=precio * cantidad, nota=item.get('nota', ''),
                    atributos_seleccionados=snapshot,
                )

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
            'products': 0,
            'puntos': calcular_puntos_fidelidad(t_pago, fidelidad)if fidelidad and fidelidad.vigente else 0
        })

    # --- Si no es POST, renderizar vista ---
    ahora = datetime.now() + timedelta(minutes=30)
    limite = datetime.now() + timedelta(days=7)
    
    dic = {
        'form': ClientFormOrder(),
        'total_compra': total_compra,
        'company': get_company(id_company),
        'categorias': categorys_from_productos(productos_by_company(id_company)),

        'datos': compra,
        't_pago': t_pago,
        'productos': productosMasVistos(id_company),
        'aviso': optener_avisos_by_company(id_company),
        'address': get_address(id_company),
        'regla': get_rule_condicion(id_company),
        'code': get_code_meta(id_company),
        'ahora': ahora.strftime("%Y-%m-%dT%H:%M"),
        'limite': limite.strftime("%Y-%m-%dT%H:%M"),
        'puntos': calcular_puntos_fidelidad(t_pago, fidelidad)if fidelidad and fidelidad.vigente else 0
    }
    return render(request, 'catalog/confirmar_compra.html', dic)

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
    ).prefetch_related('attributes')
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
    # Obtenemos la compañía correspondiente, incluyendo la relación con su plan.
    # Esto lo hacemos para tener accesible el límite de productos permitido por el plan.
    company = get_object_or_404(
        Company.objects.select_related('plan'),
        id=id_company
    )

    # Cantidad actual de productos registrados por la compañía.
    cant_productos = int(cantProductosByCompany(id_company))
    # Límite de productos permitidos según el plan contratado por la compañía.
    limite_productos = int(company.plan.cantidad)

    # Revisa si la fecha de expiración está definida y si ya expiró (es menor que hoy).
    fecha_expirada = (company.expiration_date is not None and company.expiration_date < date.today())

    # Si el número de productos es igual o mayor al límite, activamos el aviso.
    aviso = cant_productos >= limite_productos
    # Si la fecha está expirada, activamos la bandera de expiración.
    date_expiration = fecha_expirada

    if request.method == 'POST':
        if aviso or date_expiration:
            return JsonResponse({
                'error': (
                    'Alcanzaste el límite de registros para este plan '
                    'o la fecha de tu plan ha caducado.'
                ),
                'aviso': aviso,
                'date_expiration': date_expiration
            })

        form = formProducto(request.POST, request.FILES)

        if form.is_valid():
            producto = form.save(commit=False)
            producto.company = company
            producto.save()
            return JsonResponse({
                'success': 'Producto registrado exitosamente.',
                'aviso': False,
                'date_expiration': False
            })

        return JsonResponse({
            'error': 'Verifica los datos ingresados.',
            'errors': form.errors,
            'aviso': False,
            'date_expiration': False
        }, status=400)

    form = formProducto()

    categorys = Category.objects.all().order_by('-id')

    return render(
        request,
        'catalog/newProducto.html',
        {
            'form': form,
            'company': company,
            'categorys': categorys,
            'aviso': aviso,
            'date_expiration': date_expiration,
        }
    )

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
    product = get_object_or_404(Product, id=id_product)
    if not request.user.is_authenticated or product.company.user_id != request.user.id:
        raise Http404
    if request.method=='POST':
        form=formUpdateProducto(request.POST, request.FILES,instance=product)
        if form.is_valid():
            form.save()
            return JsonResponse({'success':'Registro actualizado'})
        else:
            return JsonResponse({'errors': form.errors.get_json_data()}, status=400)
    else:
        form=formUpdateProducto(instance=product)
        return render(request, 'catalog/updateProduct.html',{'form':form,'product':product})


def manage_product_attribute(request, id_product):
    product = get_object_or_404(Product, id=id_product)
    if not request.user.is_authenticated or product.company.user_id != request.user.id:
        raise Http404
    if request.method == 'GET':
        attributes = list(product.attributes.all())
        for attribute in attributes:
            attribute.options_json = json.dumps(normalize_attribute_values(attribute.values), ensure_ascii=False)
        return render(request, 'catalog/product_attributes.html', {
            'product': product,
            'attributes': attributes,
        })
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido.'}, status=405)
    attribute_id = request.POST.get('attribute_id')
    if request.POST.get('delete') == '1':
        get_object_or_404(ProductAttribute, id=attribute_id, product=product).delete()
        return JsonResponse({'success': 'Característica eliminada.'})
    name = request.POST.get('name', '').strip()
    selectable = request.POST.get('is_selectable') == 'on'
    option_names = request.POST.getlist('option_value[]')
    option_prices = request.POST.getlist('option_price[]')
    try:
        values = [{'value': name.strip(), 'price_extra': price.strip() or '0'}
                  for name, price in zip(option_names, option_prices) if name.strip()]
        if not option_names:  # compatibility with callers of the former textarea form
            values = [value.strip() for value in request.POST.get('values', '').splitlines() if value.strip()]
        values = normalize_attribute_values(values)
    except ValidationError as error:
        return JsonResponse({'error': {'values': error.messages}}, status=400)
    attribute = get_object_or_404(ProductAttribute, id=attribute_id, product=product) if attribute_id else ProductAttribute(product=product)
    attribute.name, attribute.values, attribute.is_selectable = name, values, selectable
    try:
        attribute.save()
    except ValidationError as error:
        return JsonResponse({'error': error.message_dict}, status=400)
    return JsonResponse({'success': 'Característica guardada.'})

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

def reproducir_video(request, id_producto):
    from urllib.parse import urlparse, parse_qs, quote
    producto = get_object_or_404(Product, id=id_producto)

    video_url = None
    platform = None
    embed_url = None

    raw_url = getattr(producto, 'video_url', None)

    if raw_url:

        video_url = raw_url.strip()

        parsed_url = urlparse(video_url)
        host = parsed_url.netloc.lower()

        if host.startswith('www.'):
            host = host[4:]

        # =========================
        # YOUTUBE
        # =========================
        if host == 'youtube.com' or host == 'youtu.be':

            platform = 'youtube'
            video_id = None

            if host == 'youtube.com':

                # youtube.com/watch?v=XXXXXXXX
                qs = parse_qs(parsed_url.query)
                video_id = qs.get('v', [None])[0]

                # youtube.com/shorts/XXXXXXXX
                if not video_id:
                    parts = parsed_url.path.strip('/').split('/')

                    if len(parts) >= 2 and parts[0] == 'shorts':
                        video_id = parts[1]

                # youtube.com/embed/XXXXXXXX
                if not video_id:
                    parts = parsed_url.path.strip('/').split('/')

                    if len(parts) >= 2 and parts[0] == 'embed':
                        video_id = parts[1]

            elif host == 'youtu.be':

                video_id = parsed_url.path.strip('/').split('/')[0]

            if video_id:
                embed_url = (
                    f'https://www.youtube.com/embed/{video_id}'
                    f'?rel=0'
                )

        # =========================
        # TIKTOK
        # =========================
        elif host == 'tiktok.com':

            platform = 'tiktok'

            parts = parsed_url.path.strip('/').split('/')

            if 'video' in parts:

                idx = parts.index('video')

                if idx + 1 < len(parts):

                    video_id = parts[idx + 1]

                    embed_url = (
                        f'https://www.tiktok.com/embed/v2/{video_id}'
                    )

        # =========================
        # FACEBOOK
        # =========================
        elif host in ('facebook.com', 'fb.watch'):

            platform = 'facebook'

            embed_url = (
                'https://www.facebook.com/plugins/video.php'
                f'?href={quote(video_url, safe="")}'
                '&show_text=false'
                '&width=560'
            )

        # =========================
        # OTRO
        # =========================
        else:

            platform = 'other'
            embed_url = video_url

    return render(
        request,
        'catalog/ver_video_producto.html',
        {
            'producto': producto,
            'video_url': embed_url,
            'platform': platform,
            'raw_video_url': video_url,
        }
    )
