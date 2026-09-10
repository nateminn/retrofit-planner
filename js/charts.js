/* Chart tooltips: hover and keyboard focus on any element with data-tip. Values are set with textContent only. */
(function(){
  var tip=null;
  function ensure(){if(!tip){tip=document.createElement('div');tip.className='chart-tip';tip.setAttribute('role','status');tip.hidden=true;document.body.appendChild(tip);}return tip;}
  function show(el){
    var t=ensure();var v=el.getAttribute('data-val')||'';var l=el.getAttribute('data-tip')||'';
    while(t.firstChild)t.removeChild(t.firstChild);
    var b=document.createElement('b');b.textContent=v;t.appendChild(b);t.appendChild(document.createTextNode(l));
    t.hidden=false;
    var r=el.getBoundingClientRect();var x=r.left+r.width/2+window.scrollX;var y=r.top+window.scrollY;
    t.style.left='0px';t.style.top='0px';
    var w=t.offsetWidth,h=t.offsetHeight;
    var left=Math.max(8,Math.min(x-w/2,document.documentElement.clientWidth-w-8));
    var top=y-h-10;if(top<window.scrollY+4)top=r.bottom+window.scrollY+10;
    t.style.left=left+'px';t.style.top=top+'px';
  }
  function hide(){if(tip)tip.hidden=true;}
  document.addEventListener('pointerover',function(e){var el=e.target.closest&&e.target.closest('[data-tip]');if(el)show(el);});
  document.addEventListener('pointerout',function(e){var el=e.target.closest&&e.target.closest('[data-tip]');if(el)hide();});
  document.addEventListener('focusin',function(e){var el=e.target.closest&&e.target.closest('[data-tip]');if(el)show(el);});
  document.addEventListener('focusout',function(e){var el=e.target.closest&&e.target.closest('[data-tip]');if(el)hide();});
  window.addEventListener('scroll',hide,{passive:true});
})();
