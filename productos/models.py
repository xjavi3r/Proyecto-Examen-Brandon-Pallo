from django.core.validators import MinValueValidator
from django.db import models


class Producto(models.Model):
    class Categoria(models.TextChoices):
        ZAPATOS = "zapatos", "Zapatos"
        MOCHILAS = "mochilas", "Mochilas"
        CAMISETAS = "camisetas", "Camisetas"
        UNIFORMES = "uniformes", "Uniformes"
        SOMBREROS = "sombreros", "Sombreros"
        PLASTICOS = "plasticos", "Plasticos"
        BOLSAS = "bolsas", "Bolsas"
        OTROS = "otros", "Otros"

    # ANTERIOR: nombre = models.CharField(max_length=120)
    # CAMBIO: Agregar unique=True para evitar productos duplicados (MANTENIMIENTO CORRECTIVO)
    nombre = models.CharField(max_length=120, unique=True)

    # NUEVO: Campo de descripción para mejorar información del producto (MANTENIMIENTO ADAPTATIVO)
    descripcion = models.TextField(blank=True, null=True)

    categoria = models.CharField(
        max_length=30,
        choices=Categoria.choices,
        default=Categoria.OTROS,
    )
    stock_actual = models.IntegerField(validators=[MinValueValidator(0)])
    stock_minimo = models.IntegerField(validators=[MinValueValidator(0)])
    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    # NUEVO: Campos de auditoría para rastrear cambios (MANTENIMIENTO ADAPTATIVO)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.categoria})"

    def to_dict(self):
        # ANTERIOR: Retornaba solo 6 campos
        # CAMBIO: Agregar descripción y fechas de auditoría (MANTENIMIENTO ADAPTATIVO)
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,  # NUEVO
            "categoria": self.categoria,
            "stock_actual": self.stock_actual,
            "stock_minimo": self.stock_minimo,
            "precio_venta": str(self.precio_venta),
            "fecha_creacion": self.fecha_creacion.isoformat(),  # NUEVO
            "fecha_actualizacion": self.fecha_actualizacion.isoformat(),  # NUEVO
        }
