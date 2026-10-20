# A2GC: Asymmetric Aggregation with Geometric Constraints for Locally Aggregated Descriptors

核对日期：2026-10-20。以下实验均为作者报告；本地完成原文阅读与讲解自检，未复现实验。

## 一句话总结

A²GC为地点识别的局部特征聚合加入二维坐标偏好，并用行列对数归一化平均及一次边缘校准生成分配权重，提升全局检索描述子的辨别力。

## 研究背景与动机

同一地点跨季节、视角和光照变化很大；DINOv2局部特征好，不代表简单池化就能保留稳定地标。方法沿SALAD路线把patch分配到聚类槽位，并引入位置相关打分。[§1–2，PDF1–2]

需要纠正背景解读：标准Sinkhorn本来就可处理不同维度及不同给定边缘a、b，不要求两种特征“分布相同”。本文的新归一化日程应作为经验设计评价，不能把作者的“Sinkhorn要求对称分布”当作一般最优传输定理。

## 方法总览

![A2GC 原文 Fig.2](../../../../site/figures/a2gc-original-fig2.png)

DINOv2给出patch与全局token；局部特征相似度加上坐标embedding与聚类位置embedding的内积，经包含dustbin的分配模块得到各聚类加权描述子，再与全局分支拼接并L2归一化检索。[Fig.2、§3，PDF3–4]

坐标是图像二维归一化位置，不是相机位姿或世界三维几何。

图：原论文 Fig.2，PDF第4页。仅裁去页边及无关正文，图内内容未改；著作权属于原作者，用于本篇方法分析，不按本站原创图重新授权。[原文与作者信息](https://openaccess.thecvf.com/content/CVPR2026/html/Li_A2GC_Asymmetric_Aggregation_with_Geometric_Constraints_for_Locally_Aggregated_Descriptors_CVPR_2026_paper.html) · [PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Li_A2GC_Asymmetric_Aggregation_with_Geometric_Constraints_for_Locally_Aggregated_Descriptors_CVPR_2026_paper.pdf)。点击可查看高清图。

## 核心创新与关键设计

融合打分为\(S_{ij}=S^f_{ij}+\lambda_g\,g_{xy}^\top c_j^g\)，其中\(g_{xy}=\phi_g([2x/(H-1)-1,2y/(W-1)-1])\)。以位置偏好影响聚类，而不是强制任意邻近patch拥有同一语义。[式9–12，PDF4]

对数矩阵初始化\(Z=M/\max(\tau,10^{-6})\)，迭代时分别减行/列logsumexp后取平均。之后先按a校准行，再按b校准列。[式3–8，PDF3]

最后一次列缩放通常会再次改变行和，因此“一次行校准+一次列校准”不自动保证两边缘同时精确满足；也没有正文证明该平均迭代等于原熵正则OT的收敛解。复现需报告边缘残差，不能只看检索结果推断求解器正确性。

## 实验与关键结果

GSV-Cities约120万图、每地点4张；DINOv2 ViT-B/14默认只微调末4块，224²输入、64聚类、16维坐标、温度1、归一化迭代3。AdamW学习率6e-5、batch60、单V10032G，FAISS对归一化描述子做L2检索。[§4.1，PDF5]

| 作者报告 R@1↑ | SALAD 8448 / ViTb | A²GC 8448 / ViTb | A²GC 33280 / ViTg |
| --- | --- | --- | --- |
| Pitts30k | 92.4 | 94.9 | 95.6 |
| Pitts250k | 95.1 | 97.0 | 97.3 |
| MSLS-V | 92.2 | 93.3 | 93.6 |
| MSLS-C | 75.0 | 80.3 | 80.6 |

来源Table1，PDF6。最大模型并非每个数据集第一：Pair-VPR的MSLS-V/C R@1为95.4/81.7。不能把不同骨干、维度和重排序预算混成聚合器单独的收益。

## 消融实验与证据强度

去掉两项、仅去掉A²、仅去掉GC、完整模型的Pitts30k R@1为92.5/93.9/94.1/94.9。[Table5，PDF7] 全量微调94.0低于只调末4块94.9；描述子变大对R@5也不单调。[Table3–4，PDF6]

Table6的224输入MSLS-V R@1为90.4，与Table1同默认尺寸描述的93.3不一致，配置或协议差异未交代，不能拼接成同一受控实验。Table7 SPED R@10为95.56，而正文写94.56，本笔记按表保留并标记差异。[PDF7–8]

## 局限与讨论

二维坐标偏好可能对大视角变化敏感；大型描述子增加存储和索引开销。ViTg25.06ms相较ViTs1.32ms明显更慢，这仍不是包含数据库检索与重排序的完整延迟。[Table2]

论文写验证涉及Pitts30k validation/test，实际模型选择是否严格隔离test需核实；跨季节实验不能代替未知城市和实际机器人长期定位验证。OT性质、分辨率与指标口径均需实现复核。

## 复现提示

建议 `data/vpr/a2gc/`，按GSV-Cities/Pitts/MSLS/Nordland许可取得图像及地理信息，勿公开个人轨迹。固定正样本距离阈值、数据库/查询划分、输入分辨率、骨干、描述子维度与是否重排序。另输出归一化前后行列边缘误差。

[作者代码](https://github.com/CV4RA/A2GC)在正文给出；commit、许可证与运行结果未核验，本地未训练或建立真实位置索引。

## 相关工作与阅读顺序

先读NetVLAD的软分配与SALAD的dustbin，再复习带不同边缘的熵正则OT。最后看本篇归一化日程与坐标打分，区分经验检索提升和未经证明的求解器解释。

## 来源与校验

- [CVF 官方论文页](https://openaccess.thecvf.com/content/CVPR2026/html/Li_A2GC_Asymmetric_Aggregation_with_Geometric_Constraints_for_Locally_Aggregated_Descriptors_CVPR_2026_paper.html) · [所读 PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Li_A2GC_Asymmetric_Aggregation_with_Geometric_Constraints_for_Locally_Aggregated_Descriptors_CVPR_2026_paper.pdf)。页码均为该 PDF 的页序。
- 阅读范围：正文、公式与实验表；补充材料、上游代码与权重未逐项核验。许可证和固定代码 commit 尚未确认，不复制原文全文或数据。
- PDF SHA-256：`fdd83710d44c1eb349c392b7cff8ccccf115f189b5f6986934ad7419da3456a5`；版本为本次下载的 CVF 接收稿，核对日期 2026-10-20。
- 视觉核对：PDF第4页及所引流程图已渲染检查；本地未复现实验。
