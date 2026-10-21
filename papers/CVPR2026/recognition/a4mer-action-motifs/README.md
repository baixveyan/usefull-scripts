# Action Motifs: Self-Supervised Hierarchical Representation of Human Body Movements

核对日期：2026-10-21。实验数值均为作者报告；本地完成原文阅读与讲解自检，未复现实验。

## 一句话总结

A4Mer先把3D人体运动编码为变长Action Atoms，再发现常见组合形成Action Motifs，用层级掩码预测学习可复用运动表示。

## 研究背景与动机

逐帧表示太细、固定短片可能切断有意义动作、整段视频又会掩盖可复用片段。作者把原子动作与重复组合对应到“词”和“短语”，希望同类运动在不同人、不同任务里仍有接近表示。[§1，PDF1–2]

自监督指表示预训练不需人工动作标签；输入仍需要3D姿态，下游识别也使用动作标签。不是从任意RGB视频直接无标注学会全部行为。

## 方法总览

![原文Fig.2：方法框架](../../../../site/figures/a4mer-action-motifs-original-fig2.png)

原论文Fig.2，PDF第4页。仅裁切相关图示，保留图内科学标签；著作权属于原作者，用于本篇方法分析，不并入本站原创图授权。[来源与作者](https://openaccess.thecvf.com/content/CVPR2026/html/Kinoshita_Action_Motifs_Self-Supervised_Hierarchical_Representation_of_Human_Body_Movements_CVPR_2026_paper.html) · [PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Kinoshita_Action_Motifs_Self-Supervised_Hierarchical_Representation_of_Human_Body_Movements_CVPR_2026_paper.pdf)。点击可打开高清图。

运动学轨迹偏离线性外推的位置先定义原子边界；Encoder用段内注意力和交叉注意力把变长段压成一个token，LatentFormer建模段间关系。第一层训练后，用512类k-means离散原子、GSP挖频繁序列，再动态规划选择以最少模式覆盖序列的无重叠分段，得到第二层Motifs。[Fig.2、§3.1–3.2，PDF3–4]

训练不是全程端到端自动学边界：包含运动学分段、聚类和显式模式挖掘。推理用最近邻分配已有簇；未来运动预测还要同时估计下个token和其持续长度。[§3.4，PDF5]

## 核心创新与关键设计

目标分支看完整输入、停止梯度并以EMA更新；预测分支只看可见段，学习补全被遮挡token：
\[Z=f_{\bar\theta}(X),\quad\widehat Z=g_\phi(M,f_\theta(X_{vis})),\qquad \mathcal L_{base}=\sum_{k\in\mathcal K}\operatorname{SL1}(\widehat z_k-\operatorname{sg}(z_k)).\]
层级联合训练时，遮掉Motif也遮掉其全部原子，防止下层泄漏目标。[式1–2，PDF5]

作者再将掩码位置表示拆成均值全局项和偏差局部项，对局部损失加大权重；动态系数λ_k=sg(L_k^l/L^g)，α=0.05。分母为零时的稳定处理需源码核实，停止梯度也意味着不能简单把λ_kL^g的梯度当作L_k^l。[式3–6]

## 实验与关键结果

AMD采集50人、21–69岁、24相机、14.2小时30fps日常活动，利用脚载相机与天花板/桌底ChArUco标记约束遮挡脚部SMPL拟合。它提供多视角视频与拟合标注，不是完全无误差的真实3D测量。[§4，PDF5–6]

模型实验降到5fps，输入30秒；预测未来3秒，插值缺失4–8秒，MPJPE单位mm。[§5，PDF7]

| 作者报告，Table2 | A4Mer | 参考对照 |
| --- | --- | --- |
| AMD预测 / HiK迁移预测MPJPE↓ | 150 / 120 | BehaveMAE167 / 288 |
| AMD插值 / HiK迁移插值MPJPE↓ | 126 / 110 | MacDiff186 / 110 |
| HiK k-NN top1 / top3 | 31.7 / 59.0% | USDRL31.1 / 43.0% |
| HiK训练识别头 | 38.1% | BehaveMAE35.6% |

**表格有冲突**：Table3完整模型却将k-NN/head写成38.1/59.0；Table2的MotionBERT top1/top3为1.77/0.35也不符合通常top-k包含关系。上述按Table2标注列记录，不擅自交换或修正数字。[PDF7] HiK原多标签被合并成自定义粗粒度单标签，不能与原协议排行榜直接比较。

## 消融实验与证据强度

Table3中去分解的预测222mm、仅局部254、局部加未调权全局188，完整150；取消段内注意力212。逐帧或固定10帧片段的预测309/208，支持变长分段对预测的作用。[PDF7–8]

JEPA换成BERT式目标后插值112mm，优于完整126mm，说明优势依任务而异；不能照摘要写所有任务全部严格最好。完整模型平均Motif10.6帧是5fps条件下约2.12秒，不是原30fps下0.35秒。

## 局限与讨论

发现高频组合不保证就是人类语义单元，少见动作可能被频繁模式掩盖。识别所谓零样本迁移仍需带标签参考token做k-NN，不能理解为无需任何动作标签的类别命名。

脚部约束的mask mIoU仅0.906→0.910，评估限于可见全身的10000帧，并非直接量化严重遮挡下关节3D误差。主文把SmoothL1空间称为Manhattan-like也不能推导出普通欧氏k-means自动最优；分段阈值和GSP支持度等需补充材料核查。

## 复现提示

从[作者实验室入口](https://vision.ist.i.kyoto-u.ac.jp/)查找A4Mer/AMD正式发布信息；本文未核验固定代码commit、许可证、数据下载条件和补充材料。建议 `datasets/human-motion/amd/`，原视频与身体扫描、SMPL依赖各按许可存于仓库外。

复现先固定姿态坐标、降采样、人物隔离与HiK标签合并表，再记录聚类/模式字典、掩码规则和预测长度头。表2/3识别列冲突解决前不要声称精确复现识别成绩；本地仅做原文阅读与图表核对。

## 相关工作与阅读顺序

先了解JEPA/EMA目标与变长序列聚合，再读GSP和动态规划覆盖，最后看AMD的标注来源与Table2/3。将表示预训练、带标签识别和未来姿态生成三个阶段分开理解。

## 来源与校验

- [CVF官方论文页](https://openaccess.thecvf.com/content/CVPR2026/html/Kinoshita_Action_Motifs_Self-Supervised_Hierarchical_Representation_of_Human_Body_Movements_CVPR_2026_paper.html) · [所读PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Kinoshita_Action_Motifs_Self-Supervised_Hierarchical_Representation_of_Human_Body_Movements_CVPR_2026_paper.pdf)。页码均为PDF页序。
- 所读版本：2026-10-21从CVF下载的开放接收稿；PDF SHA-256：`447cb0f3770e0bd826451ec2e85c2c5e73e8d1cc416c2cea174e94a22fce41b6`。
- 阅读范围：正文、方法公式、实验与消融；补充材料、代码及权重未逐项核验。reviewed表示本地讲解自检，不表示独立同行评审或实验复现。
- 方法图与关键公式/表格已渲染核对，所引原图已单独检查；未对新文章进行浏览器交互验收。作者图示与本站原创素材权利分开记录。
