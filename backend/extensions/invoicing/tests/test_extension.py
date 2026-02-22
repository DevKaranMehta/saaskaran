"""Invoicing extension — unit tests."""
import pytest


def test_extension_name():
    from extensions.invoicing.extension import InvoicingExtension
    ext = InvoicingExtension()
    assert ext.name == "invoicing"
    assert ext.api_prefix == "/invoicing"
    assert ext.version == "1.0.0"


def test_model_tablenames():
    from extensions.invoicing.models import Client, Invoice, LineItem
    assert Client.__tablename__ == "ext_inv_clients"
    assert Invoice.__tablename__ == "ext_inv_invoices"
    assert LineItem.__tablename__ == "ext_inv_line_items"


def test_invoice_status_enum():
    from extensions.invoicing.models import InvoiceStatus
    values = [s.value for s in InvoiceStatus]
    assert "draft"     in values
    assert "sent"      in values
    assert "paid"      in values
    assert "overdue"   in values
    assert "cancelled" in values


def test_invoice_status_is_string_enum():
    from extensions.invoicing.models import InvoiceStatus
    assert isinstance(InvoiceStatus.paid, str)
    assert InvoiceStatus.paid == "paid"


def test_line_item_create_schema():
    from extensions.invoicing.schemas import LineItemCreate
    item = LineItemCreate(description="Consulting", quantity=5, unit_price=200.0)
    assert item.description == "Consulting"
    assert item.quantity == 5
    assert item.unit_price == 200.0


def test_invoice_create_schema_defaults():
    from extensions.invoicing.schemas import InvoiceCreate
    inv = InvoiceCreate()
    assert inv.status == "draft"
    assert inv.tax_rate == 0.0
    assert inv.currency == "USD"
    assert inv.line_items == []


def test_invoice_create_schema_with_line_items():
    from extensions.invoicing.schemas import InvoiceCreate, LineItemCreate
    items = [
        LineItemCreate(description="Design", quantity=10, unit_price=150.0),
        LineItemCreate(description="Development", quantity=20, unit_price=200.0),
    ]
    inv = InvoiceCreate(
        client_name="Acme Corp",
        tax_rate=10.0,
        currency="EUR",
        line_items=items,
    )
    assert inv.client_name == "Acme Corp"
    assert inv.tax_rate == 10.0
    assert inv.currency == "EUR"
    assert len(inv.line_items) == 2


def test_client_create_schema():
    from extensions.invoicing.schemas import ClientCreate
    client = ClientCreate(name="Globex Inc", email="billing@globex.com", phone="+1-555-0100")
    assert client.name == "Globex Inc"
    assert client.email == "billing@globex.com"


def test_client_update_schema_partial():
    from extensions.invoicing.schemas import ClientUpdate
    update = ClientUpdate(email="new@email.com")
    data = update.model_dump(exclude_unset=True)
    assert "email" in data
    assert "name" not in data


def test_compute_totals_helper():
    from extensions.invoicing.routes import _compute_totals
    from extensions.invoicing.schemas import LineItemCreate
    items = [
        LineItemCreate(description="A", quantity=2, unit_price=100.0),
        LineItemCreate(description="B", quantity=3, unit_price=50.0),
    ]
    subtotal, total = _compute_totals(items, tax_rate=10.0)
    assert subtotal == 350.0
    assert total == 385.0


def test_generate_invoice_number():
    from extensions.invoicing.routes import _generate_invoice_number
    number = _generate_invoice_number()
    assert number.startswith("INV-")
    parts = number.split("-")
    assert len(parts) == 3
    assert len(parts[1]) == 6   # YYYYMM
    assert len(parts[2]) == 4   # random suffix


def test_status_update_schema():
    from extensions.invoicing.schemas import StatusUpdate
    su = StatusUpdate(status="paid")
    assert su.status == "paid"


def test_invoice_response_schema_config():
    from extensions.invoicing.schemas import InvoiceResponse
    assert InvoiceResponse.model_config.get("from_attributes") or getattr(InvoiceResponse, "model_config", {}).get("from_attributes") or hasattr(InvoiceResponse, "Config")


def test_default_config():
    from extensions.invoicing.extension import InvoicingExtension
    cfg = InvoicingExtension().default_config()
    assert cfg["default_currency"] == "USD"
    assert "invoice_number_prefix" in cfg
