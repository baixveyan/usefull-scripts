import { buildNote } from './format.mjs';

const field = (name) => document.getElementById(name);
const now = new Date();
field('date').value = [now.getFullYear(), String(now.getMonth() + 1).padStart(2, '0'), String(now.getDate()).padStart(2, '0')].join('-');
let currentNote = null;

function update() {
  try {
    currentNote = buildNote({
      title: field('title').value, url: field('url').value, category: field('category').value,
      date: field('date').value, version: field('version').value, license: field('license').value,
      notes: field('notes').value, preserveParameters: field('preserve').checked,
    });
    field('preview').value = currentNote.content;
    field('status').textContent = '仅在本地生成，导出前请检查预览。';
    field('download').disabled = false;
  } catch (error) {
    currentNote = null;
    field('preview').value = '';
    field('status').textContent = error instanceof TypeError ? '请填写有效来源地址。' : error.message;
    field('download').disabled = true;
  }
}

document.querySelectorAll('input, select, textarea:not([readonly])').forEach((element) => element.addEventListener('input', update));
field('download').addEventListener('click', () => {
  update();
  if (!currentNote) return;
  const blob = new Blob([currentNote.content], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = currentNote.filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 3000);
});

update();
const browserApi = globalThis.browser ?? globalThis.chrome;
if (browserApi?.tabs?.query) {
  try {
    const [tab] = await browserApi.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      field('title').value = tab.title ?? '';
      field('url').value = tab.url ?? '';
      update();
    }
  } catch {
    field('status').textContent = '当前页信息不可读，请手动填写标题和地址。';
  }
}
