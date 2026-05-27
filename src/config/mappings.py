"""
Central mapping configuration for Google Sheets -> PostgreSQL migration.

Contains value maps (condition, payment method/status, incident types),
column name mappings per sheet tab, employee aliases, null value sets,
and migration order respecting FK dependencies.
"""

CONDITION_MAP = {
    "perfecto": 1,
    "con tara": 2,
    "para piezas": 3,
    "desechado": 4,
    "desconocido": 5,
}
CONDITION_DEFAULT = 5
CONDITION_ID_DESECHADO = 4

TRANSACTION_TYPE_MAP = {
    "ingreso": "INGRESO",
    "retiro": "RETIRO",
}

PAYMENT_METHOD_MAP = {
    "efectivo": "EFECTIVO",
    "bizum": "BIZUM",
    "transferencia": "TRANSFERENCIA",
    "plataforma": "PLATAFORMA",
    "wallapop": "PLATAFORMA",
    "tarjeta": "TARJETA",
    "paypal": "PAYPAL",
    "ptv": "PTV",
    "recibo": "RECIBO",
    "otro": "OTRO",
}

PAYMENT_STATUS_MAP = {
    "pendiente": "PENDIENTE",
    "parcial": "PARCIAL",
    "pagado": "PAGADO",
    "deposito pagado": "DEPOSITO_PAGADO",
    "reembolsado": "REEMBOLSADO",
    "cancelado": "CANCELADO",
    "en disputa": "EN_DISPUTA",
}
PAYMENT_STATUS_DEFAULT = "PAGADO"

INCIDENT_STATUS_MAP = {
    "solucionado": "RESUELTA",
    "resuelto": "RESUELTA",
    "pendiente": "ABIERTA",
    "en proceso": "EN_PROCESO",
    "esperando cliente": "ESPERANDO_CLIENTE",
    "esperando plataforma": "ESPERANDO_PLATAFORMA",
    "escalado": "ESCALADA",
    "cerrado": "CERRADA",
}
INCIDENT_STATUS_DEFAULT = "ABIERTA"

INCIDENT_TYPE_MAP = {
    "devolucion completa": "DEVOLUCION_COMPLETA",
    "devolucion parcial": "DEVOLUCION_PARCIAL",
    "reclamacion": "RECLAMACION",
    "disputa": "DISPUTA_PLATAFORMA",
    "error envio": "ERROR_ENVIO",
    "producto defectuoso": "PRODUCTO_DEFECTUOSO",
}
INCIDENT_TYPE_DEFAULT = "RECLAMACION"

RESOLUTION_TYPE_KEYWORDS = {
    "reembolso total": "REEMBOLSO_TOTAL",
    "devolucion": "REEMBOLSO_TOTAL",
    "reembolso parcial": "REEMBOLSO_PARCIAL",
    "descuento": "DESCUENTO",
    "reemplazo": "REEMPLAZO",
    "sin accion": "CERRADA_SIN_ACCION",
}

EMPLOYEE_ALIASES = {
    "david": "otro",
    "liu": "jose",
    "gricel": "jose",
    "lina": "jose",
    "liliana": "jose",
}

TRUCKLOAD_ALIASES = {
    "reg-paolita": "REG",
}

NULL_VALUES = {"", "-", "n/a", "na", "null", "none", "sin datos", " "}
FEATURES_NULL_VALUES = NULL_VALUES | {"sin caracteristicas", "sin características"}

MIGRATION_ORDER = [
    "physical_item",
    "listing",
    "sale",
    "cash_transaction",
    "incident",
]

INVENTARIO_COLUMNS = {
    "ID": "lpn",
    "ASIN": "asin",
    "DESCR. AMAZON": "amazon_description",
    "CARACTERISTICAS": "amazon_features",
    "DEPARTAMENTO": "amazon_department",
    "CATEGORIA": "amazon_category",
    "SUBCATEGORIA": "amazon_subcategory",
    "CATEGORIA_IA_V3": "wallapop_category",
    "marca": "brand",
    "modelo": "model",
    "color": "color",
    "ESTADO": "condition_id",
    "DESCRIPCION": "condition_description",
    "VALOR PAGADO": "purchase_price",
    "UBI": "current_location",
    "PESO": "weight_kg",
    "IMAGENES": "image_urls",
    "hashtags": "hashtags",
    "VENDIDO?": "available",
    "ID A2Z": "id_a2z",
    "PVP": "_pvp",
    "PRECIO REVISADO": "_precio_revisado",
    "PRECIO VENTA": "_precio_venta",
    "titulo_wallapop": "_titulo_wallapop",
    "descripcion_wallapop": "_descripcion_wallapop",
    "Columna cuenta premium": "_cuenta_premium",
}

CAJA_COLUMNS = {
    "TIPO DE TRANSACCION": "transaction_type",
    "ESTADO PAGO": "payment_status",
    "ID": "lpn",
    "CUANTIA": "amount",
    "MODO DE PAGO": "payment_method",
    "PERSONA": "employee_name",
    "FECHA": "transaction_date",
    "COMENTARIOS": "notes",
}

INCIDENCIAS_COLUMNS = {
    "ID": "lpn",
    "QUE HAY QUE HACER": "action",
    "DISPUTA?": "has_dispute",
    "GESTOR": "assigned_to",
    "ESTADO": "status",
    "EXPLICACION PROBLEMA": "buyer_problem_description",
    "SOLUCION APORTADA": "resolution_description",
    "FECHA": "opened_at",
}
