from django import forms
from django.core.exceptions import ValidationError

from .models import Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        # ANTERIOR: fields = ["nombre", "categoria", "stock_actual", "stock_minimo", "precio_venta"]
        # CAMBIO: Agregar "descripcion" para permitir datos más completos (MANTENIMIENTO ADAPTATIVO)
        fields = [
            "nombre",
            "descripcion",
            "categoria",
            "stock_actual",
            "stock_minimo",
            "precio_venta",
        ]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej. Camiseta EPN",
                }
            ),
            # NUEVO: Widget para descripción (MANTENIMIENTO ADAPTATIVO)
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Descripción del producto",
                    "rows": 3,
                }
            ),
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "stock_actual": forms.NumberInput(
                attrs={"class": "form-control", "min": "0"}
            ),
            "stock_minimo": forms.NumberInput(
                attrs={"class": "form-control", "min": "0"}
            ),
            "precio_venta": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                    "placeholder": "0.00",
                }
            ),
        }

    # NUEVO: Validación personalizada para evitar nombres duplicados (MANTENIMIENTO CORRECTIVO)
    def clean_nombre(self):
        nombre = self.cleaned_data.get("nombre", "").strip()
        if not nombre:
            raise ValidationError("El nombre no puede estar vacío.")

        # Validar nombre único (excepto si es edición del mismo producto)
        qs = Producto.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError(f"El producto '{nombre}' ya existe.")
        return nombre

    # NUEVO: Validación para garantizar que stock_actual >= stock_minimo (MANTENIMIENTO CORRECTIVO)
    def clean(self):
        cleaned_data = super().clean()
        stock_actual = cleaned_data.get("stock_actual", 0)
        stock_minimo = cleaned_data.get("stock_minimo", 0)

        if stock_actual < stock_minimo:
            raise ValidationError(
                "El stock actual no puede ser menor al stock mínimo."
            )
        return cleaned_data

