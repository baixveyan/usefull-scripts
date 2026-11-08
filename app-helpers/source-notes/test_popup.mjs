import assert from 'node:assert/strict';
import test from 'node:test';

let sequence = 0;
async function withPopup(callback, tab = { title: 'Synthetic source', url: 'https://example.com/data?token=secret' }) {
  const saved = { document: globalThis.document, chrome: globalThis.chrome, browser: globalThis.browser,
    timer: globalThis.setTimeout, create: URL.createObjectURL, revoke: URL.revokeObjectURL };
  const anchors = [];
  const blobs = [];
  const elements = Object.fromEntries(['title', 'url', 'category', 'date', 'version', 'license', 'notes', 'preserve', 'preview', 'status', 'download'].map((id) => [id, {
    id, value: id === 'category' ? 'datasets' : '', checked: false, disabled: false, textContent: '', handlers: {},
    addEventListener(name, handler) { this.handlers[name] = handler; },
  }]));
  globalThis.document = {
    getElementById: (id) => elements[id],
    querySelectorAll: () => Object.values(elements).filter((item) => !['preview', 'status', 'download'].includes(item.id)),
    createElement: () => {
      const anchor = { clicked: false, click() { this.clicked = true; }, remove() {} };
      anchors.push(anchor);
      return anchor;
    },
    body: { append() {} },
  };
  globalThis.browser = undefined;
  globalThis.chrome = { tabs: { query: async () => [tab] } };
  URL.createObjectURL = (blob) => { blobs.push(blob); return 'blob:synthetic'; };
  URL.revokeObjectURL = () => {};
  globalThis.setTimeout = (callback) => { callback(); return 0; };
  try {
    await import(`./popup.mjs?test=${sequence++}`);
    await callback({ elements, anchors, blobs });
  } finally {
    globalThis.document = saved.document;
    globalThis.chrome = saved.chrome;
    globalThis.browser = saved.browser;
    globalThis.setTimeout = saved.timer;
    URL.createObjectURL = saved.create;
    URL.revokeObjectURL = saved.revoke;
  }
}

test('popup reads only supplied active tab metadata and previews clean URL', async () => {
  await withPopup(async ({ elements }) => {
    assert.equal(elements.title.value, 'Synthetic source');
    assert.equal(elements.download.disabled, false);
    assert.ok(!elements.preview.value.includes('token=secret'));
    elements.preserve.checked = true;
    elements.preserve.handlers.input();
    assert.ok(elements.preview.value.includes('token=secret'));
  });
});

test('invalid source disables export without creating download', async () => {
  await withPopup(async ({ elements, anchors }) => {
    elements.url.value = 'javascript:alert(1)';
    elements.url.handlers.input();
    assert.equal(elements.download.disabled, true);
    elements.download.handlers.click();
    assert.equal(anchors.length, 0);
  });
});

test('export creates only a local Markdown blob via mocked download', async () => {
  await withPopup(async ({ elements, anchors, blobs }) => {
    elements.date.value = '2026-10-19';
    elements.download.handlers.click();
    assert.equal(anchors.length, 1);
    assert.equal(anchors[0].download, 'source-note-2026-10-19.md');
    assert.equal(anchors[0].clicked, true);
    assert.match(await blobs[0].text(), /采集草稿，未验证/);
  });
});
