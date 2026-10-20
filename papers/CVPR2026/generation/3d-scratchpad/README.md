# 3D Space as a Scratchpad for Editable Text-to-Image Generation

作者：Oindrila Saha, Vojtech Krs, Radomir Mech, Subhransu Maji, Matheus Gadelha, Kevin Blackburn-Matzen。

分类：generation；交付形式：Markdown 中文论文讲解。

核对日期：2026-10-20。以下实验均为作者报告；本地完成原文阅读与讲解自检，未复现实验。

## 一句话总结

先把提示词变成可编辑三维物体布局，再用深度和身份图条件生成二维图像，让空间规划与图像编辑有明确的中间表示。

## 研究背景与动机

纯文本或二维框难以稳定表达前后遮挡、朝向和缩放；生成器容易混淆身份或数量。作者把3D当推理工作区，最终输出仍是二维图像，并不以物理真实三维场景为唯一目标（第1–3页）。

## 方法总览

主体拆解并生成身份图→图生3D网格→布局规划→从主体裁剪图估朝向并调整变换→在5个候选机位中选视角→以深度、身份图和增强提示词生成图像。编辑时先擦除旧主体，再在更新3D位置插入，配潜空间融合保持背景（第4–5页）。

## 核心创新与关键设计

布局写为B=BboxPlanner(P′,主体描述,身份图,长宽比,D)，D明确坐标轴与边界；变换规划结合当前多视图渲染、估计朝向和目标朝向。无纹理网格难判断面朝方向，因此用身份条件生成图的主体裁剪估朝向。公式是流程接口，本文没有新训练损失；“training-free”指复用现有模型而非无需模型计算。

## 实验与关键结果

第5–6页：GenAI-Bench先进子集870提示，CompoundPrompts540提示；用VQAScore评估文本对齐、Q-Align评图质。GenAI对齐Flux0.63、Idea2Img0.80、RPG-Flux0.71、本文0.83，约32%提升是相对0.63的比例而非32个百分点。Compound为0.91对Flux0.85，图质4.84持平。

## 消融实验与证据强度

第6页：仅前两规划步骤0.821，加朝向0.824，再加机位0.830，增益有限且基准中相关提示较少。加入标尺0.830对无标尺0.821；用逐主体InsertAnything对齐0.81、图质4.60，SIGMA-Gen0.83/4.81。与Idea2Img完整提示增强组合为0.85，说明方法互补。

## 局限与讨论

指标来自模型评估，不是人类或物理几何真值。多组件可能累计失败，主体网格与身份图质量限制结果；编辑能力主要定性展示。GPT-5规划、GPT-4o格式提取、FLUX.1-dev、Hunyuan3D2.5和SIGMA-Gen均有依赖、许可和成本边界，不能据论文断言本地Plus可免费复现。

## 复现提示

应保存结构化场景、随机种子、规划提示、模型版本和全部调用次数，再分别测生成、网格、规划耗时。此次未调用任何付费API，未生成样本；仅核对方法和结果。项目入口为论文3DScratchpad页，代码固定版本与各权重许可证未核验。

## 相关工作与阅读顺序

按LayoutGPT/RPG→身份保持条件生成→3D布局与图像编辑阅读。对工具库的启发是保存可编辑中间场景，而非只保存最终图片或提示词。

## 来源与校验

- 已渲染并目视核对 PDF 第6页关键表格/图；其余正文与公式通过原文文本核对。
- [CVF 官方论文页](https://openaccess.thecvf.com/content/CVPR2026/html/Saha_3D_Space_as_a_Scratchpad_for_Editable_Text-to-Image_Generation_CVPR_2026_paper.html) · [所读 PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Saha_3D_Space_as_a_Scratchpad_for_Editable_Text-to-Image_Generation_CVPR_2026_paper.pdf)。页码均为该 PDF 的页序。
- 阅读范围：正文、公式与实验表；补充材料、上游代码与权重未逐项核验。许可证和固定代码 commit 尚未确认，不复制原文全文或数据。
- PDF SHA-256：`40e60f5a8dd5eac4a462bebbf767b87b07e06ce945985af0fa4c07fa1e2112d4`；版本为本次下载的 CVF 接收稿，核对日期 2026-10-20。
