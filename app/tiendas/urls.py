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
    path('<int:id_company>/add_huvicacion/', views.add_huvicacion, name='add_huvicacion'),
    path('<int:id_company>/configuraciones', views.configuraciones_company, name='configuraciones'),
    path('<int:id_company>/precio_envio', views.precio_envio, name='precio_envio'),
    path('<int:id_company>/buscar_orden', views.buscar_orden, name='buscar_orden'),
    path('<int:id_company>/add_avisos', views.add_avisos, name='add_avisos'),
    path('<int:id_company>/get_opciones', views.get_opciones, name='get_opciones'),
    path('<int:id_precio>/del_precio', views.del_precio, name='del_precio'),
    path('<int:id_company>/banco_envio', views.banco_envio, name='banco_envio'),
    path('<int:id_company>/infor_banco', views.infor_banco, name='infor_banco'),
    path('<int:id_banco>/del_infor_banco_by_company', views.del_infor_banco_by_company, name='del_infor_banco_by_company'),
    path('<int:id_aviso>/eliminar_opciones', views.eliminar_opciones, name='eliminar_opciones'),
    
    path('<int:id_company>/<int:id_orden>/report_pdf', views.report_pdf, name='report_pdf'),
]