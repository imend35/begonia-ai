import {useEffect,useState} from 'react'
import {createClient} from '@supabase/supabase-js'
import './App.css'
const db=createClient(import.meta.env.VITE_SUPABASE_URL,import.meta.env.VITE_SUPABASE_ANON_KEY)
const cats=['Teknik','Oda','Temizlik','Misafir deneyimi','Diger']
export default function App(){
 const [s,setS]=useState(null),[email,setEmail]=useState(''),[password,setPassword]=useState(''),[msg,setMsg]=useState(''),[rows,setRows]=useState([]),[edit,setEdit]=useState(null)
 const load=async()=>{const{data,error}=await db.from('konuk_talepleri').select('*').order('created_at',{ascending:false});setRows(data||[]);if(error)setMsg(error.message)}
 useEffect(()=>{db.auth.getSession().then(x=>setS(x.data.session));const {data:{subscription}}=db.auth.onAuthStateChange((_,x)=>setS(x));return()=>subscription.unsubscribe()},[])
 useEffect(()=>{if(s)load()},[s])
 const login=async e=>{e.preventDefault();const{data,error}=await db.auth.signInWithPassword({email,password});setS(data.session);setMsg(error?.message||'Giriş yapıldı.')}
 const ai=async()=>{const text=document.querySelector('textarea')?.value.trim();if(!text){setMsg('Önce kişisel veri içermeyen bir açıklama yazın.');return}setMsg('AI önerisi hazırlanıyor…');try{const response=await fetch('/api/ai-talep',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({aciklama:text})});const data=await response.json();setMsg(data.etiket ? data.etiket+' '+data.onerı : data.error)}catch{setMsg('AI önerisi alınamadı.')} };
 const save=async e=>{e.preventDefault();const f=new FormData(e.currentTarget),v={baslik:f.get('baslik'),aciklama:f.get('aciklama'),kategori:f.get('kategori')};let error;if(edit)({error}=await db.from('konuk_talepleri').update(v).eq('id',edit.id));else({error}=await db.from('konuk_talepleri').insert({...v,durum:'taslak',olusturan_id:s.user.id,olusturan_ad:s.user.email}));setMsg(error?.message||(edit?'Talep güncellendi.':'Talep kaydedildi.'));setEdit(null);e.currentTarget.reset();load()}
 const remove=async id=>{if(!confirm('Talep silinsin mi?'))return;const{error}=await db.from('konuk_talepleri').delete().eq('id',id);setMsg(error?.message||'Talep silindi.');load()}
 if(!s)return <main><h1>Begonia AI</h1><form onSubmit={login}><input placeholder="E-posta" value={email} onChange={e=>setEmail(e.target.value)}/><input type="password" placeholder="Parola" value={password} onChange={e=>setPassword(e.target.value)}/><button>Giriş yap</button></form><p>{msg}</p></main>
 return <main><h1>Konuk Talepleri</h1><div className="grid"><form onSubmit={save}><input name="baslik" placeholder="Başlık" defaultValue={edit?.baslik||''} required/><textarea name="aciklama" placeholder="Açıklama" defaultValue={edit?.aciklama||''} required/><select name="kategori" defaultValue={edit?.kategori||'Teknik'}>{cats.map(x=><option key={x}>{x}</option>)}</select><button type='button' onClick={ai}>✨ AI ile öneri al</button><button>{edit?'Güncelle':'Talebi kaydet'}</button></form><section><button onClick={load}>Listeyi yenile</button>{rows.map(r=><article key={r.id}><b>{r.baslik}</b><p>{r.aciklama}</p><small>{r.kategori} · {r.durum}</small>{r.olusturan_id===s.user.id&&<p><button onClick={()=>setEdit(r)}>Düzenle</button><button onClick={()=>remove(r.id)}>Sil</button></p>}</article>)}</section></div><p>{msg}</p></main>
}

