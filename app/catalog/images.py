from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os

def procesar_imagen(model_instance, campo_imagen):
    imagen = getattr(model_instance, campo_imagen)
    if not imagen:
        return

    # Leer la imagen desde memoria (sin depender de .path)
    img = Image.open(imagen.file)
    formato_original = img.format or 'JPEG'

    # Límites deseados
    min_width, min_height = 600, 400
    max_width, max_height = 901, 500
    max_file_size_kb = 150

    # Tamaño original del archivo en KB (en memoria)
    imagen.file.seek(0, os.SEEK_END)
    original_size_kb = imagen.file.tell() / 1024
    imagen.file.seek(0)

    debe_escalar = img.width < min_width or img.height < min_height
    debe_optimizar = (
        img.width > max_width or
        img.height > max_height or
        original_size_kb > max_file_size_kb
    )

    if debe_escalar or debe_optimizar:
        if debe_escalar:
            scale_x = max(min_width / img.width, 1)
            scale_y = max(min_height / img.height, 1)
            scale_factor = max(scale_x, scale_y)
            new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
            img = img.resize(new_size, Image.LANCZOS)

        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.LANCZOS)

        if formato_original == 'JPEG' and img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        elif formato_original == 'PNG' and img.mode == 'P':
            img = img.convert('RGBA')

        buffer = BytesIO()
        save_kwargs = {'quality': 70, 'optimize': True} if formato_original == 'JPEG' else {}
        img.save(buffer, format=formato_original, **save_kwargs)
        buffer.seek(0)

        filename, ext = os.path.splitext(imagen.name)
        nuevo_nombre = f"{filename}{ext.lower()}"
        getattr(model_instance, campo_imagen).save(nuevo_nombre, ContentFile(buffer.read()), save=False)


def procesar_imagen_portada(model_instance, campo_imagen):
    imagen = getattr(model_instance, campo_imagen)
    if not imagen:
        return

    # Leer la imagen desde memoria (sin depender de .path)
    img = Image.open(imagen.file)
    formato_original = img.format or 'JPEG'

    # Límites deseados
    min_width, min_height = 1200, 900
    max_width, max_height = 1600, 1200
    max_file_size_kb = 200

    # Tamaño original del archivo en KB (en memoria)
    imagen.file.seek(0, os.SEEK_END)
    original_size_kb = imagen.file.tell() / 1024
    imagen.file.seek(0)

    debe_escalar = img.width < min_width or img.height < min_height
    debe_optimizar = (
        img.width > max_width or
        img.height > max_height or
        original_size_kb > max_file_size_kb
    )

    if debe_escalar or debe_optimizar:
        if debe_escalar:
            scale_x = max(min_width / img.width, 1)
            scale_y = max(min_height / img.height, 1)
            scale_factor = max(scale_x, scale_y)
            new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
            img = img.resize(new_size, Image.LANCZOS)

        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.LANCZOS)

        if formato_original == 'JPEG' and img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        elif formato_original == 'PNG' and img.mode == 'P':
            img = img.convert('RGBA')

        buffer = BytesIO()
        save_kwargs = {'quality': 70, 'optimize': True} if formato_original == 'JPEG' else {}
        img.save(buffer, format=formato_original, **save_kwargs)
        buffer.seek(0)

        filename, ext = os.path.splitext(imagen.name)
        nuevo_nombre = f"{filename}{ext.lower()}"
        getattr(model_instance, campo_imagen).save(nuevo_nombre, ContentFile(buffer.read()), save=False)
