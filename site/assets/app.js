'use strict';
const $ = s => document.querySelector(s);
function storageGet(k){try{return localStorage.getItem(k)}catch{return null}}
function storageSet(k,v){try{localStorage.setItem(k,v)}catch{}}
if(storageGet('paper-theme')==='dark')document.documentElement.dataset.theme='dark';
$('#theme')?.addEventListener('click',()=>{const t=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=t;storageSet('paper-theme',t)});
$('#print')?.addEventListener('click',()=>window.print());
$('#font-size')?.addEventListener('click',()=>{document.documentElement.style.setProperty('--body-size',getComputedStyle(document.documentElement).getPropertyValue('--body-size').trim()==='19px'?'17px':'19px')});
if($('.prose')){const update=()=>{const max=document.documentElement.scrollHeight-innerHeight;$('#reading-progress').style.width=`${max>0?scrollY/max*100:0}%`};addEventListener('scroll',update,{passive:true});update();const observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){document.querySelectorAll('.toc a').forEach(a=>a.classList.toggle('current',a.hash==='#'+e.target.id))}}),{rootMargin:'-90px 0px -65% 0px'});document.querySelectorAll('.prose h2').forEach(h=>observer.observe(h))}
if($('#search')){
 let topic='all',limit=12;
 const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const records=(window.PAPERS??[]).map(p=>({...p,query:(p.title+' '+p.authors+' '+p.summary+' '+p.category).toLocaleLowerCase()})).sort((a,b)=>a.title.localeCompare(b.title,'en'));
 function render(){const query=$('#search').value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);const matches=records.filter(p=>($('#scope').value==='all'||p.reviewed)&&(topic==='all'||p.topic===topic)&&query.every(q=>p.query.includes(q)));
 $('#result-count').textContent=`${matches.length.toLocaleString()} 篇${$('#scope').value==='reviewed'?'已完成解析':'匹配论文'}`;
 $('#paper-grid').innerHTML=matches.slice(0,limit).map(p=>`<a class="paper-card" href="${escape(p.href)}" ${p.reviewed?'':'target="_blank" rel="noopener"'}><div class="card-top"><span>${escape(p.category)}</span><span class="pill">${p.reviewed?'精读解析':'仅元数据'}</span></div><h3>${escape(p.title)}</h3><p>${escape(p.summary)}</p><div class="card-footer"><span>${p.reviewed?'CVPR 2026 · '+escape(p.checked):'CVF 官方原文 · 尚未精读'}</span><span class="arrow">${p.reviewed?'↗':'↗'}</span></div></a>`).join('');
 $('#more').hidden=matches.length<=limit;$('#empty').hidden=matches.length>0;
 }
 $('#search').addEventListener('input',()=>{limit=12;render()});$('#scope').addEventListener('change',()=>{limit=12;render()});
 document.querySelectorAll('[data-topic]').forEach(b=>b.addEventListener('click',()=>{topic=b.dataset.topic;limit=12;document.querySelectorAll('[data-topic]').forEach(x=>x.classList.toggle('active',x===b));render()}));
 $('#more').addEventListener('click',()=>{limit+=12;render()});
 document.addEventListener('keydown',e=>{if(e.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){e.preventDefault();$('#search').focus()}});
 render();
}
