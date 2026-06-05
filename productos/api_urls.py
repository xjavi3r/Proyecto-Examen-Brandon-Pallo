from django.urls import path

from . import views

app_name = "productos_api"

urlpatterns = [
    path("productos/", views.productos_list_create, name="list_create"),

    # NUEVO: Obtener un producto específico por ID (MANTENIMIENTO ADAPTATIVO - READ completo)
    path("productos/<int:producto_id>/", views.producto_detail, name="detail"),

    # NUEVO: Actualizar todos los campos del producto (MANTENIMIENTO ADAPTATIVO - UPDATE completo)
    # ANTERIOR: Solo existía producto_update_stock que actualizaba stock
    path(
        "productos/<int:producto_id>/actualizar/",
        views.producto_update_completo,
        name="update_completo",
    ),

    # ANTERIOR: path("productos/<int:producto_id>/stock/", views.producto_update_stock, name="update_stock")
    # CAMBIO: Mantener para compatibilidad backwards - actualizar solo stock
    path(
        "productos/<int:producto_id>/stock/",
        views.producto_update_stock,
        name="update_stock",
    ),

    # ANTERIOR: path("productos/<int:producto_id>/", views.producto_delete, name="delete")
    # CAMBIO: Se reemplazó por producto_detail arriba, pero mantener DELETE
    # Usando POST en caso de que sea necesario (algunos clientes no soportan DELETE)
]
