from django import forms

from app.catalog.models import *

class ClientFormOrder(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['names'].widget.attrs['autofocus'] = True

    class Meta:
        model = Client
        exclude = ('gender','date_joined','email',)
        #fields = '__all__'

class formProducto(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['autofocus'] = True

    class Meta:
        model = Product
        #exclude = ('gender','date_joined','email',)
        fields = '__all__'

class formCategory(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['autofocus'] = True

    class Meta:
        model = Category
        #exclude = ('gender','date_joined','email',)
        fields = '__all__'