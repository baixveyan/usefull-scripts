# AcTTA: Rethinking Test-Time Adaptation via Dynamic Activation

核对日期：2026-10-22。实验数值均为作者报告；本地完成原文阅读与讲解自检，未复现实验。

## 一句话总结

AcTTA在测试时调整激活函数的中心和两侧残差斜率，用少量新增参数配合已有适应损失改善部分分布偏移任务；它仍需梯度优化，而且小批次下并非总能优于原模型。（PDF第1–3、6页）

## 研究背景与动机

测试时适应常只更新归一化层的仿射参数，但偏移也会改变进入激活函数的特征分布。固定的ReLU或GELU门控可能把变化后的信息截断。作者于是把更新对象扩展到激活函数形状。这里“保持源权重”指基础参数可以冻结，不表示模型行为不变，也不表示无需训练；新增参数仍通过测试数据上的适应目标更新。（PDF第1–3页）

## 方法总览

![原文Fig.1：方法框架](../../../../site/figures/actta-original-fig1.png)

原论文Fig.1，PDF第3页。仅裁切相关图示，保留图内科学标签；著作权属于原作者，用于本篇方法分析，不并入本站原创图授权。[来源与作者](https://openaccess.thecvf.com/content/CVPR2026/html/Kim_AcTTA_Rethinking_Test-Time_Adaptation_via_Dynamic_Activation_CVPR_2026_paper.html) · [PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Kim_AcTTA_Rethinking_Test-Time_Adaptation_via_Dynamic_Activation_CVPR_2026_paper.pdf)。点击可打开高清图。

图1是激活函数分析图，展示中心、两侧系数等改变后的曲线，应与网络流程图区分。实际流程为：在部分层的激活处加入零初始化可训练参数；保留基础激活；用TENT、ETA、SAR等已有方法的损失在测试流上更新参数；再预测当前或后续样本。CNN中冻结BN仿射参数的设置常表现较好，ViT则同时更新LayerNorm仿射参数，不能一概称为只更新激活。（PDF第3–5页）

## 核心创新与关键设计

令 \(u=x-c\)，参数化形式可写成

\[g(x)=\phi(u)+[\lambda_{neg}+(\lambda_{pos}-\lambda_{neg})\sigma(\beta u)]u.\]

\(c\)控制中心，两侧系数通过sigmoid平滑连接；全部新增参数为零时恢复基础函数。括号项是残差系数，不是整个激活的导数：实际 \(g'(x)=\phi'(u)+\lambda(u)+u\lambda'(u)\)。例如ReLU正侧还含基础斜率1；零初始化也不会立即让所有负侧梯度非零。（PDF第3–4页）

AcTTA不新增一套专门适应损失，而是更换可更新参数集合。无源数据的EATA比较移除了Fisher项，标为ETA；不能把它当作含完整源信息正则的EATA结果。激活替换比例与学习率都是关键选择，冻结参数与提高新参数学习率的效果也不宜混在一起解释。（PDF第4–5页）

## 实验与关键结果

作者在CIFAR10-C、CIFAR100-C与ImageNet-C的15类最高强度腐蚀上报告三种子结果。表5的常规批次结果如下，数值是错误率，越低越好。（PDF第5–6页）

| 模型与数据 | TENT | AcTTA+TENT |
|---|---:|---:|
| WRN28 / CIFAR10-C | 18.51 | 17.03 |
| WRN40 / CIFAR100-C | 35.25 | 33.81 |
| ResNet-BN / ImageNet-C | 66.50 | 64.95 |
| ResNet-GN / ImageNet-C | 69.60 | 66.84 |
| ViT / ImageNet-C | 53.85 | 51.79 |

但组合收益并不普遍：ViT上的SAR从53.90变为54.17，DeYO从47.73变为49.64。batch4时，CIFAR100-C的TENT为57.35，AcTTA后55.03，仍差于不适应源模型46.75；ViT上的SAR从71.81恶化至82.11，ETA+AcTTA为72.70，也差于源模型62.10。（表5–6，PDF第6页）

## 消融实验与证据强度

表2中WRN只更新激活并用10倍学习率为17.03，联合更新仿射与激活为18.06；ViT则联合更新52.37优于只激活且10倍学习率55.30。这说明架构和学习率交互重要，不能从这组数值单独分离“冻结BN”的因果贡献。（PDF第4–5页）

表4显示50%层替换是折中，而非处处最优：WRN40为34.05，全部替换44.97；ViT的25%替换51.40，50%为52.47。表8还报告代价：WRN28、batch128下TENT峰值4,013MiB、112.83ms，AcTTA为6,249MiB、164.51ms。相对TENT约增加56%显存与46%时间，不应把少量参数等同于免费适应。（PDF第5、7页）

## 局限与讨论

熵最小化仍可能强化错误预测；激活更灵活不自动解决类别不平衡、样本顺序或持续偏移造成的漂移。batch4的反例说明小样本稳定性需要逐个协议检验。表7的持续适应结果支持某些遗忘缓解，但没有给出所有原始源模型对照，不能据此声称恢复或超过原始干净集性能。测试流状态如何重置、哪些层适应与学习率选择，都可能影响结论。（PDF第5–7页）

## 复现提示

[作者项目页](https://hyeongyu-kim.github.io/actta/)为后续核查入口；本轮未审查代码commit、许可证或补充材料，未做适应实验。复现时必须记录腐蚀顺序、强度、batch大小、源检查点、激活替换层、优化器状态重置及是否允许源统计信息。应同时报告冻结源模型、原始适应方法及加入AcTTA三组，并统计错误率、耗时与峰值显存。只报告相对某个已崩溃适应基线的提升，会隐藏仍差于源模型的问题。（PDF第4–7页）

## 相关工作与阅读顺序

先理解TENT为何更新归一化仿射参数，再阅读ETA/SAR对可靠样本与稳定性的处理。随后用参数化激活函数的导数理解AcTTA的额外自由度，最后比较表5和表6，尤其关注对源模型的绝对退化。它的价值是一个可组合的参数选择方向，而不是一个独立解决所有测试时偏移的算法。（PDF第2–6页）

## 来源与校验

- [CVF官方论文页](https://openaccess.thecvf.com/content/CVPR2026/html/Kim_AcTTA_Rethinking_Test-Time_Adaptation_via_Dynamic_Activation_CVPR_2026_paper.html) · [所读PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Kim_AcTTA_Rethinking_Test-Time_Adaptation_via_Dynamic_Activation_CVPR_2026_paper.pdf)。页码均为PDF页序。
- 所读版本：2026-10-22从CVF下载的开放接收稿；PDF SHA-256：`efb5b1d244e829abe34f4488c25587e8214034671d42f7a73688d64d54910a48`。
- 阅读范围：正文、方法公式、实验与消融；补充材料、代码及权重未逐项核验。reviewed表示本地讲解自检，不表示独立同行评审或实验复现。
- 方法图与关键公式/表格已渲染核对，所引原图已单独检查；未对新文章进行浏览器交互验收。作者图示与本站原创素材权利分开记录。
