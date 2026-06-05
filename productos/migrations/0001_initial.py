# Generated manually for the Fase 1 inventory CRUD.

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Producto",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nombre", models.CharField(max_length=120)),
                (
                    "categoria",
                    models.CharField(
                        choices=[
                            ("zapatos", "Zapatos"),
                            ("mochilas", "Mochilas"),
                            ("camisetas", "Camisetas"),
                            ("uniformes", "Uniformes"),
                            ("sombreros", "Sombreros"),
                            ("plasticos", "Plasticos"),
                            ("bolsas", "Bolsas"),
                            ("otros", "Otros"),
                        ],
                        default="otros",
                        max_length=30,
                    ),
                ),
                (
                    "stock_actual",
                    models.IntegerField(
                        validators=[django.core.validators.MinValueValidator(0)]
                    ),
                ),
                (
                    "stock_minimo",
                    models.IntegerField(
                        validators=[django.core.validators.MinValueValidator(0)]
                    ),
                ),
                (
                    "precio_venta",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(0)],
                    ),
                ),
            ],
            options={
                "ordering": ["nombre"],
            },
        ),
    ]
