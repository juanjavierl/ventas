
from decimal import ROUND_FLOOR, Decimal
import phonenumbers

def calcular_puntos_fidelidad(total_compra, fidelidad):
    """
    Calcula los puntos que genera una compra.
    No modifica la cuenta del cliente ni guarda datos.
    """
    total = Decimal(str(total_compra))

    if total <= 0 or not fidelidad or not fidelidad.vigente:
        return 0

    if not fidelidad.aplica(total):
        return 0

    referencia = Decimal(str(fidelidad.compra_mayores))

    # Si el valor es 0, se otorga 1 punto por compra válida.
    if referencia == 0:
        return 1

    return int(
        (total / referencia).to_integral_value(
            rounding=ROUND_FLOOR
        )
    )

def obtener_numero_nacional(numero):
    if not numero:
        return ""

    try:
        telefono = phonenumbers.parse(numero, None)

        if phonenumbers.is_valid_number(telefono):
            return str(telefono.national_number)

        return numero

    except phonenumbers.NumberParseException:
        return numero