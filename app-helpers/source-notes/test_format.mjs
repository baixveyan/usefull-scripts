import assert from 'node:assert/strict';
import test from 'node:test';
import { buildNote, sourceUrl } from './format.mjs';

const values = () => ({ title: '数据集来源', url: 'https://example.com/data?version=1&token=secret#part', category: 'datasets', date: '2026-10-19' });

test('parameters and fragments removed by default', () => {
  const note = buildNote(values());
  assert.match(note.content, /<https:\/\/example.com\/data>/);
  assert.ok(!note.content.includes('token=secret'));
  assert.match(note.content, /状态：采集草稿，未验证/);
});

test('explicit parameter preservation', () => {
  assert.equal(sourceUrl(values().url, true), values().url);
});

test('credentials and non-web protocols rejected', () => {
  for (const url of ['javascript:alert(1)', 'file:///private/file', 'https://user:pass@example.com/', 'bad-url']) {
    assert.throws(() => buildNote({ ...values(), url }));
  }
});

test('plain fields cannot insert headings or HTML', () => {
  const note = buildNote({ ...values(), title: '<script>\n# title [x]', license: 'A|B' });
  assert.ok(!note.content.includes('<script>'));
  assert.ok(note.content.includes('\\# title \\[x\\]'));
  assert.ok(note.content.includes('A\\|B'));
});

test('date category and empty title validated', () => {
  for (const update of [{ date: '2026-02-30' }, { date: '2026-1-1' }, { category: 'unknown' }, { title: ' ' }]) {
    assert.throws(() => buildNote({ ...values(), ...update }));
  }
});

test('notes normalized, no fabricated license or version', () => {
  const note = buildNote({ ...values(), notes: 'line1\r\nline2' });
  assert.match(note.content, /line1\nline2/);
  assert.match(note.content, /许可证：未核实/);
  assert.equal(note.filename, 'source-note-2026-10-19.md');
});
