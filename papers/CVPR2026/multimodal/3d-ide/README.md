# 3D-IDE: 3D Implicit Depth Emergent

作者：Chushan Zhang, Ruihan Lu, Jinguang Tong, Yikai Wang, Hongdong Li。

分类：multimodal；交付形式：Markdown 中文论文讲解。

核对日期：2026-10-20。以下实验均为作者报告；本地完成原文阅读与讲解自检，未复现实验。

## 一句话总结

把深度、跨视图与三维教师约束放在训练阶段，让单个RGB视频编码器学到几何信息，部署时移除辅助分支。

## 研究背景与动机

显式深度/位姿输入增加部署依赖，双编码器又增加参数与延迟。作者希望几何成为共享视觉token可解码的信息，避免测试阶段继续外接三维模型（第1–3页）。

## 方法总览

SigLIP编码RGB视频，接Qwen2-7B的LLaVA式架构。训练时轻量DPT样式validator预测深度和置信权重，另用已知相机约束相邻帧一致性，并与冻结三维模型的全局描述对齐；推理仅保留视觉与语言主干（第4–6页）。

## 核心创新与关键设计

总目标L=L_ce+L_geometry+L_cross-view+L_global。深度项为Σ̂加权的深度与梯度残差减αlogΣ̂，因此Σ̂更接近残差置信权重，不能直接按方差解释。局部项比较位姿warp后深度的L1，全局项1−cos(f_teacher,f_encoder)。弱validator旨在把学习压力留在编码器；互信息/涌现叙述属于设计解释，并非严格信息论保证。

## 实验与关键结果

第7页表2：ScanRefer Acc@0.25/0.5为60.9/54.5，去3D输入的Video-3D LLM基线53.7/47.8；Multi3DRefer F1为59.8/54.9。Scan2Cap CIDEr79.0低于VID-LLM81.5，非所有任务最优。32帧、8×H100、batch16，一轮约23小时。第8页VG-LLM8B与本文参数9.25B/8.06B、平均时间3.60/1.61秒，55.3%是该配置延迟下降。

## 消融实验与证据强度

第8页表3：仅全局监督ScanRefer56.9/50.8，加入从零训练validator59.8/53.3，再加跨视图60.9/54.5；预训练validator完整模型60.5/54.1，差距较小且无误差条。表3将ScanRefer列头写F1、Multi3DRef写Acc，与主表常用口径对调，应以任务和表2定义核查。几何对应Recall@2cm40.15→42.27，法向RMSE32.26→31.36。

## 局限与讨论

“零额外延迟”指辅助分支相对保留主干不进入测试，不是总推理零耗时。训练明确用深度GT、相机位姿及冻结三维教师，不能说无需几何监督。多数评估来自ScanNet，尚不证明开放环境、运动场景或任意尺度泛化。

## 复现提示

核查深度有效mask、置信项正值约束、帧采样、全局教师与场景坐标约定；validator学习率2×10⁻⁶，其他模块需对应基线配置。论文提供3D-IDE仓库地址，但未审查代码及权重许可，未本地运行。

## 相关工作与阅读顺序

先读Video-3D LLM与VG-LLM，再看特权信息训练、DPT深度读出及几何表征探测。将训练监督和部署输入分开，是理解本文贡献的关键。

## 来源与校验

- 已渲染并目视核对 PDF 第8页关键表格/图；其余正文与公式通过原文文本核对。
- [CVF 官方论文页](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_3D-IDE_3D_Implicit_Depth_Emergent_CVPR_2026_paper.html) · [所读 PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhang_3D-IDE_3D_Implicit_Depth_Emergent_CVPR_2026_paper.pdf)。页码均为该 PDF 的页序。
- 阅读范围：正文、公式与实验表；补充材料、上游代码与权重未逐项核验。许可证和固定代码 commit 尚未确认，不复制原文全文或数据。
- PDF SHA-256：`5df74903205e6983dc2c0164157517a5d7630a441898a947894c54c885486dce`；版本为本次下载的 CVF 接收稿，核对日期 2026-10-20。
