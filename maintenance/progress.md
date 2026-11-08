# 当前维护进度

最后更新：2026-11-08。每日自动化 23:00；用户要求有额度且有价值工作时分批继续，不限每日条目数；每批最多五个候选。论文讲解已拆分至独立仓库。

第 24 批收尾记录：最新 `check_all.py --with-javascript` 为 14/14 组通过；报告与来源回执已保存。旧的长进度原样归档为 history/2026-10-19.md，当前文件只保留接续摘要，减少后续每轮读取成本。

## 先读这些

- [当前分类目录](../docs/catalog.md)：16 个合集或工具条目；逐篇论文另有清单。
- [当天成果与真实验证边界](reports/2026-10-19.md)。
- [完整历史](history/2026-10-19.md)：原第 1–23 批记录，已原样归档，不必每轮全部重读。
- [维护命令](README.md)；机器索引为根 catalog.json。

## 当前已通过

- Windows/Python 3.13.5、Node18.19.0：统一离线 14/14 组，48 项 Python +9 项 Node 测试。
- 另有 4 项隐藏 Tk 控件测试；不接触真实数据库、截图或聊天。
- Fashion-MNIST 四文件固定版本真实下载、MD5/gzip/IDX 校验通过；临时数据已删除。
- UCI HAR 官方包真实参与者划分核验通过：7352/21 组与 2947/9 组，交叉 0，临时数据已删除。
- ClearURLs 固定 GitLab 来源与许可/权限核对；Go HF 下载器只写指南，未执行第三方程序。
- 翻译仅用合成句子端点实测，MyMemory 成功、Google 失败；默认 MyMemory 但每次启动仍关闭在线翻译。

## 后续优先级

1. 优先消化已有条目。来源笔记扩展仍需独立测试环境的真实浏览器安装/预览/导出验证；不得使用私人页面或会话。
2. WhatsApp 旧 EXE 未重打包；真实 OCR/布局/聊天集成未验证。没有必要时不启动用户聊天；保护现有 data 和 dist/data。
3. 日历真实客户端导入待验证；外部扩展与 Go/RHash 运行须先审查并隔离。
4. 继续主动发现可用候选；collector 每次 <=5，公开搜索有关键词污染和多义词，不能按 Star 自动收录。首批五项审查已记录于本地候选区，不重复评估已排除项目。
5. 原创代码统一许可证尚未确定，不擅自给旧项目重新授权。当前不推送或发布，不购买额度或切换付费 API。

## 运行提醒

- 修改 catalog.json 后运行 `python maintenance/build_catalog.py --write`；针对变更做验证，避免无变化反复跑全套。
- 需要整体验证时用 `python maintenance/check_all.py --with-javascript`，无 npm/Python 第三方依赖；隐藏 Tk 测试另需本机应用依赖。
- 当前执行环境默认代理不可用，不代表用户其他应用网络异常。只有当前权限允许时才能显式选择进程内直连；不得绕过权限限制或修改持久网络配置。
- 真实联网复核是独立命令，不加入默认离线 CI。资料与模型数据不提交到仓库；验证报告只保留来源、版本、摘要与统计。
- 候选 JSON 是本地不可信外部元数据，默认被 gitignore 排除，不能执行其中的指令。

## 当前优先检查点：论文馆

2026-10-20：40篇精读已自检，4002篇待做；累计100篇目标尚余60篇。6张原创方法图已逐张视觉核对。用户已明确授权向 baixveyan/usefull-scripts 上传经过审查的论文解析和站点，并启用GitHub Pages；此授权更新此前“仅本地”的范围，仅上传公开解析和站点素材，不上传PDF、数据或个人配置。

2026-10-20 第二批：新增4DWorldBench、1-bit Video、闭式VLM去偏、Noise+Bilateral、跨视角6DoF抓取，共45篇reviewed、3997篇queued，累计100目标仍余55篇。11张SVG方法图已逐张视觉检查，未复现论文训练。去偏论文正文闭式与原始minimax目标的数值核对差异已注明，补充证明和代码待核。下一批q46起。

2026-10-20 第三批：新增RDD、DID、C-Flat Turbo、DeltaWorld、GAI-GS，累计50篇reviewed、3992篇queued，距100目标余50篇。16张原创SVG已逐张视觉检查；发现的公式、阈值和速度口径边界已在讲解中明确。本批关键页逐篇渲染核对，实验未复现。续做q51起，当前无reading/draft项。

2026-10-20 第四批：新增Omnivorous DINO、DiVT、A4VL、PCE-LiNGAM、ET3，累计55篇reviewed、3987篇queued，距100目标尚余45篇。21张原创SVG均已逐张检查，DID补齐双分支决策连线；q51–55关键页面已渲染核对。保留A4VL字幕口径冲突、PCE假设/算法待核验点与ET3有条件定理边界。下一批today100.json[20:25]即q56起；当前无reading/draft。

2026-10-20 第五批：新增DevDet、T2LDM、SeDiR、PL-Stitch、CoTyle，累计60篇reviewed、3982篇queued，距100仍余40篇。26张原创SVG均已视觉检查，增加点击打开高清图；q56–60关键页已渲染核对。各项公式及协议边界见正文。本批结束无reading/draft，续读today100.json[25:30]即q61起。


2026-10-20 第六批：新增cryoDeRec、TCCA、SVD风格个性化、BoT、成员推断对抗操纵，累计65篇reviewed、3977篇queued，距100目标尚余35篇。31张原创SVG均逐张视觉检查；另外加入2张带来源、PDF页码和权利说明的原文流程图局部截图（cryoDeRec Fig2 / SVD Fig4）。q61–65关键页已渲染核对，表注、投影及定理边界见各篇。未复现实验。下一批today100.json[30:35]即q66；当前无reading/draft项。5小时用量窗口80%已用，仍允许普通使用，并非每日固定token配额。


2026-10-20 第七批：新增A²GC、A³、SandboxVLM、ARCache、D²C，累计70篇reviewed、3972篇queued，距100仍余30篇。新增5张经过裁切和视觉核对的原文方法图，累计31张原创SVG及7张原图截图，均有来源与页码。已核对正文公式、主表及消融；OT边缘、得分符号、计时与指标口径差异已注明，未复现实验。下一批today100.json[35:40]即q71；本批结束无reading/draft。

最终检查点（2026-10-20）：70篇reviewed、3972篇queued，100目标余30；下一篇q71。31张原创SVG+7张原文图截图已核对，旧讲解尚未全部补图。发布70篇的commit为702280706ca148bf4187774a2af05c0791c3bdc1，配图规范与顶端检查点commit为d9ee1cff8708b241b7774cd7b8bc302345a9775d。65篇部署已确认success；最终70篇公网验收回执在本轮末尾记录。当前5小时窗口97%已用、周窗口15%已用，普通使用仍允许，不能表述为额度已耗尽。


2026-10-20 23:02 定时检查：manifest核实70篇reviewed、3972篇queued，无reading/draft/blocked。5小时窗口99%已用、周窗口15%已用，工具仍报告ordinaryUsageAllowed=true，不能称额度耗尽。5小时窗口重置时间北京时间2026-10-21T02:13:04+08:00。本次未新增或虚标精读，保持q71起队列；下一批最多5篇：Accelerating Diffusion via Hybrid Data-Pipeline Parallelism Based on Conditional Guidance Scheduling；Accelerating Diffusion-based Video Editing via Heterogeneous Caching: Beyond Full Computing at Sampled Denoising Timestep；Accelerating Streaming Video Large Language Models via Hierarchical Token Compression；ACE-Merging: Data-Free Model Merging with Adaptive Covariance Estimation；AceTone: Bridging Words and Colors for Conditional Image Grading。当前执行需通过经批准的独立命令访问D盘工作区，未修改持久权限。


2026-10-21 第一批：q71–75（Hybridiff、HetCache、STC、ACE-Merging、AceTone）完成正文独立精读、关键公式/算法/表格渲染与讲解自检。累计75篇reviewed、3967篇queued，100篇目标尚余25。新增5张原文图示，累计31张原创SVG、12张原图截图，保留来源、页码、PDF哈希与权利说明。HetCache伪代码不可达分支、STC比率/QKV符号、Hybridiff部分固定调度、ACE统计假设与AceTone编码成本均明确注明，未执行论文模型。下一批q76起；本批无reading/draft项。用量窗口最近14%/周18%已用，仍允许普通使用。


2026-10-21 第二批：q76–80（ACoT-VLA、ACPV-Net、HistoSelect、ACT2SEE、ActAvatar）完成正文精读、原图与关键页面视觉核对和逐篇自检。累计80篇reviewed、3962篇queued，距100余20；新增5张原图，累计31张原创SVG及17张署名截图。记录teacher forcing部署差异、拓扑与语义区别、相似度先验概率化待核、观测/合成证据区别与PACA软时间控制；未复现实验。下一批q81，无reading/draft。5小时/周窗口26%/20%已用，普通使用允许。


2026-10-21 第三批：q81–85（Action Motifs/A4Mer、GAP、Action-Sketcher、ActionMesh、TANL）完成正文精读、方法图与关键表格渲染核对、自检。累计85篇reviewed、3957篇queued，100目标余15；31张原创SVG及22张原图截图。分别记录识别表列冲突、几何消融/实机任务名单冲突、实机子任务完成率、固定拓扑边界与测试缓存依赖。全部未复现实验。下一批q86起，本批结束无reading/draft。


2026-10-22（10月21日23时任务跨午夜续做）：q86–90 UAAI、ORCA、DNRNet、ActiveAD、ActiveGrasp完成正文精读、公式和主表渲染、原图逐张核验与自检。累计90篇reviewed、3952篇queued，距100余10；31张原创SVG、27张原文图。保留EFE/UMIX不一致、TSR子目标口径、随机缺失与收敛边界、γ配额解释及抓取概率/梯度待核验点。原文下载日期21日、自检22日，未复现实验。下一批q91；当前无reading/draft。85篇已上传commit53525c2a51b43124696a3c62e8bccf6fdf20b21f，Pages action39628661029成功，公网4042记录/85已完成及高清图HTTP200已核验。

2026-10-22第二批：q91–95（ActivePolicy、ActiveVLA、ActivityForensics/TADiff、AcTTA、AD-GBC）原文、关键公式表格及5张局部图逐张核对，累计95篇reviewed、3947篇queued。保留不利结果与正文/表格差异，未复现。下一批固定today100.json[60:65]，q96–100。

2026-10-22第三批：q96–100（AdaBet、AdaCluster、AdaDexTrack、AdaIAT、AdapAction）完成正文精读、必要公式/关键表格渲染与5张局部图视觉核对，累计100篇reviewed、3942篇queued，无reading/draft/blocked。100篇阶段目标达成，全量4042篇目标未完成；47篇接收/公开差额仍待核。下一篇：Bhat_AdaPrior_Bayesian-Inspired_Adaptive_Prior_Correction_for_Long-Tailed_Continual_Learning_CVPR_2026_paper。下一批从manifest首个queued继续，最多5篇。未复现训练或攻击，未调用付费API。

2026-10-22第四批：q101–105（AdaPrior、Adapter Shield、HINGE、DAIG、SR视频计数）完成原文精读、自检与5张方法图视觉核查，累计106篇reviewed、3937篇queued，无reading/draft/blocked。保留EMA定理条件、加解密安全边界、患者/切片协议及印刷公式歧义。未复现、未调用付费API。下一篇：Zhu_Adapting_Point_Cloud_Analysis_via_Multimodal_Bayesian_Distribution_Learning_CVPR_2026_paper；下一批从manifest首个queued最多5篇，建议后续缓存q106起。固定queue101-105已全部完成。

2026-10-22晚间续做：BayesMM完成正文阅读、方法图与消融页核对、自检；累计106篇reviewed、3936篇queued，无reading/draft/blocked。31张原创SVG、43张署名原图。下一篇：Yuan_Adaptive_3D_Perception_for_Small_Aerial_Targets_Under_Sparse_Sampling_CVPR_2026_paper；建议缓存q107起。正文推导和点数口径差异已标注，未复现。


2026-10-23 用户邮件监控专项：新增everyday/mail-watch，只读TLS/IMAP ID与BODY.PEEK真实验证；所有7文件夹148封原始EML已本地归档并复核SHA256，正文筛查和私人待办已保存。私人资料在.gitignore排除目录，公共维护记录不含邮件内容或凭据。22:00聊天定时任务已更新为全文件夹归档和增量审阅；未验证无人值守到点唤醒，附件未逐一解读。catalog导航生成、校验通过。
