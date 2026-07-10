const fs = require('fs');
const file = 'D:\\mrl\\bridge\\server.js';
let code = fs.readFileSync(file, 'utf-8');

// 在 app.get('/health' 之前加入 /MRL_platform 路由
const platformRoute = `
// === MRL Platform UI (no auth, public) ===
app.get('/MRL_platform', (req, res) => {
  const htmlPath = 'D:\\\\mrl\\\\platform\\\\MRL_Platform_UI.html';
  try {
    if (require('fs').existsSync(htmlPath)) {
      const html = require('fs').readFileSync(htmlPath, 'utf-8');
      res.set('Content-Type', 'text/html; charset=utf-8');
      res.set('Cache-Control', 'no-cache');
      res.set('Access-Control-Allow-Origin', '*');
      return res.send(html);
    }
    res.status(404).json({ error: 'Platform UI not found' });
  } catch(e) {
    res.status(500).json({ error: e.message });
  }
});

`;

// Insert before the first app.get('/health'
if (code.includes('/MRL_platform')) {
  console.log('Route already exists');
  process.exit(0);
}

const insertPoint = "app.get('/health'";
const idx = code.indexOf(insertPoint);
if (idx === -1) {
  console.log('ERROR: Cannot find insertion point');
  process.exit(1);
}

code = code.slice(0, idx) + platformRoute + code.slice(idx);

// Backup
fs.writeFileSync(file + '.bak_platform', fs.readFileSync(file));
fs.writeFileSync(file, code, 'utf-8');
console.log('Patched: /MRL_platform route added');
console.log('Lines: ' + code.split('\n').length);
