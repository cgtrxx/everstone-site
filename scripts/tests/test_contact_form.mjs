import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';

const source = readFileSync(new URL('../../assets/main.js', import.meta.url), 'utf8');
const html = readFileSync(new URL('../../contact/index.html', import.meta.url), 'utf8');

function harness(valid = true) {
  let submit, prevented = false, reported = false, focused = false, requests = 0;
  const status = { textContent:'', focus(){ focused = true; } };
  const form = { addEventListener(event, fn){ if(event === 'submit') submit = fn; },
    checkValidity:()=>valid, reportValidity(){ reported = true; } };
  const document = { querySelector:selector=>selector === '#estimate-form' ? form : selector === '#form-status' ? status : null };
  vm.runInNewContext(source, { document, Date, fetch(){ requests++; throw Error('Unexpected network request'); } });
  return { submit(){ submit({preventDefault(){prevented = true;}}); }, status,
    state:()=>({prevented,reported,focused,requests}) };
}

test('valid inquiry stays local and explicitly reports that nothing was sent',()=>{
  const h = harness(); h.submit();
  assert.match(h.status.textContent,/does not send inquiries/);
  assert.deepEqual(h.state(),{prevented:true,reported:false,focused:true,requests:0});
});
test('invalid inquiry stays local and invokes native validity feedback',()=>{
  const h = harness(false); h.submit();
  assert.match(h.status.textContent,/required fields/);
  assert.deepEqual(h.state(),{prevented:true,reported:true,focused:false,requests:0});
});
test('contact markup clearly describes the prototype review flow',()=>{
  assert.match(html,/id="estimate-form"/);
  assert.match(html,/submissions are not sent yet/);
  assert.doesNotMatch(html,/action="https?:/);
  assert.match(html,/role="status" aria-live="polite"/);
});
test('navigation remains usable and Escape closes an expanded menu',()=>{
  let click, key, open = false;
  const attrs = new Map();
  const toggle = {addEventListener:(event,fn)=>{click=fn;},setAttribute:(k,v)=>attrs.set(k,v),focus(){}};
  const nav = {classList:{toggle(){open=!open;return open;},contains(){return open;},remove(){open=false;}}};
  vm.runInNewContext(source,{Date,document:{querySelector:s=>s==='.menu-toggle'?toggle:s==='.nav-links'?nav:null,addEventListener:(event,fn)=>{key=fn;}}});
  click(); assert.equal(attrs.get('aria-expanded'),'true');
  key({key:'Escape'}); assert.equal(open,false); assert.equal(attrs.get('aria-expanded'),'false');
});
