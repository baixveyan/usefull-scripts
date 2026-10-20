# 3D-Fixer: Coarse-to-Fine In-place Completion for 3D Scenes from a Single Image

作者：Ze-Xin Yin, Liu Liu, Xinjie Wang, Wei Sui, Zhizhong Su, Jian Yang, Jin Xie。

分类：generation；交付形式：Markdown 中文论文讲解。

核对日期：2026-10-20。以下实验均为作者报告；本地完成原文阅读与讲解自检，未复现实验。

## 一句话总结

3D-Fixer在单图估计的局部几何原位置补全物体，通过粗到细边界预测减少独立生成后再配准造成的布局偏差。

## 研究背景与动机

直接生成整场景易受训练域限制；逐物体生成再优化位姿成本高且容易错配。可见点云虽不完整，却已含位置、尺度和朝向线索，适合充当生成的空间锚点（第1–3页）。

## 方法总览

实例分割与单图几何估计提供碎片点云；TRELLIS先验的新增条件分支结合二维与三维上下文，先在宽松盒内补全轮廓，再在预测精细盒内生成细节，最后进行遮挡感知纹理化。各物体可并行生成，不再显式逐个搜索6DoF配准（第4–5页）。

## 核心创新与关键设计

初始扩展盒以可见点云AABB中心为中心、边长取最大可见边长4倍；它是工程范围假设，不保证任意严重遮挡都覆盖完整物体。ORFA在相同噪声与时间步下，令学生遮挡条件中间特征接近教师干净图特征，L_AL=−E[平均sim(h_s,h)]，与flow matching共同训练。GAFP将MoGe v2图像特征投影到可见体素（第5页）。

## 实验与关键结果

ARSG-110K由180k+资产、110k+场景、每景30视角组成，约3M图，提供实例mask、相机和物体网格。第6页MIDI测试：场景CD0.069、F-score78.67、对象CD0.032，对比MIDI0.080/50.19/0.103；盒IoU0.492低于MIDI0.518。RTX5090推理30秒对MIDI40秒。ScanNet子集场景CD0.130对MIDI0.163，GT为MetaScenes估计，不是完美实测资产。

## 消融实验与证据强度

第8页12层加入粗到细后场景CD0.276→0.266，再加对齐0.264；对象CD0.271→0.329先变差，加对齐后0.283。18层场景0.252优于12层，但作者选择效率与完整性折中。混合几何源对象CD0.329→0.262，场景CD0.266→0.272却略差，说明收益有口径差异。

## 局限与讨论

单图不可见部分仍是生成猜测，受分割和初始几何错误影响。实拍小样本验证，正文对15场景/15视图表述不同；自建测试仅选可见度最高5物体计算定量，全部物体主要用于可视化，不能混同。资产素材许可与实际公开情况尚待核验。

## 复现提示

需分别保存mask、碎片点云、坐标归一化、两阶段边界及纹理路径。训练配置在补充材料，未读部分不推断。论文称代码数据将公开，不能据此写成已下载可用；此次未运行其代码，也未镜像ARSG数据。

## 相关工作与阅读顺序

先读TRELLIS与MoGe，再比较MIDI和Gen3DSR。重点看“在已有场景坐标补全”相对“生成规范坐标资产再配准”的差别。

## 来源与校验

- 已渲染并目视核对 PDF 第6页关键表格/图；其余正文与公式通过原文文本核对。
- [CVF 官方论文页](https://openaccess.thecvf.com/content/CVPR2026/html/Yin_3D-Fixer_Coarse-to-Fine_In-place_Completion_for_3D_Scenes_from_a_Single_CVPR_2026_paper.html) · [所读 PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Yin_3D-Fixer_Coarse-to-Fine_In-place_Completion_for_3D_Scenes_from_a_Single_CVPR_2026_paper.pdf)。页码均为该 PDF 的页序。
- 阅读范围：正文、公式与实验表；补充材料、上游代码与权重未逐项核验。许可证和固定代码 commit 尚未确认，不复制原文全文或数据。
- PDF SHA-256：`5d4bd59de94147d24712a58229019046ef08cb721dfda06506d2b1c0228a461e`；版本为本次下载的 CVF 接收稿，核对日期 2026-10-20。
