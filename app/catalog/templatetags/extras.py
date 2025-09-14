import re
from django import template
from django.utils.html import urlize
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(is_safe=True)
def urlize_mode(text, mode="ver_mas"):
    """
    Filtro personalizado:
    - ver_mas: convierte URLs en 'Ver más' con target="_blank'
    - ocultar: elimina las URLs del texto
    Además respeta saltos de línea (\n) como <br>.
    """
    if not text:
        return ""

    url_pattern = r'(https?://[^\s]+)'

    if mode == "ver_mas":
        def replace_url(match):
            url = match.group(0)
            return f'<a href="{url}" target="_blank">Ver video</a>'
        new_text = re.sub(url_pattern, replace_url, text)

    elif mode == "ocultar":
        new_text = re.sub(url_pattern, '', text).strip()

    else:
        new_text = urlize(text, nofollow=True, autoescape=True)

    # Reemplazar saltos de línea por <br>
    new_text = new_text.replace("\n", "<br>")

    return mark_safe(new_text)