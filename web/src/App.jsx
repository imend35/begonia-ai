import {useState} from 'react'
import {createClient} from '@supabase/supabase-js'
import './App.css'
const db=createClient(import.meta.env.VITE_SUPABASE_URL,import.meta.env.VITE_SUPABASE_ANON_KEY)
export default function App(){
 const [session,setSession]=useState(null),[email,setEmail]=useState(''),[password,setPassword]=useState(''),[message,setMessage]=useState('')
 async function login(e){e.preventDefault();const {data,error}=await db.auth.signInWithPassword({email,password});if(error)setMessage(error.message);else{setSession(data.session);setMessage('Giriş yapıldı.')}}
 async function save(e){e.preventDefault();const form=new FormData(e.currentTarget);const {error}=await db.from('konuk_talepleri').insert({baslik:form.get('baslik'),aciklama:form.get('aciklama'),kategori:form.get('kategori'),durum:'taslak',olusturan_id:session.user.id,olusturan_ad:session.user.email});setMessage(error?error.message:'Talep kaydedildi.')}
 if(!session)return <main><h1>Begonia AI</h1><form onSubmit={login}><input placeholder="E-posta" value={email} onChange={e=>setEmail(e.target.value)}/><input type="password" placeholder="Parola" value={password} onChange={e=>setPassword(e.target.value)}/><button>Giriş yap</button></form><p>{message}</p></main>
 return <main><h1>Konuk Talepleri</h1><form onSubmit={save}><input name="baslik" placeholder="Başlık" required/><textarea name="aciklama" placeholder="Kişisel veri içermeyen açıklama" required/><select name="kategori"><option>Teknik</option><option>Oda</option><option>Temizlik</option><option>Diger</option></select><button>Talebi kaydet</button></form><p>{message}</p></main>
}
