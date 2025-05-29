# Proyecto Django

Este es un proyecto basado en Django. A continuación, encontrarás los pasos necesarios para clonar el repositorio, instalar los requerimientos y ejecutar el proyecto localmente.

## Requisitos previos

Antes de iniciar, asegúrate de tener instalado:

- **Python** (versión 3.8 o superior): https://www.python.org/downloads/
- **pip** (instalador de paquetes de Python): Generalmente viene incluido con Python. Puedes verificarlo con:
  pip --version
- **Git** (opcional, para clonar el repositorio): https://git-scm.com/

## Pasos para iniciar el proyecto

### 1. Clona este repositorio
git clone https://github.com/izak20/Ferremas.git
cd tu-repo

### 2. Instala Django y otras dependencias

pip install -r requirements.txt

> Asegúrate de tener un archivo requirements.txt con las dependencias necesarias, incluyendo Django. Si no lo tienes, puedes instalar Django manualmente con:
pip install django

### 3. Aplica las migraciones a la base de datos

python manage.py migrate

### 4. Crea un superusuario (opcional, para acceder al panel de administración)

python manage.py createsuperuser

### 5. Ejecuta el servidor de desarrollo

python manage.py runserver

Accede a tu aplicación en el navegador en: http://127.0.0.1:8000

## Notas adicionales

- Para hacer migraciones personalizadas (cuando cambias modelos):
  python manage.py makemigrations
  python manage.py migrate

---

¡Listo! Con estos pasos podrás iniciar y ejecutar correctamente tu aplicación Django.
