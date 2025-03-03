#encoding:utf-8
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django import forms
from django.contrib.auth.forms import User
from django.forms.models import ModelForm
from .models import *

class RegisterForm(UserCreationForm):
    username = forms.CharField(max_length=140, label="Email / Usuario")
    class Meta:
        model = get_user_model()
        fields = ('username','email', 'password1', 'password2')

class formCompany(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['autofocus'] = True
    class Meta:
        model = Company
        exclude = ('user','website','date_joined','image','plan', 'status', 'expiration_date')
    
#clase para actualizar la companias de los clientes
class formCompanyImage(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['autofocus'] = True
    class Meta:
        model = Company
        exclude = ('user','date_joined','plan', 'status','expiration_date','is_service')

class FormHuvicacion(forms.ModelForm):
    class Meta:
        model = Sucursal
        exclude = ('date_joined','company')

class PrecioForm(forms.ModelForm):
    class Meta:
        model = Precio_envio
        exclude = ('date_joined','company')

class FormBanco(forms.ModelForm):
    class Meta:
        model = Banco
        exclude = ('company',)

class Form_avisos(forms.ModelForm):
    class Meta:
        model = Aviso
        exclude = ('company',)

class Form_condiciones(forms.ModelForm):
    class Meta:
        model = Condicion
        exclude = ('company',)