# 研读 / Paper Atlas

从本仓库 `papers/CVPR2026/manifest.json` 与已完成 Markdown 讲解构建静态论文馆，适合 GitHub Pages。首页计数来自清单；`queued` 只展示官方原文链接，不生成空文章。

```powershell
python -m pip install -r site/requirements.txt
python site/build.py
python -m http.server 8765 --directory site/dist
```

打开 http://localhost:8765 。输出在 `site/dist/`，不修改笔记。搜索覆盖标题、作者、主题和一句话总结，支持分类、状态切换；文章支持固定目录、阅读进度、字号、打印、公式和流程图。小屏隐藏长目录，表格及公式横向滚动。

KaTeX 0.16.22、Mermaid 10.9.3 固定资源随站点提供，不依赖 CDN；授权文件位于对应 vendor 目录。Python-Markdown 3.7 用于构建，不把论文公开访问当成全文再分发授权。构建器只处理本地自有笔记，不应输入不可信 HTML。

未运行论文实验。深浅主题与字号属于阅读辅助，不改变论文本身。PDF、提取文本、私有配置、模型权重及研究数据不发布。

最后检查：2026-10-20。已验证首页搜索与文章目录；TokenGS 公式和重绘流程图在浏览器中成功渲染。上线状态以 GitHub Pages 回执为准。

配图分为原创中文SVG重绘与有限的原文图示截图。截图在文章旁注明作者来源、Fig.编号、PDF页码和裁切范围，追溯记录见 `figures/sources.json`；原图权利仍属原作者，不随本站原创图重新授权。所有文章配图可点击打开高清图。
