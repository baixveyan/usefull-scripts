# CVPR 2026 接续记录

更新：2026-10-20。本次“继续20篇”已完成，累计35篇reviewed、4,007篇queued，无reading/draft/blocked。当前最高优先级为完成主会论文讲解；每日北京时间23:00的现有自动化已更新为优先续做本合集。仍按可用运行资源推进，不承诺一天完成数千篇。

## 清单与已完成

- 官方 `day=all` 快照：4,042 个唯一论文页，均附 PDF 链接与作者；独立清单 `manifest.json`。
- 官方新闻接收数4,089，差额47未解释，未伪造条目；Workshops、Findings未计入。
- 首批完成5篇：TokenGS、D4RT、Native and Compact Structured Latents、NitroGen、SAM 3D。均阅读正文，核对关键表格或结果图页面，独立撰写、自检；没有实验复现或独立专家审稿。
- 第二批完成5篇：BackSplit、AdaSpark、跨域少样本检测与并行解码器、CLIP-IRM、CostSet。当前总计10篇reviewed、4,032篇queued，涵盖3D、生成、智能体、医学、视频、多模态与分割检测。
- 第三批完成5篇：αMatte4K与μMatting、SCADA-UL、φ-DPO、L²DGS、2-Shots in the Dark。正文精读、关键页面渲染核对及讲解自检完成，累计15篇reviewed、4,027篇queued，无reading/draft/blocked项。新增计算成像和学习方法分类；所有实验仍为作者报告，未本地复现。
- 统一离线检查16/16组通过（原工具回归及新增论文清单5项测试），共53项Python、9项Node测试；另外包含目录一致性和模拟构建检查。只证明结构与本地工具回归，不证明论文科学结论正确或实验复现成功。
- 快照 SHA-256 在 manifest；各篇 PDF SHA-256、阅读边界在笔记和 manifest。原始资料仅存被忽略的本地阅读缓存。

## 恢复顺序

1. 以 manifest 的状态为准，不凭本页计数覆盖清单。先完成 `reading` / `draft` 项；再开始最多5篇的下一批。
2. 七批35篇已完成，目前无reading/draft项。下一批最多5篇：4D Primitive-Mache: Glueing Primitives for Persistent 4D Scene Reconstruction；4D-RGPT: Toward Region-level 4D Understanding via Perceptual Distillation；4DEquine: Disentangling Motion and Appearance for 4D Equine Reconstruction from Monocular Video；4DP-QA: Scalable QA for 4D Perception in Vision Language Models；4DSurf: High-Fidelity Dynamic Scene Surface Reconstruction。以上仅是待办元数据，未阅读，不计完成。
3. 从官方论文页读取原文；必要时渲染公式和实验表，记录适用设置、指标方向和失败项。补充材料未读则明确写出。
4. 写完并自检后才设 reviewed，补充 topic、note_path、checked_on、pdf_sha256、validation；生成 index.md，并同步通用目录的验证说明。
5. 每批结束检查额度，保存当前论文和下一步；发生运行/用量限制时停止，后续自动化续做。额度不可读取时不虚构 token 余额。

## 维护命令

```powershell
python maintenance/build_paper_index.py --write
python maintenance/build_paper_index.py --check
python maintenance/build_catalog.py --write
python maintenance/validate_catalog.py
```

## 已知边界

当前为35篇reviewed、4,007篇queued；实时计数以manifest为准。参考站只借鉴章节结构。完整代码许可证、模型权重和运行条件还没有逐篇核验。官方目录在web工具返回403，当前权限允许的进程内HTTPS直连成功；未修改持久代理、证书或DNS，不应反复重试失败端点。

本次heartbeat开始时5小时窗口已用3%、周窗口14%，第三批结束时分别12%和16%；这不是固定每日token额度，也没有使用赠送重置或购买额度。本次检查点不是因额度耗尽；全量阅读受单轮执行与上下文容量约束，不能靠清单批量生成冒充已完成。后续运行持续按未完成队列推进。

## 本次新增20篇（第4–7批）

- 第4批：240FPS Stereo Vision from Monocular Mixed Spikes；2D-LFM: Lifting Foundation Model without 3D Supervision；2ndMatch: Finetuning Pruned Diffusion Models via Second-Order Jacobian Matching；3D Gaussian Splatting at Arbitrary Resolutions with Compact Proxy Anchors；3D Gaussian Splatting from Unposed Spike Stream。
- 第5批：3D Gaussian Splatting with Self-Constrained Priors for High Fidelity Surface Reconstruction；3D sans 3D Scans: Scalable Pre-training from Video-Generated Point Clouds；3D Space as a Scratchpad for Editable Text-to-Image Generation；3D-Aware Implicit Motion Control for View-Adaptive Human Video Generation；3D-Aware Multi-Task Learning with Cross-View Correlations for Dense Scene Understanding。
- 第6批：3D-Fixer: Coarse-to-Fine In-place Completion for 3D Scenes from a Single Image；3D-IDE: 3D Implicit Depth Emergent；3D-LATTE: Latent Space 3D Editing from Textual Instructions；3D-Object Perception Transformer (3PT)；3D-VCD: Hallucination Mitigation in 3D-LLM Embodied Agents through Visual Contrastive Decoding。
- 第7批：3DrawAgent: Teaching LLM to Draw in 3D with Early Contrastive Experience；3DReflecNet: A Large-Scale Dataset for 3D Reconstruction of Reflective, Transparent, and Low-Texture Objects；3M-TI: High-Quality Mobile Thermal Imaging via Calibration-free Multi-Camera Cross-Modal Diffusion；4C4D: 4 Camera 4D Gaussian Splatting；4D Local Modeling Toward Dynamic Global Perception for Ambiguity-free Rotation-Invariant Point Cloud Analysis。

每篇均核对正文、方法公式及结果，并渲染查看至少一个关键页面；记录PDF SHA-256、核对日期与未读补充材料边界。实验均为作者报告，未运行上游代码或权重。分类索引与通用catalog已同步。

本次额度开始5小时窗口14%／周16%已用；四批结束分别23%／17%、26%／18%、30%／19%、34%／19%。结束原因是用户指定的新增20篇任务完成，并非额度耗尽；未购买或使用额度重置。此前段落中的额度、15篇及10篇计数保留为历史记录。

本次最终结构验证：论文索引检查、catalog校验/生成一致性及5项论文维护测试通过；新增20篇PDF摘要逐一匹配本地所读文件。

## 网站与插图升级检查点（2026-10-20）

累计40篇 reviewed、4002篇 queued；新增4DPM、4D-RGPT、4DEquine、4DP-QA、4DSurf。6张原创SVG方法图已逐张浏览器检查，包含TokenGS升级。图内标注依据与省略边界，不作为原文图。当前目标累计100篇，尚余60篇，续读本地 today100.json 的 q41 起；不得把待办计为完成。GitHub Pages已获用户授权并首次部署成功。

2026-10-20 第二批：新增4DWorldBench、1-bit Video、闭式VLM去偏、Noise+Bilateral、跨视角6DoF抓取，共45篇reviewed、3997篇queued，累计100目标仍余55篇。11张SVG方法图已逐张视觉检查，未复现论文训练。去偏论文正文闭式与原始minimax目标的数值核对差异已注明，补充证明和代码待核。下一批q46起。
