# 3D-Aware Implicit Motion Control for View-Adaptive Human Video Generation

作者：Zhixue Fang, Xu He, Songlin Tang, Haoxian Zhang, Qingfeng Li, Xiaoqiang Liu, Pengfei Wan, Kun Gai。

分类：video；交付形式：Markdown 中文论文讲解。

核对日期：2026-10-20。以下实验均为作者报告；本地完成原文阅读与讲解自检，未复现实验。

## 一句话总结

3DiMo把驱动视频压缩为隐式动作token，通过丰富视角训练和逐渐撤去的几何辅助监督，实现动作迁移与文字运镜的共存。

## 研究背景与动机

二维姿态控制会绑定驱动视角；SMPL重建又可能错误估计前后关系和接触。本文希望生成器自身三维先验参与动作解释，而非强行投影外部骨架，但也不宣称完全没有使用参数化人体监督（第1–3页）。

## 方法总览

身体和手分别由Transformer编码，单帧5个可学习latent token保留动作语义；视频token经新增cross-attention读取动作token，参考图和文字通过原DiT机制参与。三阶段从单视图重建走向混合跨视图，再专注多视图及运动相机数据（第4–6页）。

## 核心创新与关键设计

训练以flow的v预测损失加早期几何辅助项：可概括L=L_v+λ(t)L_geo，λ随后衰减到零。MLP把动作编码回归SMPL/MANO姿态，排除全局根朝向；随机透视与外观增强降低视角和身份泄漏。语义瓶颈鼓励视角无关，并非仅靠压缩便可证明严格几何不变（第4–6页）。

## 实验与关键结果

数据按来源为互联网600k、自采100k、UE60k；121帧、约480×854面积、batch64、Adam10⁻⁵，三阶段10k/15k/5k步约3天，不能由此推断单卡时长。第7页150个评估视频静态相机条件下，FID36.92/FVD297.4优于Uni3C41.28/321.9；PSNR17.96、SSIM0.7390低于MTVCrafter18.03/0.7489。30人MOS总体4.38±0.08。

## 消融实验与证据强度

第7–8页表2：去几何监督FID51.3，通道拼接48.2，全模型36.9；SMPL控制39.7。仅第一阶段PSNR18.3高于全模型18.0，但新视角运镜能力差，说明像素指标不能独立验证解耦。去手编码FID38.1/FVD298.7，小幅退化同时有手势定性差异。

## 局限与讨论

文字运镜是生成式能力，不保证精确相机矩阵或轨迹控制。定量主表固定相机，跨视角优势还依赖定性结果与用户评价。部分自有采集数据和未完整披露的预训练生成器，会限制完全复现；动作合理性不等于真实人体动力学测量。

## 复现提示

分别验证同视图重建、跨视图动作一致性及运镜，而非只报FID。保留辅助监督退火、数据配比、手裁剪和训练阶段；核查预训练DiT与私有数据可得性。论文给出3DiMo项目页，本地未下载、训练或执行视频生成。

## 相关工作与阅读顺序

先读人体动画AnimateAnyone、MimicMotion，再比较Uni3C和MTVCrafter的显式3D控制；最后看隐式token如何与DiT跨注意力配合。

## 来源与校验

- 已渲染并目视核对 PDF 第7页关键表格/图；其余正文与公式通过原文文本核对。
- [CVF 官方论文页](https://openaccess.thecvf.com/content/CVPR2026/html/Fang_3D-Aware_Implicit_Motion_Control_for_View-Adaptive_Human_Video_Generation_CVPR_2026_paper.html) · [所读 PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Fang_3D-Aware_Implicit_Motion_Control_for_View-Adaptive_Human_Video_Generation_CVPR_2026_paper.pdf)。页码均为该 PDF 的页序。
- 阅读范围：正文、公式与实验表；补充材料、上游代码与权重未逐项核验。许可证和固定代码 commit 尚未确认，不复制原文全文或数据。
- PDF SHA-256：`0db5368bf2dd8ac4782ed302de502701f579f53e9fe3c6270c9fdc46ca35da8c`；版本为本次下载的 CVF 接收稿，核对日期 2026-10-20。
