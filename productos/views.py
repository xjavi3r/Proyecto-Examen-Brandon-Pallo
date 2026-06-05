import json

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .event_client import enviar_evento_async
from .forms import ProductoForm
from .models import Producto


def _json_body(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        raise ValidationError("El cuerpo de la peticion debe ser JSON valido.")


def _error(message, status=400):
    return JsonResponse({"ok": False, "error": message}, status=status)


def _dashboard_queryset(request):
    productos = Producto.objects.all()
    busqueda = request.GET.get("q", "").strip()
    categoria = request.GET.get("categoria", "").strip()

    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda)

    if categoria:
        productos = productos.filter(categoria=categoria)

    return productos, busqueda, categoria


@require_http_methods(["GET"])
def index(request):
    productos, busqueda, categoria = _dashboard_queryset(request)
    productos_list = list(productos)

    enviar_evento_async(
        "QUERY",
        f"Se consulto el dashboard de inventario. Total encontrados: {len(productos_list)}",
        {
            "total": len(productos_list),
            "busqueda": busqueda,
            "categoria": categoria,
        },
        title="Consulta de dashboard",
    )

    context = {
        "productos": productos_list,
        "categorias": Producto.Categoria.choices,
        "busqueda": busqueda,
        "categoria_actual": categoria,
        "producto_form": ProductoForm(),
        "total_productos": Producto.objects.count(),
        "productos_bajo_stock": Producto.objects.filter(
            stock_actual__lte=models.F("stock_minimo")
        ).count(),
    }
    return render(request, "productos/index.html", context)


@require_http_methods(["POST"])
def producto_create_web(request):
    form = ProductoForm(request.POST)

    if not form.is_valid():
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(request, error)
        return redirect("productos:index")

    producto = form.save()
    payload = producto.to_dict()
    enviar_evento_async(
        "CREATE",
        f"Se registro un nuevo producto: {producto.nombre} con stock inicial de {producto.stock_actual}",
        payload,
        title="Producto creado",
    )
    messages.success(request, f"Producto {producto.nombre} agregado correctamente.")
    return redirect("productos:index")


# NUEVO: Función para actualizar producto completo vía formulario web (MANTENIMIENTO ADAPTATIVO)
@require_http_methods(["GET", "POST"])
def producto_update_web(request, producto_id):
    """
    Permite editar todos los campos del producto (nombre, descripción, categoría, precios, etc.)
    No solo el stock como la función anterior.
    """
    try:
        producto = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        messages.error(request, "Producto no encontrado.")
        return redirect("productos:index")

    if request.method == "POST":
        form = ProductoForm(request.POST, instance=producto)
        if not form.is_valid():
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)
            return redirect("productos:index")

        # Guardar estado anterior para auditoría
        producto_anterior = producto.to_dict()
        producto = form.save()

        # Enviar evento con cambios
        payload = {
            "id": producto.id,
            "anterior": producto_anterior,
            "nuevo": producto.to_dict(),
        }
        enviar_evento_async(
            "UPDATE",
            f"Se actualizo el producto {producto.nombre}",
            payload,
            title="Producto actualizado",
        )
        messages.success(request, f"Producto {producto.nombre} actualizado correctamente.")
        return redirect("productos:index")

    form = ProductoForm(instance=producto)
    context = {"form": form, "producto": producto, "accion": "editar"}
    return render(request, "productos/form.html", context)


@require_http_methods(["POST"])
def producto_stock_web(request, producto_id):
    try:
        producto = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        messages.error(request, "Producto no encontrado.")
        return redirect("productos:index")

    movimiento = request.POST.get("movimiento")
    try:
        cantidad = int(request.POST.get("cantidad", "0"))
    except ValueError:
        cantidad = 0

    if cantidad <= 0:
        messages.error(request, "La cantidad debe ser mayor a cero.")
        return redirect("productos:index")

    stock_anterior = producto.stock_actual
    if movimiento == "entrada":
        producto.stock_actual += cantidad
        descripcion = f"Se ingreso stock de {producto.nombre}: +{cantidad} unidades"
        titulo = "Ingreso de stock"
    elif movimiento == "venta":
        if producto.stock_actual < cantidad:
            messages.error(request, "No hay stock suficiente para registrar la venta.")
            return redirect("productos:index")
        producto.stock_actual -= cantidad
        descripcion = f"Se registro una venta de {producto.nombre}: -{cantidad} unidades"
        titulo = "Venta registrada"
    else:
        messages.error(request, "Movimiento de stock no valido.")
        return redirect("productos:index")

    producto.full_clean()
    producto.save(update_fields=["stock_actual"])

    payload = producto.to_dict()
    payload.update(
        {
            "stock_actual_anterior": stock_anterior,
            "cantidad": cantidad,
            "movimiento": movimiento,
        }
    )
    enviar_evento_async("UPDATE", descripcion, payload, title=titulo)
    messages.success(request, "Stock actualizado correctamente.")
    return redirect("productos:index")


@require_http_methods(["POST"])
def producto_delete_web(request, producto_id):
    try:
        producto = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        messages.error(request, "Producto no encontrado.")
        return redirect("productos:index")

    payload = producto.to_dict()
    producto.delete()
    enviar_evento_async(
        "DELETE",
        f"Se elimino el producto {payload['nombre']} del inventario",
        payload,
        title="Producto eliminado",
    )
    messages.success(request, f"Producto {payload['nombre']} eliminado.")
    return redirect("productos:index")


@require_http_methods(["POST"])
def venta_express_web(request):
    try:
        cart_items = json.loads(request.POST.get("cart_payload", "[]"))
    except json.JSONDecodeError:
        messages.error(request, "No se pudo procesar el carrito de venta.")
        return redirect("productos:index")

    if not cart_items:
        messages.error(request, "El carrito esta vacio.")
        return redirect("productos:index")

    cantidades = {}
    for item in cart_items:
        try:
            producto_id = int(item.get("id"))
            cantidad = int(item.get("quantity"))
        except (TypeError, ValueError):
            messages.error(request, "El carrito contiene datos invalidos.")
            return redirect("productos:index")

        if cantidad <= 0:
            messages.error(request, "Todas las cantidades deben ser mayores a cero.")
            return redirect("productos:index")

        cantidades[producto_id] = cantidades.get(producto_id, 0) + cantidad

    eventos = []
    total_unidades = 0

    try:
        with transaction.atomic():
            productos = {
                producto.id: producto
                for producto in Producto.objects.select_for_update().filter(
                    id__in=cantidades.keys()
                )
            }

            if len(productos) != len(cantidades):
                messages.error(request, "Uno de los productos ya no esta disponible.")
                return redirect("productos:index")

            for producto_id, cantidad in cantidades.items():
                producto = productos[producto_id]

                if producto.stock_actual < cantidad:
                    messages.error(
                        request,
                        f"No hay stock suficiente para vender {producto.nombre}.",
                    )
                    return redirect("productos:index")

                stock_anterior = producto.stock_actual
                producto.stock_actual -= cantidad
                producto.full_clean()
                producto.save(update_fields=["stock_actual"])
                total_unidades += cantidad

                payload = producto.to_dict()
                payload.update(
                    {
                        "stock_actual_anterior": stock_anterior,
                        "cantidad": cantidad,
                        "movimiento": "venta_express",
                        "subtotal": str(producto.precio_venta * cantidad),
                    }
                )
                eventos.append(
                    (
                        "UPDATE",
                        f"Venta express: {cantidad} unidad(es) de {producto.nombre}",
                        payload,
                        "Venta express confirmada",
                    )
                )
    except ValidationError:
        messages.error(request, "La venta no pudo validarse correctamente.")
        return redirect("productos:index")

    for action, description, payload, title in eventos:
        enviar_evento_async(action, description, payload, title=title)

    messages.success(
        request,
        f"Venta confirmada. Se descontaron {total_unidades} unidad(es) del inventario.",
    )
    return redirect("productos:index")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def productos_list_create(request):
    if request.method == "GET":
        productos = [producto.to_dict() for producto in Producto.objects.all()]
        enviar_evento_async(
            "QUERY",
            f"Se consulto el listado de productos. Total encontrados: {len(productos)}",
            {"total": len(productos), "productos": productos},
            title="Consulta de productos",
        )
        return JsonResponse({"ok": True, "productos": productos})

    try:
        data = _json_body(request)
        producto = Producto(
            nombre=data.get("nombre", ""),
            descripcion=data.get("descripcion", ""),
            ubicacion=data.get("ubicacion", ""),
            categoria=data.get("categoria", Producto.Categoria.OTROS),
            stock_actual=data.get("stock_actual", 0),
            stock_minimo=data.get("stock_minimo", 0),
            precio_venta=data.get("precio_venta", 0),
        )
        producto.full_clean()
        producto.save()
    except ValidationError as exc:
        return _error(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

    payload = producto.to_dict()
    enviar_evento_async(
        "CREATE",
        f"Se registro un nuevo producto: {producto.nombre} con stock inicial de {producto.stock_actual}",
        payload,
        title="Producto creado",
    )
    return JsonResponse({"ok": True, "producto": payload}, status=201)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def producto_detail(request, producto_id):
    """
    NUEVO: Endpoint API para obtener un producto específico por ID (MANTENIMIENTO ADAPTATIVO)
    Complementa la funcionalidad de lectura (READ del CRUD)
    """
    try:
        producto = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        return _error("Producto no encontrado.", status=404)

    if request.method == "DELETE":
        payload = producto.to_dict()
        producto.delete()
        enviar_evento_async(
            "DELETE",
            f"Se elimino el producto {payload['nombre']} del inventario",
            payload,
            title="Producto eliminado",
        )
        return JsonResponse({"ok": True, "producto": payload})

    enviar_evento_async(
        "QUERY",
        f"Se consulto el producto {producto.nombre}",
        producto.to_dict(),
        title="Consulta de producto",
    )
    return JsonResponse({"ok": True, "producto": producto.to_dict()})


@csrf_exempt
@require_http_methods(["PUT"])
def producto_update_completo(request, producto_id):
    """
    NUEVO: Endpoint API para actualizar todos los campos del producto (MANTENIMIENTO ADAPTATIVO)
    ANTERIOR: Solo existía producto_update_stock que actualizaba solo stock
    CAMBIO: Agregar función que permite editar nombre, descripción, categoría, precios, etc.
    """
    try:
        producto = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        return _error("Producto no encontrado.", status=404)

    try:
        data = _json_body(request)
        # Guardar estado anterior para auditoría
        producto_anterior = producto.to_dict()

        # Actualizar solo campos permitidos (no permitir id, fechas)
        campos_permitidos = [
            "nombre",
            "descripcion",
            "ubicacion",
            "categoria",
            "stock_actual",
            "stock_minimo",
            "precio_venta",
        ]
        for campo in campos_permitidos:
            if campo in data:
                setattr(producto, campo, data[campo])

        # Validar antes de guardar
        producto.full_clean()
        producto.save()
    except ValidationError as exc:
        return _error(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

    # Enviar evento con cambios comparativos
    payload = {
        "id": producto.id,
        "anterior": producto_anterior,
        "nuevo": producto.to_dict(),
    }
    enviar_evento_async(
        "UPDATE",
        f"Se actualizo el producto {producto.nombre}",
        payload,
        title="Producto actualizado",
    )
    return JsonResponse({"ok": True, "producto": producto.to_dict()})


@csrf_exempt
# ANTERIOR: @require_http_methods(["PATCH", "PUT"])
# CAMBIO: Mantener ambos métodos para compatibilidad (MANTENIMIENTO CORRECTIVO)
@require_http_methods(["PATCH", "PUT"])
def producto_update_stock(request, producto_id):
    """
    Actualiza SOLO el stock del producto vía API.
    NOTA: Mantener por compatibilidad backwards. Usar producto_update_completo para cambios más complejos.
    """
    try:
        producto = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        return _error("Producto no encontrado.", status=404)

    try:
        data = _json_body(request)
        stock_actual_anterior = producto.stock_actual
        producto.stock_actual = data["stock_actual"]
        producto.full_clean()
        producto.save(update_fields=["stock_actual"])
    except KeyError:
        return _error("El campo stock_actual es obligatorio.")
    except ValidationError as exc:
        return _error(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

    payload = producto.to_dict()
    payload["stock_actual_anterior"] = stock_actual_anterior
    enviar_evento_async(
        "UPDATE",
        f"Se actualizo el stock de {producto.nombre}: {stock_actual_anterior} -> {producto.stock_actual}",
        payload,
        title="Stock actualizado",
    )
    return JsonResponse({"ok": True, "producto": producto.to_dict()})


@csrf_exempt
@require_http_methods(["DELETE"])
def producto_delete(request, producto_id):
    try:
        producto = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        return _error("Producto no encontrado.", status=404)
    payload = producto.to_dict()
    producto.delete()

    enviar_evento_async(
        "DELETE",
        f"Se elimino el producto {payload['nombre']} del inventario",
        payload,
        title="Producto eliminado",
    )
    return JsonResponse({"ok": True, "producto": payload})
