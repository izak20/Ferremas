from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from .serializers import UsuarioSerializer, LoginSerializer
from .serializers import UsuarioListaSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from .models import Usuario
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404
from carro_compras.models import Venta
from django.utils import timezone
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

def iniciosesion(request):
    return render(request, 'usuarios/iniciosesion.html')

def registro(request):
    return render(request, 'usuarios/registro.html')

def cerrar_sesion(request):
    logout(request)
    return redirect('/')

class RegistroAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Registra un nuevo usuario en el sistema",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Nombre de usuario único'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='Correo electrónico'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Contraseña del usuario'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='Nombre'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Apellido'),
            },
            required=['username', 'email', 'password']
        ),
        responses={
            201: openapi.Response(
                description="Usuario registrado exitosamente",
                examples={
                    "application/json": {
                        "status": "success",
                        "message": "Usuario registrado exitosamente",
                        "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
                        "redirect_url": "/"
                    }
                }
            ),
            400: openapi.Response(
                description="Datos inválidos",
                examples={
                    "application/json": {
                        "username": ["Este campo es requerido."],
                        "email": ["Ingrese una dirección de correo electrónico válida."]
                    }
                }
            )
        }
    )
    def post(self, request):
        serializer = UsuarioSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'status': 'success',
                'message': 'Usuario registrado exitosamente',
                'token': token.key,
                'redirect_url': '/'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Inicia sesión de un usuario existente",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Nombre de usuario o email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Contraseña del usuario'),
            },
            required=['username', 'password']
        ),
        responses={
            200: openapi.Response(
                description="Inicio de sesión exitoso",
                examples={
                    "application/json": {
                        "status": "success",
                        "message": "Inicio de sesión exitoso",
                        "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
                        "redirect_url": "/"
                    }
                }
            ),
            400: openapi.Response(
                description="Credenciales incorrectas",
                examples={
                    "application/json": {
                        "non_field_errors": ["Credenciales incorrectas."]
                    }
                }
            )
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'status': 'success',
                'message': 'Inicio de sesión exitoso',
                'token': token.key,
                'redirect_url': '/'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get',
    operation_description="Obtiene la lista de todos los usuarios (solo administradores)",
    responses={
        200: openapi.Response(
            description="Lista de usuarios",
            examples={
                "application/json": [
                    {
                        "id": 1,
                        "username": "admin",
                        "email": "admin@example.com",
                        "first_name": "Administrador",
                        "last_name": "Sistema",
                        "is_active": True,
                        "is_staff": True,
                        "date_joined": "2024-01-01T10:00:00Z"
                    },
                    {
                        "id": 2,
                        "username": "usuario1",
                        "email": "usuario1@example.com",
                        "first_name": "Juan",
                        "last_name": "Pérez",
                        "is_active": True,
                        "is_staff": False,
                        "date_joined": "2024-01-02T15:30:00Z"
                    }
                ]
            }
        ),
        403: openapi.Response(description="Sin permisos de administrador")
    }
)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def api_lista_usuarios(request):
    usuarios = Usuario.objects.all()
    serializer = UsuarioListaSerializer(usuarios, many=True)
    return Response(serializer.data)    

@user_passes_test(lambda u: u.is_staff)
def vista_lista_usuarios(request):
    return render(request, 'usuarios/lista_usuarios.html')

################################################################
@user_passes_test(lambda u: u.is_staff, login_url='/usuarios/iniciosesion/')
def vista_agregar_usuario(request):
    return render(request, 'usuarios/agregar_usuario.html')

@swagger_auto_schema(
    method='post',
    operation_description="Crea un nuevo usuario (solo administradores)",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='Nombre de usuario único'),
            'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='Correo electrónico'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='Contraseña del usuario'),
            'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='Nombre'),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Apellido'),
            'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Si es administrador'),
            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Si está activo', default=True),
        },
        required=['username', 'email', 'password']
    ),
    responses={
        201: openapi.Response(
            description="Usuario creado exitosamente",
            examples={
                "application/json": {
                    "id": 3,
                    "username": "nuevo_usuario",
                    "email": "nuevo@example.com",
                    "first_name": "Nuevo",
                    "last_name": "Usuario",
                    "is_active": True,
                    "is_staff": False
                }
            }
        ),
        400: openapi.Response(
            description="Datos inválidos",
            examples={
                "application/json": {
                    "username": ["Ya existe un usuario con este nombre."],
                    "email": ["Este campo es requerido."]
                }
            }
        ),
        403: openapi.Response(description="Sin permisos de administrador")
    }
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def api_agregar_usuario(request):
    serializer = UsuarioSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)    

@swagger_auto_schema(
    method='patch',
    operation_description="Activa o desactiva un usuario (solo administradores)",
    manual_parameters=[
        openapi.Parameter(
            'id',
            openapi.IN_PATH,
            description="ID del usuario a modificar",
            type=openapi.TYPE_INTEGER
        )
    ],
    responses={
        200: openapi.Response(
            description="Estado del usuario actualizado",
            examples={
                "application/json": {
                    "message": "Estado actualizado",
                    "is_active": False
                }
            }
        ),
        403: openapi.Response(
            description="Sin permisos o intento de auto-suspensión",
            examples={
                "application/json": {
                    "error": "No puedes suspender tu propia cuenta."
                }
            }
        ),
        404: openapi.Response(description="Usuario no encontrado")
    }
)
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def api_toggle_activo_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)

    # Evitar que un administrador se auto-banee
    if usuario == request.user:
        return Response(
            {"error": "No puedes suspender tu propia cuenta."},
            status=403
        )

    usuario.is_active = not usuario.is_active
    usuario.save()
    return Response({"message": "Estado actualizado", "is_active": usuario.is_active})

@user_passes_test(lambda u: u.is_staff)
def vista_editar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)
    return render(request, 'usuarios/editar_usuario.html', {'usuario': usuario})

@swagger_auto_schema(
    method='put',
    operation_description="Edita un usuario existente (solo administradores)",
    manual_parameters=[
        openapi.Parameter(
            'id',
            openapi.IN_PATH,
            description="ID del usuario a editar",
            type=openapi.TYPE_INTEGER
        )
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='Nombre de usuario único'),
            'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='Correo electrónico'),
            'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='Nombre'),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Apellido'),
            'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Si es administrador'),
            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Si está activo'),
        }
    ),
    responses={
        200: openapi.Response(
            description="Usuario editado exitosamente",
            examples={
                "application/json": {
                    "id": 2,
                    "username": "usuario_editado",
                    "email": "editado@example.com",
                    "first_name": "Usuario",
                    "last_name": "Editado",
                    "is_active": True,
                    "is_staff": False
                }
            }
        ),
        400: openapi.Response(description="Datos inválidos"),
        403: openapi.Response(
            description="Sin permisos, usuario suspendido o auto-edición",
            examples={
                "application/json": {
                    "error": "No puedes editar un usuario suspendido."
                }
            }
        ),
        404: openapi.Response(description="Usuario no encontrado")
    }
)
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def api_editar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)

    # 🚫 No permitir editar usuarios suspendidos
    if not usuario.is_active:
        return Response({"error": "No puedes editar un usuario suspendido."}, status=status.HTTP_403_FORBIDDEN)

    # 🚫 No permitir editarse a uno mismo
    if request.user == usuario:
        return Response({"error": "No puedes editar tu propia cuenta desde el panel."}, status=status.HTTP_403_FORBIDDEN)

    serializer = UsuarioSerializer(usuario, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VistaRecuperarConValidacion(PasswordResetView):
    template_name = 'usuarios/recuperar.html'
    email_template_name = 'usuarios/password_reset_email.html'
    subject_template_name = 'usuarios/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        Usuario = get_user_model()
        if not Usuario.objects.filter(email=email).exists():
            messages.error(self.request, "El correo ingresado no está registrado.")
            return self.form_invalid(form)
        return super().form_valid(form)