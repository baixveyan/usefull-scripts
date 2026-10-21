# ActiveGrasp: Information-Guided Active Grasping with Calibrated Energy-based Model

核对日期：2026-10-22。实验数值均为作者报告；本地完成原文阅读与讲解自检，未复现实验。

## 一句话总结

ActiveGrasp以校准能量模型估计抓取成功的不确定性，从候选相机视角中选择预计最能改善抓取判断的观测。

## 研究背景与动机

杂乱场景中多看见表面不一定能抓住目标，只看2D/3D抓取热图也丢失姿态方向。作者在SE(3)位姿上建模成功与失败，用任务相关信息指导下一视角。[§1–2，PDF1–2]

目标是把有限观测用于抓取，不是全面重建；较低不确定性不自动保证真实执行成功。

## 方法总览

![原文Fig.2：方法框架](../../../../site/figures/activegrasp-original-fig2.png)

原论文Fig.2，PDF第3页。仅裁切相关图示，保留图内科学标签；著作权属于原作者，用于本篇方法分析，不并入本站原创图授权。[来源与作者](https://openaccess.thecvf.com/content/CVPR2026/html/Lei_ActiveGrasp_Information-Guided_Active_Grasping_with_Calibrated_Energy-based_Model_CVPR_2026_paper.html) · [PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Lei_ActiveGrasp_Information-Guided_Active_Grasping_with_Calibrated_Energy-based_Model_CVPR_2026_paper.pdf)。点击可打开高清图。

标定RGBD和目标分割初始化3DGS，每加一视角优化1000步。模型输入前景/背景各512点、抓手锚点和噪声尺度，输出成功/失败logit；训练联合成功与失败score matching、AP排序、SDF及可学习温度。[Fig.2、§3–4.1，PDF3–6]

距目标0.3–0.5m球面Fibonacci采128候选，按指标选观测，预算用完再生成抓取、规划检查和执行。使用深度、分割和机器人正运动学，不是无需标定单目系统。

## 核心创新与关键设计

定义成功事件的Bernoulli熵平均：
\[\eta(w)=\mathbb E_{p(g|w)}[-s(g,w)\log s(g,w)-(1-s(g,w))\log(1-s(g,w))].\]
它不是抓取位姿密度的Shannon熵。场景MAP附近高斯近似、二阶展开给候选评分：
\[I_x\approx\tfrac12\operatorname{tr}[\nabla_w^2\eta(w^*)(H_D^{-1}-H_{D+x}^{-1})].\]
H用Gauss-Newton/对角近似，η的曲率再用梯度外积加正则，所以是多重近似指标，不是已证无偏精确互信息。[式9–16，PDF4–5]

式19的p_S=e^{a_S}/(e^{a_S}+e^{a_F}+2)，p_F同分母，两者和<1，不按普通二类softmax直接互补。式17末项印为负E[h]E[∇E]，而归一化e^{-E}/Z求导通常有正的归一化补偿项；未读附录/源码，保留疑点，不掩盖符号差异。[PDF5]

## 实验与关键结果

Acronym训练200K步、batch24、Adam lr1e-3，AP仅接近无噪声样本。PyBullet仿真每场景10个YCB物体，20场景×5目标×4重复=400试验，初始2视角加2；实机Kinova7DoF+RealSense初始4加2，三场景各10次。[§4，PDF6–8]

| 作者报告，仿真400次 | 成功率 | ECE↓ |
| --- | --- | --- |
| 校准模型+随机2新视角 | 74.25% | 0.06 |
| 校准模型+ActiveNGF | 74.00% | 0.06 |
| 校准模型+ActiveGrasp | 79.00% | 0.02 |

来源Table1，PDF6。同抓取模型增加4.75pp较能隔离选视角收益；不同抓取骨干的差距不能全算给NBV。随机多8视角报76.50%，但该行计数合计402而非400，其他部分行也有计数/百分比冲突，不据此重算精确统计。

实机本文9/10、8/10、9/10合计26/30，样本小，不能认为普遍成功率86.7%已充分确定。[Table2，PDF7]

## 消融实验与证据强度

Acronym原模型AP34.69、ECE0.17，完整AP87.84、ECE0.03；Bullet ECE0.35→0.05。模块间几何距离有折中，并非每次添加都提升所有指标；这里0.05与主表0.02是不同实验。[Table3，PDF8]

AP衡量排序，不是严格概率校准的适当评分规则；低ECE是经验表现，不构成跨分布成功保证。选视角9.61±0.09秒，比ACE18.24快、比FisherRF7.43慢，未含全程移动、3DGS更新及执行，不能称整体实时。[§4.5.2]

## 局限与讨论

材料、摩擦和遮挡变化可能破坏校准；局部高斯、对角曲率和外积忽略多峰后验及高斯点关联，这是作者承认的边界。[§5，PDF8]

低条件熵也可能表示确信失败，是否存在好抓法还依赖采样与排序。近似选样、AP训练和经验ECE不证明无偏或执行保证，公式归一化和梯度符号需先查明。

## 复现提示

正文只承诺公开源码，未给可确认专用仓库，不写成已经下载验证。以CVF官方页追踪发布，commit/许可证待核。建议 `experiments/robotics/activegrasp/`，Acronym/YCB数据与网格按许可存仓库外。

先检查概率归一化、式17梯度、视角可达和400次计数，再做同模型同预算比较。本地未执行模型、仿真或机器人，结果均为作者报告。

## 相关工作与阅读顺序

先读SE(3)能量模型与抓取成功校准，再区分位姿熵和成功事件条件熵。最后看高斯后验/曲率近似与Table1同模型对照，避免将信息论动机直接当成已证最优视角。

## 来源与校验

- [CVF官方论文页](https://openaccess.thecvf.com/content/CVPR2026/html/Lei_ActiveGrasp_Information-Guided_Active_Grasping_with_Calibrated_Energy-based_Model_CVPR_2026_paper.html) · [所读PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Lei_ActiveGrasp_Information-Guided_Active_Grasping_with_Calibrated_Energy-based_Model_CVPR_2026_paper.pdf)。页码均为PDF页序。
- 所读版本：2026-10-21从CVF下载的开放接收稿；PDF SHA-256：`9af4fc55e689f9050777f76cd41bdfe863d9e84165cbbd76f42aed7e0d1204df`。
- 阅读范围：正文、方法公式、实验与消融；补充材料、代码及权重未逐项核验。reviewed表示本地讲解自检，不表示独立同行评审或实验复现。
- 方法图与关键公式/表格已渲染核对，所引原图已单独检查；未对新文章进行浏览器交互验收。作者图示与本站原创素材权利分开记录。
