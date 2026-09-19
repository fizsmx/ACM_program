'use strict';
const $ = (id) => document.getElementById(id);
const els = {
  status: $('status'), problem: $('problem'), language: $('language'), reasoning: $('reasoning'),
  stmtlang: $('stmtlang'),
  solve: $('btnSolve'), cancel: $('btnCancel'), clear: $('btnClear'), copy: $('btnCopy'), run: $('btnRun'),
  phase: $('phase'), analysis: $('analysis'), code: $('code'), results: $('results'),
  thinking: $('thinking'), thinkLen: $('thinkLen'), thinkBox: $('thinkBox'), devlog: $('devlog'),
  tests: $('tests'), testsCount: $('testsCount'), addTest: $('btnAddTest'), devmode: $('devmode'),
  runModal: $('runModal'), runInput: $('runInput'), runOutput: $('runOutput'), runGo: $('btnRunGo'), runClose: $('btnRunClose'),
};
let solving = false, streamBuf = '', lastEvents = [];
let phaseName = 'idle', phaseStart = 0, solveStart = 0, timerId = null;
function fmt(ms) { const s = Math.floor(ms / 1000); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; }
function tick() { if (!solving) return; els.phase.textContent = `${phaseName}  ·  ${fmt(Date.now() - phaseStart)} (total ${fmt(Date.now() - solveStart)})`; }

function dev(msg) { els.devlog.textContent += msg + '\n'; els.devlog.scrollTop = els.devlog.scrollHeight; }
function setPhase(t, cls) { phaseName = t; phaseStart = Date.now(); els.phase.textContent = t; els.phase.className = 'phase' + (cls ? ' ' + cls : ''); }
function pill(r) {
  const p = document.createElement('span');
  p.className = 'pill ' + r.status; p.textContent = `#${r.index + 1} ${r.status} ${r.time_ms}ms`;
  p.title = (r.detail || '') + (r.stderr ? '\n' + r.stderr : '');
  p.onclick = () => alert(`Test ${r.index + 1}: ${r.status}\n${r.detail || ''}\n\n--- stdout ---\n${r.stdout || ''}\n--- stderr ---\n${r.stderr || ''}`);
  return p;
}

// ---------------- tests editor
function renderTests(tests) {
  els.tests.innerHTML = '';
  tests.forEach((t) => addTestRow(t.input, t.expected));
  updateTestCount();
}
function addTestRow(input = '', expected = '') {
  const row = document.createElement('div'); row.className = 'test';
  row.innerHTML = `<textarea placeholder="input"></textarea><textarea placeholder="expected output"></textarea><button class="small" title="remove">×</button>`;
  row.children[0].value = input; row.children[1].value = expected;
  row.children[2].onclick = () => { row.remove(); updateTestCount(); };
  els.tests.appendChild(row); updateTestCount();
}
function readTests() {
  return [...els.tests.querySelectorAll('.test')].map((r) => ({ input: r.children[0].value, expected: r.children[1].value }))
    .filter((t) => t.input.trim() && t.expected.trim()).map((t) => ({ input: t.input.replace(/\r\n/g, '\n').replace(/\s+$/, '') + '\n', expected: t.expected.replace(/\r\n/g, '\n').replace(/\s+$/, '') + '\n' }));
}
function updateTestCount() { const n = els.tests.querySelectorAll('.test').length; els.testsCount.textContent = n ? `(${n})` : ''; }
els.addTest.onclick = (e) => { e.preventDefault(); addTestRow(); };

// ---------------- status
async function refreshStatus() {
  try {
    const r = await fetch('/api/status'); const s = await r.json();
    const rt = s.runtime;
    els.status.textContent = `${s.llm_ok ? '● ' : '○ '}${rt.model} · ${rt.profile} · ${rt.backend} · ${rt.gen_tps} tok/s · thinking budget ${rt.reasoning_budget}` + (s.busy ? ' · BUSY' : '');
    els.status.style.color = s.llm_ok ? 'var(--ok)' : 'var(--bad)';
  } catch (e) { els.status.textContent = 'backend unreachable'; els.status.style.color = 'var(--bad)'; }
}
refreshStatus(); setInterval(refreshStatus, 10000);

// ---------------- solve
function handleEvent(ev) {
  lastEvents.push(ev);
  switch (ev.type) {
    case 'phase':
      setPhase(ev.name + (ev.reasoning_budget ? ` (thinking ≤ ${ev.reasoning_budget} tok)` : ''));
      streamBuf = ''; els.thinking.textContent = ''; els.thinkLen.textContent = '';
      dev(`--- phase ${ev.name}`); break;
    case 'token':
      if (ev.channel === 'reasoning') { els.thinking.textContent += ev.text; els.thinkLen.textContent = `(${els.thinking.textContent.length} chars)`; if (els.thinkBox.open) els.thinking.scrollTop = els.thinking.scrollHeight; }
      else { streamBuf += ev.text; els.code.textContent = streamBuf; els.code.scrollTop = els.code.scrollHeight; }
      break;
    case 'llm_done': dev(`llm ${ev.phase}: ${ev.seconds}s, reasoning ${ev.reasoning_chars} chars, answer ${ev.content_chars} chars, ${ev.gen_tps ? ev.gen_tps.toFixed(1) : '?'} tok/s`); break;
    case 'examples': renderTests(ev.tests); dev(`examples: ${ev.tests.length} (source ${ev.source})`); break;
    case 'code': els.code.textContent = ev.code; els.analysis.textContent = ev.analysis || ''; els.results.innerHTML = ''; setPhase('testing…'); break;
    case 'test_result': els.results.appendChild(pill(ev)); break;
    case 'attempt_done': dev(`attempt ${ev.attempt}: ${ev.passed}/${ev.total} passed`); break;
    case 'status': dev(ev.text); break;
    case 'done': {
      const b = document.createElement('div'); b.className = 'banner ' + ev.status;
      b.textContent = ev.status === 'PASS' ? `✔ All sample tests passed (${ev.seconds}s, ${ev.attempts.length} attempt${ev.attempts.length > 1 ? 's' : ''})`
        : ev.status === 'UNVERIFIED' ? `⚠ No sample tests: code NOT verified (${ev.seconds}s)`
        : ev.status === 'TIMEOUT' ? `⏱ Time limit reached (${ev.seconds}s) — showing the last code produced, NOT verified` : `✖ Still failing after ${ev.attempts.length} attempts (${ev.seconds}s) — check the code`;
      els.results.prepend(b); els.code.textContent = ev.code || els.code.textContent; setPhase(ev.status, ev.status);
      break; }
    case 'cancelled': setPhase('cancelled'); break;
    case 'error': { const b = document.createElement('div'); b.className = 'banner error'; b.textContent = 'Error: ' + ev.message; els.results.prepend(b); setPhase('error'); break; }
  }
}

async function solve() {
  const problem = els.problem.value.trim();
  if (!problem) { els.problem.focus(); return; }
  solving = true; els.solve.disabled = true; els.cancel.disabled = false;
  els.results.innerHTML = ''; els.analysis.textContent = ''; els.code.textContent = ''; els.devlog.textContent = ''; lastEvents = [];
  solveStart = Date.now(); setPhase('starting…'); if (timerId) clearInterval(timerId); timerId = setInterval(tick, 1000);
  const body = { problem, language: els.language.value, reasoning: els.reasoning.checked, statement_lang: els.stmtlang.value };
  const tests = readTests(); if (tests.length) body.tests = tests;
  try {
    const r = await fetch('/api/solve', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.error || r.statusText); }
    const reader = r.body.getReader(); const dec = new TextDecoder(); let buf = '';
    for (;;) {
      const { value, done } = await reader.read(); if (done) break;
      buf += dec.decode(value, { stream: true });
      let i;
      while ((i = buf.indexOf('\n\n')) >= 0) {
        const chunk = buf.slice(0, i); buf = buf.slice(i + 2);
        if (chunk.startsWith('data: ')) { try { handleEvent(JSON.parse(chunk.slice(6))); } catch (e) { dev('bad event ' + e); } }
      }
    }
  } catch (e) { handleEvent({ type: 'error', message: e.message }); }
  solving = false; clearInterval(timerId); timerId = null; els.solve.disabled = false; els.cancel.disabled = true; refreshStatus();
}
els.solve.onclick = solve;
els.cancel.onclick = () => fetch('/api/cancel', { method: 'POST' });
els.clear.onclick = () => { if (solving) return; els.problem.value = ''; els.code.textContent = ''; els.results.innerHTML = ''; els.analysis.textContent = ''; els.tests.innerHTML = ''; updateTestCount(); setPhase('idle'); };
els.copy.onclick = async () => {
  const code = els.code.textContent;
  try { await navigator.clipboard.writeText(code); } catch (e) {
    const ta = document.createElement('textarea'); ta.value = code; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove();
  }
  els.copy.textContent = 'Copied!'; setTimeout(() => (els.copy.textContent = 'Copy code'), 1200);
};
els.devmode.onchange = () => document.body.classList.toggle('dev', els.devmode.checked);

// ---------------- run with custom input
els.run.onclick = () => { els.runModal.classList.remove('hidden'); els.runOutput.textContent = ''; els.runInput.focus(); };
els.runClose.onclick = () => els.runModal.classList.add('hidden');
els.runGo.onclick = async () => {
  els.runOutput.textContent = 'running…';
  const r = await fetch('/api/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code: els.code.textContent, language: els.language.value, input: els.runInput.value }) });
  const j = await r.json();
  els.runOutput.textContent = `[${j.status} ${j.time_ms || 0} ms exit=${j.exit_code}]\n${j.stdout || ''}${j.stderr ? '\n--- stderr ---\n' + j.stderr : ''}`;
};
document.addEventListener('keydown', (e) => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && !solving) solve(); });
