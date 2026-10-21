# ActivityForensics: A Comprehensive Benchmark for Localizing Manipulated Activity in Videos

核对日期：2026-10-22。实验数值均为作者报告；本地完成原文阅读与讲解自检，未复现实验。

## 一句话总结

ActivityForensics把“视频是否被改过”细化为“哪段活动被生成或编辑过”，并提出TADiff，以特征加噪与少步去噪改善伪造活动的时间边界定位。（PDF第1–5页）

## 研究背景与动机

只输出整段视频真假标签，不能告诉使用者哪段行为受到修改。局部活动编辑可能保留人物、背景和大部分帧，检测器需要同时识别异常活动并定位起止时间。该论文构建的是受控生成与编辑基准，不是对任意网络视频的事实核查系统；未检测到操纵也不能证明视频叙事真实。（PDF第1–3页）

## 方法总览

![原文Fig.4：方法框架](../../../../site/figures/activityforensics-tadiff-original-fig4.png)

原论文Fig.4，PDF第5页。仅裁切相关图示，保留图内科学标签；著作权属于原作者，用于本篇方法分析，不并入本站原创图授权。[来源与作者](https://openaccess.thecvf.com/content/CVPR2026/html/Bao_ActivityForensics_A_Comprehensive_Benchmark_for_Localizing_Manipulated_Activity_in_Videos_CVPR_2026_paper.html) · [PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Bao_ActivityForensics_A_Comprehensive_Benchmark_for_Localizing_Manipulated_Activity_in_Videos_CVPR_2026_paper.pdf)。点击可打开高清图。

数据流程先定位或描述原始活动片段，再修改活动描述，经生成或编辑工具产生片段并并入视频，保存时间标注。图3列出Wan1,437、Scifi1,152、FCVG1,559、VACE1,061、LTX1,058和Vidu265条；各来源并不等量，超过60%的操纵片段短于整段视频的30%。Vidu只用于开放生成器评估。（PDF第3–4页）

图4对应TADiff：帧特征进入ActionFormer式多尺度时序编码器，训练时加入扩散噪声；带FiLM时间调制的卷积去噪器恢复有用表示；分类头判断操纵活动，回归头预测边界。去噪发生在特征空间，而非逐帧恢复“原始真视频”。（PDF第5–6页）

## 核心创新与关键设计

给定特征 \(f\)，加噪为 \(x_s=\sqrt{\bar\alpha_s}f+\sqrt{1-\bar\alpha_s}\epsilon\)。噪声迫使网络少依赖某个生成器的偶然痕迹，去噪器再通过少步DDIM式更新提取可定位信号。最终监督使用focal分类损失和SmoothL1边界损失，正文没有采用常见的噪声预测MSE作为额外核心目标；不能把它讲成普通扩散生成训练。（PDF第5–6页）

式(3)仍包含由参数控制的随机项。只有相关噪声系数取零，DDIM更新才能严格称为确定性；初始加噪本身也需要固定随机种子。作者关于语义分离的解释受到可视化支持，但不构成不变表示的理论保证。

## 实验与关键结果

实验用AdamW、batch16、学习率0.001、默认3步去噪。AP在时间IoU阈值0.75/0.85/0.95下取平均，AR对1/5/10个候选取平均；这些都是时间定位指标，不是视频分类准确率。（PDF第6–7页）

| 协议 | ActionFormer AP | TADiff AP | ActionFormer AR | TADiff AR |
|---|---:|---:|---:|---:|
| 同生成器分布 | 70.67 | 75.05 | 74.31 | 77.15 |
| 未见Vidu生成器 | 77.82 | 83.64 | 83.31 | 87.92 |
| A→B跨生成器 | 67.18 | 69.63 | 72.14 | 74.91 |
| B→A跨生成器 | 37.14 | 40.89 | 51.03 | 52.56 |

表2–3（PDF第6–7页）。其中A含Wan、Scifi及VACE，B含FCVG与LTX，所以不能简单等同于“纯生成→纯编辑”。严格tIoU0.95下，同分布AP从46.79升至56.57，开放协议从57.08升至69.06。开放协议数值更高可能来自测试素材难度差异，不能推导现实开放世界更容易。

## 消融实验与证据强度

表4中，同分布基线AP70.67，只有加噪70.38，只有去噪73.52，两者结合75.05。仅加噪甚至略降，说明不能把改进全部归因于“噪声增强”；开放协议对应77.82、79.75、80.10、83.64。（PDF第7页）

图5还显示正文与曲线的细微差异：作者文字称3步最好，但同分布曲线3步75.05、4步75.18，开放协议3步83.64、4步83.99。应把3步理解为接近最优的成本选择，而不是严格数值最高。t-SNE与Fisher比值1.74→2.64提供表征变化的证据，仍不能证明对未来生成器普遍有效。（PDF第7–8页）

## 局限与讨论

跨生成器B→A的AP仍只有40.89，说明分布迁移没有解决。受控拼接、压缩和生成后处理是否形成捷径，需要额外测试。正文未充分说明同一原视频、人物或场景是否跨训练测试隔离；若存在近重复，评估可能偏乐观。真实未操纵负样本的误报、自然剪辑与恶意编辑的区分、全新生成器长期泛化都不应由当前结果代替。系统输出可作定位线索，不能直接作为对个人行为的事实判定。（PDF第3–8页）

## 复现提示

[作者项目页](https://activityforensics.github.io)可用于后续核查数据协议和代码。本轮未核查发布文件的许可证、下载条件、代码commit与补充实验，也未下载视频或运行模型。建议数据放在仓库外的`datasets/video-forensics/activityforensics/`，保留原视频ID、片段边界、生成器、分割规则与文件校验。复现时应先审计来源隔离，再核对特征骨干、采样步长、proposal后处理以及AP阈值；正文未明确的配置不能自行补全后宣称严格复现。（PDF第3–7页）

## 相关工作与阅读顺序

先读时间动作定位中ActionFormer的多尺度特征与边界回归，再读视频伪造检测的跨生成器评估。最后对照扩散去噪理解TADiff：它使用扩散思想正则化定位特征，最终产品是操纵活动时间段，而不是生成视频或还原原视频。结合数据协议阅读表2–3，比单看平均AP更能理解贡献边界。（PDF第2、5–7页）

## 来源与校验

- [CVF官方论文页](https://openaccess.thecvf.com/content/CVPR2026/html/Bao_ActivityForensics_A_Comprehensive_Benchmark_for_Localizing_Manipulated_Activity_in_Videos_CVPR_2026_paper.html) · [所读PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Bao_ActivityForensics_A_Comprehensive_Benchmark_for_Localizing_Manipulated_Activity_in_Videos_CVPR_2026_paper.pdf)。页码均为PDF页序。
- 所读版本：2026-10-22从CVF下载的开放接收稿；PDF SHA-256：`883815564464a047404a4f34572e8619f3223b45aa7fb36b447be256a9c005b3`。
- 阅读范围：正文、方法公式、实验与消融；补充材料、代码及权重未逐项核验。reviewed表示本地讲解自检，不表示独立同行评审或实验复现。
- 方法图与关键公式/表格已渲染核对，所引原图已单独检查；未对新文章进行浏览器交互验收。作者图示与本站原创素材权利分开记录。
