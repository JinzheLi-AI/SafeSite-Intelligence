import fs from 'node:fs';
import path from 'node:path';
import ts from 'typescript';
const en=JSON.parse(fs.readFileSync('../shared/locales/en.json','utf8'));
const zh=JSON.parse(fs.readFileSync('../shared/locales/zh-CN.json','utf8'));
const missing=[];
for (const key of new Set([...Object.keys(en),...Object.keys(zh)])) if (!en[key] || !zh[key]) missing.push(key);
function visitFile(file) {
 const source=ts.createSourceFile(file,fs.readFileSync(file,'utf8'),ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
 function visit(node) {
  if(ts.isCallExpression(node) && node.expression.getText(source)==='t' && node.arguments[0] && ts.isStringLiteral(node.arguments[0])) {
   const key=node.arguments[0].text;
   if(!en[key] || !zh[key]) missing.push(file+': '+key);
  }
  ts.forEachChild(node,visit);
 }
 visit(source);
}
function walk(dir) {for(const entry of fs.readdirSync(dir,{withFileTypes:true})) {const p=path.join(dir,entry.name); if(entry.isDirectory()) walk(p); else if(p.endsWith('.tsx')) visitFile(p);}}
walk('src');
if(missing.length) { console.error(missing.join('\n')); process.exit(1); }
console.log(`Locale parity and all literal UI translation keys passed (${Object.keys(en).length} keys per locale).`);
