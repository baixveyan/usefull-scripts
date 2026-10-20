# φ-DPO：用困难偏好对改善多模态持续学习

论文：**$\phi$-DPO: Fairness Direct Preference Optimization Approach to Continual Learning in Large Multimodal Models**，Thanh-Dat Truong、Huu-Thien Tran、Jackson Cothren、Bhiksha Raj、Khoa Luu，CVPR2026，39922–39934页。

[官方页](https://openaccess.thecvf.com/content/CVPR2026/html/Truong_phi-DPO_Fairness_Direct_Preference_Optimization_Approach_to_Continual_Learning_in_CVPR_2026_paper.html) · [PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Truong_phi-DPO_Fairness_Direct_Preference_Optimization_Approach_to_Continual_Learning_in_CVPR_2026_paper.pdf) · [论文所列项目](http://uark-cviu.github.io/projects/Fai-DPO)

分类：多模态／持续学习／偏好优化。核对日期：2026-10-20。正文精读、自检完成，未运行实验；页码为PDF页码。

## 一句话总结

以上一学习阶段模型为DPO参考，在新任务训练中同时学习标准答案与偏好对，并通过focal式权重增加困难偏好对的影响，尝试缓解遗忘与数据不平衡。

## 研究背景与动机

连续学习ScienceQA、定位、OCR等任务会改变视觉语言对齐，旧任务能力可能退化；任务内大量常见主题还会主导更新。本文的fairness主要围绕数据分布与任务／主题不平衡讨论，不能自动解释成对人口群体的全面公平保证。[PDF 1–3]

## 方法总览

```mermaid
flowchart LR
 A[当前任务图文指令与答案] --> B[构建偏好与拒绝回答]
 B --> C[DPO加困难对权重]
 R[上一阶段冻结参考模型] --> C
 C --> D[与监督损失共同优化LoRA]
 D --> E[更新模型用于下一任务]
```

图依据Fig.4与式17重绘。偏好数据并非全由真实用户提供：标准答案为正例，LLM生成貌似合理但错误的负例，再人工验证。[§3.3，PDF 6]

## 核心创新与关键设计

令 \(\Delta_t=\log\pi_t(y^+|x)-\log\pi_t(y^-|x)\)，参考模型对应 \(\Delta_{t-1}\)。偏好概率为 \(p=\sigma(\beta(\Delta_t-\Delta_{t-1}))\)，公平DPO损失为：

\[
L_{\phi DPO}=-\mathbb E[(1-p)^\gamma\log p].
\]

\(\gamma=0\)退化为普通DPO；已轻松区分的偏好对权重下降。总目标再加当前任务答案的负对数似然，使用LoRA更新。[式7、14、17，PDF 4–6] 它没有直接按每个群体的逆频率重加权，困难样本与少数群体相关只是可能情形，不是恒等关系。

作者给出DPO与KL界及梯度差异分析，证明细节在附录。本轮未独立验证这些条件。特别是“γ趋于无穷使群体梯度差趋零”也可能伴随所有梯度消失，不能单独证明模型获得有用且公平的能力；正文也承认此风险。[PDF 5–6]

## 实验与关键结果

基于LLaVA1.5、CLIP-ViT-L/14与Vicuna7B；测试CoIN、MLLM-CL Domain与Ability。[§4，PDF 6–8] Table 4（第8页已渲染核对）域持续学习结果：

| 配置 | 最终均值MFN↑ | 历程均值MAA↑ | BWT↑ |
| --- | ---: | ---: | ---: |
| LoRA-FT | 53.00 | 61.13 | -14.97 |
| 知识蒸馏KD | 69.21 | 71.49 | -2.71 |
| DPO | 71.74 | 73.68 | -1.33 |
| φ-DPO | 74.00 | 75.68 | -0.37 |

BWT越接近零通常意味着少遗忘，但最终平均能力与BWT不是同一指标。主表MR-LoRA的BWT为-0.01，比本文-0.37更高；不能写成本文每项指标都最好。正文与表格个别数字略有差异，这里按表。

## 消融实验与证据强度

Table 5中β=0.05的MAA76.27高于默认β=0.1的75.68，但遗忘更大（BWT-1.66）；默认是权衡而非所有指标最优。Table 6的γ=2表现较好，γ=5的MFN降到72.18，说明不能无限强调困难对。[PDF 8]

这些平均任务指标支持所测持续学习能力，不直接给出所有细群体的公平性测量。额外偏好标注与人工核验成本也应纳入比较。

## 局限与讨论

作者承认β、γ、损失权重和负回答质量敏感；错误偏好对可能加大偏差。上一阶段输出只是保留能力的参考，不能保证尚未在当前数据覆盖的旧任务完全不遗忘。理论界的常数与分布条件必须查证明，不能从“小DPO损失”无条件推出所有旧知识保留。

## 复现提示

正文配置LoRA rank32、AdamW、基准学习率2×10⁻⁵、cosine调度、batch64、每阶段1epoch，16张A100 40GB，默认β0.1、γ2。[PDF 6、8] 先固定任务顺序和偏好生成规则，按阶段保存所有任务评价。实现应优先由式14自动微分，并核对正文式15的展开梯度符号，避免直接照搬未经核实的手写梯度。代码commit、许可与依赖未核验；未调用付费模型生成数据，未复现实验。

## 相关工作与阅读顺序

DPO解释参考策略与偏好比，focal loss解释困难样本权重，持续学习评价解释BWT。建议式7→14→17→Table 4–6→局限；避免把偏好对齐、遗忘控制和群体公平三个概念混为一谈。

## 来源与校验

依据正文1–8页，第8页表格已渲染查看。PDF SHA-256：`8e2e3d177534a898d982e73cac810fb322ada851b6f71477354834825bc73447`。补充证明及代码未读；AI辅助独立讲解已自检，无独立专家审稿，未复现实验。不转载作者图片或全文。
