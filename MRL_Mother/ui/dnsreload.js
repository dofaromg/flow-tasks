// MRL 前端 DNS/後端自癒 — origin_signature: MrLiouWord
// 放進前端 <head>:確認後端通,DNS 舊快取時自動重載一次
(function(){'use strict';
  var KEY='mrl_dns_ok', API='https://api.mrliouword.com/health';
  if(sessionStorage.getItem(KEY))return;
  fetch(API,{method:'GET',cache:'no-store'})
    .then(function(r){ if(r.ok){sessionStorage.setItem(KEY,'1');} else {throw 0;} })
    .catch(function(){ sessionStorage.setItem(KEY,'1'); setTimeout(function(){location.reload(true);},800); });
})();
