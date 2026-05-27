"""
Row-level validation rules per destination table.

Each validator receives a transformed row dict and a context dict
(containing DB state like existing LPNs) and returns a list of error
strings. Empty list = valid row.
"""
from typing import Any


class RowStatus:
    VALID = "VALIDA"
    TRANSFORMED = "TRANSFORMADA"
    CRITICAL = "ERROR_CRITICO"
    SKIP = "OMITIR"


def validate_physical_item(row: dict, context: dict) -> list[str]:
    """
    Validate a row destined for physical_item table.

    Context keys: existing_lpns (set of LPNs already in DB)
    """
    errors = []

    lpn = row.get("lpn")
    if not lpn or not str(lpn).strip():
        errors.append("LPN vacio (campo PK obligatorio)")
    elif str(lpn).strip() in context.get("existing_lpns", set()):
        errors.append(f"LPN '{lpn}' ya existe en la BD")

    asin = row.get("asin")
    if not asin or not str(asin).strip():
        errors.append("ASIN vacio (campo NOT NULL)")

    condition_id = row.get("condition_id")
    if condition_id is None:
        errors.append("condition_id es None")
    elif not isinstance(condition_id, int) or condition_id not in range(1, 6):
        errors.append(f"condition_id invalido: {condition_id} (debe ser 1-5)")

    purchase_price = row.get("purchase_price")
    if purchase_price is not None and not isinstance(purchase_price, (int, float)):
        errors.append(f"purchase_price no es numerico: {purchase_price}")

    weight_kg = row.get("weight_kg")
    if weight_kg is not None and not isinstance(weight_kg, (int, float)):
        errors.append(f"weight_kg no es numerico: {weight_kg}")

    id_a2z_raw = row.get("_id_a2z_raw")
    id_a2z = row.get("id_a2z")
    if id_a2z_raw and id_a2z is None:
        errors.append(f"ID A2Z '{id_a2z_raw}' no existe en truckloads")

    return errors


def validate_listing(row: dict, context: dict) -> list[str]:
    errors = []
    lpn = row.get("lpn")
    if not lpn or not str(lpn).strip():
        errors.append("LPN vacio (FK obligatoria)")
    title = row.get("title")
    if not title or not str(title).strip():
        errors.append("titulo_wallapop vacio (no se creara listing)")
    listing_price = row.get("listing_price")
    if listing_price is not None and not isinstance(listing_price, (int, float)):
        errors.append(f"listing_price no es numerico: {listing_price}")
    return errors


def validate_sale(row: dict, context: dict) -> list[str]:
    errors = []
    lpn = row.get("lpn")
    if not lpn or not str(lpn).strip():
        errors.append("LPN vacio (FK obligatoria)")
    final_price = row.get("final_price")
    if final_price is None:
        errors.append("final_price es None (PRECIO VENTA requerido)")
    elif not isinstance(final_price, (int, float)):
        errors.append(f"final_price no es numerico: {final_price}")
    return errors


def validate_cash_transaction(row: dict, context: dict) -> list[str]:
    errors = []
    transaction_type = row.get("transaction_type")
    if transaction_type not in ("INGRESO", "RETIRO"):
        errors.append(
            f"transaction_type invalido: '{transaction_type}' (debe ser INGRESO o RETIRO)"
        )
    amount = row.get("amount")
    if amount is None:
        errors.append("amount es None (NOT NULL)")
    elif not isinstance(amount, (int, float)):
        errors.append(f"amount no es numerico: {amount}")
    employee_id = row.get("employee_id")
    if employee_id is None:
        errors.append(
            f"employee_id no resuelto para '{row.get('_employee_name_raw')}' (NOT NULL)"
        )
    payment_method_id = row.get("payment_method_id")
    if payment_method_id is None:
        errors.append(
            f"payment_method_id no resuelto para '{row.get('_payment_method_raw')}'"
        )
    payment_status_id = row.get("payment_status_id")
    if payment_status_id is None:
        errors.append("payment_status_id no resuelto (NOT NULL)")
    transaction_date = row.get("transaction_date")
    if transaction_date is None:
        errors.append("transaction_date es None (NOT NULL)")
    return errors


def validate_incident(row: dict, context: dict) -> list[str]:
    errors = []
    sale_id = row.get("sale_id")
    if sale_id is None:
        errors.append(
            f"sale_id no resuelto para LPN '{row.get('lpn')}' (NOT NULL, FK a sale)"
        )
    incident_type = row.get("incident_type")
    valid_types = {
        "DEVOLUCION_COMPLETA", "DEVOLUCION_PARCIAL", "RECLAMACION",
        "DISPUTA_PLATAFORMA", "ERROR_ENVIO", "PRODUCTO_DEFECTUOSO", "OTRO",
    }
    if incident_type not in valid_types:
        errors.append(f"incident_type invalido: '{incident_type}'")
    status = row.get("status")
    valid_statuses = {
        "ABIERTA", "EN_PROCESO", "ESPERANDO_CLIENTE",
        "ESPERANDO_PLATAFORMA", "RESUELTA", "ESCALADA", "CERRADA",
    }
    if status not in valid_statuses:
        errors.append(f"status invalido: '{status}'")
    buyer_problem = row.get("buyer_problem_description")
    if not buyer_problem or not str(buyer_problem).strip():
        errors.append("buyer_problem_description vacio (NOT NULL)")
    return errors


VALIDATORS = {
    "physical_item": validate_physical_item,
    "listing": validate_listing,
    "sale": validate_sale,
    "cash_transaction": validate_cash_transaction,
    "incident": validate_incident,
}
