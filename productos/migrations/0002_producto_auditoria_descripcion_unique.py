# Generated to align Producto with the current model definition.

import django.core.validators
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("productos", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="producto",
            name="descripcion",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="producto",
            name="fecha_creacion",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="producto",
            name="fecha_actualizacion",
            field=models.DateTimeField(
                auto_now=True,
                default=django.utils.timezone.now,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="producto",
            name="nombre",
            field=models.CharField(max_length=120, unique=True),
        ),
        migrations.AlterField(
            model_name="producto",
            name="precio_venta",
            field=models.DecimalField(
                decimal_places=2,
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
    ]
