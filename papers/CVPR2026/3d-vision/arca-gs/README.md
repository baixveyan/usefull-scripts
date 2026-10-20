# 3D Gaussian Splatting at Arbitrary Resolutions with Compact Proxy Anchors

作者：Mingyun Jeong, Seongro Yoon, Francois Bremond, Donghyeon Cho。

分类：3d-vision；交付形式：Markdown 中文论文讲解。

核对日期：2026-10-20。以下实验均为作者报告；本地完成原文阅读与讲解自检，未复现实验。

## 一句话总结

ARCA-GS用分辨率条件化特征、像素覆盖门控与代理锚点压缩，让同一个高斯场适应多种渲染尺寸。

## 研究背景与动机

固定分辨率训练的3DGS在缩小时容易混叠，锚点特征也占存储。单纯在推理时删小高斯可能损坏经过训练形成的透明度组合，因此需要联合训练处理分辨率与压缩（第1–3页）。

## 方法总览

在Scaffold-GS锚点表示上，输入位置和缩放比例ξ，经FiLM调节特征；投影面积门控调节透明度；约30%代理锚点保留特征，其余叶锚点由近邻代理及几何关系预测特征（第3–4页）。

## 核心创新与关键设计

FiLM写为f̂=(1+γ)f+β。投影面积A=πρ²√detΣ₂D，门控g=sigmoid(κ(A−η))，α′=αg，降低亚像素高斯的贡献。残差MLP仍需要叶锚点位置等信息，并非删除所有叶元数据。训练以图像L1/SSIM及特征MSE、余弦项共同优化（第3–6页）。

## 实验与关键结果

30k迭代，随机10%–100%训练分辨率。第5页Mip-NeRF360表中10%尺寸PSNR29.742，对比Scaffold24.681；100%为26.710对26.498。存储41.6MB对78.9MB，但Context-GS9.3MB、TC-GS8.2MB更小，不能称绝对最小。Tanks平均PSNR24.600对24.060、锚点67.2k对208k；NeRF Synthetic的64%尺寸反而30.689低于基线31.562。

## 消融实验与证据强度

第7页FiLM平均PSNR28.183，高于无调制27.199和加法调制28.036。第8页仅推理时加门控的Deep Blending平均PSNR28.147，低于原Scaffold29.465，联合训练29.905；证据说明门控不是可无损即插即用的过滤器。

## 局限与讨论

代理特征预测存在计算开销，朴素实现可能慢于不压缩模型；存储下降不能直接转换成FPS提升。当前主要针对静态场景和已知相机；不同数据、尺寸并非全面领先，动态场景仍待研究。

## 复现提示

先重现Scaffold-GS，再固定训练/测试尺寸和存储统计口径。压缩在锚点增长剪枝后延迟启动，随机20%叶特征由预测替换；特征重建权重20k前0.1、之后0.01。论文给出ARCA-GS仓库入口，但代码、commit和许可证未核验，未在本地运行。

## 相关工作与阅读顺序

按3DGS→Scaffold-GS→多尺度抗混叠与锚点压缩阅读。官方元数据题名使用“at Arbitrary Resolutions”，PDF题名使用“for”，本笔记保留清单题名，避免误作两篇论文。

## 来源与校验

- 已渲染并目视核对 PDF 第5页关键表格/图；其余正文与公式通过原文文本核对。
- [CVF 官方论文页](https://openaccess.thecvf.com/content/CVPR2026/html/Jeong_3D_Gaussian_Splatting_at_Arbitrary_Resolutions_with_Compact_Proxy_Anchors_CVPR_2026_paper.html) · [所读 PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Jeong_3D_Gaussian_Splatting_at_Arbitrary_Resolutions_with_Compact_Proxy_Anchors_CVPR_2026_paper.pdf)。页码均为该 PDF 的页序。
- 阅读范围：正文、公式与实验表；补充材料、上游代码与权重未逐项核验。许可证和固定代码 commit 尚未确认，不复制原文全文或数据。
- PDF SHA-256：`c29306e7a15679e5c5941b1f7cabfb4289c7bfdee42d02f23e52dbf36945ff84`；版本为本次下载的 CVF 接收稿，核对日期 2026-10-20。
