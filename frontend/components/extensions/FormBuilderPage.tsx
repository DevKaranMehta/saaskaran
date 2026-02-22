'use client'
import { useState, useEffect, useRef, useCallback } from 'react'

// ── Types ─────────────────────────────────────────────────────────────────────
type FieldType = 'text'|'textarea'|'email'|'number'|'select'|'checkbox'|'date'|'phone'|'url'

interface FieldDef {
  id: string; type: FieldType; label: string
  placeholder?: string; required: boolean; options: string[]; order: number
}
interface Form {
  id: string; title: string; description?: string; status: string
  public_id: string; fields: FieldDef[]
  submit_button_text: string; success_message: string; created_at: string
}
interface Submission {
  id: string; form_id: string; data: Record<string,unknown>; ip_address?: string; submitted_at: string
}
interface EmbedResp { public_id: string; embed_code: string }

const TYPES: { v: FieldType; label: string; icon: string; color: string }[] = [
  { v:'text',     label:'Text',       icon:'Aa', color:'#6366f1' },
  { v:'textarea', label:'Long Text',  icon:'¶',  color:'#8b5cf6' },
  { v:'email',    label:'Email',      icon:'@',  color:'#3b82f6' },
  { v:'number',   label:'Number',     icon:'#',  color:'#10b981' },
  { v:'select',   label:'Dropdown',   icon:'▾',  color:'#f59e0b' },
  { v:'date',     label:'Date',       icon:'📅', color:'#ef4444' },
  { v:'checkbox', label:'Checkbox',   icon:'☑',  color:'#14b8a6' },
  { v:'phone',    label:'Phone',      icon:'☎',  color:'#f97316' },
  { v:'url',      label:'URL/Link',   icon:'🔗', color:'#64748b' },
]

function api(p:string){ return `/api/v1/form-builder${p}` }
function auth(): Record<string, string> { const t=typeof window!=='undefined'?localStorage.getItem('token'):null; return t?{Authorization:`Bearer ${t}`}:{} }
function uid(){ return Math.random().toString(36).slice(2,10) }
function fmtDate(s:string){ try{return new Date(s).toLocaleString(undefined,{month:'short',day:'numeric',year:'numeric',hour:'2-digit',minute:'2-digit'})}catch{return s} }

// ── Field edit modal ──────────────────────────────────────────────────────────
function FieldModal({init,onSave,onClose}:{init:Partial<FieldDef>|null;onSave:(f:FieldDef)=>void;onClose:()=>void}){
  const isNew=!init?.label
  const [f,setF]=useState<FieldDef>({id:uid(),type:'text',label:'',placeholder:'',required:false,options:[],order:0,...init})
  const [opts,setOpts]=useState((init?.options??[]).join('\n'))
  function lbl(l:string){setF(x=>({...x,label:l,id:isNew?l.toLowerCase().replace(/[^a-z0-9]+/g,'_').slice(0,30)||uid():x.id}))}
  function save(){if(!f.label.trim())return;const options=f.type==='select'?opts.split('\n').map(s=>s.trim()).filter(Boolean):[];onSave({...f,options})}
  return(
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={e=>e.target===e.currentTarget&&onClose()}>
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md shadow-2xl">
        <div className="flex items-center justify-between p-5 border-b border-slate-700">
          <h3 className="text-white font-semibold">{isNew?'Add Field':'Edit Field'}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white w-8 h-8 flex items-center justify-center text-xl">✕</button>
        </div>
        <div className="p-5 space-y-4">
          <div><label className="text-xs text-slate-400 uppercase tracking-wider mb-1.5 block">Label *</label>
            <input value={f.label} onChange={e=>lbl(e.target.value)} autoFocus className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2.5 text-white focus:outline-none focus:border-indigo-500" placeholder="e.g. Full Name"/>
          </div>
          <div><label className="text-xs text-slate-400 uppercase tracking-wider mb-1.5 block">Field Type</label>
            <div className="grid grid-cols-3 gap-2">{TYPES.map(t=>(
              <button key={t.v} onClick={()=>setF(x=>({...x,type:t.v}))} className={`px-2 py-1.5 rounded-lg text-xs font-medium border transition ${f.type===t.v?'bg-indigo-600 border-indigo-500 text-white':'bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-500'}`}>
                {t.icon} {t.label}
              </button>
            ))}</div>
          </div>
          {f.type==='select'&&<div><label className="text-xs text-slate-400 uppercase tracking-wider mb-1.5 block">Options (one per line)</label>
            <textarea value={opts} onChange={e=>setOpts(e.target.value)} rows={4} className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm font-mono focus:outline-none focus:border-indigo-500" placeholder={"Option A\nOption B\nOption C"}/>
          </div>}
          {!['checkbox','date'].includes(f.type)&&<div><label className="text-xs text-slate-400 uppercase tracking-wider mb-1.5 block">Placeholder</label>
            <input value={f.placeholder??''} onChange={e=>setF(x=>({...x,placeholder:e.target.value}))} className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"/>
          </div>}
          <label className="flex items-center gap-2.5 cursor-pointer">
            <input type="checkbox" checked={f.required} onChange={e=>setF(x=>({...x,required:e.target.checked}))} className="w-4 h-4"/>
            <span className="text-slate-300 text-sm">Required field</span>
          </label>
        </div>
        <div className="flex justify-end gap-3 p-5 border-t border-slate-700">
          <button onClick={onClose} className="px-4 py-2 text-sm text-slate-400 hover:text-white transition">Cancel</button>
          <button onClick={save} disabled={!f.label.trim()} className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-lg text-sm font-medium transition">{isNew?'Add Field':'Save'}</button>
        </div>
      </div>
    </div>
  )
}

// ── Form settings modal ───────────────────────────────────────────────────────
function FormModal({init,onSave,onClose}:{init?:Partial<Form>;onSave:(d:Partial<Form>)=>void;onClose:()=>void}){
  const [title,setTitle]=useState(init?.title??'')
  const [desc,setDesc]=useState(init?.description??'')
  const [btn,setBtn]=useState(init?.submit_button_text??'Submit')
  const [msg,setMsg]=useState(init?.success_message??'Thank you for your submission!')
  return(
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={e=>e.target===e.currentTarget&&onClose()}>
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md shadow-2xl">
        <div className="flex items-center justify-between p-5 border-b border-slate-700">
          <h3 className="text-white font-semibold">{init?.id?'Form Settings':'New Form'}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white w-8 h-8 flex items-center justify-center text-xl">✕</button>
        </div>
        <div className="p-5 space-y-4">
          <div><label className="text-xs text-slate-400 uppercase tracking-wider mb-1.5 block">Form Name *</label>
            <input value={title} onChange={e=>setTitle(e.target.value)} autoFocus className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2.5 text-white focus:outline-none focus:border-indigo-500" placeholder="e.g. Contact Us"/>
          </div>
          <div><label className="text-xs text-slate-400 uppercase tracking-wider mb-1.5 block">Description</label>
            <textarea value={desc} onChange={e=>setDesc(e.target.value)} rows={2} className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"/>
          </div>
          <div><label className="text-xs text-slate-400 uppercase tracking-wider mb-1.5 block">Submit Button Label</label>
            <input value={btn} onChange={e=>setBtn(e.target.value)} className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"/>
          </div>
          <div><label className="text-xs text-slate-400 uppercase tracking-wider mb-1.5 block">Success Message</label>
            <textarea value={msg} onChange={e=>setMsg(e.target.value)} rows={2} className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500"/>
          </div>
        </div>
        <div className="flex justify-end gap-3 p-5 border-t border-slate-700">
          <button onClick={onClose} className="px-4 py-2 text-sm text-slate-400 hover:text-white transition">Cancel</button>
          <button onClick={()=>onSave({title,description:desc,submit_button_text:btn,success_message:msg})} disabled={!title.trim()} className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-lg text-sm font-medium transition">{init?.id?'Save':'Create Form'}</button>
        </div>
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function FormBuilderPage(){
  const [forms,setForms]=useState<Form[]>([])
  const [loading,setLoading]=useState(true)
  const [selId,setSelId]=useState<string|null>(null)
  const [tab,setTab]=useState<'builder'|'embed'|'submissions'>('builder')

  // Builder
  const [fields,setFields]=useState<FieldDef[]>([])
  const [dirty,setDirty]=useState(false)
  const [saving,setSaving]=useState(false)
  const [fieldModal,setFieldModal]=useState<{open:boolean;init:Partial<FieldDef>|null;idx:number|null}>({open:false,init:null,idx:null})
  const [formModal,setFormModal]=useState<{open:boolean;target?:Partial<Form>}>({open:false})

  // Embed
  const [embed,setEmbed]=useState<EmbedResp|null>(null)
  const [embedLoading,setEmbedLoading]=useState(false)
  const [copied,setCopied]=useState(false)

  // Submissions
  const [subs,setSubs]=useState<Submission[]>([])
  const [subsLoading,setSubsLoading]=useState(false)

  // Drag
  const dragFrom=useRef<number|null>(null)
  const dragOver=useRef<number|null>(null)

  const selForm=forms.find(f=>f.id===selId)

  const loadForms=useCallback(async()=>{
    const r=await fetch(api('/forms'),{headers:auth()})
    if(!r.ok){setLoading(false);return}
    const d:Form[]=await r.json()
    setForms(d);setLoading(false)
    if(!selId&&d.length>0)setSelId(d[0].id)
  },[selId])

  useEffect(()=>{loadForms()},[])

  useEffect(()=>{
    if(!selId){setFields([]);return}
    fetch(api(`/forms/${selId}`),{headers:auth()}).then(r=>r.json()).then((d:Form)=>{setFields(d.fields??[]);setDirty(false)})
  },[selId])

  useEffect(()=>{
    if(!selId)return
    if(tab==='embed'){
      setEmbedLoading(true)
      fetch(api(`/forms/${selId}/embed-code`),{headers:auth()}).then(r=>r.json()).then(setEmbed).finally(()=>setEmbedLoading(false))
    }
    if(tab==='submissions'){
      setSubsLoading(true)
      fetch(api(`/forms/${selId}/submissions`),{headers:auth()}).then(r=>r.json()).then(setSubs).finally(()=>setSubsLoading(false))
    }
  },[tab,selId])

  async function createForm(d:Partial<Form>){
    const r=await fetch(api('/forms'),{method:'POST',headers:{...auth(),'Content-Type':'application/json'},body:JSON.stringify({title:d.title,description:d.description||null,fields:[],submit_button_text:d.submit_button_text??'Submit',success_message:d.success_message??'Thank you for your submission!'})})
    if(!r.ok)return
    const created:Form=await r.json()
    setFormModal({open:false});await loadForms();setSelId(created.id);setTab('builder')
  }

  async function updateSettings(d:Partial<Form>){
    if(!selId)return
    await fetch(api(`/forms/${selId}`),{method:'PATCH',headers:{...auth(),'Content-Type':'application/json'},body:JSON.stringify(d)})
    setFormModal({open:false});await loadForms()
  }

  async function deleteForm(id:string){
    if(!confirm('Delete this form and all submissions?'))return
    await fetch(api(`/forms/${id}`),{method:'DELETE',headers:auth()})
    const rest=forms.filter(f=>f.id!==id);setForms(rest);setSelId(rest[0]?.id??null)
  }

  async function saveFields(){
    if(!selId)return;setSaving(true)
    const ordered=fields.map((f,i)=>({...f,order:i}))
    await fetch(api(`/forms/${selId}`),{method:'PATCH',headers:{...auth(),'Content-Type':'application/json'},body:JSON.stringify({fields:ordered})})
    setDirty(false);setSaving(false);await loadForms()
  }

  function openAdd(type:FieldType){setFieldModal({open:true,init:{type,order:fields.length},idx:null})}
  function openEdit(i:number){setFieldModal({open:true,init:fields[i],idx:i})}

  function saveField(f:FieldDef){
    if(fieldModal.idx!==null&&fieldModal.idx>=0){setFields(p=>{const u=[...p];u[fieldModal.idx!]=f;return u})}
    else{setFields(p=>[...p,f])}
    setFieldModal({open:false,init:null,idx:null});setDirty(true)
  }

  function delField(i:number){setFields(p=>p.filter((_,x)=>x!==i));setDirty(true)}
  function moveField(i:number,dir:-1|1){const j=i+dir;if(j<0||j>=fields.length)return;const u=[...fields];[u[i],u[j]]=[u[j],u[i]];setFields(u);setDirty(true)}

  function onDragStart(i:number){dragFrom.current=i}
  function onDragOver(e:React.DragEvent,i:number){e.preventDefault();dragOver.current=i}
  function onDrop(){const f=dragFrom.current,t=dragOver.current;if(f===null||t===null||f===t)return;const u=[...fields];const[m]=u.splice(f,1);u.splice(t,0,m);setFields(u);setDirty(true);dragFrom.current=null;dragOver.current=null}

  async function copyEmbed(){if(!embed)return;try{await navigator.clipboard.writeText(embed.embed_code);setCopied(true);setTimeout(()=>setCopied(false),2000)}catch{}}

  async function delSub(id:string){if(!confirm('Delete this submission?'))return;await fetch(api(`/submissions/${id}`),{method:'DELETE',headers:auth()});setSubs(p=>p.filter(s=>s.id!==id))}

  if(loading) return <div className="flex items-center justify-center h-full text-slate-400 text-sm">Loading forms…</div>

  return(
    <div className="flex h-full overflow-hidden">
      {/* Sidebar */}
      <div className="w-56 flex-shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <span className="text-white font-semibold text-sm">📋 My Forms</span>
          <button onClick={()=>setFormModal({open:true,target:undefined})} className="w-7 h-7 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xl leading-none flex items-center justify-center transition">+</button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {forms.length===0?<p className="text-slate-500 text-xs text-center py-8">No forms yet.</p>:forms.map(form=>(
            <button key={form.id} onClick={()=>{setSelId(form.id);setTab('builder')}} className={`w-full text-left px-3 py-2.5 rounded-lg transition ${selId===form.id?'bg-indigo-600 text-white':'text-slate-300 hover:bg-slate-800'}`}>
              <div className="text-sm font-medium truncate">{form.title}</div>
              <div className={`text-xs mt-0.5 ${selId===form.id?'text-indigo-200':'text-slate-500'}`}>{form.status==='active'?'Active':'Inactive'}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Main */}
      {!selForm?<div className="flex-1 flex flex-col items-center justify-center text-slate-500 gap-3"><div className="text-5xl">📋</div><p className="text-sm">Create your first form using the + button</p></div>:(
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between flex-shrink-0">
            <div>
              <h1 className="text-white font-semibold text-lg">{selForm.title}</h1>
              {selForm.description&&<p className="text-slate-400 text-sm mt-0.5">{selForm.description}</p>}
            </div>
            <div className="flex gap-2">
              <button onClick={()=>setFormModal({open:true,target:selForm})} className="px-3 py-1.5 text-sm text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 rounded-lg transition">⚙ Settings</button>
              <button onClick={()=>deleteForm(selForm.id)} className="px-3 py-1.5 text-sm text-red-400 hover:text-red-300 border border-red-900/50 hover:border-red-700 rounded-lg transition">Delete</button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-slate-800 px-6 flex-shrink-0">
            {(['builder','embed','submissions'] as const).map(t=>(
              <button key={t} onClick={()=>setTab(t)} className={`px-4 py-3 text-sm font-medium border-b-2 transition ${tab===t?'border-indigo-500 text-indigo-400':'border-transparent text-slate-400 hover:text-white'}`}>
                {t==='builder'?'Form Builder':t==='embed'?'Embed Code':`Submissions`}
              </button>
            ))}
          </div>

          {/* Builder tab */}
          {tab==='builder'&&(
            <div className="flex flex-1 overflow-hidden">
              {/* Field palette */}
              <div className="w-44 flex-shrink-0 border-r border-slate-800 p-3 overflow-y-auto bg-slate-900/50">
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">Add Field</p>
                <div className="space-y-1.5">{TYPES.map(t=>(
                  <button key={t.v} onClick={()=>openAdd(t.v)} className="w-full flex items-center gap-2 px-2.5 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-indigo-500 text-slate-300 hover:text-white rounded-lg text-xs transition font-medium">
                    <span className="w-5 text-center" style={{color:t.color}}>{t.icon}</span>{t.label}
                  </button>
                ))}</div>
              </div>

              {/* Field list */}
              <div className="flex-1 overflow-y-auto p-5">
                <div className="flex items-center justify-between mb-4">
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Fields ({fields.length})</p>
                  {dirty&&<button onClick={saveFields} disabled={saving} className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition">{saving?'Saving…':'💾 Save Form'}</button>}
                </div>
                {fields.length===0?(
                  <div className="flex flex-col items-center justify-center h-48 border-2 border-dashed border-slate-700 rounded-xl text-slate-500 text-sm gap-2">
                    <div className="text-3xl">←</div><div>Click a field type on the left to add it</div>
                  </div>
                ):(
                  <div className="space-y-2 max-w-xl">
                    {fields.map((field,i)=>{
                      const t=TYPES.find(x=>x.v===field.type)
                      return(
                        <div key={`${field.id}-${i}`} draggable onDragStart={()=>onDragStart(i)} onDragOver={e=>onDragOver(e,i)} onDrop={onDrop}
                          className="flex items-center gap-3 bg-slate-800 border border-slate-700 rounded-xl px-3 py-3 group hover:border-slate-600 transition cursor-grab active:cursor-grabbing">
                          <span className="text-slate-600 select-none">⠿</span>
                          <span className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0" style={{background:`${t?.color}22`,color:t?.color}}>{t?.icon??'?'}</span>
                          <div className="flex-1 min-w-0">
                            <span className="text-white text-sm font-medium">{field.label}</span>
                            <span className="ml-2 text-xs text-slate-500">{field.type}</span>
                            {field.required&&<span className="ml-1 text-xs text-red-400">*</span>}
                          </div>
                          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button onClick={()=>moveField(i,-1)} disabled={i===0} className="p-1 text-slate-400 hover:text-white disabled:opacity-25 text-sm">↑</button>
                            <button onClick={()=>moveField(i,1)} disabled={i===fields.length-1} className="p-1 text-slate-400 hover:text-white disabled:opacity-25 text-sm">↓</button>
                            <button onClick={()=>openEdit(i)} className="px-2 py-0.5 text-indigo-400 hover:text-indigo-200 text-xs">Edit</button>
                            <button onClick={()=>delField(i)} className="px-2 py-0.5 text-red-400 hover:text-red-200 text-xs">✕</button>
                          </div>
                        </div>
                      )
                    })}
                    <button onClick={()=>setFieldModal({open:true,init:null,idx:null})} className="w-full py-2.5 border-2 border-dashed border-slate-700 hover:border-indigo-600 text-slate-500 hover:text-indigo-400 rounded-xl text-sm transition">+ Add Field</button>
                  </div>
                )}
              </div>

              {/* Preview */}
              <div className="w-72 flex-shrink-0 border-l border-slate-800 p-4 overflow-y-auto bg-slate-900/30">
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-3">Live Preview</p>
                <div className="bg-white rounded-xl p-5 shadow-lg">
                  <h3 className="font-bold text-gray-800 text-base mb-1">{selForm.title}</h3>
                  {selForm.description&&<p className="text-gray-500 text-xs mb-4">{selForm.description}</p>}
                  {fields.length===0?<p className="text-gray-400 text-xs italic">No fields yet.</p>:(
                    <div className="space-y-3">
                      {fields.map((f,i)=>(
                        <div key={i}>
                          <label className="block text-xs font-semibold text-gray-700 mb-1">{f.label}{f.required&&<span className="text-red-500 ml-0.5">*</span>}</label>
                          {f.type==='textarea'?<textarea rows={2} className="w-full border border-gray-200 rounded px-2 py-1 text-xs text-gray-400" placeholder={f.placeholder} readOnly/>
                          :f.type==='select'?<select className="w-full border border-gray-200 rounded px-2 py-1 text-xs text-gray-400"><option>Select…</option>{(f.options??[]).map(o=><option key={o}>{o}</option>)}</select>
                          :f.type==='checkbox'?<label className="flex items-center gap-1.5 text-xs text-gray-600"><input type="checkbox" readOnly/> {f.label}</label>
                          :<input type={f.type==='phone'?'tel':f.type} className="w-full border border-gray-200 rounded px-2 py-1 text-xs text-gray-400" placeholder={f.placeholder} readOnly/>}
                        </div>
                      ))}
                      <button className="w-full bg-indigo-600 text-white text-xs py-2 rounded-lg font-semibold mt-2">{selForm.submit_button_text}</button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Embed tab */}
          {tab==='embed'&&(
            <div className="flex-1 overflow-y-auto p-6 max-w-3xl">
              <h2 className="text-white font-semibold mb-1">Embed Code</h2>
              <p className="text-slate-400 text-sm mb-6">Copy the code below and paste it into any website where you want the form to appear.</p>
              {embedLoading?<p className="text-slate-400 text-sm">Loading…</p>:!embed?<p className="text-slate-400 text-sm">Failed to load embed code.</p>:(
                <div className="space-y-5">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-slate-200 font-medium text-sm">JavaScript Embed Snippet</span>
                    <button onClick={copyEmbed} className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white text-xs rounded-lg font-medium transition">{copied?'✓ Copied!':'Copy Code'}</button>
                  </div>
                  <pre className="bg-slate-800 border border-slate-700 rounded-xl p-4 text-xs text-yellow-300 overflow-x-auto whitespace-pre-wrap">{embed.embed_code}</pre>
                  <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
                    <p className="text-slate-300 text-sm font-medium mb-2">How to use:</p>
                    <ol className="text-slate-400 text-sm space-y-1 list-decimal list-inside">
                      <li>Copy the code above</li>
                      <li>Paste it into any HTML page where you want the form</li>
                      <li>The form will load automatically and collect submissions</li>
                      <li>View all responses in the <strong className="text-slate-300">Submissions</strong> tab</li>
                    </ol>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Submissions tab */}
          {tab==='submissions'&&(
            <div className="flex-1 overflow-y-auto p-6">
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-white font-semibold">Submissions <span className="text-slate-500 font-normal text-sm">({subs.length})</span></h2>
                <button onClick={()=>{setSubsLoading(true);fetch(api(`/forms/${selId}/submissions`),{headers:auth()}).then(r=>r.json()).then(setSubs).finally(()=>setSubsLoading(false))}} className="text-sm text-slate-400 hover:text-white transition">↻ Refresh</button>
              </div>
              {subsLoading?<p className="text-slate-400 text-sm">Loading…</p>:subs.length===0?(
                <div className="flex flex-col items-center justify-center py-20 text-center">
                  <div className="text-5xl mb-3">📭</div>
                  <p className="text-slate-400 text-sm">No submissions yet.</p>
                  <p className="text-slate-500 text-xs mt-1">Share the embed code to start collecting responses.</p>
                </div>
              ):(
                <div className="space-y-3 max-w-3xl">
                  {subs.map(sub=>(
                    <div key={sub.id} className="bg-slate-800 border border-slate-700 rounded-xl p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <span className="text-slate-400 text-xs">{fmtDate(sub.submitted_at)}</span>
                          {sub.ip_address&&<span className="text-slate-600 text-xs ml-2">• {sub.ip_address}</span>}
                        </div>
                        <button onClick={()=>delSub(sub.id)} className="text-xs text-red-400 hover:text-red-300">Delete</button>
                      </div>
                      <div className="grid grid-cols-2 gap-x-6 gap-y-2">
                        {Object.entries(sub.data).map(([k,v])=>{
                          const label=fields.find(f=>f.id===k)?.label??k
                          return(<div key={k}><div className="text-xs text-slate-500 uppercase tracking-wide">{label}</div><div className="text-slate-200 text-sm mt-0.5 break-words">{String(v)||<span className="text-slate-600 italic">empty</span>}</div></div>)
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {fieldModal.open&&<FieldModal init={fieldModal.init} onSave={saveField} onClose={()=>setFieldModal({open:false,init:null,idx:null})}/>}
      {formModal.open&&<FormModal init={formModal.target} onSave={formModal.target?.id?updateSettings:createForm} onClose={()=>setFormModal({open:false})}/>}
    </div>
  )
}
