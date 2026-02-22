"""Live Chat — API routes (agent + widget)."""
from __future__ import annotations
import secrets
from datetime import UTC, datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.database import get_db
from api.models import User

from .models import LiveChatSite, LiveChatConversation, LiveChatMessage, ConvStatus, MsgSender
from .schemas import (
    SiteCreate, SiteUpdate, SiteResponse,
    ConvUpdate, ConvResponse,
    AgentReply, MsgResponse,
    WidgetStartConv, WidgetSendMsg,
    LiveChatStats,
)

router = APIRouter()

# ── Widget JavaScript ──────────────────────────────────────────────────────

WIDGET_JS_TEMPLATE = r"""
(function() {
  var SITE_KEY = '__SITE_KEY__';
  var API_BASE = '__API_BASE__';
  var COLOR    = '__COLOR__';
  var GREETING = '__GREETING__';

  var convId    = localStorage.getItem('lc_conv_' + SITE_KEY);
  var visName   = localStorage.getItem('lc_name_' + SITE_KEY) || '';
  var visEmail  = localStorage.getItem('lc_email_' + SITE_KEY) || '';
  var pollTimer = null;
  var lastMsgId = null;
  var unread    = 0;

  /* ── Styles ── */
  var style = document.createElement('style');
  style.textContent = [
    '#lc-btn{position:fixed;bottom:24px;right:24px;width:56px;height:56px;border-radius:50%;background:' + COLOR + ';border:none;cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,.3);display:flex;align-items:center;justify-content:center;z-index:99999;transition:transform .2s}',
    '#lc-btn:hover{transform:scale(1.08)}',
    '#lc-badge{position:absolute;top:-4px;right:-4px;background:#ef4444;color:#fff;border-radius:50%;width:20px;height:20px;font-size:11px;display:none;align-items:center;justify-content:center;font-weight:700}',
    '#lc-box{position:fixed;bottom:92px;right:24px;width:340px;height:480px;background:#fff;border-radius:16px;box-shadow:0 8px 40px rgba(0,0,0,.18);display:none;flex-direction:column;z-index:99998;font-family:system-ui,sans-serif;overflow:hidden}',
    '#lc-head{background:' + COLOR + ';padding:16px;color:#fff;font-weight:700;font-size:15px;display:flex;align-items:center;justify-content:space-between}',
    '#lc-msgs{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px;background:#f8fafc}',
    '#lc-form{padding:10px;border-top:1px solid #e2e8f0;display:flex;gap:6px;background:#fff}',
    '#lc-input{flex:1;padding:8px 12px;border:1px solid #cbd5e1;border-radius:20px;font-size:13px;outline:none}',
    '#lc-send{background:' + COLOR + ';color:#fff;border:none;border-radius:50%;width:36px;height:36px;cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center}',
    '.lc-msg{max-width:80%;padding:8px 12px;border-radius:12px;font-size:13px;line-height:1.4;word-break:break-word}',
    '.lc-visitor{align-self:flex-end;background:' + COLOR + ';color:#fff;border-bottom-right-radius:4px}',
    '.lc-agent{align-self:flex-start;background:#fff;color:#1e293b;border:1px solid #e2e8f0;border-bottom-left-radius:4px}',
    '.lc-name{font-size:10px;color:#94a3b8;margin-bottom:2px}',
    '#lc-intro{padding:20px;display:flex;flex-direction:column;gap:10px}',
    '#lc-intro input{padding:10px;border:1px solid #cbd5e1;border-radius:8px;font-size:13px;outline:none;width:100%;box-sizing:border-box}',
    '#lc-intro button{background:' + COLOR + ';color:#fff;border:none;padding:10px;border-radius:8px;cursor:pointer;font-size:13px;font-weight:600}',
  ].join('');
  document.head.appendChild(style);

  /* ── DOM ── */
  var btn = document.createElement('button'); btn.id='lc-btn';
  btn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>';
  var badge = document.createElement('span'); badge.id='lc-badge'; btn.appendChild(badge);

  var box = document.createElement('div'); box.id='lc-box';
  box.innerHTML = '<div id="lc-head"><span>💬 Live Chat</span><span id="lc-close" style="cursor:pointer;font-size:18px;line-height:1">×</span></div>' +
    '<div id="lc-msgs"></div>' +
    '<div id="lc-form" style="display:none"><input id="lc-input" placeholder="Type a message…"><button id="lc-send">➤</button></div>';

  document.body.appendChild(btn);
  document.body.appendChild(box);

  var msgs  = box.querySelector('#lc-msgs');
  var form  = box.querySelector('#lc-form');
  var input = box.querySelector('#lc-input');
  var open  = false;

  /* ── Helpers ── */
  function apiFetch(path, opts) {
    return fetch(API_BASE + path, Object.assign({ headers: { 'Content-Type': 'application/json' } }, opts));
  }

  function addMsg(content, sender, name) {
    var wrap = document.createElement('div');
    wrap.style.cssText = 'display:flex;flex-direction:column;' + (sender==='visitor' ? 'align-items:flex-end' : 'align-items:flex-start');
    var nm = document.createElement('div'); nm.className='lc-name'; nm.textContent=name;
    var m  = document.createElement('div'); m.className='lc-msg lc-' + sender; m.textContent=content;
    wrap.appendChild(nm); wrap.appendChild(m);
    msgs.appendChild(wrap);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function showBadge(n) {
    unread = n;
    if (n > 0 && !open) { badge.style.display='flex'; badge.textContent=n>99?'99+':n; }
    else { badge.style.display='none'; }
  }

  function showGreeting() {
    msgs.innerHTML = '';
    var g = document.createElement('div');
    g.style.cssText='text-align:center;padding:16px 0;color:#64748b;font-size:13px';
    g.textContent = GREETING;
    msgs.appendChild(g);
  }

  /* ── Intro form ── */
  function showIntro() {
    msgs.innerHTML = '';
    var intro = document.createElement('div'); intro.id='lc-intro';
    intro.innerHTML = '<p style="color:#475569;font-size:13px;margin:0 0 4px">' + GREETING + '</p>' +
      '<input id="lc-iname" placeholder="Your name *" required>' +
      '<input id="lc-iemail" placeholder="Your email (optional)">' +
      '<button id="lc-istart">Start Chat</button>';
    msgs.appendChild(intro);
    if (visName) intro.querySelector('#lc-iname').value = visName;
    if (visEmail) intro.querySelector('#lc-iemail').value = visEmail;
    intro.querySelector('#lc-istart').onclick = function() {
      var n = intro.querySelector('#lc-iname').value.trim();
      var e = intro.querySelector('#lc-iemail').value.trim();
      if (!n) { alert('Please enter your name'); return; }
      visName = n; visEmail = e;
      localStorage.setItem('lc_name_' + SITE_KEY, n);
      localStorage.setItem('lc_email_' + SITE_KEY, e);
      startConversation();
    };
  }

  /* ── API ── */
  function startConversation() {
    msgs.innerHTML = '<div style="text-align:center;color:#94a3b8;font-size:12px;padding:20px">Connecting…</div>';
    apiFetch('/conversations', {
      method: 'POST',
      body: JSON.stringify({ visitor_name: visName, visitor_email: visEmail || null }),
    }).then(function(r){ return r.json(); }).then(function(d) {
      if (d.id) {
        convId = d.id;
        localStorage.setItem('lc_conv_' + SITE_KEY, convId);
        showGreeting();
        form.style.display = 'flex';
        startPolling();
      }
    }).catch(function(){ msgs.innerHTML='<div style="color:#ef4444;text-align:center;padding:20px;font-size:13px">Connection failed. Please try again.</div>'; });
  }

  function loadMessages() {
    if (!convId) return;
    apiFetch('/conversations/' + convId + '/messages').then(function(r){ return r.json(); }).then(function(data) {
      if (!Array.isArray(data)) return;
      var newMsgs = lastMsgId ? data.filter(function(m){ return m.created_at > lastMsgTs; }) : data;
      if (newMsgs.length) {
        if (!lastMsgId) msgs.innerHTML = '';
        newMsgs.forEach(function(m) {
          addMsg(m.content, m.sender, m.sender_name);
          lastMsgId = m.id; lastMsgTs = m.created_at;
          if (m.sender === 'agent' && !open) showBadge(unread+1);
        });
      }
      if (!lastMsgId && data.length === 0) showGreeting();
    }).catch(function(){});
  }

  var lastMsgTs = null;

  function startPolling() { if (!pollTimer) pollTimer = setInterval(loadMessages, 3000); loadMessages(); }
  function stopPolling()  { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } }

  function sendMessage() {
    var text = input.value.trim();
    if (!text || !convId) return;
    input.value = '';
    apiFetch('/conversations/' + convId + '/messages', {
      method: 'POST',
      body: JSON.stringify({ content: text, visitor_name: visName }),
    }).then(function(r){ return r.json(); }).then(function(m) {
      if (m.id) addMsg(m.content, 'visitor', visName);
    });
  }

  /* ── Toggle ── */
  btn.onclick = function() {
    open = !open;
    box.style.display = open ? 'flex' : 'none';
    if (open) {
      showBadge(0);
      if (!convId && !visName) showIntro();
      else if (!convId) startConversation();
      else { form.style.display='flex'; startPolling(); }
    } else { stopPolling(); }
  };
  box.querySelector('#lc-close').onclick = function() { open=false; box.style.display='none'; stopPolling(); };
  box.querySelector('#lc-send').onclick = sendMessage;
  input.addEventListener('keydown', function(e){ if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); sendMessage(); } });

  /* ── Pre-check existing conv ── */
  if (convId) { loadMessages(); }
})();
"""


@router.get("/widget/{site_key}/script.js", include_in_schema=False)
async def widget_script(site_key: str, request: Request, db: Annotated[AsyncSession, Depends(get_db)] = None):
    """Serve the embeddable widget JavaScript."""
    result = await db.execute(
        select(LiveChatSite).where(LiveChatSite.site_key == site_key, LiveChatSite.is_active == True)  # noqa: E712
    )
    site = result.scalar_one_or_none()
    if not site:
        return Response("/* Invalid site key */", media_type="application/javascript")

    # Build absolute URL using forwarded headers (so it works through Nginx proxy)
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("host", request.url.netloc)
    server_origin = f"{scheme}://{host}"
    api_base = f"{server_origin}/api/v1/live-chat/widget/{site_key}"
    js = WIDGET_JS_TEMPLATE \
        .replace("__SITE_KEY__", site_key) \
        .replace("__API_BASE__", api_base) \
        .replace("__COLOR__", site.color) \
        .replace("__GREETING__", site.greeting.replace('"', '\\"'))

    return Response(js, media_type="application/javascript",
                    headers={"Cache-Control": "no-cache"})


# ── Widget API (no JWT auth — site_key is the secret) ─────────────────────

async def _get_site_or_404(site_key: str, db: AsyncSession) -> LiveChatSite:
    result = await db.execute(
        select(LiveChatSite).where(LiveChatSite.site_key == site_key, LiveChatSite.is_active == True)  # noqa: E712
    )
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@router.post("/widget/{site_key}/conversations", response_model=ConvResponse, status_code=201)
async def widget_start_conv(
    site_key: str,
    payload: WidgetStartConv,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Widget: start a new conversation (no auth required)."""
    site = await _get_site_or_404(site_key, db)
    conv = LiveChatConversation(
        tenant_id=site.tenant_id,
        site_id=site.id,
        visitor_name=payload.visitor_name,
        visitor_email=payload.visitor_email,
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@router.get("/widget/{site_key}/conversations/{conv_id}/messages", response_model=list[MsgResponse])
async def widget_get_messages(
    site_key: str,
    conv_id: str,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Widget: poll for messages (no auth required)."""
    site = await _get_site_or_404(site_key, db)
    # Verify conv belongs to this site
    c = await db.execute(
        select(LiveChatConversation).where(
            LiveChatConversation.id == conv_id,
            LiveChatConversation.site_id == site.id,
        )
    )
    if not c.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await db.execute(
        select(LiveChatMessage)
        .where(LiveChatMessage.conversation_id == conv_id)
        .order_by(LiveChatMessage.created_at.asc())
    )
    return result.scalars().all()


@router.post("/widget/{site_key}/conversations/{conv_id}/messages", response_model=MsgResponse, status_code=201)
async def widget_send_message(
    site_key: str,
    conv_id: str,
    payload: WidgetSendMsg,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Widget: visitor sends a message (no auth required)."""
    site = await _get_site_or_404(site_key, db)
    c_result = await db.execute(
        select(LiveChatConversation).where(
            LiveChatConversation.id == conv_id,
            LiveChatConversation.site_id == site.id,
        )
    )
    conv = c_result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.status == ConvStatus.closed:
        raise HTTPException(status_code=400, detail="Conversation is closed")

    msg = LiveChatMessage(
        tenant_id=site.tenant_id,
        conversation_id=conv_id,
        content=payload.content,
        sender=MsgSender.visitor,
        sender_name=payload.visitor_name,
        is_read=False,
    )
    db.add(msg)

    # Update conversation
    conv.message_count += 1
    conv.unread_count += 1
    conv.last_message = payload.content[:200]
    conv.last_message_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(msg)
    return msg


# ── Agent API (JWT required) ───────────────────────────────────────────────

@router.get("/sites", response_model=list[SiteResponse])
async def list_sites(
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(LiveChatSite)
        .where(LiveChatSite.tenant_id == current_user.tenant_id)
        .order_by(LiveChatSite.created_at.desc())
    )
    return result.scalars().all()


@router.post("/sites", response_model=SiteResponse, status_code=201)
async def create_site(
    payload: SiteCreate,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    site_key = secrets.token_urlsafe(32)
    site = LiveChatSite(
        **payload.model_dump(),
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        site_key=site_key,
    )
    db.add(site)
    await db.commit()
    await db.refresh(site)
    return site


@router.patch("/sites/{site_id}", response_model=SiteResponse)
async def update_site(
    site_id: str,
    payload: SiteUpdate,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(LiveChatSite).where(LiveChatSite.id == site_id, LiveChatSite.tenant_id == current_user.tenant_id)
    )
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(site, k, v)
    await db.commit()
    await db.refresh(site)
    return site


@router.delete("/sites/{site_id}", status_code=204)
async def delete_site(
    site_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(LiveChatSite).where(LiveChatSite.id == site_id, LiveChatSite.tenant_id == current_user.tenant_id)
    )
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    await db.delete(site)
    await db.commit()


@router.get("/conversations", response_model=list[ConvResponse])
async def list_conversations(
    status: Optional[ConvStatus] = Query(None),
    site_id: Optional[str] = Query(None),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    q = select(LiveChatConversation).where(LiveChatConversation.tenant_id == current_user.tenant_id)
    if status:
        q = q.where(LiveChatConversation.status == status)
    if site_id:
        q = q.where(LiveChatConversation.site_id == site_id)
    q = q.order_by(LiveChatConversation.last_message_at.desc().nulls_last(), LiveChatConversation.created_at.desc())
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/conversations/{conv_id}", response_model=ConvResponse)
async def get_conversation(
    conv_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(LiveChatConversation).where(
            LiveChatConversation.id == conv_id,
            LiveChatConversation.tenant_id == current_user.tenant_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.patch("/conversations/{conv_id}", response_model=ConvResponse)
async def update_conversation(
    conv_id: str,
    payload: ConvUpdate,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(LiveChatConversation).where(
            LiveChatConversation.id == conv_id,
            LiveChatConversation.tenant_id == current_user.tenant_id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(conv, k, v)
    await db.commit()
    await db.refresh(conv)
    return conv


@router.get("/conversations/{conv_id}/messages", response_model=list[MsgResponse])
async def get_messages(
    conv_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    # Verify ownership
    c = await db.execute(
        select(LiveChatConversation).where(
            LiveChatConversation.id == conv_id,
            LiveChatConversation.tenant_id == current_user.tenant_id,
        )
    )
    if not c.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await db.execute(
        select(LiveChatMessage)
        .where(LiveChatMessage.conversation_id == conv_id)
        .order_by(LiveChatMessage.created_at.asc())
    )
    return result.scalars().all()


@router.post("/conversations/{conv_id}/reply", response_model=MsgResponse, status_code=201)
async def agent_reply(
    conv_id: str,
    payload: AgentReply,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    c_result = await db.execute(
        select(LiveChatConversation).where(
            LiveChatConversation.id == conv_id,
            LiveChatConversation.tenant_id == current_user.tenant_id,
        )
    )
    conv = c_result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg = LiveChatMessage(
        tenant_id=current_user.tenant_id,
        conversation_id=conv_id,
        content=payload.content,
        sender=MsgSender.agent,
        sender_name=current_user.name,
        is_read=True,
    )
    db.add(msg)

    conv.message_count += 1
    conv.last_message = payload.content[:200]
    conv.last_message_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(msg)
    return msg


@router.post("/conversations/{conv_id}/mark-read", status_code=200)
async def mark_read(
    conv_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Mark all visitor messages in a conversation as read, reset unread_count."""
    c_result = await db.execute(
        select(LiveChatConversation).where(
            LiveChatConversation.id == conv_id,
            LiveChatConversation.tenant_id == current_user.tenant_id,
        )
    )
    conv = c_result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.execute(
        update(LiveChatMessage)
        .where(LiveChatMessage.conversation_id == conv_id, LiveChatMessage.sender == MsgSender.visitor)
        .values(is_read=True)
    )
    conv.unread_count = 0
    await db.commit()
    return {"success": True}


@router.get("/stats", response_model=LiveChatStats)
async def get_stats(
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    total_r = await db.execute(
        select(func.count()).select_from(
            select(LiveChatConversation).where(LiveChatConversation.tenant_id == current_user.tenant_id).subquery()
        )
    )
    open_r = await db.execute(
        select(func.count()).select_from(
            select(LiveChatConversation).where(
                LiveChatConversation.tenant_id == current_user.tenant_id,
                LiveChatConversation.status == ConvStatus.open,
            ).subquery()
        )
    )
    unread_r = await db.execute(
        select(func.sum(LiveChatConversation.unread_count)).where(
            LiveChatConversation.tenant_id == current_user.tenant_id
        )
    )
    sites_r = await db.execute(
        select(func.count()).select_from(
            select(LiveChatSite).where(LiveChatSite.tenant_id == current_user.tenant_id).subquery()
        )
    )
    return LiveChatStats(
        total_conversations=total_r.scalar() or 0,
        open_conversations=open_r.scalar() or 0,
        total_unread=int(unread_r.scalar() or 0),
        total_sites=sites_r.scalar() or 0,
    )
