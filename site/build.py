"""Build static reading pages from the reviewed paper manifest."""
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'maintenance/site-deps'))
import markdown
sys.path.insert(0, str(ROOT / 'maintenance'))
from build_paper_index import TOPICS, validate

OUT = ROOT / 'site/dist'
REPO = 'https://github.com/baixveyan/usefull-scripts'


def esc(value):
    return html.escape(str(value), quote=True)


def page(title, body, prefix=''):
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="从原文出发的中文论文解析：方法、公式、证据与复现边界。">
<title>{esc(title)} · 研读 / Paper Atlas</title>
<link rel="stylesheet" href="{prefix}assets/style.css"><link rel="icon" href="{prefix}assets/mark.svg">
<script defer src="{prefix}assets/app.js"></script></head><body>
<a class="skip" href="#main">跳到正文</a><div id="reading-progress"></div>
<header class="top"><a class="brand" href="{prefix}index.html"><img src="{prefix}assets/mark.svg" alt="" width="30" height="30"><span>研读<span class="brand-en">PAPER ATLAS</span></span></a>
<nav aria-label="主导航"><a href="{prefix}index.html">论文馆</a><a href="{REPO}" target="_blank" rel="noopener">GitHub ↗</a><button id="theme" aria-label="切换深浅主题">◐</button></nav></header>
{body}<footer class="footer">研读 / Paper Atlas <span>从原文出发，保留证据的边界。</span><a href="{REPO}">开放共建 ↗</a></footer></body></html>'''


def render_note(text):
    formulas = []
    def hold(match):
        formulas.append(match.group(0))
        return 'PAPERMATHPLACEHOLDER' + str(len(formulas)-1) + 'END'
    text = re.sub(r'\\\[.*?\\\]|\\\(.*?\\\)', hold, text, flags=re.S)
    md = markdown.Markdown(extensions=['fenced_code', 'tables', 'toc', 'sane_lists'])
    result = md.convert(text)
    for i, formula in enumerate(formulas):
        result = result.replace(f'PAPERMATHPLACEHOLDER{i}END', esc(formula))
    result = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>', r'<pre class="mermaid">\1</pre>', result, flags=re.S)
    return result, md.toc


def build():
    manifest = json.loads((ROOT / 'papers/CVPR2026/manifest.json').read_text(encoding='utf-8'))
    counts = validate(manifest)
    done = [r for r in manifest['papers'] if r['status'] == 'reviewed']
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'notes').mkdir(exist_ok=True)
    shutil.copytree(ROOT / 'site/assets', OUT / 'assets', dirs_exist_ok=True)
    if (ROOT / 'site/figures').exists():
        shutil.copytree(ROOT / 'site/figures', OUT / 'figures', dirs_exist_ok=True)
    records = []
    for r in manifest['papers']:
        reviewed = r['status'] == 'reviewed'
        display_checked = max(filter(None, (r.get('checked_on'), r.get('method_revision_on'), r.get('figure_revision_on'))), default='')
        summary = '官方论文元数据；尚未完成原文解析。'
        name = r['id'] + '.html'
        if reviewed:
            source = (ROOT / r['note_path']).read_text(encoding='utf-8')
            summary = re.search(r'## 一句话总结\s+(.*?)(?=\n## |\Z)', source, re.S).group(1).strip()
            j = done.index(r)
            neighbors = [(done[j-1] if j else None, '上一篇'), (done[j+1] if j+1 < len(done) else None, '下一篇')]
            body, toc = render_note(source)
            body = re.sub(r'src="(?:\.\./)+site/figures/', 'src="../figures/', body)
            body = re.sub(r'href="(?:\.\./)+[^"#]*?\.md"', 'href="../index.html"', body)
            body = re.sub(r'(<img\b[^>]*\bsrc="(\.\./figures/[^"]+)"[^>]*>)', r'<a class="figure-link" href="\2" target="_blank" rel="noopener" title="打开高清图">\1</a>', body)
            links = ''.join(f'<a href="{x["id"]}.html"><small>{label}</small>{esc(x["title"])}</a>' for x, label in neighbors if x)
            article = f'''<div class="article-shell"><aside class="article-nav"><a href="../index.html">← 返回论文馆</a><p class="eyebrow">CVPR 2026 / {esc(TOPICS[r['topic']])}</p><div class="toc">{toc}</div></aside>
<main id="main" class="prose"><div class="article-meta"><span class="pill">{esc("正文与配图详细版 · 已自检" if r.get("method_revision") == "completed" and r.get("figure_revision") == "completed" else "方法详细版 · 配图返工中" if r.get("method_revision") == "completed" else "正文与配图返工中" if r.get("method_revision") == "pending" else "原文精读 · 已自检")}</span><span>核对 {display_checked}</span><button id="font-size" aria-label="调整正文字号">Aa</button><button id="print">打印</button></div>
{body}<div class="article-end">读完并不等于复现。实验数字来自作者报告，复现边界见正文。</div><div class="prev-next">{links}</div></main></div><script type="module" src="../assets/reading.js"></script>'''
            (OUT / 'notes' / name).write_text(page(r['title'], article, '../'), encoding='utf-8')
        authors = r['authors']
        records.append(dict(title=r['title'], authors=', '.join(authors) if isinstance(authors, list) else authors,
                            topic=r['topic'], category=TOPICS[r['topic']], reviewed=reviewed,
                            summary=re.sub(r'[*`#]', '', summary), href='notes/'+name if reviewed else r['url'],
                            source=r['url'], checked=display_checked,
                            revised=r.get('method_revision') == 'completed' and r.get('figure_revision') == 'completed'))
    (OUT / 'assets/papers.js').write_text('window.PAPERS='+json.dumps(records, ensure_ascii=False).replace('<', '\\u003c')+';', encoding='utf-8')
    chips = ''.join(f'<button class="chip" data-topic="{key}">{label} <span>{sum(r["topic"] == key for r in done)}</span></button>' for key, label in TOPICS.items() if any(r['topic'] == key for r in done))
    body = f'''<main id="main"><section class="hero"><div><p class="eyebrow"><span class="dot"></span> OPEN RESEARCH LIBRARY / 2026</p>
<h1>读懂一篇，<br>连接<span class="accent">更多可能。</span></h1><p class="hero-copy">从问题出发，拆解方法、公式与实验。<br>把论文变成可以理解、比较和继续探索的知识。</p>
<a class="primary" href="#library">进入论文馆 <span>↗</span></a><p class="hero-note">中文独立解析 · 官方来源可追溯 · 持续更新</p></div>
<div class="hero-art" aria-hidden="true"><div class="orbit orbit-one"></div><div class="orbit orbit-two"></div><div class="sphere"></div><div class="art-label">SEE THE STRUCTURE<br>BEHIND THE PIXELS.</div><span class="coordinate">x · y · z · t</span><div class="art-tag">CVPR <b>2026</b></div></div></section>
<section class="stats" aria-label="真实收录进度"><div><strong>{counts['reviewed']:02d}</strong><span>原文阅读与解析</span></div><div><strong>{manifest['listed_count']:,}</strong><span>官方公开主会论文</span></div><div><strong>{sum(r['revised'] for r in records):02d} / {counts['reviewed']}</strong><span>正文与配图返工完成</span></div><div class="stats-note">逐篇重读，逐图核对。<small>已自检 ≠ 实验已复现</small></div></section>
<section class="library" id="library"><div class="section-top"><div><p class="eyebrow">THE READING ROOM</p><h2>发现值得深读的研究</h2></div><p>从兴趣进入，从证据读起。</p></div>
<div class="search-bar"><label class="search"><span>⌕</span><input id="search" type="search" placeholder="搜索论文、作者、方法或研究问题…" autocomplete="off" aria-label="搜索论文"><kbd>/</kbd></label><select id="scope" aria-label="阅读状态"><option value="reviewed">已有解析（含返工中）</option><option value="all">全部官方清单</option></select></div>
<div class="chips"><button class="chip active" data-topic="all">全部主题</button>{chips}</div><div class="results-meta"><span id="result-count" aria-live="polite"></span><span>CVPR 2026 主会 · 按题名排序</span></div><div id="paper-grid" class="paper-grid"></div><button id="more" class="more">继续浏览 ↓</button><div id="empty" class="empty" hidden>没有找到匹配论文。试试其他关键词，或切换到全部官方清单。</div>
<noscript>交互搜索需要 JavaScript；<a href="{REPO}/blob/main/papers/CVPR2026/index.md">打开完整 Markdown 目录</a>。</noscript></section>
<section class="principles"><div><p class="eyebrow">HOW WE READ</p><h2>不止是摘要。<br>把推导与边界一起读。</h2></div><div><h3>01 / 先问为什么</h3><p>还原研究动机，解释设计取舍与核心公式。</p><h3>02 / 再看证据</h3><p>保留具体设置、消融与不利结果，区分报告与复现。</p><h3>03 / 最后回到原文</h3><p>每篇附官方来源、页码与版本校验；清单不冒充解析。</p></div></section>
<p class="inventory-note">范围说明：公开主会清单 {manifest['listed_count']:,} 篇；官方接收数4,089与清单相差47篇，原因尚未核实。未计入Workshops与Findings。</p></main><script src="assets/papers.js"></script>'''
    (OUT / 'index.html').write_text(page('论文馆', body), encoding='utf-8')
    (OUT / '.nojekyll').write_text('')
    print(f'Built {len(done)} reading pages + {len(records)} inventory records -> {OUT}')


if __name__ == '__main__':
    build()
