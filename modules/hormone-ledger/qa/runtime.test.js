import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { emptyState, isAssistant, parseSnapshot, replay } from '../src/runtime.js';

const block = rows => `<hormone>\n${rows}\n</hormone>`;
const first = block('漩涡鸣子|0|无\n日向雏田|100|九尾九喇嘛活体铠甲');
test('role/is_user compatibility excludes users and systems', () => {
  for (const m of [{role:'assistant'}, {is_user:false}, {mes:first}]) assert.ok(isAssistant(m));
  for (const m of [{role:'user'}, {role:'system'}, {is_system:true}, {is_user:true,role:'assistant'},null]) assert.equal(isAssistant(m),false);
});
test('exactly two records; valid empty and boundaries', () => {
  assert.deepEqual(parseSnapshot(block('')).state, emptyState());
  const {state} = parseSnapshot(first);
  assert.deepEqual(Object.keys(state), ['角色荷尔蒙','角色活体铠甲']);
  assert.deepEqual(state.角色荷尔蒙, {'漩涡鸣子':0,'日向雏田':100});
});
test('reject malformed, duplicate, nested, incremental and hostile rows atomically', () => {
  for (const text of [first+first, '<status>'+first+'</status>', '<affinity>'+first+'</affinity>', '<wlog>'+first+'</wlog>',
    block('甲|101|无'),block('甲|-1|无'),block('甲|1.5|无'),block('甲|+3|无'),block('甲|01|无'),
    block('甲|30|'),block('甲|30|无|额外'),block('甲|1|无\n甲|2|无'),block('__proto__|1|无'),
    '<hormone>甲|1|无', '</hormone>', block('<hormone>甲|1|无'),block('甲|1|<img>')]) assert.ok(parseSnapshot(text).error,text);
});
test('inheritance validates completeness and retains first encounter order', () => {
  const previous = parseSnapshot(first).state;
  assert.ok(parseSnapshot(block('漩涡鸣子|9|无'),previous).error);
  const next = parseSnapshot(block('日向雏田|70|无\n新角色|50|某铠甲\n漩涡鸣子|7|无'),previous).state;
  assert.deepEqual(Object.keys(next.角色荷尔蒙),['漩涡鸣子','日向雏田','新角色']);
});
test('missing snapshot retains old data with exact upstream diagnostic', () => {
  const result = replay([{role:'assistant',message:first},{is_user:true,mes:block('假人|99|无')},{is_user:false,mes:'无变化'}]);
  assert.equal(result.state.角色荷尔蒙.日向雏田,100);
  assert.deepEqual(result.diagnostics,[{message_id:2,error:'本回合 hormone 输出缺失',cause:'上游输出契约失败'}]);
});
test('edits, deletes and new chat replay selected raw history without stale data', () => {
  assert.deepEqual(replay([]).state, emptyState());
  assert.deepEqual(replay([{mes:first}]).state,parseSnapshot(first).state);
  assert.deepEqual(replay([{mes:block('另一人|20|无')}]).state.角色荷尔蒙,{'另一人':20});
  assert.equal(replay([{mes:'<opening>'+first+'</opening>'}]).latest,null);
});
test('case-insensitive multiline CRLF snapshot and metadata-shaped messages', () => {
  const parsed = parseSnapshot('<HORMONE>\r\n漩涡鸣子 | 37 | 无\r\n</HORMONE>  ');
  assert.equal(parsed.state.角色荷尔蒙.漩涡鸣子,37);
  assert.equal(replay([{message_id:42,is_user:false,mes:first}]).latest,42);
});
test('display regex wraps full multiline snapshot without changing prompt or state', () => {
  const config = JSON.parse(readFileSync(new URL('../dist/regex.json',import.meta.url),'utf8'));
  assert.equal(config.findRegex,String(/<hormone>\s*([\s\S]*?)\s*<\/hormone>\s*/gi));
  assert.equal(config.markdownOnly,true);assert.equal(config.promptOnly,false);
  assert.deepEqual(config.placement,[2]);
  const re = new RegExp(config.findRegex.slice(1,config.findRegex.lastIndexOf('/')),'gi');
  const source = '正文\n<HORMONE>\r\n角色|0|无\r\n角色乙|100|长名称铠甲\r\n</HORMONE>\r\n';
  const result = source.replace(re,config.replaceString);
  assert.equal((result.match(/<details/g)||[]).length,1);
  assert.ok(result.includes('角色|0|无\r\n角色乙|100|长名称铠甲'));
  assert.ok(!/<\/?hormone>/i.test(result));
  assert.ok(!/<script|background-image|<img|<iframe| open[ >]/i.test(result));
  assert.ok(source.includes('<HORMONE>'));
});
