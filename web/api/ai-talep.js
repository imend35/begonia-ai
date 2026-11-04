import OpenAI from 'openai'
export default async function handler(req,res){
 if(req.method!=='POST')return res.status(405).json({error:'POST kullanın.'})
 if(!process.env.OPENAI_API_KEY)return res.status(500).json({error:'OPENAI_API_KEY Vercel ortam değişkeni olarak eklenmeli.'})
 const aciklama=String(req.body?.aciklama||'').trim()
 if(aciklama.length<10)return res.status(400).json({error:'Açıklama en az 10 karakter olmalı.'})
 try{const client=new OpenAI({apiKey:process.env.OPENAI_API_KEY});const result=await client.responses.create({model:'gpt-4.1-mini',input:'Otel talebini yalnızca verilen metne dayanarak kısa ve nazik biçimde düzenle. Kişisel veri ekleme. Başlık, kategori ve önerilen açıklama ver. Talep: '+aciklama});return res.status(200).json({onerı:result.output_text,etiket:'Yapay zekâ önerisidir; kaydetmeden önce kontrol edin.'})}catch{return res.status(500).json({error:'AI önerisi alınamadı.'})}
}
