"""Appointment Booking extension tests."""
import pytest


def test_extension_name():
    from extensions.appointment_booking.extension import AppointmentBookingExtension
    ext = AppointmentBookingExtension()
    assert ext.name == "appointment_booking"


def test_extension_api_prefix():
    from extensions.appointment_booking.extension import AppointmentBookingExtension
    ext = AppointmentBookingExtension()
    assert ext.api_prefix == "/appointment-booking"


def test_service_tablename():
    from extensions.appointment_booking.models import Service
    assert Service.__tablename__ == "ext_appointment_services"


def test_appointment_tablename():
    from extensions.appointment_booking.models import Appointment
    assert Appointment.__tablename__ == "ext_appointments"


def test_appointment_status_values():
    from extensions.appointment_booking.models import AppointmentStatus
    assert AppointmentStatus.pending   == "pending"
    assert AppointmentStatus.confirmed == "confirmed"
    assert AppointmentStatus.completed == "completed"
    assert AppointmentStatus.cancelled == "cancelled"


def test_service_schema_defaults():
    from extensions.appointment_booking.schemas import ServiceCreate
    svc = ServiceCreate(name="Consultation")
    assert svc.duration_minutes == 60
    assert svc.is_active is True
    assert svc.price is None


def test_appointment_schema_requires_fields():
    from extensions.appointment_booking.schemas import AppointmentCreate
    from datetime import datetime, timezone
    appt = AppointmentCreate(
        service_id="some-uuid",
        client_name="Jane Doe",
        client_email="jane@example.com",
        start_time=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 3, 1, 11, 0, tzinfo=timezone.utc),
    )
    assert appt.client_name == "Jane Doe"
    assert appt.notes is None
