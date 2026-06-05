from django.urls import path

from . import views

app_name = "productos"

urlpatterns = [
    path("", views.index, name="index"),
    path("productos/agregar/", views.producto_create_web, name="create_web"),

    # NUEVO: Ruta para editar producto completo vía web (MANTENIMIENTO ADAPTATIVO)
    # ANTERIOR: Solo había stock_web para editar stock
    path(
        "productos/<int:producto_id>/editar/",
        views.producto_update_web,
        name="update_web",
    ),

    path(
        "productos/<int:producto_id>/stock/movimiento/",
        views.producto_stock_web,
        name="stock_web",
    ),
    path(
        "productos/<int:producto_id>/eliminar/",
        views.producto_delete_web,
        name="delete_web",
    ),
    path("venta/confirmar/", views.venta_express_web, name="venta_express"),
]
