from django.db.models import Avg, Max, Min, Count
from django.http import JsonResponse, request
from django.shortcuts import render, get_object_or_404,HttpResponse,redirect
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.forms import User
from django.contrib.auth import authenticate,login, logout

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.forms import SetPasswordForm

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy

from app.inicio.models import *
from app.tiendas.models import *
from .forms import *

# Create your views here.

def robots_txt(request):
    sitemap_url = f"https://{request.get_host()}/sitemap.xml"
    lines = [
        "User-Agent: *",
        "Disallow: /admin/",
        "Disallow: /ver_planes/",
        "Disallow: /change_password/",
        "Disallow: /login_user/",
        "Disallow: /registro_company/",
        "Allow: /",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

def inicio(request):
    ciudades = Ciudad.objects.all().order_by('-id')
    type_company = Tipo_company.objects.all().order_by('-id')
    #contar todas las conpanyas q pertenecen a cada categoria
    #conpanias = Company.objects.all().order_by('-id')
    count_comp = {}
    for t_companys in type_company:
        count_comp[t_companys.name] = Company.objects.filter(category_id = int(t_companys.id)).count()
    
    dic = {
        'dashboard':get_Dashboard(),
        'type_company':type_company,
        'count_comp':count_comp,
        'ciudades':ciudades
    }
    return render(request,'index.html',dic)


def get_Dashboard():
    try:
        dashboard = Dashboard.objects.get(id=1)
    except:
        dashboard = {'name':"AMCEB",'mobile':79436914,'codigo':''}
    return dashboard

def verPlanes(request):
    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return redirect('/')
    idCompany = int(request.GET.get('id_company', 0))
    if idCompany == 0:
        planes = Plataforma.objects.all()
        company = False
    else:
        company = Company.objects.get(id = idCompany)
        planes = Plataforma.objects.exclude(id=company.plan.id)
        company = company
    dic = {
        'celular':get_Dashboard(),
        'planes':planes,
        'company':company
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


class AjaxPasswordResetView(PasswordResetView):
    template_name = 'password_reset.html'
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form.save(self.request)
            return JsonResponse({'message': 'Correo enviado con éxito'})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'errors': form.errors}, status=400)
        return super().form_invalid(form)

def password_reset_confirm_ajax(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except Exception:
        return JsonResponse({'error': 'Token inválido'}, status=400)

    if not default_token_generator.check_token(user, token):
        return JsonResponse({'error': 'Token inválido o expirado'}, status=400)

    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'message': 'Tu contraseña fue restablecida correctamente.'})
        else:
            return JsonResponse({'errors': form.errors}, status=400)
    else:
        form = SetPasswordForm(user)

    return render(request, 'password_confirm.html', {'form': form})

def guardar_datos_extra(backend, user, response, *args, **kwargs):
    if backend.name == 'google-oauth2':
        user.first_name = response.get('given_name', '')
        user.last_name = response.get('family_name', '')
        user.email = response.get('email', '')
        user.save()

def redirigir_a_companys(backend, user, response, *args, **kwargs):
    if user and user.is_authenticated:
        return redirect(f"/{user.id}/companys/")

