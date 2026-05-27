"""Tests for data cleaning and transformation functions."""
import pytest
from datetime import date
from src.transform.cleaners import (
    clean_null, clean_null_features, clean_price, clean_weight,
    map_condition, map_available, map_do_not_list,
    map_transaction_type, map_incident_status,
    parse_incident_action, infer_resolution_type,
    parse_date, resolve_listing_price, _normalize_text,
)


# ─── clean_null ─────────────────────────────────────────────────────────

class TestCleanNull:
    def test_none(self):
        assert clean_null(None) is None

    def test_empty(self):
        assert clean_null("") is None

    def test_dash(self):
        assert clean_null("-") is None

    def test_na(self):
        assert clean_null("n/a") is None

    def test_null_text(self):
        assert clean_null("null") is None

    def test_valid(self):
        assert clean_null("hello") == "hello"

    def test_whitespace(self):
        assert clean_null("  hello  ") == "hello"

    def test_sin_datos(self):
        assert clean_null("sin datos") is None


# ─── clean_null_features ───────────────────────────────────────────────

class TestCleanNullFeatures:
    def test_sin_caracteristicas(self):
        assert clean_null_features("sin caracteristicas") is None

    def test_sin_caracteristicas_accent(self):
        assert clean_null_features("sin características") is None

    def test_valid(self):
        assert clean_null_features("Has buttons") == "Has buttons"


# ─── clean_price ───────────────────────────────────────────────────────

class TestCleanPrice:
    def test_simple(self):
        assert clean_price("45.00") == 45.0

    def test_euro_symbol(self):
        assert clean_price("45.00 €") == 45.0

    def test_euro_attached(self):
        assert clean_price("50.00€") == 50.0

    def test_eur_text(self):
        assert clean_price("99.99 EUR") == 99.99

    def test_european_format(self):
        assert clean_price("1.234,56") == 1234.56

    def test_american_format(self):
        assert clean_price("1,234.56") == 1234.56

    def test_comma_decimal(self):
        assert clean_price("45,50") == 45.5

    def test_none(self):
        assert clean_price(None) is None

    def test_empty(self):
        assert clean_price("") is None

    def test_dash(self):
        assert clean_price("-") is None

    def test_invalid(self):
        assert clean_price("abc") is None

    def test_dollar(self):
        assert clean_price("$25.00") == 25.0

    def test_integer(self):
        assert clean_price("100") == 100.0

    def test_zero(self):
        assert clean_price("0") == 0.0


# ─── clean_weight ──────────────────────────────────────────────────────

class TestCleanWeight:
    def test_simple(self):
        assert clean_weight("2") == 2.0

    def test_with_kg(self):
        assert clean_weight("1.5kg") == 1.5

    def test_with_g(self):
        assert clean_weight("500g") == 500.0

    def test_none(self):
        assert clean_weight(None) is None

    def test_invalid(self):
        assert clean_weight("heavy") is None


# ─── map_condition ─────────────────────────────────────────────────────

class TestMapCondition:
    def test_perfecto(self):
        assert map_condition("perfecto") == 1

    def test_con_tara(self):
        assert map_condition("con tara") == 2

    def test_para_piezas(self):
        assert map_condition("para piezas") == 3

    def test_desechado(self):
        assert map_condition("desechado") == 4

    def test_unknown(self):
        assert map_condition("random") == 5

    def test_none(self):
        assert map_condition(None) == 5

    def test_case_insensitive(self):
        assert map_condition("PERFECTO") == 1

    def test_empty(self):
        assert map_condition("") == 5


# ─── map_available ─────────────────────────────────────────────────────

class TestMapAvailable:
    def test_none_is_available(self):
        assert map_available(None) is True

    def test_true_is_not_available(self):
        assert map_available("TRUE") is False

    def test_si_is_not_available(self):
        assert map_available("SI") is False

    def test_si_accent(self):
        assert map_available("SÍ") is False

    def test_yes(self):
        assert map_available("YES") is False

    def test_one(self):
        assert map_available("1") is False

    def test_false_is_available(self):
        assert map_available("FALSE") is True

    def test_no_is_available(self):
        assert map_available("NO") is True


# ─── map_do_not_list ───────────────────────────────────────────────────

class TestMapDoNotList:
    def test_no_se_anuncia(self):
        assert map_do_not_list("No se anuncia") is True

    def test_no_se_anuncia_spaces(self):
        assert map_do_not_list("Nose anuncia") is True

    def test_different_text(self):
        assert map_do_not_list("Se anuncia normal") is False

    def test_none(self):
        assert map_do_not_list(None) is False

    def test_empty(self):
        assert map_do_not_list("") is False

    def test_other(self):
        assert map_do_not_list("Something else") is False


# ─── map_transaction_type ──────────────────────────────────────────────

class TestMapTransactionType:
    def test_ingreso(self):
        assert map_transaction_type("ingreso") == "INGRESO"

    def test_retiro(self):
        assert map_transaction_type("retiro") == "RETIRO"

    def test_unknown(self):
        assert map_transaction_type("other") is None

    def test_none(self):
        assert map_transaction_type(None) is None


# ─── map_incident_status ──────────────────────────────────────────────

class TestMapIncidentStatus:
    def test_solucionado(self):
        assert map_incident_status("solucionado") == "RESUELTA"

    def test_resuelto(self):
        assert map_incident_status("resuelto") == "RESUELTA"

    def test_pendiente(self):
        assert map_incident_status("pendiente") == "ABIERTA"

    def test_unknown(self):
        assert map_incident_status("xyz") == "ABIERTA"

    def test_none(self):
        assert map_incident_status(None) == "ABIERTA"


# ─── parse_incident_action ────────────────────────────────────────────

class TestParseIncidentAction:
    def test_numeric_discount(self):
        r = parse_incident_action("50€")
        assert r["discount_amount"] == 50.0
        assert r["incident_type"] == "RECLAMACION"

    def test_numeric_comma(self):
        r = parse_incident_action("25,50")
        assert r["discount_amount"] == 25.5

    def test_devolucion_completa(self):
        r = parse_incident_action("devolucion completa")
        assert r["incident_type"] == "DEVOLUCION_COMPLETA"

    def test_devolucion_completa_accent(self):
        r = parse_incident_action("devolución completa")
        assert r["incident_type"] == "DEVOLUCION_COMPLETA"

    def test_reclamacion_accent(self):
        r = parse_incident_action("reclamación formal")
        assert r["incident_type"] == "RECLAMACION"

    def test_error_envio_accent(self):
        r = parse_incident_action("error envío")
        assert r["incident_type"] == "ERROR_ENVIO"

    def test_disputa(self):
        r = parse_incident_action("disputa")
        assert r["incident_type"] == "DISPUTA_PLATAFORMA"

    def test_none(self):
        r = parse_incident_action(None)
        assert r["incident_type"] == "RECLAMACION"
        assert r["discount_amount"] == 0.0

    def test_empty(self):
        r = parse_incident_action("")
        assert r["incident_type"] == "RECLAMACION"

    def test_unknown_text(self):
        r = parse_incident_action("something random")
        assert r["incident_type"] == "RECLAMACION"


# ─── infer_resolution_type ────────────────────────────────────────────

class TestInferResolutionType:
    def test_reembolso_total(self):
        assert infer_resolution_type("Se hizo reembolso total") == "REEMBOLSO_TOTAL"

    def test_descuento(self):
        assert infer_resolution_type("Se aplico descuento") == "DESCUENTO"

    def test_devolucion(self):
        assert infer_resolution_type("devolucion del producto") == "REEMBOLSO_TOTAL"

    def test_devolucion_accent(self):
        assert infer_resolution_type("devolución total") == "REEMBOLSO_TOTAL"

    def test_sin_accion_accent(self):
        assert infer_resolution_type("cerrado sin acción") == "CERRADA_SIN_ACCION"

    def test_reemplazo(self):
        assert infer_resolution_type("reemplazo por otro") == "REEMPLAZO"

    def test_none(self):
        assert infer_resolution_type(None) is None

    def test_unknown(self):
        assert infer_resolution_type("hablamos con el cliente") is None


# ─── parse_date ───────────────────────────────────────────────────────

class TestParseDate:
    def test_iso(self):
        assert parse_date("2024-12-23") == date(2024, 12, 23)

    def test_eu_format(self):
        assert parse_date("23/12/2024") == date(2024, 12, 23)

    def test_eu_short_year(self):
        assert parse_date("23/12/24") == date(2024, 12, 23)

    def test_none(self):
        assert parse_date(None) is None

    def test_empty(self):
        assert parse_date("") is None

    def test_invalid(self):
        assert parse_date("not-a-date") is None

    def test_dash_format(self):
        assert parse_date("23-12-2024") == date(2024, 12, 23)

    def test_outside_range(self):
        assert parse_date("01/01/2019") is None

    def test_slash_ymd(self):
        assert parse_date("2024/03/15") == date(2024, 3, 15)


# ─── resolve_listing_price ────────────────────────────────────────────

class TestResolveListingPrice:
    def test_revisado_priority(self):
        assert resolve_listing_price("100", "200") == 100.0

    def test_fallback_pvp(self):
        assert resolve_listing_price(None, "200") == 200.0

    def test_both_none(self):
        assert resolve_listing_price(None, None) is None

    def test_revisado_empty(self):
        assert resolve_listing_price("", "200") == 200.0
