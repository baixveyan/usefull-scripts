# AdaPrior: Bayesian-Inspired Adaptive Prior Correction for Long-Tailed Continual Learning

核对日期：2026-10-22。实验数值均为作者报告；本地完成原文阅读与讲解自检，未复现实验。

## 一句话总结

AdaPrior用模型预测概率的动态平均估计类别偏置，分别在训练损失与推理logit中校正长尾持续学习；实验显示有效，但正文关于KL分解和固定步长EMA几乎必然收敛的表述需要额外条件，不能直接当作已成立的保证。（PDF第1–8页）

## 研究背景与动机

长尾类增量学习同时面临新旧任务失衡和任务内部类别长尾。历史类只有少量回放样本，新任务又可能由头部类主导。静态类别计数未必反映模型在蒸馏、回放与优化后的实际偏向。作者于是跟踪预测分布的平均值，把它作为模型诱导先验，面向通常类别均衡的评价分布纠偏；这仍依赖类条件近似稳定等假设。（PDF第1–4页）

## 方法总览

![原文Fig.2：方法框架](../../../../site/figures/adaprior-original-fig2.png)

原论文Fig.2，PDF第2页。仅裁切相关图示，保留图内科学标签；著作权属于原作者，用于本篇方法分析，不并入本站原创图授权。[来源与作者](https://openaccess.thecvf.com/content/CVPR2026/html/Bhat_AdaPrior_Bayesian-Inspired_Adaptive_Prior_Correction_for_Long-Tailed_Continual_Learning_CVPR_2026_paper.html) · [PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Bhat_AdaPrior_Bayesian-Inspired_Adaptive_Prior_Correction_for_Long-Tailed_Continual_Learning_CVPR_2026_paper.pdf)。点击可打开高清图。

图2分成训练时AdaPrior Loss和推理后处理。训练过程中维护长度K的EMA概率向量，并在交叉熵的logit里加入先验比值；训练结束后可重新估计预测均值，进行强度α控制的后处理。三种模式为只后处理、只改损失和二者结合的Full AdaPrior。统计向量detach、不通过它反向传播，因此新增的是O(K)统计存储；原有骨干、回放和蒸馏成本仍存在。（PDF第4、6–7页）

## 核心创新与关键设计

EMA更新为 \(p_i=(1-\gamma)p_{i-1}+\gamma\,\mathrm{mean}_{x\in B_i}P_m(y|x)\)。推理调整 \(z'_y=z_y+\alpha[\log P_t(y)-\log p_y]\)，均匀目标先验下等价于减去 \(\alpha\log p_y\)。训练损失式(7)则对logit加 \(\log[p_y/P_t(y)]\)，方向相反：前者直接修正预测，后者让学习过程补偿偏置。（PDF第4页）

**理论核对。** 式(8)缺少式(7)的归一化项，直接展开也不会一般得到正文宣称的 \(CE+KL(P_m\|P_t)\)：求和权重与符号均需进一步推导。对于定理3，固定γ且批均值有独立非零噪声时，标量EMA稳态方差为 \(\gamma\sigma^2/(2-\gamma)\)，并不会自动几乎必然收敛到常数均值。该反例是本笔记的代数核查；衰减步长或消失噪声可能得到不同结论，但正文条件不足以直接支持其强表述。温和α的公式也需重新归一化，不能把未归一化权重直接当概率。（PDF第4、6页）

## 实验与关键结果

在LUCIR流程上，CIFAR100-LT用ResNet32、500轮，ImageNet100类子集和iNaturalist100类子集用ResNet18、180轮；前两者IF100，后者约435。默认每类20个回放样本，主指标为各任务平均增量准确率。LFS从较少初始类开始，LFH从一半类别开始，Ordered/Shuffled顺序分别报告。（PDF第7页）

| 平均增量准确率/% | LUCIR+CE | AdaPrior Loss | Full |
|---|---:|---:|---:|
| Shuffled CIFAR，LFS10任务 | 29.97 | 34.07 | 36.94 |
| Shuffled ImageNet，LFH10任务 | 48.98 | 58.21 | 59.28 |
| Ordered ImageNet，LFH5任务 | 61.18 | 61.79 | 61.36 |
| iNaturalist Ordered，LFH10任务 | 68.98 | 72.52 | 72.26 |

表1–3（PDF第5–6页）。Full并非处处优于只改损失，不能照搬“所有split最优”。表6在ImageNet子集5任务下ECE0.1500→0.1322、NLL2.5242→2.4218，属于验证划分的校准结果，不是独立临床或部署可靠性保证。（PDF第8页）

## 消融实验与证据强度

表5中Shuffled ImageNet LFH10任务：原始48.98，静态logN55.03，只后处理56.27，只损失58.21，Full59.28，支持训练与推理校正互补。在CIFAR LFH5任务，只后处理42.08却略低于静态logN42.37，动态先验没有逐格胜出。（PDF第8页）

去Mixup的表4仍报告增益，图5偏好γ约0.05、α约0.6–0.7；α默认在保留验证集选择，所以不属于完全无调参。Food101、1000类ImageNet与跨骨干结果主要在补充材料，未独立核对其数值。（PDF第7–8页）

## 局限与讨论

先验校正不能恢复已经丢失的类别特征；条件分布显著改变时，Bayes先验比值解释也会失效。预测均值同时混合采样偏差、分类错误与置信度偏差，不是真实人口类别比例。理论条件问题不自动否定表中经验效果，但需要把实践有效与证明有效分开。部分基线来自他文、部分作者重现，缺少统一重复实验误差条，细小差异不宜解释成稳定优势。（PDF第4–8页）

## 复现提示

本轮未核查作者代码、固定commit、许可证或补充证明，也未运行持续训练。复现需记录类别顺序、回放策略、Mixup、蒸馏、EMA初始化、新类扩展和对log零值的平滑；后处理估计用的数据不能泄漏评价标签。应先用独立噪声序列验证固定γ的方差边界，再逐项核查式(7)/(8)的实现含义，不能把本笔记建议修正当作作者原实现。（PDF第3–8页）

## 相关工作与阅读顺序

先理解LUCIR类增量学习，再读静态logit adjustment和balanced softmax，最后阅读AdaPrior的动态统计。查看定理时区分固定步长追踪、期望收敛与几乎必然收敛；查看实验时区分均衡目标先验与真实应用中可能不均衡的目标分布。这些前提比“Bayesian”名称更决定方法是否适合具体任务。（PDF第3–8页）

## 来源与校验

- [CVF官方论文页](https://openaccess.thecvf.com/content/CVPR2026/html/Bhat_AdaPrior_Bayesian-Inspired_Adaptive_Prior_Correction_for_Long-Tailed_Continual_Learning_CVPR_2026_paper.html) · [所读PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Bhat_AdaPrior_Bayesian-Inspired_Adaptive_Prior_Correction_for_Long-Tailed_Continual_Learning_CVPR_2026_paper.pdf)。页码均为PDF页序。
- 所读版本：2026-10-22从CVF下载的开放接收稿；PDF SHA-256：`a36d8aeb91a603323e86af48ce4e6634f21cc23ce2fd1b8634d2f50e1ebdd265`。
- 阅读范围：正文、方法公式、实验与消融；补充材料、代码及权重未逐项核验。reviewed表示本地讲解自检，不表示独立同行评审或实验复现。
- 方法图与关键公式/表格已渲染核对，所引原图已单独检查；未对新文章进行浏览器交互验收。作者图示与本站原创素材权利分开记录。
