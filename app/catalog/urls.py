from django.urls import path

from app.catalog import views


urlpatterns = [
    path('<int:id_company>/catalogo', views.CatalogView, name='CatalogView'),
    path('<int:id_producto>/detail_product', views.optenerProducto, name='detail_product'),
    path('ver_carrito/', views.ver_carrito, name='ver_carrito'),
    path('vaciar_carrito/', views.vaciar_carrito, name='vaciar_carrito'),
    path('eliminarProducto/<int:id_producto>', views.eliminarProducto, name='eliminarProducto'),
    path('shear_product/',views.shear_product, name='shear_product'),
    path('<int:id_categoria>/mostrar_por_categoria', views.mostrar_por_categoria, name='mostrar_por_categoria'),
    path('confirmar_compra/', views.confirmar_compra, name='confirmar_compra'),
    path('new_producto/', views.newProducto, name='new_producto'),
]