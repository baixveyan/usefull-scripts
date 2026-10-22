# CVPR 2026 中文论文讲解

2026-10-23联合返工检查点：正文详细版14/106，配图详细版14/106，二者均通过自检14/106；余92篇继续返工，完成全部返工后再新增。下一篇：papers/CVPR2026/3d-vision/2d-lfm/README.md。旧reviewed计数106仅保留原文阅读历史，不代表本轮返工完成。


目标是覆盖 CVPR 2026 主会全部可核实论文。当前以 [CVF 官方 day=all 目录](https://openaccess.thecvf.com/CVPR2026?day=all) 为清单来源，抓取日期为 2026-10-19，共 **4,042 篇**。目前106篇讲解自检完成、3,936篇待读。完整状态和已完成讲解见[全量目录](index.md)，接续位置见[进度](progress.md)。

大会[官方闭幕新闻](https://cvpr.thecvf.com/Conferences/2026/News/Closing)报告接收 4,089 篇，与公开目录相差 47 篇。原因尚未核实，不推测为撤稿、不用第三方列表填充后冒充官方全量。当前范围排除 CVPR Workshops 和 CVPR Findings；若以后扩展，单独建清单。其他年份及会议尚未启动。

## 讲解标准

结构参考用户指定的 [TokenGS Paper Notes](https://m0rtzz.github.io/paper-notes/CVPR2026/3d_vision/tokengs_decoupling_3d_gaussian_prediction_from_pixels_with_learnable_tokens/)，内容从原论文独立撰写。每篇包括：一句话总结、背景与动机、方法总览、核心设计与必要公式、实验与关键结果、消融证据、局限、复现提示、相关工作和来源校验。图示优先重绘，不搬运作者或参考站全文。

用中文解释“为什么这样设计、结果支持什么、不能支持什么”。表格记录数据集、设置、指标方向和原文位置。保留不利结果与公平比较条件，区别作者结论、笔记推断和实际复现。未阅读补充材料、未检查代码或未复现的部分明确注明。

## 分类与状态

目录按 `3d-vision`、`generation`、`multimodal`、`recognition`、`segmentation`、`video`、`medical`、`robotics`、`theory`、`imaging`、`other` 分类。精读后确定主分类，跨领域用笔记标签补充。元数据阶段保留 `unclassified`，不根据标题猜测成确定分类。

- `queued`：仅取得官方元数据，尚无讲解。
- `reading`：已开始核对原文。
- `draft`：讲解待自检。
- `reviewed`：原文阅读与讲解自检完成；**不代表独立同行审稿或实验复现**。
- `blocked`：来源暂不可得或有待解决问题，记录原因后继续其他论文。

`manifest.json` 是完整机器清单；通用 `catalog.json` 只登记本合集，避免把四千条论文与实用工具混在一起。笔记路径为 `<主题>/<短标识>/README.md`。元数据不等于完成讲解，不批量建立伪完成空壳。

## 本地维护与验证

在仓库根目录执行：

```powershell
python maintenance/build_paper_index.py --write
python maintenance/build_paper_index.py --check
```

第一条生成导航，第二条检查状态、来源、文件路径、完成笔记章节和导航同步。检查通过仅证明结构一致，不证明科学内容正确；数值和结论仍需逐篇人工式阅读核对。

如需重建清单，先保存官方 HTML，再运行 `python maintenance/cvpr_inventory.py <本地HTML路径> --checked-on 2026-10-19` 预览，日期须改为实际抓取日，确认后加 `--write`。脚本不联网、不执行外部代码；重建保留已有状态，发现清单丢失原条目时拒绝覆盖。

原文、提取文本与页面图只放被忽略的 `maintenance/paper-sources/` 本地阅读缓存，清单保存来源 URL、PDF SHA-256 和日期。论文与代码权利分别归作者和上游；本仓库不将论文公开访问误认为可任意再发布授权。最后检查：2026-10-22。

## 插图标准

优先依据原文重绘可缩放SVG方法图，清楚区分输入、模块、训练损失和推理路径；标明原文图号、章节及简化边界。只有在原图细节对理解不可替代且使用条件允许时，才引用必要局部截图并注明来源、图号和PDF页码。概念重绘不声称与原文实现逐算子等价。

## 配图质量

优先保留能够解释方法的原文流程图局部截图，并根据需要配中文概念重绘。保留张量、空间关系和训练/推理差异，避免仅把摘要放进方框。截图记录作者来源、原图编号、PDF页码与版本哈希；原创图写明简化范围。每张需视觉检查，可点击打开高清图。具体见[图示规范](../../site/FIGURES.md)。
