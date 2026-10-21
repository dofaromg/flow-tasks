const fs = require('fs');
const { runPipeline } = require('../MRL_API/MRL_RuntimeServer');
const action = process.argv[2] || 'execute';
const file = process.argv[3];
const source = file && fs.existsSync(file) ? fs.readFileSync(file,'utf8') : 'particle CTX { @layer: L2 @data: "hello" }';
const result = runPipeline({source, filename:file||'stdin.fpp', command:source});
console.log(JSON.stringify(action === 'parse' ? result.bundle : result, null, 2));
