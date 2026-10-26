// 静态校验 server/gm/console.html 内联脚本的语法（node --check 语义）
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const m = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
if (!m.length) { console.error('NO SCRIPT BLOCK'); process.exit(1); }
const vm = require('vm');
m.forEach((mm, i) => {
  try { new vm.Script(mm[1], { filename: 'console.html#script' + i }); console.log('script#' + i + ' syntax OK (' + mm[1].length + ' chars)'); }
  catch (e) { console.error('script#' + i + ' SYNTAX ERROR: ' + e.message); process.exit(1); }
});
// 粗查：标签配对 + 引用到的 DOM id 是否都存在
const ids = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(x => x[1]));
const refs = new Set([...html.matchAll(/\$\('([^']+)'\)/g)].map(x => x[1]));
const missing = [...refs].filter(r => !ids.has(r));
console.log('DOM ids=' + ids.size + ' refs=' + refs.size + ' missing=' + JSON.stringify(missing));
if (missing.length) process.exit(2);
console.log('CONSOLE STATIC CHECK OK');
