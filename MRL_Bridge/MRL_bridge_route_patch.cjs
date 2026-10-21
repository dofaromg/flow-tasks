const fs = require('fs');
const path = 'D:\\mrl\\bridge\\server.js';

// 先備份
const src = fs.readFileSync(path, 'utf8');
fs.writeFileSync(path.replace('server.js', 'server_v3.0_pre_rename.js'), src, 'utf8');

// 路由重命名對照表：只改 app.get/post 的第一個參數字串
const routeMap = [
  // GET routes
  ["app.get('/pg',",        "app.get('/MRL_pg',"],
  ["app.get('/tables',",    "app.get('/MRL_tables',"],
  ["app.get('/ls',",        "app.get('/MRL_ls',"],
  ["app.get('/cat',",       "app.get('/MRL_cat',"],
  ["app.get('/run',",       "app.get('/MRL_run',"],
  ["app.get('/redis-cmd',", "app.get('/MRL_redis_cmd',"],
  ["app.get('/sysinfo',",   "app.get('/MRL_sysinfo',"],
  ["app.get('/write',",     "app.get('/MRL_write',"],
  ["app.get('/audit',",     "app.get('/MRL_audit',"],
  // POST routes
  ["app.post('/file/write',", "app.post('/MRL_file/write',"],
  ["app.post('/file/read',",  "app.post('/MRL_file/read',"],
  ["app.post('/file/list',",  "app.post('/MRL_file/list',"],
  ["app.post('/exec',",       "app.post('/MRL_exec',"],
  ["app.post('/pg/query',",   "app.post('/MRL_pg/query',"],
  ["app.post('/redis',",      "app.post('/MRL_redis',"],
];

let result = src;
let count = 0;
for (const [old, rep] of routeMap) {
  if (result.includes(old)) {
    result = result.replace(old, rep);
    count++;
  } else {
    console.log('WARN: not found: ' + old);
  }
}

// 版本號推進
result = result.replace("MRL_Bridge_API v3.0.0", "MRL_Bridge_API v3.1.0");
result = result.replace("version: '3.0.0'", "version: '3.1.0'");

fs.writeFileSync(path, result, 'utf8');
console.log('Patched ' + count + '/15 routes → MRL_ prefix');
console.log('Version: v3.0.0 → v3.1.0');
console.log('Backup: server_v3.0_pre_rename.js');
