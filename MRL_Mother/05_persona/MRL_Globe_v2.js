/**
 * MRL_Globe_v2 — 粒子地球儀世界模組
 * origin_signature: MrLiouWord
 * 核心組: 世界模組/粒子地球儀 | 層級: L4 | 狀態: 可運行
 * v2.0: F3地理映射 + F8反推 + 衛星星座層 + 真實經緯度
 * 怎麼過去就怎麼回來
 */

const V='2.0.0',O='MrLiouWord',N=686,GRID=N>>1,G=1.618033988749895,R_E=6371;
const J=(d,s=200)=>new Response(JSON.stringify(d,null,2),{status:s,headers:{'Content-Type':'application/json','Access-Control-Allow-Origin':'*'}});
const GROUPS=['母體核心','粒子可逆原理','FlowAgent運行','世界模組地球儀','檔案索引管理員','人格共振演化','母體核心'];

// ═══ Haversine 距離 (km) ═══
function hav(lat1,lon1,lat2,lon2){
  const dLat=(lat2-lat1)*Math.PI/180;
  const dLon=(lon2-lon1)*Math.PI/180;
  const a=Math.sin(dLat/2)**2+Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
  return 2*R_E*Math.asin(Math.sqrt(a));
}

// ═══ F3: 地理映射 (經緯度 ↔ 粒子索引) ═══
function F3(lat,lon){
  const la=Math.floor(((lat+90)/180)*GRID);
  const lo=Math.floor(((lon+180)/360)*GRID);
  return((la+lo)%N+N)%N;
}
function F3_inv(pid,refLat,refLon){
  const c=[];
  for(let la=0;la<GRID;la++){
    const lo=((pid-la)%N+N)%N;
    if(lo<GRID)c.push({lat:+((la/GRID)*180-90).toFixed(4),lon:+((lo/GRID)*360-180).toFixed(4)});
  }
  // 如果提供參考座標，按距離排序
  if(refLat!==undefined&&refLon!==undefined){
    c.sort((a,b)=>hav(refLat,refLon,a.lat,a.lon)-hav(refLat,refLon,b.lat,b.lon));
  }
  return c.slice(0,8);
}

// ═══ 686粒子生成 (黃金螺旋+經緯度) ═══
function gen686(){
  const ps=[];
  for(let i=0;i<N;i++){
    // 黃金螺旋球面均勻分佈
    const phi=Math.acos(1-2*(i+0.5)/N);
    const theta=2*Math.PI*i*G;
    const lat=+(90-phi*180/Math.PI).toFixed(4);
    const lon=+(((theta*180/Math.PI)%360+360)%360-180).toFixed(4);
    ps.push({pid:i,lat,lon,group:GROUPS[i%GROUPS.length]});
  }
  return ps;
}

// ═══ 衛星星座層 (6軌道面 × 24顆) ═══
function genSatellites(){
  const sats=[];
  const ORBITS=6,PER=24;
  for(let o=0;o<ORBITS;o++){
    const inc=30+o*25;          // 軌道傾角 (deg)
    const alt=550+o*200;        // 高度 (km)
    const raan=(o*360/ORBITS);  // 升交點赤經 (deg)
    for(let s=0;s<PER;s++){
      const ma=s*(360/PER);     // 平近點角 (deg)
      sats.push({id:`SAT-${o}-${s}`,orbit:o,inc,alt,raan,ma});
    }
  }
  return sats;
}

// ═══ 模組級快取 (粒子分佈恆定，避免重複運算) ═══
const PARTICLES=gen686();
const SATELLITES=genSatellites();

// ═══ F8: 反推 (粒子索引 → 地理資訊) ═══
function F8(pid){
  const p=PARTICLES[((pid%N)+N)%N];
  return{pid:p.pid,lat:p.lat,lon:p.lon,group:p.group,candidates:F3_inv(p.pid,p.lat,p.lon)};
}

// ═══ 最近鄰粒子查詢 ═══
function nearest(lat,lon,n=5){
  return PARTICLES
    .map(p=>({...p,dist:+hav(lat,lon,p.lat,p.lon).toFixed(3)}))
    .sort((a,b)=>a.dist-b.dist)
    .slice(0,Math.min(n,N));
}

// ═══ Cloudflare Worker fetch handler ═══
export default{
  async fetch(req){
    const url=new URL(req.url);
    const p=url.pathname;

    if(req.method==='OPTIONS')return J({ok:true});

    // GET /
    if(p==='/')return J({v:V,origin:O,n:N,golden_ratio:G,earth_radius_km:R_E,groups:GROUPS});

    // GET /particles
    if(p==='/particles')return J(PARTICLES);

    // GET /satellites
    if(p==='/satellites')return J(SATELLITES);

    // GET /f3/:lat/:lon
    const m3=p.match(/^\/f3\/([-\d.]+)\/([-\d.]+)$/);
    if(m3){
      const lat=+m3[1],lon=+m3[2];
      if(lat<-90||lat>90||lon<-180||lon>180)return J({error:'座標超出範圍'},400);
      return J({pid:F3(lat,lon),lat,lon});
    }

    // GET /f3inv/:pid?lat=&lon=
    const mi=p.match(/^\/f3inv\/(\d+)$/);
    if(mi){
      const pid=+mi[1];
      if(pid<0||pid>=N)return J({error:`pid須在0–${N-1}之間`},400);
      const refLat=url.searchParams.has('lat')?+url.searchParams.get('lat'):undefined;
      const refLon=url.searchParams.has('lon')?+url.searchParams.get('lon'):undefined;
      return J(F3_inv(pid,refLat,refLon));
    }

    // GET /f8/:pid
    const m8=p.match(/^\/f8\/(\d+)$/);
    if(m8){
      const pid=+m8[1];
      if(pid<0||pid>=N)return J({error:`pid須在0–${N-1}之間`},400);
      return J(F8(pid));
    }

    // GET /nearest?lat=&lon=&n=
    if(p==='/nearest'){
      const lat=+url.searchParams.get('lat');
      const lon=+url.searchParams.get('lon');
      const n=Math.min(+(url.searchParams.get('n')||5),50);
      if(isNaN(lat)||isNaN(lon)||lat<-90||lat>90||lon<-180||lon>180)
        return J({error:'需提供有效的lat/lon參數'},400);
      return J(nearest(lat,lon,n));
    }

    return J({error:'not found'},404);
  }
};
