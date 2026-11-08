export const categories = {
  datasets: '论文与数据集',
  'app-helpers': '软件辅助',
  'booking-helpers': '预约与提醒',
  everyday: '日常实用',
};

function plain(value) {
  return String(value ?? '').replace(/\s+/g, ' ').trim()
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/[\\`*_\[\]#|]/g, '\\$&');
}

export function sourceUrl(value, preserveParameters = false) {
  const url = new URL(String(value).trim());
  if (!['http:', 'https:'].includes(url.protocol) || !url.hostname || url.username || url.password) {
    throw new Error('仅支持不带用户名密码的 HTTP/HTTPS 来源');
  }
  if (!preserveParameters) {
    url.search = '';
    url.hash = '';
  }
  return url.href.replace(/</g, '%3C').replace(/>/g, '%3E');
}

export function buildNote(values) {
  const title = plain(values.title);
  if (!title) throw new Error('请填写标题');
  if (!Object.hasOwn(categories, values.category)) throw new Error('请选择有效分类');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(values.date) ||
      Number.isNaN(Date.parse(values.date + 'T00:00:00Z')) ||
      new Date(values.date + 'T00:00:00Z').toISOString().slice(0, 10) !== values.date) {
    throw new Error('日期格式应为有效的 YYYY-MM-DD');
  }
  const url = sourceUrl(values.url, values.preserveParameters);
  const notes = String(values.notes ?? '').replace(/\r\n?/g, '\n').trim();
  return {
    filename: `source-note-${values.date}.md`,
    content: [
      `# ${title}`, '',
      `- 场景：${categories[values.category]}`,
      `- 来源：<${url}>`,
      `- 记录日期：${values.date}`,
      `- 上游版本 / commit：${plain(values.version) || '未核实'}`,
      `- 许可证：${plain(values.license) || '未核实'}`,
      '- 状态：采集草稿，未验证', '',
      '## 用途与备注', '',
      notes || '待补充用途、访问条件、存放路径与验证方法。', '',
      '## 后续整理', '',
      '核对作者来源、许可证和版本，再按仓库分类整理。此草稿不代表已审核或测试通过。', '',
    ].join('\n'),
  };
}
