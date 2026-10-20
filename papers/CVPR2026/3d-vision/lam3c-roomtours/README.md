# 3D sans 3D Scans: Scalable Pre-training from Video-Generated Point Clouds

作者：Ryousuke Yamada, Kohsuke Ide, Yoshihiro Fukuhara, Hirokatsu Kataoka, Gilles Puy, Andrei Bursuc, Yuki M. Asano。

分类：3d-vision；交付形式：Markdown 中文论文讲解。

核对日期：2026-10-20。以下实验均为作者报告；本地完成原文阅读与讲解自检，未复现实验。

## 一句话总结

LAM3C用网页房屋视频重建的有噪点云进行自监督预训练，以局部平滑和噪声一致性弥补真实三维扫描稀缺。

## 研究背景与动机

室内扫描采集昂贵，而看房视频丰富。核心问题不是视频能否重建，而是有缺洞、重影和尺度不一致的伪点云能否学出可迁移三维特征。无需扫描指预训练点云来源，不代表下游微调或评估不使用真实扫描和标签（第1–2页）。

## 方法总览

收集3462条自选视频并加入已有视频数据；CLIP切分室内片段，ω3前馈重建，过滤离群点、对齐Z轴与尺度并估计法向。RoomTours-16k为自采视频15921场景，全49k为49219场景。PTv3教师学生用EMA和Sinkhorn原型聚类学习（第3–5页）。

## 核心创新与关键设计

总目标L=L_clustering+λR_Lap+μR_cons。R_Lap以kNN边权exp(−‖p_i−p_j‖²/σ²)约束近邻特征，实际采用度归一化与Huber惩罚；R_cons对齐噪声增强与遮蔽视图对应点特征。λ由2×10⁻⁴升至3×10⁻³，μ=0.05。平滑项单独不能数学保证不坍塌，需要聚类及跨视图目标共同理解（第3–4页）。

## 实验与关键结果

第6页：Base/49k的ScanNet语义Full-FT mIoU77.7，随机初始化74.7，Sonata全真实78.5；Large/49k为79.5，但模型及步数均更大。S3DIS实例Full-FT mAP45.7，Large47.2，Sonata真实+合成45.5。不能把Large优势全归于新损失。预训练8张H200、batch16，默认145600步，大模型437k步（第5–6页）。

## 消融实验与证据强度

第7页1k设置中去正则LP51.1→加入57.1；去平滑55.0、去一致性55.3。Z轴对齐LP51.8→57.1，但Full-FT76.1→75.1反而下降；尺度对齐也主要惠及LP。第8页干净ScanNet上Sonata67.1、LAM3C66.8，无通用胜出；噪声RoomTours上51.1→57.1，支持针对噪声的设计。

## 局限与讨论

点云尺度通过ScanNet统计分布对齐，因此“无真实扫描预训练样本”不等于完全没有真实数据统计先验。网页视频权利、重建模型权重来源和室内域偏置仍需核查。PCA彩色可视化不是带语义标签的零样本分类精度；数据生成每场约5分钟也有总计算成本。

## 复现提示

记录视频可用性和授权、ω3版本、对齐失败处理及数据划分。作者为公平比较移除Sonata预训练中的验证/测试输入，虽原方法没用其标签，也会影响比较。论文给出lam3c仓库入口，此次未运行下载或预训练，未确认数据总体积及发行许可。

## 相关工作与阅读顺序

先读DINO教师学生聚类、Sonata与PTv3，再读VGGT/ω3的前馈重建。本文贡献需要同时看数据源扩展与抗噪目标，不能只把它概括成“视频转点云”。

## 来源与校验

- 已渲染并目视核对 PDF 第6页关键表格/图；其余正文与公式通过原文文本核对。
- [CVF 官方论文页](https://openaccess.thecvf.com/content/CVPR2026/html/Yamada_3D_sans_3D_Scans_Scalable_Pre-training_from_Video-Generated_Point_Clouds_CVPR_2026_paper.html) · [所读 PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Yamada_3D_sans_3D_Scans_Scalable_Pre-training_from_Video-Generated_Point_Clouds_CVPR_2026_paper.pdf)。页码均为该 PDF 的页序。
- 阅读范围：正文、公式与实验表；补充材料、上游代码与权重未逐项核验。许可证和固定代码 commit 尚未确认，不复制原文全文或数据。
- PDF SHA-256：`1cb78bbf3478b3620347884762f7f95862aa73cb69a5bcd31f232765bfe5c70e`；版本为本次下载的 CVF 接收稿，核对日期 2026-10-20。
