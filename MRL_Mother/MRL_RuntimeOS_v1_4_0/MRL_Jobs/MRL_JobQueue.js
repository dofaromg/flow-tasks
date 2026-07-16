const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
class MRLJobQueue {
  constructor(root, runner, logger) { this.root=root; this.runner=runner; this.logger=logger; this.dir=path.join(root,'MRL_Storage','MRL_Jobs'); fs.mkdirSync(this.dir,{recursive:true}); }
  _file(id){ return path.join(this.dir, `${id}.json`); }
  submit(body){ const id='MRL_JOB_'+Date.now()+'_'+crypto.randomBytes(4).toString('hex'); const rec={job_id:id, origin_signature:'MrLiouWord', status:'queued', created_at:new Date().toISOString(), input:body}; fs.writeFileSync(this._file(id), JSON.stringify(rec,null,2)); this.logger && this.logger.log('MRL_JOB_QUEUED',{job_id:id}); setImmediate(()=>this.run(id)); return rec; }
  run(id){ const f=this._file(id); if(!fs.existsSync(f)) return null; const rec=JSON.parse(fs.readFileSync(f,'utf8')); rec.status='running'; rec.started_at=new Date().toISOString(); fs.writeFileSync(f, JSON.stringify(rec,null,2)); try { rec.result=this.runner(rec.input||{}); rec.status='completed'; rec.completed_at=new Date().toISOString(); } catch(e) { rec.status='failed'; rec.error={message:e.message, stack:e.stack}; rec.failed_at=new Date().toISOString(); } fs.writeFileSync(f, JSON.stringify(rec,null,2)); this.logger && this.logger.log('MRL_JOB_FINISHED',{job_id:id,status:rec.status}); return rec; }
  get(id){ const f=this._file(id); return fs.existsSync(f) ? JSON.parse(fs.readFileSync(f,'utf8')) : null; }
  list(){ return fs.readdirSync(this.dir).filter(x=>x.endsWith('.json')).sort().reverse().slice(0,200).map(x=>this.get(x.replace(/\.json$/,''))); }
}
module.exports = { MRLJobQueue };
