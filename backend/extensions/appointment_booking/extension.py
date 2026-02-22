"""Appointment Booking Extension."""
from __future__ import annotations
from saas_builder.core import ExtensionBase


class AppointmentBookingExtension(ExtensionBase):
    name        = "appointment_booking"
    version     = "1.0.0"
    description = "Appointment booking system with services and scheduled appointments."
    author      = "SaaS Factory"
    dependencies: list[str] = []

    api_prefix  = "/appointment-booking"
    permissions = ["appointment_booking.read", "appointment_booking.write"]
    admin_menu  = [
        {"label": "Services",     "icon": "briefcase",  "route": "/admin/appointment-booking/services"},
        {"label": "Appointments", "icon": "calendar",   "route": "/admin/appointment-booking/appointments"},
    ]

    def default_config(self) -> dict:
        return {"max_appointments_per_day": 50}

    def on_install(self) -> None:
        from . import models  # noqa: F401

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass
