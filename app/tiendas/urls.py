from app.tiendas import views
from django.urls import path

urlpatterns = [
    path('<int:id_type>/type/', views.getTypes, name='type'),
    path('registro_company/', views.registro_company, name='registro_company'),
    path('validar_form/', views.validar_form, name='validar_form'),
    path('validar_username/', views.validar_username, name='validar_username'),
    path('login_user/', views.login_user, name='login_user'),
    path('salir/', views.salir, name='salir'),
    path('<int:id_plan>/get_img/', views.get_img_plan, name='get_img_plan'),
    path('register_data/', views.datos_registro, name='datos_registro'),
    path('<int:user_id>/companys/', views.companys_from_user, name='companys_from_user'),
    path('<int:id_company>/updateCompany/', views.updateCompany, name='updateCompany'),
    path('<int:id_company>/deleteCompany/', views.deleteCompany, name='deleteCompany'),
    path('<int:user_id>/update_perfil_user/', views.update_perfil_user, name='update_perfil_user'),
]