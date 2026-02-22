"""Form Builder extension tests."""
import pytest


def test_extension_name():
    from extensions.form_builder.extension import FormBuilderExtension
    ext = FormBuilderExtension()
    assert ext.name == "form_builder"


def test_extension_api_prefix():
    from extensions.form_builder.extension import FormBuilderExtension
    ext = FormBuilderExtension()
    assert ext.api_prefix == "/form-builder"


def test_form_table_name():
    from extensions.form_builder.models import Form
    assert Form.__tablename__ == "ext_form_builder_forms"


def test_submission_table_name():
    from extensions.form_builder.models import FormSubmission
    assert FormSubmission.__tablename__ == "ext_form_builder_submissions"


def test_field_config_generates_unique_ids():
    from extensions.form_builder.schemas import FieldConfig
    f1 = FieldConfig(type="text", label="Name")
    f2 = FieldConfig(type="email", label="Email")
    assert f1.id != f2.id
    assert len(f1.id) == 36  # standard UUID length


def test_embed_code_contains_required_parts():
    from extensions.form_builder.routes import _build_embed_code
    code = _build_embed_code(
        form_id="test-form-id",
        token="test-token-abc",
        api_base="http://localhost:8000/api/v1/form-builder",
        form_name="Contact Form",
    )
    assert 'id="fb-test-form-id"' in code
    assert "test-token-abc" in code
    assert "http://localhost:8000/api/v1/form-builder" in code
    assert "<script>" in code
    assert "<div" in code
    assert "Contact Form" in code


def test_form_create_schema_defaults():
    from extensions.form_builder.schemas import FormCreate
    form = FormCreate(name="My Form")
    assert form.is_active is True
    assert form.submit_button_text == "Submit"
    assert form.fields == []
