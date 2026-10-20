# 2ndMatch: Finetuning Pruned Diffusion Models via Second-Order Jacobian Matching

作者：Caleb Zheng, Eli Shlizerman。

分类：generation；交付形式：Markdown 中文论文讲解。

核对日期：2026-10-20。以下实验均为作者报告；本地完成原文阅读与讲解自检，未复现实验。

## 一句话总结

给已经剪枝的扩散模型增加教师与学生局部Jacobian的二阶匹配损失，在不增加推理模型规模的情况下改善微调质量。

## 研究背景与动机

剪枝破坏扩散网络对输入扰动的响应；仅拟合教师输出可能保留当前点的预测，却丢失邻域动态。本文解决剪枝后的恢复训练，不提出新的剪枝决策器（第1–3页）。

## 方法总览

保留稠密教师，对学生同时施加噪声预测、输出蒸馏和Jacobian响应匹配。借随机方向上的Jacobian-vector product估计局部扰动扩张，训练时增加计算，部署仍使用同样的剪枝学生（第4–6页）。

## 核心创新与关键设计

设J=∂s(x,t)/∂x，核心项为 E_v[(‖J_s v‖²−‖J_t v‖²)²]。它约束JᵀJ诱导的方向能量，不是Hessian或直接计算二阶导数；灵感来自有限时间Lyapunov指数，但单步代理并非完整多步FTLE。随机方向避免显式构造巨型Jacobian，也无法保证有限采样下整个矩阵完全一致（第4–5页）。

## 实验与关键结果

第6页表1中LSUN Bedroom的Diff-Pruning FID17.90→9.68，稠密教师6.62；ImageNet10.23→5.68，教师3.6。第7页表2，MSCOCO30k/512分辨率下SD1.4 BK-Base FID15.76→13.84、CLIP0.2878→0.2900；BK-Tiny FID17.12→16.68，但CLIP0.2653→0.2636下降，不能概括为全部指标改善。

## 消融实验与证据强度

第8页表4的CIFAR设置中噪声预测5.29、蒸馏5.05、一阶匹配5.14、二阶4.58，支持损失设计，仍不及教师4.19。第7页U-ViT CIFAR FID4.63→4.05、CelebA3.57→3.35。不同表的训练与采样配置不同，不跨表直接合并排名。

## 局限与讨论

仍依赖可访问的稠密教师；JVP与梯度回传增加微调成本。匹配能量可能遗漏方向和符号信息，且无法证明采样分布完全保持。推理参数不变不等于训练免费，也不等于任何剪枝比例都能恢复。

## 复现提示

记录剪枝来源、教师权重、损失系数、随机向量数和微调步数。作者硬件为A10080GB；U-Net用100步DDIM，SD25步，U-ViT1000步EM，评估时必须对应相同采样器。此次仅核对原文，未执行训练或生成FID样本。

## 相关工作与阅读顺序

先读Diff-Pruning、BK-SDM及蒸馏，再理解JVP、局部扰动增长与FTLE。将本文定位为模型压缩后的质量恢复工具，比把它当独立生成模型更准确；代码许可证及固定版本尚未确认。

## 来源与校验

- 已渲染并目视核对 PDF 第7页关键表格/图；其余正文与公式通过原文文本核对。
- [CVF 官方论文页](https://openaccess.thecvf.com/content/CVPR2026/html/Zheng_2ndMatch_Finetuning_Pruned_Diffusion_Models_via_Second-Order_Jacobian_Matching_CVPR_2026_paper.html) · [所读 PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Zheng_2ndMatch_Finetuning_Pruned_Diffusion_Models_via_Second-Order_Jacobian_Matching_CVPR_2026_paper.pdf)。页码均为该 PDF 的页序。
- 阅读范围：正文、公式与实验表；补充材料、上游代码与权重未逐项核验。许可证和固定代码 commit 尚未确认，不复制原文全文或数据。
- PDF SHA-256：`6cf5f0b4bd37557e92d841b5d904d7e7fb41709ee0fd86ce0c1e2ef824c95a2a`；版本为本次下载的 CVF 接收稿，核对日期 2026-10-20。
