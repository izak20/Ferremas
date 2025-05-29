from django.shortcuts import render, get_object_or_404
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import Producto, HistorialPrecio
from .serializers import ProductoSerializer
from rest_framework.permissions import BasePermission
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import OuterRef, Subquery, F
from django.http import HttpResponse
from carro_compras import views
from carro_compras.models import Venta, Detalle
from rest_framework import viewsets
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

#--------------------GET-----------------------

# Vista HTML
def vista_ofertas(request):
    return render(request, 'productos/ofertas.html')

def lista_productos(request):
    return render(request, 'productos/lista_productos.html', {
        'entorno': settings.ENTORNO
    })

# Vista API (muestra los productos en formato JSON)
@swagger_auto_schema(
    method='get',
    operation_description="Obtiene la lista de productos activos",
    responses={
        200: openapi.Response(
            description="Lista de productos",
            examples={
                "application/json": [
                    {
                        "id": 1,
                        "nombre": "Producto Ejemplo",
                        "descripcion": "Descripción del producto",
                        "precio": 25000,
                        "stock": 10,
                        "imagen": "url_imagen.jpg",
                        "activo": True
                    }
                ]
            }
        )
    }
)
@api_view(['GET'])
def api_lista_productos(request):
    productos = Producto.objects.filter(activo=True)
    serializer = ProductoSerializer(productos, many=True)
    return Response(serializer.data)

#--------------------POST----------------------

class EsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff

def es_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(es_admin)
def formulario_producto(request):
    return render(request, 'productos/formulario_producto.html')

@swagger_auto_schema(
    method='post',
    operation_description="Crea un nuevo producto (solo administradores)",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'nombre': openapi.Schema(type=openapi.TYPE_STRING, description='Nombre del producto'),
            'descripcion': openapi.Schema(type=openapi.TYPE_STRING, description='Descripción del producto'),
            'precio': openapi.Schema(type=openapi.TYPE_INTEGER, description='Precio del producto'),
            'stock': openapi.Schema(type=openapi.TYPE_INTEGER, description='Stock disponible'),
            'imagen': openapi.Schema(type=openapi.TYPE_STRING, description='URL de la imagen'),
            'activo': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Si el producto está activo')
        },
        required=['nombre', 'precio', 'stock']
    ),
    responses={
        201: openapi.Response(
            description="Producto creado exitosamente",
            examples={
                "application/json": {
                    "id": 1,
                    "nombre": "Nuevo Producto",
                    "descripcion": "Descripción del nuevo producto",
                    "precio": 15000,
                    "stock": 5,
                    "imagen": "nueva_imagen.jpg",
                    "activo": True
                }
            }
        ),
        400: openapi.Response(description="Datos inválidos"),
        403: openapi.Response(description="Sin permisos de administrador")
    }
)
@api_view(['POST'])
@permission_classes([EsAdmin])
def api_agregar_producto(request):
    serializer = ProductoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@login_required
def detalle_producto(request, id):
    try:
        producto = Producto.objects.get(id=id)
    except Producto.DoesNotExist:
        return render(request, 'productos/404.html')

    productos_en_carrito = []
    if request.user.is_authenticated:
        carrito = Venta.objects.filter(id_usuario=request.user, estado_venta='carrito').first()
        if carrito:
            productos_en_carrito = Detalle.objects.filter(id_venta=carrito).values_list('producto_id', flat=True)

    return render(request, 'productos/detalle.html', {
        'producto': producto,
        'productos_en_carrito': productos_en_carrito
    })

#--------------------------------

@csrf_exempt
@require_http_methods(["PATCH"])
@login_required(login_url='/usuarios/iniciosesion/')
def api_toggle_activo_producto(request, id):
    if not request.user.is_staff:
        return JsonResponse({'error': 'No tienes permisos para modificar productos.'}, status=403)

    try:
        producto = Producto.objects.get(id=id)
        producto.activo = not producto.activo
        producto.save()
        return JsonResponse({'mensaje': 'Estado del producto actualizado correctamente', 'activo': producto.activo}, status=200)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

@user_passes_test(es_admin, login_url='/')
def lista_productos_crud(request):
    return render(request, 'productos/crud_productos.html', {
        'entorno': settings.ENTORNO
    })

@swagger_auto_schema(
    method='put',
    operation_description="Edita un producto existente (solo administradores)",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'nombre': openapi.Schema(type=openapi.TYPE_STRING, description='Nombre del producto'),
            'descripcion': openapi.Schema(type=openapi.TYPE_STRING, description='Descripción del producto'),
            'precio': openapi.Schema(type=openapi.TYPE_INTEGER, description='Precio del producto'),
            'stock': openapi.Schema(type=openapi.TYPE_INTEGER, description='Stock disponible'),
            'imagen': openapi.Schema(type=openapi.TYPE_STRING, description='URL de la imagen'),
            'activo': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Si el producto está activo')
        }
    ),
    responses={
        200: openapi.Response(
            description="Producto editado exitosamente",
            examples={
                "application/json": {
                    "id": 1,
                    "nombre": "Producto Editado",
                    "descripcion": "Nueva descripción",
                    "precio": 20000,
                    "stock": 8,
                    "imagen": "imagen_editada.jpg",
                    "activo": True
                }
            }
        ),
        400: openapi.Response(description="Datos inválidos"),
        403: openapi.Response(description="Sin permisos de administrador"),
        404: openapi.Response(description="Producto no encontrado")
    }
)
@api_view(['PUT'])
@permission_classes([EsAdmin])
def api_editar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    nuevo_precio = request.data.get('precio')

    if nuevo_precio and int(nuevo_precio) != producto.precio:
        HistorialPrecio.objects.create(
            producto=producto,
            precio_anterior=producto.precio,
            precio_nuevo=int(nuevo_precio)
        )

    serializer = ProductoSerializer(producto, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@user_passes_test(es_admin, login_url='/usuarios/iniciosesion/')
def editar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    return render(request, 'productos/editar_producto.html', {
        'producto': producto,
        'entorno': settings.ENTORNO
    })

@login_required
def prueba_permisos(request):
    return HttpResponse(f"Usuario: {request.user.username} | Staff: {request.user.is_staff}")

@swagger_auto_schema(
    method='get',
    operation_description="Obtiene productos en oferta (con descuento)",
    responses={
        200: openapi.Response(
            description="Lista de productos en oferta",
            examples={
                "application/json": [
                    {
                        "id": 1,
                        "nombre": "Producto en Oferta",
                        "descripcion": "Producto con descuento",
                        "precio": 15000,
                        "precio_anterior": 20000,
                        "imagen": "producto_oferta.jpg",
                        "stock": 5
                    }
                ]
            }
        )
    }
)
@api_view(['GET'])
def api_ofertas(request):
    from django.db.models import OuterRef, Subquery, F
    from .models import Producto, HistorialPrecio

    ultimos = HistorialPrecio.objects.filter(
        producto=OuterRef('pk')
    ).order_by('-fecha')

    productos_con_descuento = Producto.objects.annotate(
        precio_anterior=Subquery(ultimos.values('precio_anterior')[:1]),
        precio_nuevo=Subquery(ultimos.values('precio_nuevo')[:1])
    ).filter(precio_anterior__gt=F('precio_nuevo'))

    resultado = []
    for p in productos_con_descuento:
        resultado.append({
            'id': p.id,
            'nombre': p.nombre,
            'descripcion': p.descripcion,
            'precio': p.precio,
            'imagen': p.imagen,
            'precio_anterior': getattr(p, 'precio_anterior', None),
            'stock': p.stock
        })

    return Response(resultado)

@swagger_auto_schema(
    method='get',
    operation_description="Obtiene todos los productos para administradores",
    responses={
        200: openapi.Response(
            description="Lista completa de productos",
            examples={
                "application/json": [
                    {
                        "id": 1,
                        "nombre": "Producto Admin",
                        "descripcion": "Producto visible para admin",
                        "precio": 25000,
                        "stock": 10,
                        "imagen": "admin_producto.jpg",
                        "activo": False
                    }
                ]
            }
        ),
        403: openapi.Response(description="Sin permisos de administrador")
    }
)
@api_view(['GET'])
@permission_classes([EsAdmin])
def api_lista_productos_admin(request):
    productos = Producto.objects.all()
    serializer = ProductoSerializer(productos, many=True)
    return Response(serializer.data)