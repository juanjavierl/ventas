from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os
#procesar imagen produto
def procesar_imagen(model_instance, campo_imagen):
    imagen = getattr(model_instance, campo_imagen)
    if not imagen:
        return

    image_path = imagen.path
    img = Image.open(image_path)
    formato_original = img.format or 'JPEG'

    # Límites deseados
    min_width, min_height = 300, 200
    max_width, max_height = 900, 500
    max_file_size_kb = 150

    original_size_kb = os.path.getsize(image_path) / 1024
    # ¿Redimensionar hacia arriba?
    debe_escalar = img.width < min_width or img.height < min_height
    # ¿Optimizar tamaño?
    debe_optimizar = (
        img.width > max_width or
        img.height > max_height or
        original_size_kb > max_file_size_kb
    )

    if debe_escalar or debe_optimizar:
        # Agrandar si es muy pequeña
        if debe_escalar:
            scale_x = max(min_width / img.width, 1)
            scale_y = max(min_height / img.height, 1)
            scale_factor = max(scale_x, scale_y)
            new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
            img = img.resize(new_size, Image.LANCZOS)
        # Reducir si es muy grande
        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.LANCZOS)
        # Convertir si es necesario (para JPEG/PNG)
        if formato_original == 'JPEG' and img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        elif formato_original == 'PNG' and img.mode == 'P':
            img = img.convert('RGBA')
        # Guardar con compresión si es muy pesada
        buffer = BytesIO()
        save_kwargs = {'quality': 70} if formato_original == 'JPEG' else {}
        img.save(buffer, format=formato_original, **save_kwargs)
        buffer.seek(0)

        filename, ext = os.path.splitext(imagen.name)
        nuevo_nombre = f"{filename}{ext.lower()}"
        getattr(model_instance, campo_imagen).save(nuevo_nombre, ContentFile(buffer.read()), save=False)


def procesar_imagen_portada(model_instance, campo_imagen):
    imagen = getattr(model_instance, campo_imagen)
    if not imagen:
        return

    image_path = imagen.path
    img = Image.open(image_path)
    formato_original = img.format or 'JPEG'

    # Límites deseados
    min_width, min_height = 800, 600
    max_width, max_height = 1200, 800
    max_file_size_kb = 300

    original_size_kb = os.path.getsize(image_path) / 1024
    # ¿Redimensionar hacia arriba?
    debe_escalar = img.width < min_width or img.height < min_height
    # ¿Optimizar tamaño?
    debe_optimizar = (
        img.width > max_width or
        img.height > max_height or
        original_size_kb > max_file_size_kb
    )

    if debe_escalar or debe_optimizar:
        # Agrandar si es muy pequeña
        if debe_escalar:
            scale_x = max(min_width / img.width, 1)
            scale_y = max(min_height / img.height, 1)
            scale_factor = max(scale_x, scale_y)
            new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
            img = img.resize(new_size, Image.LANCZOS)
        # Reducir si es muy grande
        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.LANCZOS)
        # Convertir si es necesario (para JPEG/PNG)
        if formato_original == 'JPEG' and img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        elif formato_original == 'PNG' and img.mode == 'P':
            img = img.convert('RGBA')
        # Guardar con compresión si es muy pesada
        buffer = BytesIO()
        save_kwargs = {'quality': 95} if formato_original == 'JPEG' else {}
        img.save(buffer, format=formato_original, **save_kwargs)
        buffer.seek(0)

        filename, ext = os.path.splitext(imagen.name)
        nuevo_nombre = f"{filename}{ext.lower()}"
        getattr(model_instance, campo_imagen).save(nuevo_nombre, ContentFile(buffer.read()), save=False)
