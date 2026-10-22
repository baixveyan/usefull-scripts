# CVPR 2026 接续记录

2026-10-23联合返工检查点：正文详细版7/106，配图详细版7/106，二者均通过自检7/106；余99篇继续返工，完成全部返工后再新增。下一篇：papers/CVPR2026/multimodal/clip-irm/README.md。旧reviewed计数106仅保留原文阅读历史，不代表本轮返工完成。


更新：2026-10-22晚间续做：BayesMM完成正文阅读、方法图与消融页核对、自检；累计106篇reviewed、3936篇queued，无reading/draft/blocked。31张原创SVG、43张署名原图。下一篇：Yuan_Adaptive_3D_Perception_for_Small_Aerial_Targets_Under_Sparse_Sampling_CVPR_2026_paper；建议缓存q107起。正文推导和点数口径差异已标注，未复现。

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
2. 固定today100.json与queue101-105.json均已完成。优先处理manifest中reading/draft，再从首个queued续做，每批最多5篇。配图按[图示规范](../../site/FIGURES.md)制作。
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

早期历史检查点为35篇reviewed、4,007篇queued；实时计数以manifest为准。参考站只借鉴章节结构。完整代码许可证、模型权重和运行条件还没有逐篇核验。官方目录在web工具返回403，当前权限允许的进程内HTTPS直连成功；未修改持久代理、证书或DNS，不应反复重试失败端点。

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

2026-10-20 第三批：新增RDD、DID、C-Flat Turbo、DeltaWorld、GAI-GS，累计50篇reviewed、3992篇queued，距100目标余50篇。16张原创SVG已逐张视觉检查；发现的公式、阈值和速度口径边界已在讲解中明确。本批关键页逐篇渲染核对，实验未复现。续做q51起，当前无reading/draft项。

2026-10-20 第四批：新增Omnivorous DINO、DiVT、A4VL、PCE-LiNGAM、ET3，累计55篇reviewed、3987篇queued，距100目标尚余45篇。21张原创SVG均已逐张检查，DID补齐双分支决策连线；q51–55关键页面已渲染核对。保留A4VL字幕口径冲突、PCE假设/算法待核验点与ET3有条件定理边界。下一批today100.json[20:25]即q56起；当前无reading/draft。

2026-10-20 第五批：新增DevDet、T2LDM、SeDiR、PL-Stitch、CoTyle，累计60篇reviewed、3982篇queued，距100仍余40篇。26张原创SVG均已视觉检查，增加点击打开高清图；q56–60关键页已渲染核对。各项公式及协议边界见正文。本批结束无reading/draft，续读today100.json[25:30]即q61起。


2026-10-20 第六批：新增cryoDeRec、TCCA、SVD风格个性化、BoT、成员推断对抗操纵，累计65篇reviewed、3977篇queued，距100目标尚余35篇。31张原创SVG均逐张视觉检查；另外加入2张带来源、PDF页码和权利说明的原文流程图局部截图（cryoDeRec Fig2 / SVD Fig4）。q61–65关键页已渲染核对，表注、投影及定理边界见各篇。未复现实验。下一批today100.json[30:35]即q66；当前无reading/draft项。5小时用量窗口80%已用，仍允许普通使用，并非每日固定token配额。


2026-10-20 第七批：新增A²GC、A³、SandboxVLM、ARCache、D²C，累计70篇reviewed、3972篇queued，距100仍余30篇。新增5张经过裁切和视觉核对的原文方法图，累计31张原创SVG及7张原图截图，均有来源与页码。已核对正文公式、主表及消融；OT边缘、得分符号、计时与指标口径差异已注明，未复现实验。下一批today100.json[35:40]即q71；本批结束无reading/draft。


2026-10-21 第一批：q71–75（Hybridiff、HetCache、STC、ACE-Merging、AceTone）完成正文独立精读、关键公式/算法/表格渲染与讲解自检。累计75篇reviewed、3967篇queued，100篇目标尚余25。新增5张原文图示，累计31张原创SVG、12张原图截图，保留来源、页码、PDF哈希与权利说明。HetCache伪代码不可达分支、STC比率/QKV符号、Hybridiff部分固定调度、ACE统计假设与AceTone编码成本均明确注明，未执行论文模型。下一批q76起；本批无reading/draft项。用量窗口最近14%/周18%已用，仍允许普通使用。


2026-10-21 第二批：q76–80（ACoT-VLA、ACPV-Net、HistoSelect、ACT2SEE、ActAvatar）完成正文精读、原图与关键页面视觉核对和逐篇自检。累计80篇reviewed、3962篇queued，距100余20；新增5张原图，累计31张原创SVG及17张署名截图。记录teacher forcing部署差异、拓扑与语义区别、相似度先验概率化待核、观测/合成证据区别与PACA软时间控制；未复现实验。下一批q81，无reading/draft。5小时/周窗口26%/20%已用，普通使用允许。


2026-10-21 第三批：q81–85（Action Motifs/A4Mer、GAP、Action-Sketcher、ActionMesh、TANL）完成正文精读、方法图与关键表格渲染核对、自检。累计85篇reviewed、3957篇queued，100目标余15；31张原创SVG及22张原图截图。分别记录识别表列冲突、几何消融/实机任务名单冲突、实机子任务完成率、固定拓扑边界与测试缓存依赖。全部未复现实验。下一批q86起，本批结束无reading/draft。


2026-10-22（10月21日23时任务跨午夜续做）：q86–90 UAAI、ORCA、DNRNet、ActiveAD、ActiveGrasp完成正文精读、公式和主表渲染、原图逐张核验与自检。累计90篇reviewed、3952篇queued，距100余10；31张原创SVG、27张原文图。保留EFE/UMIX不一致、TSR子目标口径、随机缺失与收敛边界、γ配额解释及抓取概率/梯度待核验点。原文下载日期21日、自检22日，未复现实验。下一批q91；当前无reading/draft。85篇已上传commit53525c2a51b43124696a3c62e8bccf6fdf20b21f，Pages action39628661029成功，公网4042记录/85已完成及高清图HTTP200已核验。

2026-10-22第二批：q91–95（ActivePolicy、ActiveVLA、ActivityForensics/TADiff、AcTTA、AD-GBC）原文、关键公式表格及5张局部图逐张核对，累计95篇reviewed、3947篇queued。保留不利结果与正文/表格差异，未复现。下一批固定today100.json[60:65]，q96–100。

2026-10-22第三批：q96–100（AdaBet、AdaCluster、AdaDexTrack、AdaIAT、AdapAction）完成正文精读、必要公式/关键表格渲染与5张局部图视觉核对，累计100篇reviewed、3942篇queued，无reading/draft/blocked。100篇阶段目标达成，全量4042篇目标未完成；47篇接收/公开差额仍待核。下一篇：Bhat_AdaPrior_Bayesian-Inspired_Adaptive_Prior_Correction_for_Long-Tailed_Continual_Learning_CVPR_2026_paper。下一批从manifest首个queued继续，最多5篇。未复现训练或攻击，未调用付费API。

2026-10-22第四批：q101–105（AdaPrior、Adapter Shield、HINGE、DAIG、SR视频计数）完成原文精读、自检与5张方法图视觉核查，累计105篇reviewed、3937篇queued，无reading/draft/blocked。保留EMA定理条件、加解密安全边界、患者/切片协议及印刷公式歧义。未复现、未调用付费API。下一篇：Zhu_Adapting_Point_Cloud_Analysis_via_Multimodal_Bayesian_Distribution_Learning_CVPR_2026_paper；下一批从manifest首个queued最多5篇，建议后续缓存q106起。固定queue101-105已全部完成。

2026-10-22晚间续做：BayesMM完成正文阅读、方法图与消融页核对、自检；累计106篇reviewed、3936篇queued，无reading/draft/blocked。31张原创SVG、43张署名原图。下一篇：Yuan_Adaptive_3D_Perception_for_Small_Aerial_Targets_Under_Sparse_Sampling_CVPR_2026_paper；建议缓存q107起。正文推导和点数口径差异已标注，未复现。
