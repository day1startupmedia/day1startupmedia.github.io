(function(){var q=document.getElementById("q"),o=document.getElementById("sr"),B=document.querySelectorAll(".schips button"),c="",D=[];
function e(s){return String(s).replace(/[&<>"]/g,function(x){return"&#"+x.charCodeAt(0)+";"})}
function r(){var v=q.value.toLowerCase().trim(),w=v.split(/\s+/).filter(Boolean),h="",k=0;
D.forEach(function(a){if(c&&c.split("|").indexOf(a.c)<0)return;var x=(a.t+" "+a.s+" "+a.c+" "+a.g).toLowerCase();
for(var i=0;i<w.length;i++)if(x.indexOf(w[i])<0)return;k++;
h+='<a class="sres" href="/news/'+a.u+'/"><img src="'+a.i+'" alt="" loading="lazy" width="96" height="54"><span><em>'+e(a.c)+" · "+e(a.d)+"</em><b>"+e(a.t)+"</b></span></a>"});
o.innerHTML='<p class="scount">'+(k?k+(k>1?" stories":" story"):'No story found. Try a startup name or "funding".')+"</p>"+h;
history.replaceState(null,"",v?"?q="+encodeURIComponent(q.value.trim()):location.pathname)}
B.forEach(function(b){b.onclick=function(){B.forEach(function(x){x.className=""});b.className="on";c=b.getAttribute("data-c");r()}});
q.value=new URLSearchParams(location.search).get("q")||"";q.oninput=r;
fetch("/search.json").then(function(x){return x.json()}).then(function(d){D=d;r()})})();
