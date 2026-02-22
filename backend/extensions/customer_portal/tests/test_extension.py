"""Basic tests for the customer_portal extension."""
import pytest
from extensions.customer_portal.extension import CustomerPortalExtension
from extensions.customer_portal.models import Ticket, TicketReply, TicketStatus, TicketPriority, TicketCategory


def test_extension_metadata():
    ext = CustomerPortalExtension()
    assert ext.name == "customer_portal"
    assert ext.api_prefix == "/customer-portal"
    assert ext.version == "1.0.0"


def test_ticket_table_name():
    assert Ticket.__tablename__ == "ext_customer_tickets"


def test_reply_table_name():
    assert TicketReply.__tablename__ == "ext_ticket_replies"


def test_status_enum_values():
    assert set(s.value for s in TicketStatus) == {"open", "in_progress", "resolved", "closed"}


def test_priority_enum_values():
    assert set(p.value for p in TicketPriority) == {"low", "medium", "high", "urgent"}


def test_category_enum_values():
    assert set(c.value for c in TicketCategory) == {"billing", "technical", "general", "feature_request"}
