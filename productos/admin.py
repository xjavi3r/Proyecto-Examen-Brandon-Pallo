from django.contrib import admin

from .models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    # ANTERIOR: list_display = ("id", "nombre", "categoria", "stock_actual", "stock_minimo", "precio_venta")
    # CAMBIO: Agregar fecha_creacion para rastreo. Mostrar más información de auditoría (MANTENIMIENTO ADAPTATIVO)
    list_display = (
        "id",
        "nombre",
        "categoria",
        "stock_actual",
        "stock_minimo",
        "precio_venta",
        "fecha_creacion",
    )

    # ANTERIOR: list_filter = ("categoria",)
    # CAMBIO: Agregar filtro por fecha para mejor búsqueda de registros (MANTENIMIENTO ADAPTATIVO)
    list_filter = ("categoria", "fecha_creacion")

    # ANTERIOR: search_fields = ("nombre",)
    # CAMBIO: Agregar búsqueda por descripción también (MANTENIMIENTO ADAPTATIVO)
    search_fields = ("nombre", "descripcion")

    # NUEVO: Campos de solo lectura para evitar edición accidental de fechas (MANTENIMIENTO CORRECTIVO)
    readonly_fields = ("fecha_creacion", "fecha_actualizacion")

    # NUEVO: Organizar campos en grupos (fieldsets) para mejor legibilidad (MANTENIMIENTO ADAPTATIVO)
    fieldsets = (
        ("Información General", {
            "fields": ("nombre", "descripcion", "categoria")
        }),
        ("Inventario", {
            "fields": ("stock_actual", "stock_minimo", "precio_venta")
        }),
        ("Auditoría", {
            "fields": ("fecha_creacion", "fecha_actualizacion"),
            "classes": ("collapse",)  # Contraer sección por defecto
        }),
    )
