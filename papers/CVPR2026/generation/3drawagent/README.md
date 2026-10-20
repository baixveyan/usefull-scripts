# 3DrawAgent: Teaching LLM to Draw in 3D with Early Contrastive Experience

作者：Hongcan Xiao, Xinyue Xiao, Yilin Wang, Yue Zhang, Yonggang Qi。

分类：generation；交付形式：Markdown 中文论文讲解。

核对日期：2026-10-20。以下实验均为作者报告；本地完成原文阅读与讲解自检，未复现实验。

## 一句话总结

3DrawAgent把LLM输出的三维Bézier曲线渲染打分，从优劣样本中总结提示词经验，在不更新模型权重的情况下改善后续草图。

## 研究背景与动机

二维绘图智能体缺少深度和空间连续性；逐对象训练三维生成器成本高。作者改用冻结LLM和外部经验库，让生成、解析、多视图评价与经验更新形成循环，输出是曲线草图而非封闭实体网格（第1–2页）。

## 方法总览

给出坐标、数据结构和示例，LLM生成每条4个三维控制点；解析后从16个固定视角渲染。每题采5候选并按CLIP比较，LLM总结结构、连续性与格式差异，对经验库执行添加、删除、修改或保留；后续生成把经验加入上下文（第2–4页）。

## 核心创新与关键设计

三次Bézier为B(t)=Σ_{j=0}³C(3,j)(1−t)^{3−j}t^jP_j；评价r=平均_v cos(E_image(I_v),E_text(T))。经验更新E←Update(E,A_text)属于离散提示优化，不是标准GRPO参数梯度更新。所谓自我改进主要写入外部上下文，不能说冻结权重永久学会新的几何能力。

## 实验与关键结果

第4–5页采用DeepSeek-V3.2-Exp或Gemini2.5Pro API、RTX3090渲染512²×16视角；经验采样温度0.7，最终0.3。类别文本Gemini CLIP0.649/AES4.161，Dream3DVG0.660/4.150；精细文本0.669/4.175对0.670/4.174，不是全指标超越。图生3D CLIP0.873，3Doodle0.869，但AES4.255略低于4.264。

## 消融实验与证据强度

第6页无经验CLIP0.5735，2轮经验0.6643，继续3/4轮跌至0.6428/0.6416；更多迭代并不稳定提升。K10第2轮0.5612低于K5的0.6643。GT辅助首轮0.6648，无GT次轮0.6643相近；这不取消提示中格式示例的监督作用。200次单任务rollout有30次零分与500+冗余曲线问题。

## 局限与讨论

奖励与评测同属CLIP，可能偏向其审美或语义代理；不直接衡量拓扑、可制造性或真实深度。API服务版本、延迟、token及上下文经验长度影响可复现性；“单3090”不含远端LLM算力，不能推论本地低成本完整运行。

## 复现提示

先实现严格结构校验、数值范围及曲线数上限；模型给出的列表当数据解析，不能eval执行。保留16视角、经验库版本、筛选轮次及失败样本，检查是否用测试分数选最佳轮。此次未调用API、未执行第三方渲染代码，仓库与许可未核验。

## 相关工作与阅读顺序

先读SketchAgent、三次Bézier和CLIP多视图打分，再比较Diff3DS、3Doodle与训练自由提示优化。实用启发是保存可审查的经验和中间几何，而不是无限增加自我反馈轮数。

## 来源与校验

- 已渲染并目视核对 PDF 第6页关键表格/图；其余正文与公式通过原文文本核对。
- [CVF 官方论文页](https://openaccess.thecvf.com/content/CVPR2026/html/Xiao_3DrawAgent_Teaching_LLM_to_Draw_in_3D_with_Early_Contrastive_CVPR_2026_paper.html) · [所读 PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Xiao_3DrawAgent_Teaching_LLM_to_Draw_in_3D_with_Early_Contrastive_CVPR_2026_paper.pdf)。页码均为该 PDF 的页序。
- 阅读范围：正文、公式与实验表；补充材料、上游代码与权重未逐项核验。许可证和固定代码 commit 尚未确认，不复制原文全文或数据。
- PDF SHA-256：`ea6e7cab1677f9e20d5938e2eb6e875870392307bb720bd8132e91e40000753c`；版本为本次下载的 CVF 接收稿，核对日期 2026-10-20。
