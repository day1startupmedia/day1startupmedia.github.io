/* Day1: share article as Instagram Story image (1080x1920) */
(function(){
var W=1080,H=1920,Y='#FFC800',file=null,busy=null;
function $(s){return document.querySelector(s)}
function load(src){return new Promise(function(ok,no){var i=new Image();i.onload=function(){ok(i)};i.onerror=no;i.src=src})}
function rr(c,x,y,w,h,r){c.beginPath();c.moveTo(x+r,y);c.arcTo(x+w,y,x+w,y+h,r);c.arcTo(x+w,y+h,x,y+h,r);c.arcTo(x,y+h,x,y,r);c.arcTo(x,y,x+w,y,r);c.closePath()}
function wrap(c,t,max){var w=t.split(/\s+/),L=[],l='';w.forEach(function(x){var s=l?l+' '+x:x;if(c.measureText(s).width>max&&l){L.push(l);l=x}else l=s});if(l)L.push(l);return L}
var F='system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif';
function draw(){
 var h1=$('article.post h1'),cv=$('figure.cover img'),cat=$('.meta .cat');
 var title=h1?h1.textContent.trim():document.title;
 return Promise.all([load('/static/img/logo.png').catch(function(){}),cv?load(cv.currentSrc||cv.src).catch(function(){}):null]).then(function(r){
  var k=document.createElement('canvas');k.width=W;k.height=H;var c=k.getContext('2d');
  c.fillStyle='#0b0b0b';c.fillRect(0,0,W,H);
  var g=c.createRadialGradient(W,0,0,W,0,1100);g.addColorStop(0,'rgba(255,200,0,.35)');g.addColorStop(1,'rgba(255,200,0,0)');c.fillStyle=g;c.fillRect(0,0,W,H);
  g=c.createRadialGradient(0,H,0,0,H,900);g.addColorStop(0,'rgba(255,200,0,.18)');g.addColorStop(1,'rgba(255,200,0,0)');c.fillStyle=g;c.fillRect(0,0,W,H);
  var lg=r[0],im=r[1],y=170;
  if(lg){var lw=340,lh=lw*lg.height/lg.width;c.drawImage(lg,(W-lw)/2,y,lw,lh);y+=lh+50}else y+=150;
  if(im){var x=60,w=W-120,hh=w*9/16,s=Math.max(w/im.width,hh/im.height),sw=w/s,sh=hh/s;
   c.save();rr(c,x,y,w,hh,28);c.clip();c.drawImage(im,(im.width-sw)/2,(im.height-sh)/2,sw,sh,x,y,w,hh);c.restore();
   c.lineWidth=6;c.strokeStyle=Y;rr(c,x,y,w,hh,28);c.stroke();y+=hh+60}
  if(cat){var ct=cat.textContent.trim().toUpperCase();c.font='800 34px '+F;var cw=c.measureText(ct).width+48;c.fillStyle=Y;rr(c,60,y,cw,62,31);c.fill();c.fillStyle='#0b0b0b';c.textBaseline='middle';c.fillText(ct,84,y+33);y+=100}
  c.textBaseline='top';c.fillStyle='#fff';
  var fs=78,L;for(;fs>=48;fs-=4){c.font='800 '+fs+'px '+F;L=wrap(c,title,W-120);if(L.length*fs*1.18<=1400-y)break}
  if(L.length*fs*1.18>1400-y){var n=Math.floor((1400-y)/(fs*1.18));L=L.slice(0,n);L[n-1]+='…'}
  L.forEach(function(l,i){c.fillText(l,60,y+i*fs*1.18)});
  y=1430;c.fillStyle=Y;rr(c,60,y,W-120,110,24);c.fill();
  c.fillStyle='#0b0b0b';c.font='800 42px '+F;c.textAlign='center';c.textBaseline='middle';c.fillText('Read full story on Day1 Startup Media',W/2,y+57);
  c.fillStyle='#fff';c.font='700 40px '+F;var cl=$('link[rel=canonical]');c.fillText(cl?cl.href.split('/')[2]:location.host,W/2,1610);
  c.fillStyle=Y;c.font='800 46px '+F;c.fillText('@day1_startup',W/2,1680);
  return new Promise(function(ok){k.toBlob(function(b){file=new File([b],'day1-story.png',{type:'image/png'});ok(file)},'image/png')});
 })}
function get(){return file?Promise.resolve(file):(busy||(busy=draw()))}
function toast(m){var t=document.createElement('div');t.className='ig-toast';t.textContent=m;document.body.appendChild(t);setTimeout(function(){t.remove()},7000)}
function copy(u){try{navigator.clipboard.writeText(u).catch(function(){})}catch(e){}}
function save(f,u){var a=document.createElement('a');a.href=URL.createObjectURL(f);a.download='day1-story.png';document.body.appendChild(a);a.click();a.remove();
 toast('Image saved. Open Instagram → Story → pick this image → paste this link in a link sticker: '+u)}
function go(f,u){var d={files:[f],title:document.title};
 if(navigator.canShare&&navigator.canShare(d)){navigator.share(d).catch(function(e){if(e.name!='AbortError')save(f,u)});toast('Choose Instagram → Story. Link copied: paste it in a link sticker')}
 else save(f,u)}
function tap(e){e.preventDefault();var l=$('link[rel=canonical]'),u=l?l.href:location.href.split('#')[0];copy(u);
 if(file)go(file,u);else get().then(function(f){go(f,u)})}
document.querySelectorAll('[data-igstory]').forEach(function(b){b.addEventListener('click',tap)});
window.day1Story=get;
addEventListener('load',function(){setTimeout(get,800)});
})();
/* Day1: on the Google Translate proxy, point links back to the original English site */
(function(){if(!/\.translate\.goog$/.test(location.hostname))return;var O='https://day1startup.com';document.querySelectorAll('a[href]').forEach(function(a){var h=a.getAttribute('href'),u;try{u=new URL(h,location.href)}catch(e){return}
if(u.hostname=='translate.google.com'&&u.searchParams.get('u'))a.setAttribute('href',u.searchParams.get('u'));
else if(/\.translate\.goog$/.test(u.hostname)){if(u.pathname==location.pathname&&/#/.test(h)){a.setAttribute('href',u.hash||'#');return}['_x_tr_sl','_x_tr_tl','_x_tr_hl','_x_tr_pto','_x_tr_hist'].forEach(function(k){u.searchParams.delete(k)});a.setAttribute('href',O+u.pathname+u.search+u.hash)}})})();
/* Day1: native Share button + Android app links for LinkedIn/X */
(function(){
var ua=navigator.userAgent,A=/Android/i.test(ua);
function url(){var l=document.querySelector('link[rel=canonical]');return l?l.href:location.href.split('#')[0]}
function toast(m){var t=document.createElement('div');t.className='ig-toast';t.textContent=m;document.body.appendChild(t);setTimeout(function(){t.remove()},6000)}
document.querySelectorAll('[data-share]').forEach(function(b){b.addEventListener('click',function(e){e.preventDefault();var u=url(),h=document.querySelector('article.post h1'),t=h?h.textContent.trim():document.title;
 if(navigator.share){navigator.share({title:t,text:t,url:u}).catch(function(){});return}
 try{navigator.clipboard.writeText(u).catch(function(){})}catch(x){}
 if(A&&/FBAN|FBAV|FB_IAB|Instagram/.test(ua)){toast('Opening in Chrome. Tap Share there');location.href='intent://'+u.replace(/^https?:\/\//,'')+'#Intent;scheme=https;package=com.android.chrome;S.browser_fallback_url='+encodeURIComponent(u)+';end';return}
 toast('Link copied: '+u)})});
if(A)[['s-li','com.linkedin.android'],['s-x','com.twitter.android']].forEach(function(p){document.querySelectorAll('a.'+p[0]).forEach(function(a){var w=a.href,v=w.replace('x.com/intent/post','twitter.com/intent/tweet');
 a.href='intent://'+v.replace(/^https:\/\//,'')+'#Intent;scheme=https;package='+p[1]+';S.browser_fallback_url='+encodeURIComponent(w)+';end';a.removeAttribute('target')})});
})();
/* Day1: "Read in" language selector -> Google Translate website proxy */
(function(){var s=document.getElementById('lg');if(!s)return;[['hi','हिन्दी (Hindi)'],['bn','বাংলা (Bengali)'],['mr','मराठी (Marathi)'],['te','తెలుగు (Telugu)'],['ta','தமிழ் (Tamil)'],['gu','ગુજરાતી (Gujarati)'],['ur','اردو (Urdu)'],['kn','ಕನ್ನಡ (Kannada)'],['ml','മലയാളം (Malayalam)'],['pa','ਪੰਜਾਬੀ (Punjabi)']].forEach(function(l){s.add(new Option(l[1],l[0]))});var q=new URLSearchParams(location.search).get('_x_tr_tl');if(q&&s.querySelector('[value="'+q+'"]'))s.value=q;
s.onchange=function(){var c=s.value,p=location.pathname;location.href=c=='en'?'https://day1startup.com'+p:'https://day1startup-com.translate.goog'+p+'?_x_tr_sl=en&_x_tr_tl='+c+'&_x_tr_hl='+c}})();
