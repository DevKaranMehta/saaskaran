"""Form Builder — FastAPI routes."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth     import get_current_user
from api.database import get_db
from api.models   import User

from .models  import Form, FormSubmission
from .schemas import (
    EmbedCodeResponse,
    FormCreate,
    FormResponse,
    FormSubmissionCreate,
    FormSubmissionResponse,
    FormUpdate,
    PublicFormResponse,
)

router = APIRouter(tags=["form-builder"])

# ---------------------------------------------------------------------------
# Embed code JS template — placeholders replaced at generation time
# ---------------------------------------------------------------------------
_EMBED_JS_TEMPLATE = """(function() {
  var TOKEN = "__TOKEN__";
  var API_BASE = "__API_BASE__";
  var container = document.getElementById("fb-__FORM_ID__");
  if (!container) {
    console.error("Form Builder: container #fb-__FORM_ID__ not found");
    return;
  }

  fetch(API_BASE + "/public/" + TOKEN)
    .then(function(r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then(function(form) { renderForm(form); })
    .catch(function(err) {
      console.error("Form Builder:", err);
      container.innerHTML = '<p style="color:#dc2626;font-family:sans-serif;">Failed to load form.</p>';
    });

  function renderForm(form) {
    var fields = (form.fields || []).slice().sort(function(a, b) {
      return (a.order || 0) - (b.order || 0);
    });
    var IS = "width:100%;padding:8px 12px;border:1px solid #d1d5db;border-radius:6px;font-size:14px;box-sizing:border-box;";
    var html = '<form id="fbf-__FORM_ID__" style="font-family:sans-serif;max-width:520px;">';
    fields.forEach(function(field) {
      var nm = 'name="' + field.id + '"';
      var req = field.required ? " required" : "";
      var ph = ' placeholder="' + (field.placeholder || "") + '"';
      html += '<div style="margin-bottom:16px;">';
      if (field.type !== "checkbox") {
        html += '<label style="display:block;font-weight:600;margin-bottom:6px;font-size:14px;">'
             + field.label
             + (field.required ? ' <span style="color:#ef4444">*</span>' : "")
             + '</label>';
      }
      if (field.type === "textarea") {
        html += '<textarea ' + nm + req + ph + ' style="' + IS + 'min-height:100px;resize:vertical;"></textarea>';
      } else if (field.type === "select") {
        html += '<select ' + nm + req + ' style="' + IS + '"><option value="">-- Select --</option>';
        (field.options || []).forEach(function(o) {
          html += '<option value="' + o + '">' + o + '</option>';
        });
        html += '</select>';
      } else if (field.type === "checkbox") {
        html += '<label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:14px;">'
             + '<input type="checkbox" ' + nm + '> <span>' + field.label + '</span></label>';
      } else {
        var TYPE_MAP = {phone: "tel", url: "url", email: "email", number: "number", date: "date"};
        var t = TYPE_MAP[field.type] || "text";
        html += '<input type="' + t + '" ' + nm + req + ph + ' style="' + IS + '">';
      }
      html += '</div>';
    });
    html += '<button type="submit" style="background:#4f46e5;color:#fff;padding:10px 28px;border:none;border-radius:6px;cursor:pointer;font-size:15px;font-weight:600;">'
         + form.submit_button_text + '</button>';
    html += '</form>';
    container.innerHTML = html;

    document.getElementById("fbf-__FORM_ID__").addEventListener("submit", function(e) {
      e.preventDefault();
      var data = {};
      fields.forEach(function(field) {
        var el = container.querySelector('[name="' + field.id + '"]');
        if (el) data[field.label] = field.type === "checkbox" ? el.checked : el.value;
      });
      var btn = container.querySelector('button[type="submit"]');
      if (btn) { btn.disabled = true; btn.textContent = "Sending..."; }
      fetch(API_BASE + "/public/" + TOKEN + "/submit", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({data: data})
      }).then(function(r) {
        if (r.ok) {
          container.innerHTML = '<p style="color:#15803d;font-size:16px;font-weight:600;font-family:sans-serif;">'
            + form.success_message + '</p>';
        } else {
          if (btn) { btn.disabled = false; btn.textContent = form.submit_button_text; }
          container.insertAdjacentHTML("beforeend",
            '<p style="color:#dc2626;font-size:14px;font-family:sans-serif;margin-top:8px;">Submission failed. Please try again.</p>');
        }
      }).catch(function() {
        if (btn) { btn.disabled = false; btn.textContent = form.submit_button_text; }
        container.insertAdjacentHTML("beforeend",
          '<p style="color:#dc2626;font-size:14px;font-family:sans-serif;margin-top:8px;">Network error. Please try again.</p>');
      });
    });
  }
})();"""


def _build_embed_code(form_id: str, token: str, api_base: str, form_name: str) -> str:
    js = (
        _EMBED_JS_TEMPLATE
        .replace("__FORM_ID__", form_id)
        .replace("__TOKEN__", token)
        .replace("__API_BASE__", api_base)
    )
    return (
        f"<!-- Form Builder: {form_name} -->\n"
        f'<div id="fb-{form_id}"></div>\n'
        f"<script>\n{js}\n</script>"
    )


# ── Authenticated: Forms CRUD ─────────────────────────────────────────────────

@router.get("/forms/", response_model=list[FormResponse])
async def list_forms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Form)
        .where(Form.tenant_id == current_user.tenant_id)
        .order_by(Form.created_at.desc())
    )
    return result.scalars().all()


@router.post("/forms/", response_model=FormResponse, status_code=status.HTTP_201_CREATED)
async def create_form(
    payload: FormCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    form = Form(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        **payload.model_dump(),
    )
    db.add(form)
    await db.commit()
    await db.refresh(form)
    return form


@router.get("/forms/{item_id}", response_model=FormResponse)
async def get_form(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Form).where(Form.id == item_id, Form.tenant_id == current_user.tenant_id)
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    return form


@router.patch("/forms/{item_id}", response_model=FormResponse)
async def update_form(
    item_id: str,
    payload: FormUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Form).where(Form.id == item_id, Form.tenant_id == current_user.tenant_id)
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    for attr, value in payload.model_dump(exclude_unset=True).items():
        setattr(form, attr, value)
    await db.commit()
    await db.refresh(form)
    return form


@router.delete("/forms/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_form(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Form).where(Form.id == item_id, Form.tenant_id == current_user.tenant_id)
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    await db.delete(form)
    await db.commit()


# ── Authenticated: Embed Code ─────────────────────────────────────────────────

@router.get("/forms/{item_id}/embed-code", response_model=EmbedCodeResponse)
async def get_embed_code(
    item_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Form).where(Form.id == item_id, Form.tenant_id == current_user.tenant_id)
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    base_url = str(request.base_url).rstrip("/")
    api_base = f"{base_url}/api/v1/form-builder"
    embed_code = _build_embed_code(form.id, form.embed_token, api_base, form.name)
    return EmbedCodeResponse(form_id=form.id, embed_token=form.embed_token, embed_code=embed_code)


# ── Authenticated: Submissions ────────────────────────────────────────────────

@router.get("/forms/{item_id}/submissions", response_model=list[FormSubmissionResponse])
async def list_form_submissions(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    form_result = await db.execute(
        select(Form).where(Form.id == item_id, Form.tenant_id == current_user.tenant_id)
    )
    if not form_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Form not found")
    result = await db.execute(
        select(FormSubmission)
        .where(FormSubmission.form_id == item_id)
        .order_by(FormSubmission.created_at.desc())
    )
    return result.scalars().all()


@router.delete(
    "/forms/{item_id}/submissions/{sub_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_submission(
    item_id: str,
    sub_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    form_result = await db.execute(
        select(Form).where(Form.id == item_id, Form.tenant_id == current_user.tenant_id)
    )
    if not form_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Form not found")
    result = await db.execute(
        select(FormSubmission).where(
            FormSubmission.id == sub_id,
            FormSubmission.form_id == item_id,
        )
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    await db.delete(submission)
    await db.commit()


@router.get("/submissions/", response_model=list[FormSubmissionResponse])
async def list_all_submissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(FormSubmission)
        .where(FormSubmission.tenant_id == current_user.tenant_id)
        .order_by(FormSubmission.created_at.desc())
    )
    return result.scalars().all()


# ── Public: No Auth ───────────────────────────────────────────────────────────

@router.get("/public/{embed_token}", response_model=PublicFormResponse)
async def get_public_form(
    embed_token: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Form).where(Form.embed_token == embed_token, Form.is_active == True)  # noqa: E712
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found or inactive")
    return form


@router.post("/public/{embed_token}/submit", status_code=status.HTTP_201_CREATED)
async def submit_public_form(
    embed_token: str,
    payload: FormSubmissionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Form).where(Form.embed_token == embed_token, Form.is_active == True)  # noqa: E712
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found or inactive")
    submission = FormSubmission(
        tenant_id=form.tenant_id,
        form_id=form.id,
        created_by="anonymous",
        data=payload.data,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(submission)
    await db.execute(
        update(Form)
        .where(Form.id == form.id)
        .values(submission_count=Form.submission_count + 1)
    )
    await db.commit()
    return {"status": "ok", "message": form.success_message}
