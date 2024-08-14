from django.urls import path

from app.catalog import views


urlpatterns = [
    path('<int:id_company>/catalogo', views.CatalogView, name='CatalogView'),
    path('<int:id_producto>/<int:id_company>/detail_product', views.optenerProducto, name='detail_product'),
    path('<int:id_company>/ver_carrito/', views.ver_carrito, name='ver_carrito'),
    path('vaciar_carrito/', views.vaciar_carrito, name='vaciar_carrito'),
    path('eliminarProducto/<int:id_producto>', views.eliminarProducto, name='eliminarProducto'),
    path('<int:id_company>/shear_product/',views.shear_product, name='shear_product'),
    path('<int:id_company>/<int:id_categoria>/mostrar_por_categoria', views.mostrar_por_categoria, name='mostrar_por_categoria'),
    path('<int:id_company>/confirmar_compra/', views.confirmar_compra, name='confirmar_compra'),
    path('<int:id_company>/new_producto/', views.newProducto, name='new_producto'),
    path('new_category/', views.newCategory, name='new_category'),

    path('<int:id_product>/updateProduct/', views.updateProduct, name='updateProduct'),
    path('<int:id_product>/deleteProduct/', views.deleteProduct, name='deleteProduct'),
]