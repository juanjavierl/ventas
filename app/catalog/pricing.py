from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError


def normalize_attribute_values(values):
    """Return [{value, price_extra}] while preserving legacy string options."""
    if not isinstance(values, list):
        raise ValidationError('Las opciones deben ser una lista.')
    normalized = []
    for option in values:
        if isinstance(option, str):
            label, extra = option, Decimal('0')
        elif isinstance(option, dict) and isinstance(option.get('value'), str):
            label = option['value']
            try:
                extra = Decimal(str(option.get('price_extra', '0')))
            except (InvalidOperation, TypeError, ValueError):
                raise ValidationError('El precio adicional debe ser numérico.')
            if not extra.is_finite() or extra.as_tuple().exponent < -2:
                raise ValidationError('El precio adicional debe ser válido y tener hasta dos decimales.')
        else:
            raise ValidationError('Cada opción debe contener un nombre válido.')
        if not label.strip():
            raise ValidationError('Las opciones no pueden estar vacías.')
        normalized.append({'value': label.strip(), 'price_extra': format(extra, '.2f')})
    if len({item['value'] for item in normalized}) != len(normalized):
        raise ValidationError('No se permiten opciones repetidas.')
    return normalized


def option_label(option):
    return option['value'] if isinstance(option, dict) else option


def calculate_product_price(product, selected):
    """Validate selected labels against current DB options and return snapshot and price."""
    attributes = list(product.attributes.filter(is_selectable=True))
    expected = {attribute.name: attribute for attribute in attributes}
    if not isinstance(selected, dict) or set(selected) != set(expected):
        raise ValidationError('Las opciones seleccionadas no son válidas.')
    snapshot, total_extra = {}, Decimal('0')
    for name, attribute in expected.items():
        options = normalize_attribute_values(attribute.values)
        choice = next((o for o in options if o['value'] == selected[name]), None)
        if choice is None:
            raise ValidationError('Una opción no pertenece al producto.')
        extra = Decimal(choice['price_extra']) if attribute.is_selectable else Decimal('0')
        snapshot[name] = {'value': choice['value'], 'price_extra': format(extra, '.2f')}
        total_extra += extra
    return Decimal(product.price) + total_extra, snapshot
