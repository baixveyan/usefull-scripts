# 4DEquine: Disentangling Motion and Appearance for 4D Equine Reconstruction from Monocular Video

核对日期：2026-10-20。以下实验均为作者报告；本地完成原文阅读与讲解自检，未复现实验。

## 一句话总结

4DEquine用共享VAREN模板把视频动作估计和单图静态外观分开，得到可随时间驱动的马科高斯avatar。

## 研究背景与动机

整段视频同时优化几何与外观成本高，也依赖较完整环视；普通视频常只拍动物一侧。作者利用短片外观近似不变的事实，让动作网络处理时序，让另一个前馈网络一次生成规范空间外观。[PDF1–2]

## 方法总览

![4DEquine 动作与外观双路径](../../../../site/figures/4dequine.svg)

原创重绘，依据Fig.2及§4。两条路径通过VAREN形状/姿态与LBS连接，不能把“单图外观”误读为从单图观测到所有真实表面。

AniMoFormer用空间+时间Transformer预测VAREN参数，再以图像关键点和mask后优化；EquineGS从代表图像与模板点特征生成高斯，绑定网格随动作变形。[PDF3–5]

## 核心创新与关键设计

VAREN有39维形状、38关节旋转，基网格13873顶点；细分到55486点作为高斯初始化。动作训练含参数、2D/3D关键点及跨帧平滑；后优化加姿态先验与mask。外观双流DSTG融合DINOv3图像特征及位置编码点，输出位移、四元数、尺度、颜色与透明度，以L1+LPIPS和mask训练。

VarenPoser从PFERD动作拟合及虚拟镜头渲染，1171段、512²、60FPS；VarenTex经ControlNet/UniTex生成150k多视图图像。两个“合成数据集”用途不同，也依赖已学习的真实动物先验。[PDF3–5]

## 实验与关键结果

第8页Table1：APT36K马子集30视频402帧，PCK@.05由AniMer44.5至61.8；AiM10视频453帧55.5→84.2；三维CD3.4只在合成VarenPoser测试，且Procrustes对齐，不能直接说实拍3D真值精度。

AiM马35视频，新视角/姿态PSNR15.66、SSIM.8364、LPIPS.1720；全优化GART16.19/.7819/.2308，PSNR更好但感知指标较差。斑马10视频本文15.54/.7828/.2000，GART15.21/.6752/.2287。第7页A100约11秒/帧，与GART固定15分钟/视频统计单位不同，不能直接算统一倍数提速。

## 消融实验与证据强度

第8页去后优化APT PCK37.7对完整61.8；去时间模块加速度143.2对128.6，说明时序有助平滑。外观去后优化LPIPS.2170，完整.1720；去DSTG为.1733，改善较小。少点数未细分PSNR15.76反高于15.66，但SSIM/LPIPS较差；不把单指标当完整质量结论。

## 局限与讨论

马科模板可能限制其他物种和特殊结构，单图不可见纹理来自先验。驴的定性例图用同一输入作GT，不能验证其真实新视角。基线输入帧数、是否用测试帧及优化预算不同；作者对GART改用VAREN及本文动作，仍需按各自协议公平解读。[PDF6–8]

原文还指出尾巴与鬃毛的物理运动、光照变化仍是困难情形，不能将演示中的外观保持理解为任意条件下都稳定。[PDF 8]

## 复现提示

记录VAREN授权、关键点与mask估计、16帧窗口拼接及后优化次数，单独统计动作、外观和渲染耗时。训练细节在未读补充材料，此处不提供一键成功命令。项目页见PDF1，未核验固定代码和数据发行许可，本地未运行权重。

## 相关工作与阅读顺序

先读VAREN、AniMer和LBS，再读GART与4D-Fauna。本文适合研究类别先验如何换取单视图完整性，也提醒评估时区分生成补全与真实观测恢复。

## 来源与校验

- [CVF 官方论文页](https://openaccess.thecvf.com/content/CVPR2026/html/Lyu_4DEquine_Disentangling_Motion_and_Appearance_for_4D_Equine_Reconstruction_from_CVPR_2026_paper.html) · [所读 PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Lyu_4DEquine_Disentangling_Motion_and_Appearance_for_4D_Equine_Reconstruction_from_CVPR_2026_paper.pdf)。页码均为该 PDF 的页序。
- 阅读范围：正文、公式与实验表；补充材料、上游代码与权重未逐项核验。许可证和固定代码 commit 尚未确认，不复制原文全文或数据。
- PDF SHA-256：`892e2c86b7f22a02877b2952c62d0a4e0710534073271694c232628d7163ccd0`；版本为本次下载的 CVF 接收稿，核对日期 2026-10-20。

- 视觉核对：渲染查看 PDF 第 8 页，检查关键实验表或方法相关证据；未将作者实验表述为本地复现。
