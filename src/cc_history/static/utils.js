/* CC History - Utility Functions */

function formatTime(ts) {
  if (!ts) return '';
  try {
    let d = new Date(ts);
    if (isNaN(d.getTime())) d = new Date(Number(ts));
    if (isNaN(d.getTime())) return ts;
    const now = new Date(), diff = now - d, oneDay = 86400000;
    if (diff < oneDay && d.getDate() === now.getDate()) return d.toLocaleTimeString('zh-CN', {hour:'2-digit',minute:'2-digit'});
    if (diff < 2 * oneDay) return '昨天 ' + d.toLocaleTimeString('zh-CN', {hour:'2-digit',minute:'2-digit'});
    if (d.getFullYear() === now.getFullYear()) return d.toLocaleDateString('zh-CN',{month:'short',day:'numeric'})+' '+d.toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'});
    return d.toLocaleDateString('zh-CN',{year:'numeric',month:'short',day:'numeric'});
  } catch { return ts; }
}

function escapeHtml(t) { const d=document.createElement('div'); d.textContent=t; return d.innerHTML; }

let _codeBlockId = 0;
function renderMarkdown(text) {
  let h = escapeHtml(text);
  h = h.replace(/```(\w*)\n([\s\S]*?)```/g,(_,l,c)=>{
    const id = 'cb-' + (++_codeBlockId);
    return `<div class="code-block"><button class="copy-btn" onclick="copyCode(this,'${id}')" title="复制代码"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> 复制</button><pre><code id="${id}">${c}</code></pre></div>`;
  });
  h = h.replace(/`([^`]+)`/g,'<code>$1</code>');
  h = h.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');
  h = h.replace(/\*(.+?)\*/g,'<em>$1</em>');
  h = h.replace(/(https?:\/\/[^\s<]+)/g,'<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
  return h;
}

function copyCode(btn, id) {
  const code = document.getElementById(id);
  if (!code) return;
  navigator.clipboard.writeText(code.textContent).then(() => {
    btn.classList.add('copied');
    btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><polyline points="20 6 9 17 4 12"></polyline></svg> 已复制';
    setTimeout(() => {
      btn.classList.remove('copied');
      btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> 复制';
    }, 2000);
  });
}

async function fetchJson(url, options) {
  const res = await fetch(url, options);
  let data = null;
  try { data = await res.json(); } catch { data = null; }
  if (!res.ok) throw new Error((data && data.error) || `请求失败 (${res.status})`);
  return data;
}
