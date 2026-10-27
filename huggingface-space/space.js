let model, dataset, report, currentPage = 1;
const el = id => document.getElementById(id);
const escapeText = text => String(text).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");

// Same transform, standardization, coefficients and sigmoid as ml_model.py.
function predict(values) {
  const transformed=values.map((v,i)=>model.log_features.includes(i)?Math.log1p(Math.max(0,v)):v);
  const effects=transformed.map((v,i)=>(v-model.mean[i])/model.scale[i]*model.weights[i]);
  const z=model.intercept+effects.reduce((a,b)=>a+b,0);
  const probability=1/(1+Math.exp(-Math.max(-700,Math.min(700,z))));
  return {probability,flag:probability>=model.threshold,effects};
}
function showPrediction() {
  if(!model)return;
  const values=Array.from({length:6},(_,i)=>Number(el("f"+i).value));
  if(!values.every(Number.isFinite))return;
  const result=predict(values);
  const effects=result.effects.map((effect,i)=>({name:model.features[i],value:values[i],effect}))
    .sort((a,b)=>Math.abs(b.effect)-Math.abs(a.effect));
  el("result").innerHTML='<strong class="'+(result.flag?'high':'')+'">'+(100*result.probability).toFixed(1)+'%</strong> model estimate · <b>'+(result.flag?'Flagged for investigation':'Not flagged')+'</b><p>Decision threshold: '+(100*model.threshold).toFixed(1)+'%. This estimate is not proof of fraud.</p>'+
    effects.map(f=>'<div class="effect"><span>'+escapeText(f.name)+' = '+f.value+'</span><b>'+(f.effect>=0?'+':'')+f.effect.toFixed(3)+' log-odds</b></div>').join('')+
    '<p class="metric-note">Effects are coefficient × standardized feature value, relative to the training mean. Positive values raise the estimate; negative values reduce it. They are model contributions, not causal proof. Model intercept: '+model.intercept.toFixed(3)+'.</p>';
}
el("predict").onsubmit=e=>{e.preventDefault();showPrediction()};
function example(values){values.forEach((v,i)=>el("f"+i).value=v);showPrediction()}
el("ordinary").onclick=()=>example([0,.2,0,400,.5,0]);
el("campaign").onclick=()=>example([15,.92,3,8,2,1.7]);

function filteredReviews(){
  const business=Number(el("business").value),q=el("search").value.toLowerCase();
  return dataset.reviews.filter(r=>(!business||r.business_id===business)&&r.body.toLowerCase().includes(q)&&(!el("only-flags").checked||r.ml_suspicious));
}
function renderReviews(){
  const rows=filteredReviews(),pages=Math.max(1,Math.ceil(rows.length/20));
  currentPage=Math.min(currentPage,pages);
  el("match-count").textContent=rows.length+" matching reviews";
  el("page").textContent="Page "+currentPage+" of "+pages;
  el("prev").disabled=currentPage===1;el("next").disabled=currentPage===pages;
  el("reviews").innerHTML='<table><tr><th>BUSINESS / REVIEW</th><th>REVIEWER</th><th>RATING</th><th>RULE SCORE</th><th>ML ESTIMATE</th></tr>'+
    rows.slice((currentPage-1)*20,currentPage*20).map(r=>'<tr><td><b>'+escapeText(r.business)+'</b><p>'+escapeText(r.body)+'</p><small>'+escapeText(r.posted.slice(0,10))+'</small></td><td>'+escapeText(r.reviewer)+'</td><td>'+r.rating+'/5</td><td>'+r.score+'/100</td><td class="'+(r.ml_suspicious?'high':'')+'"><b>'+r.ml_score.toFixed(1)+'%</b><p>'+(r.ml_suspicious?'Flagged':'Not flagged')+'</p><details><summary>ML factors</summary>'+r.ml_reasons.map(f=>'<p>'+escapeText(f.feature)+' = '+f.value+' ('+(f.effect>=0?'+':'')+f.effect.toFixed(3)+' log-odds)</p>').join('')+'</details></td></tr>').join('')+'</table>';
}
for(const id of ["business","search","only-flags"])el(id).addEventListener("input",()=>{currentPage=1;renderReviews()});
el("prev").onclick=()=>{currentPage--;renderReviews()};
el("next").onclick=()=>{currentPage++;renderReviews()};
document.addEventListener("click",e=>{const button=e.target.closest("[data-business]");if(button){el("business").value=button.dataset.business;currentPage=1;renderReviews();el("business").scrollIntoView({behavior:"smooth"})}});

async function load(){
  const files=await Promise.all(["model.json","demo_data.json","metrics.json"].map(async name=>{
    const response=await fetch(name);if(!response.ok)throw Error("Could not load "+name);return response.json()}));
  [model,dataset,report]=files;
  el("analyze").disabled=false;
  const flags=dataset.reviews.filter(r=>r.ml_suspicious).length;
  el("stats").innerHTML=[["Snapshot reviews",dataset.reviews.length],["Businesses",dataset.businesses.length],["ML flags",flags],["Training examples",report.rows]].map(x=>'<div class="stat">'+x[0]+'<strong>'+x[1]+'</strong></div>').join('');
  el("business").innerHTML='<option value="0">All businesses</option>'+dataset.businesses.map(b=>'<option value="'+b.id+'">'+escapeText(b.name)+'</option>').join('');
  el("businesses").innerHTML='<table><tr><th>BUSINESS</th><th>REVIEWS</th><th>AVERAGE RATING</th><th>ML FLAGS</th></tr>'+dataset.businesses.map(b=>{
    const rows=dataset.reviews.filter(r=>r.business_id===b.id),average=rows.reduce((s,r)=>s+r.rating,0)/Math.max(1,rows.length);
    return '<tr><td><button class="light" data-business="'+b.id+'">'+escapeText(b.name)+'</button></td><td>'+rows.length+'</td><td>'+average.toFixed(1)+'/5</td><td>'+rows.filter(r=>r.ml_suspicious).length+'</td></tr>'}).join('')+'</table>';
  const t=report.test;
  el("metrics").innerHTML='<p><b>Held-out synthetic test only:</b> Precision '+(100*t.precision).toFixed(1)+'% · Recall '+(100*t.recall).toFixed(1)+'% · F1 '+t.f1.toFixed(3)+' · ROC-AUC '+t.roc_auc.toFixed(3)+'</p><p class="metric-note">Test set: '+report.counts.test.rows+' reviews from '+report.test_groups.length+' unseen simulated businesses. Majority-class accuracy baseline: '+(100*report.majority_baseline.accuracy).toFixed(1)+'%. These numbers do not measure real review fraud accuracy.</p><p>Confusion matrix [actual genuine, actual campaign] × [predicted genuine, predicted campaign]: '+escapeText(JSON.stringify(t.confusion_matrix))+'.</p>';
  el("status").textContent="Model loaded · Snapshot exported "+dataset.exported_at.slice(0,10)+" · Read-only demonstration";
  renderReviews();showPrediction();
}
load().catch(error=>el("status").textContent=error.message);
