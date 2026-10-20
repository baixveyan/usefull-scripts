"""Original explanatory SVGs, redrawn from method understanding; no paper artwork copied."""
from pathlib import Path
from html import escape

OUT=Path(__file__).parent/'figures'
OUT.mkdir(exist_ok=True)
C={'green':('#e5f3ec','#237958'),'blue':('#e7effb','#3b6fba'),'orange':('#fff1df','#aa6b29'),'purple':('#f0eafa','#7753a8'),'red':('#fcebea','#b45853')}


def text(x,y,value,size=16,color='#253d3c',weight=400):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}">{escape(value)}</text>'


def card(x,y,w,h,title,lines,color='green',badge=None):
    fill,ink=C[color]
    s=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{ink}" stroke-opacity=".25"/>'
    s+=text(x+20,y+32,title,18,ink,650)
    for i,line in enumerate(lines):s+=text(x+20,y+61+i*25,line,14)
    if badge:s+=text(x+20,y+h-17,badge,11,ink,600)
    return s


def arrow(x1,y1,x2,y2,label='',dashed=False):
    dash='stroke-dasharray="7 6"' if dashed else ''
    s=f'<path d="M{x1} {y1} L{x2} {y2}" stroke="#6e8a83" stroke-width="2" fill="none" marker-end="url(#arrow)" {dash}/>'
    if label:s+=text((x1+x2)/2+5,(y1+y2)/2-9,label,11,'#627b73')
    return s


def save(name,title,subtitle,content,foot):
    s=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 660" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(subtitle)}</desc><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10" fill="#6e8a83"/></marker><pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="#dde6dd"/></pattern></defs><rect width="1200" height="660" rx="20" fill="#fafcf8"/><rect y="110" width="1200" height="490" fill="url(#dots)"/><g font-family="Inter,Segoe UI,Microsoft YaHei,sans-serif">{text(40,38,'PAPER ATLAS / METHOD EXPLAINED',11,'#688279',650)}{text(40,75,title,28,'#1f3d34',650)}{text(40,103,subtitle,13,'#71867e')}{content}<path d="M40 606H1160" stroke="#dae5dc"/>{text(40,631,foot,12,'#71867e')}{text(1000,631,'原创概念重绘 · 非原图',11,'#71867e')}</g></svg>'''
    (OUT/(name+'.svg')).write_text(s,encoding='utf-8')


# TokenGS: image evidence and learnable query streams merge at cross attention.
s=card(40,155,235,145,'多视图观测',['图像 patch 特征','相机参数 → Plücker 射线'],'blue','输入仍依赖相机标定')
s+=card(40,355,235,145,'可学习高斯 tokens',['Nₜ 个场景槽位','数量独立于输入像素'],'purple','不是一 token 对应一高斯')
s+=card(365,155,250,145,'图像编码器',['跨视图 Transformer','组织共享图像证据'],'blue')
s+=card(365,355,250,145,'解码器',['tokens 读取图像 K / V','交叉注意力 + 自注意力'],'purple')
s+=card(725,260,205,145,'属性解码',['每 token → 64 高斯','位置 / 颜色 / 尺度等'],'green','M = 64 × Nₜ')
s+=arrow(275,225,365,225)+arrow(275,425,365,425)+arrow(490,300,490,355,'K / V')+arrow(615,425,725,350)
s+=arrow(930,330,998,330)
for i in range(5):
    for j in range(6):
        s+=f'<ellipse cx="{1015+j*24}" cy="{270+i*24}" rx="12" ry="6" transform="rotate({i*13-25} {1015+j*24} {270+i*24})" fill="{["#73b69c","#a8c6e2","#d5b8e8"][j%3]}" opacity=".8"/>'
s+=text(1005,420,'可微高斯渲染',15)+arrow(825,405,825,545)+arrow(825,545,155,545,'测试时仅调 token；权重固定',True)+arrow(155,545,155,500,'',True)
save('tokengs','TokenGS：把表示预算交给 tokens','两路输入、一个场景表示：图像提供证据，tokens 负责组织高斯。',s,'依据原论文 Fig.2 / §3 重绘；省略层重复、动态分支与完整损失。')

# 4DPM: temporal primitive persistence and explicit coordinate transforms.
s=''
for i,t in enumerate(['t = 0','t = 1','t = 2']):
    x=40+i*290;s+=card(x,155,235,120,'局部观测 '+t,['π³ 点图 + SAM2 分区','仅包含当时可见的表面'],'blue')
    for j in range(3):s+=f'<rect x="{x+20+j*55}" y="300" width="42" height="28" rx="5" fill="{["#79bca1","#9fbbe5","#c9ace5"][j]}"/>'
    if i<2:s+=arrow(x+235,215,x+290,215,'跟踪')
s+=card(930,155,230,175,'共享物体坐标',['稠密 2D 对应 → 3D 配对','Huber + Gauss–Newton','一段 primitive 一个 SE(3)'],'purple','把不同时间的碎片粘合')
s+=arrow(855,215,930,215)
s+=card(40,390,370,150,'时间重映射',['T(p → q) = T(q)⁻¹ T(p)','所有已见表面移到目标时间 q','得到完整、可重放的场景'],'green')
s+=card(490,390,360,150,'暂时不可见的物体',['包围盒接触 + 速度相似','建立父子运动组，支持传递关联','例如：抽屉关上，内部物体随动'],'orange','运动延续基于假设，而非重新观测')
s+=arrow(1045,330,1045,465)+arrow(1045,465,850,465)+arrow(490,465,410,465)
save('4dpm','4DPM：把跨时间的几何碎片粘起来','持久性意味着保留曾经见过的表面，而不只是重建当前帧。',s,'依据原论文 Fig.2 / §3.4–3.6 重绘；刚性分块与运动组假设必须成立。')

# 4D-RGPT: teacher/student training branches and removable heads.
s=card(40,150,210,145,'视频 + 时间戳',['采样帧与区域提示','视觉特征加入 TPE'],'blue')
s+=card(330,150,300,145,'学生：4D-RGPT',['视觉编码 → projector → LLM','生成回答；隐藏态送训练读出'],'green','推理保留此主干与 TPE')
s+=card(730,150,200,145,'训练期读出',['MLP → 4D latent','冻结模态 decoder'],'orange','部署时移除')
s+=card(330,400,300,130,'冻结教师：L4P',['统一 4D 表征','深度 / 光流 / 运动 / 相机射线'],'purple')
s+=card(730,400,200,130,'教师目标',['latent features','explicit signals'],'purple')
s+=card(1000,270,160,150,'P4D 约束',['latent 对齐','signal 对齐','加上 SFT'],'red')
s+=arrow(250,222,330,222)+arrow(630,222,730,222)+arrow(250,250,330,450,'同一视频')+arrow(630,465,730,465)+arrow(930,222,1000,300,'学生')+arrow(930,465,1000,390,'教师')+arrow(1065,270,1065,120,'训练梯度',True)+arrow(1065,120,480,120,'',True)
save('4d-rgpt','4D-RGPT：教师在训练时教，学生在部署时答','双重蒸馏把低层时空感知与语言问答连接；额外教师不进入推理链路。',s,'依据原论文 Fig.2 / §4 重绘；四类显式信号与真实时间戳不可混为文本标签。')

# 4DEquine: two streams share VAREN; geometry and static appearance are distinct.
s=card(40,150,210,140,'单目视频',['连续 16 帧窗口','长视频滑窗推进'],'blue')
s+=card(330,150,360,140,'AniMoFormer：动作',['空间 → 时间 Transformer','VAREN 姿态 / 形状 / 相机','后优化：关键点 + mask 对齐'],'blue')
s+=card(40,395,210,140,'一张代表性图像',['提取静态外观','不需要完整环视'],'purple')
s+=card(330,395,360,140,'EquineGS：外观',['DINOv3 图像 + 模板点特征','双流 DSTG → 高斯属性','55,486 个模板绑定高斯'],'purple')
s+=card(805,265,350,160,'VAREN 桥梁 → 可动画 avatar',['动作参数驱动模板与 LBS','规范空间高斯变形到各帧','渲染新姿态 / 视角'],'green','不可见表面来自学习先验')
s+=arrow(250,220,330,220)+arrow(250,465,330,465)+arrow(690,220,805,305,'动态几何')+arrow(690,465,805,385,'静态外观')
save('4dequine','4DEquine：动作随时间变化，外观只重建一次','两条网络以同一个马科参数模板相接；“前馈”并未取消几何后优化。',s,'依据原论文 Fig.2 / §4 重绘；VarenPoser 教动作，VarenTex 教多视图外观。')

# True motion tracking: same 3D path, moving vs fixed cameras.
s=card(40,155,290,135,'同一物体三维轨迹',['世界空间 X(t)','相机外参随时间 T(t) 变化'],'green')
s+=card(455,145,345,145,'常规图像轨迹 P₂D',['p(t) = Π(K, T(t), X(t))','投影相机也在移动','物体运动与相机运动纠缠'],'blue')
s+=card(455,380,345,145,'True-motion 轨迹 M₂D',['m(t) = Π(K, T(tq), X(t))','固定参考时刻 tq 的相机','背景静止，物体轨迹更直观'],'purple')
s+=arrow(330,205,455,205)+arrow(330,245,455,435)
for y,col in [(165,'#3b6fba'),(400,'#7753a8')]:
    s+=f'<rect x="895" y="{y}" width="255" height="120" rx="8" fill="#fff" stroke="#d5dfd7"/><path d="M915 {y+85} L1130 {y+85}" stroke="#cad5cf"/>'
    for i in range(5):
        cx=925+i*43;cy=y+70-(i*9 if y==400 else -i*5);s+=f'<circle cx="{cx}" cy="{cy}" r="{4+i}" fill="{col}" opacity="{.35+i*.13}"/>'
    s+=arrow(800,y+55,895,y+55)
s+=text(45,560,'4DP-QA 以可解释的 QA 模板生成监督；输出坐标并非完整、唯一的世界三维重建。',16)
save('4dp-qa','4DP-QA：固定相机，才能看清“真正的运动”','同一条世界轨迹可以有两种二维投影；区别只在参考相机是否随时间变化。',s,'依据原论文 Fig.2 / 式1–2 重绘；两种轨迹互补，不可用光流直接替代固定参考轨迹。')

# 4DSurf: geometric vs motion SDF flow agree; overlap passes information.
s=card(40,150,235,145,'分段规范高斯',['多视角 RGB + 前景 mask','2D 高斯 / canonical shape'],'blue')
s+=card(355,135,325,145,'运动侧：速度场 GVF',['预测线速度 v / 角速度 ω','由局部刚性运动推导 SDF flow','f = −(ω × Rx + v) · n'],'purple')
s+=card(355,340,325,145,'几何侧：渲染深度',['深度图作为伪表面','估计 signed-distance 随时间变化','f̃ = ∂(D − d) / ∂t'],'green')
s+=card(820,235,330,145,'表面演化一致性',['Lflow = Σ |f − f̃|','加颜色 / 法向 / 深度 / mask 损失','约束表面变化与运动一致'],'red')
s+=arrow(275,205,355,205)+arrow(275,255,355,410)+arrow(680,205,820,280)+arrow(680,410,820,335)
s+=text(45,550,'段 1',13)+text(385,550,'共享虚拟时间 → 初始化下一段',13)+text(925,550,'段 2；可用 LoRA 调运动场',13)
s+='<path d="M100 560H340 M700 560H900" stroke="#6e8a83" stroke-width="3"/>'
save('4dsurf','4DSurf：让“怎么动”和“表面怎么变”互相校验','重叠分段缓解大形变；连续性来自约束和初始化传递，不是对任意形变的保证。',s,'依据原论文 Fig.2 / §4.1–4.3 重绘；深度仅近似 SDF，LoRA 只压缩运动场增量。')
print('Wrote original method figures')
# Benchmark: four complementary evaluation branches.
s=card(40,190,215,150,'输入条件与生成视频',['文本 / 图像 / 视频','统一条件文字描述'],'blue')
s+=card(350,140,350,150,'物理与条件问答',['按语义选择相关维度','生成问题 → 预测 / 参考答案','物理分支：先字幕，再 LLM 判断'],'purple')
s+=card(350,350,350,155,'视觉与几何指标',['感知：质量 / 美学 / 纹理','一致性：重投影 / 光流 / 风格','静态 3D 只评价适用维度'],'green')
s+=card(820,240,330,185,'多维报告与人工对照',['不是单一“物理正确”证明','保留条件类型和子指标','检查评委偏差与字幕遗漏'],'orange')
s+=arrow(255,255,350,215)+arrow(255,285,350,420)+arrow(700,215,820,285)+arrow(700,425,820,380)
s+=text(45,560,'Sphy = 正确回答数 / 问题总数；得分依赖问题、参考答案与评委。',16)
save('4dworldbench','4DWorldBench：精美之外，还要检查什么？','四个维度互补：感知质量、条件对齐、物理合理性、时空一致性。',s,'依据原论文 Fig.1 / Fig.5 / §4 重绘；未展开全部评估器和提示词。')
# 1bit sensing.
s=card(40,180,235,160,'模拟强度 X(t)',['每个时刻保留一条强度约束','全帧共享阈值 T(t)','阈值在时间上非平滑变化'],'blue')
s+=card(365,180,230,160,'比较器 → 二值 M',['M = H(X − T)','每像素每帧 1 bit','主要实验从已有视频模拟'],'purple')
s+=card(690,180,230,160,'恢复网络',['已知阈值参与输入缩放','10 阈值重复 → 20 帧窗口','L1 训练 + 时间先验'],'green')
s+=arrow(275,255,365,255)+arrow(595,255,690,255)+arrow(920,255,975,255)
s+=text(1000,230,'高位深',18)+text(1000,260,'视频估计',18)+text(1000,295,'并非唯一解',13)
for i,v in enumerate([.1,.7,.3,.9,.2,.8,.4,.95,.05,.6]):
 x=90+i*90;y=535-v*130
 s+=f'<circle cx="{x}" cy="{y}" r="7" fill="#7753a8"/>'
 if i:s+=f'<path d="M{x-90} {535-[.1,.7,.3,.9,.2,.8,.4,.95,.05,.6][i-1]*130} L{x} {y}" stroke="#bda7d6" fill="none"/>'
s+=text(45,575,'阈值序列示意（非论文实际数值）；跨帧运动过大会降低可恢复性。',15)
save('single-bit-video','1-bit 视频：把位深预算移到时间与计算中','前端数据减少，后端计算增加；不能据此推断整机无损压缩或实时帧率。',s,'依据原论文 Fig.1 / §3–4 重绘；省略网络层与硬件电路。')
# Debiasing.
s=card(40,155,250,145,'群体提示与变体',['围绕同一内容构造','锚点 + 变体 → 球面均值','得到群体原型 p₁, p₂, …'],'blue')
s+=card(390,155,300,145,'属性差子空间 A',['span{p₂ − p₁, p₃ − p₁, …}','保留共同内容方向','原型定义影响去偏含义'],'purple')
s+=arrow(290,225,390,225)
s+=card(40,380,250,145,'原图像 / 文字嵌入 e',['分类与检索：两端处理','生成：只处理文本端'],'blue')
s+=card(390,380,300,145,'正交分解与折中',['e = e∥ + e⊥','沿二维曲线选择 u(α)','减少属性泄漏，控制表示变化'],'green')
s+=arrow(290,455,390,455)+arrow(540,300,540,380)
s+=card(825,270,320,180,'任务继续使用 u',['公平：对群体原型相似度','效用界：嵌入余弦变化','不是 F1 / Recall 不下降保证'],'orange')
s+=arrow(690,455,825,385)+text(45,575,'几何折中不等于现实公平的完整定义；附录证明与闭式公式仍需实现复核。',16)
save('closed-form-vlm-debias','VLM 去偏：分离属性变化，保留共同内容','先定义属性子空间，再讨论公平替代量与效用；不把模型标签当作个人身份。',s,'依据原论文 Fig.1–3 / §3–4 重绘；图为概念解释，非定理证明。')
# Noise + filtering.
s=card(40,190,220,145,'输入图像 x',['干净样本或对抗样本','统一输入尺度与范数预算'],'blue')
s+=card(360,190,240,145,'独立高斯噪声',['ε ~ N(0, σ²I)','使攻击需覆盖随机邻域','训练和推理均加入'],'purple')
s+=card(700,190,245,145,'重复双边滤波',['空间邻近 + 强度相近','平滑扰动并保留边缘','训练 / 推理 K 可不同'],'green')
s+=arrow(260,260,360,260)+arrow(600,260,700,260)+arrow(945,260,1020,260)
s+=text(1005,225,'CNN',22)+text(1005,295,'类别',18)
s+=card(150,420,400,125,'训练：适应预处理分布',['基础 CNN；或再结合 TRADES 与合成数据','不是仅给冻结分类器套一个滤镜'],'blue')
s+=card(650,420,400,125,'评价：攻击必须考虑预处理',['普通攻击 + EoT + BPDA / TABPDA','同时报告干净精度、鲁棒精度和总成本'],'orange')
save('noise-bilateral','先噪声，再滤波：互补收益也需要严格攻击验证','默认顺序不交换；随机性与梯度遮蔽可能让普通攻击高估鲁棒性。',s,'依据原论文 §3–5 重绘；理想几何分析不等于实际模型认证鲁棒性。')
# Cross-view grasp.
s=card(40,155,235,145,'主视角 + 辅助视角',['RGB-D → 各自点云特征','共享 ResUNet14','需要已知相对位姿'],'blue')
s+=card(355,155,270,145,'种子与圆柱邻域',['预测抓取种子 / 接近方向','两视角收集局部点','按坐标与特征寻找对应'],'purple')
s+=card(735,155,300,145,'任务相关后融合',['圆柱坐标位置编码','局部自注意力 ↔ 种子交叉注意力','保留原视角和重叠区域'],'green')
s+=arrow(275,225,355,225)+arrow(625,225,735,225)
s+=card(40,395,390,140,'仅训练：跨视角对比约束',['同位置点 → 特征接近','同物体不同抓取方向 → 特征分离','仍需有监督抓取标签'],'orange')
s+=arrow(235,395,160,300,'特征正则',True)
s+=card(660,395,375,140,'抓取参数候选评分',['离散方向 / 面内旋转 / 深度','预测质量分数与夹爪宽度','选择后再由机器人执行'],'green')
s+=arrow(885,300,885,395)
save('cross-view-grasp','跨视角抓取：多看一眼，只融合要抓的附近','局部几何补全带来收益；相机移动、标定和执行时间也必须计入。',s,'依据原论文 Fig.2 / §3 重绘；省略骨干层与碰撞检测执行细节。')
# RDD: image and latent evidence are complementary rather than always synergistic.
s=card(40,260,200,140,'待检图片 x',['预训练模型保持冻结','不训练新分类器'],'blue')
s+=card(335,155,370,150,'图像：校正背景干扰',['AE 误差 f(x)','低通 F / 旋转 R / 组合 FR','四项作差 → Simage'],'purple')
s+=card(335,375,370,150,'潜空间：校正范数干扰',['编码 z → 小噪声预测误差','比较 z 与旋转 Rz','两项作差 → Slatent'],'green')
s+=arrow(240,305,335,235)+arrow(240,365,335,450)
s+=card(840,255,310,155,'融合检测分数',['SRDD = Simage × Slatent²','较低分数更偏向生成','AUROC 不等于单张真假证明'],'orange')
s+=arrow(705,235,840,300)+arrow(705,450,840,365)
s+=text(45,575,'增强只用于对照误差；“去偏”不表示修改图片真实性或完成社会公平去偏。',15)
save('rdd-detection','RDD：用对照误差抑制错误线索','简单背景也容易重建；潜变量范数也会影响误差，因此需要两个校正分支。',s,'依据原论文 Fig.1 / 式1–7 重绘；latent展开符号问题见正文说明。')
# DID: chain and two error streams.
s=card(40,155,190,120,'原图 x',['待判断真实 / 生成'],'blue')
s+=card(405,155,190,120,'重建 x′',['x′ = R(x)'],'purple')
s+=card(810,155,230,120,'再次重建 x″',['x″ = R(x′)'],'purple')
s+=arrow(230,215,405,215,'同一重建器 R')+arrow(595,215,810,215,'再次调用 R')
s+=card(40,375,310,150,'一阶残差 Δ',['|x − x′|','保留基础重建信号','ResNet50 分类器 A'],'green')
s+=card(465,375,360,150,'二阶差 Δ²',['|x − x′| − |x′ − x″|','尝试抵消相关重建扰动','ResNet50 分类器 B'],'green')
s+=arrow(140,275,140,375)+arrow(925,275,650,375)
s+=card(875,375,285,150,'决策融合',['两支均判真实','才输出真实'],'orange')
s+='<path d="M195 525 V545 H1080 V525" stroke="#6e8a83" stroke-width="2" fill="none" marker-end="url(#arrow)"/>'
s+=arrow(825,450,875,450)+text(45,575,'Δ² 是差值记号，不是平方；两个分类器需要真假标签训练。',16)
save('did-detection','DID：残差再作差，不只是重建一次','多一次重建与双分类器带来计算成本；噪声抵消依赖相关性假设。',s,'依据原论文 Fig.2 / 式4 / §3.4 重绘；省略重建内部扩散步骤。')
# Turbo: alternating expensive refresh / cached updates with explicit timeline.
s=card(40,160,300,180,'刷新步：完整梯度',['经验 g / 扰动 gs','代理 g₀ / 平坦修正 gf','提取正交分量 gvf','缓存 sharpness 与 flatness'],'blue')
s+=card(455,160,300,180,'后续 k−1 步',['计算当前基础方向','复用已缓存正交分量','用缩放项近似修正','减少额外反向传播'],'green')
s+=arrow(340,245,455,245)
s+=card(865,160,285,180,'动态控制',['任务后期逐渐增大 k','EMA 统计触发正则','保持普通优化更新','缓存稳定性属经验观察'],'orange')
s+=arrow(755,245,865,245)
for i in range(12):
 x=60+i*90;refresh=i in (0,5,10);fill='#3b6fba' if refresh else '#b2d9c3'
 s+=f'<rect x="{x}" y="440" width="62" height="55" rx="8" fill="{fill}"/>'+text(x+15,473,'R' if refresh else 'C',18,'#ffffff' if refresh else '#237958',600)
s+=text(45,545,'刷新 R → 缓存步 C → 再刷新（示意）；k 是刷新间隔，不是学习率。',16)
save('c-flat-turbo','C-Flat Turbo：缓存慢变方向，把反向传播花在需要时','追求更平坦的解，同时降低 C-Flat 成本；仍比普通 SGD / Adam 昂贵。',s,'依据原论文 Fig.1–2 / §3.2 重绘；完整触发顺序须核对附录算法。')
# DeltaTok + world prediction.
s=card(40,150,265,150,'连续帧特征',['冻结 DINOv3：x(t−1), x(t)','DeltaTok 条件编码 g','单枚连续向量 z(t)'],'blue')
s+=card(415,150,320,150,'世界预测器 f',['只看历史 delta 与时间戳','多个随机 query 并行产生','K 个未来 delta 候选'],'purple')
s+=arrow(305,225,415,225)
s+=card(850,150,300,150,'训练：Best-of-Many',['在 token 空间比较真值','只监督最接近的候选','不需要逐个解码空间图'],'orange')
s+=arrow(735,225,850,225)
s+=card(415,405,320,150,'推理：DeltaTok 解码 h',['前一帧特征 + 预测 delta','恢复空间特征图','长时预测逐步自回归'],'green')
s+=arrow(575,300,575,405)
s+=card(850,405,300,150,'固定任务头',['分割 / 深度预测','报告 best-of-20 与 mean','best 需要真值挑选'],'green')
s+=arrow(735,480,850,480)+text(45,550,'一 token / 帧',23)+text(45,579,'表示变化；不等于独立无损视频编码。',12)
save('deltaworld','DeltaWorld：保留前帧，只预测怎么变','tokenizer 先学重建，预测器再学未来；初始黑帧让第一枚 token 承载绝对信息。',s,'依据原论文 Fig.3–4 / §3 重绘；省略多步 rollout 与冻结模块的内部层。')
# Wireless: show top M anchors and dependency on all N Gaussians.
s=card(40,155,255,160,'场景高斯与 Tx',['N 个高斯 + 发射机位置','选高不透明度 M 个锚点','M ≪ N；训练中更新'],'blue')
s+=card(400,155,330,160,'双流 tokenizer',['GA Transformer → 全局 CLS','欧氏位置 → 距离 / 布局编码','CLS 广播到全部 N 个高斯'],'purple')
s+=arrow(295,235,400,235)
s+=card(840,155,315,160,'衰减 / 信号分支',['发射机条件 MLP','几何 / 信号 / 不透明度残差','残差正则约束'],'green')
s+=arrow(730,235,840,235)
s+=card(840,405,315,145,'角度投影与累积',['投影到接收机角度平面','tile 中排序与信号累积','得到功率谱与 RSSI'],'green')
s+=arrow(995,315,995,405)
s+=card(60,405,600,145,'物理启发的表示 ≠ 完整电磁方程求解',['交互算子隐式学习；不要求逐条真实路径标注','注意力 O(M²)，整体映射和渲染仍与 N 有关','GA 签名与注意力的物理解读需对照实现核验'],'orange')
save('gai-gs','GAI-GS：用场景几何组织无线传播信息','多路径、遮挡与发射机条件共同影响接收场；质量、渲染耗时和总推理分开评价。',s,'依据原论文 Fig.1–3 / §4 重绘；不把隐式特征解释为可验证的真实射线路径。')
# Omnivorous: shared frozen trunk + two losses.
s=card(40,145,265,185,'同场景三种视觉模态',['RGB / Depth / Segmentation','深度与分割：RGB 调色板着色','训练：再混入 0–50% RGB','评价：不混合，但仍采用着色'],'blue')
s+=card(410,145,295,185,'共享学生编码器',['前 8 块冻结','末 4 块适配（ViT-B）','各模态共用参数','输出归一化语义特征'],'green')
s+=arrow(305,235,410,235)
s+=card(825,145,330,185,'双目标监督',['跨模态：同场景特征接近','跨场景：负例保持区分','教师锚定：减少语义漂移','L = Lalign + 10 Lanchor'],'purple')
s+=arrow(705,235,825,235)
s+=card(410,425,295,120,'冻结教师原 DINOv2',['同模态目标作为稳定锚点','不更新教师参数'],'blue')
s+=arrow(705,475,990,330,'锚定监督',True)
s+=text(45,575,'对齐更好不表示所有下游任务都提高；独立模态部署须核对 RGB 着色依赖。',15)
save('omnivorous-dino','Omnivorous DINO：多模态对齐，也保留原来的区分力','训练是后期少层适配；共享空间不等于原始传感器信号可以直接互换。',s,'依据原论文 Fig.2–3 / §3 重绘；图中冻结层数针对默认 ViT-B。')
# DiVT use actual colored patch schematic, not fixed output count.
for i in range(6):
 for j in range(6):
  color=['#b8d6ee','#b8d6ee','#d7bee8','#b9dccb','#b9dccb','#eecfa5'][(i//2+j//3)%6]
  s0=f'<rect x="{50+j*30}" y="{170+i*30}" width="26" height="26" rx="4" fill="{color}"/>'
  if i==j==0:s=s0
  else:s+=s0
s+=text(45,395,'N 个 patch 特征',16)
s+=card(330,165,285,170,'特征空间聚类',['余弦相似度图 + 阈值 θ','密集中心选择 → 重新分配','按空间位置排列中心','θ 越高，通常 token 越多'],'purple')
s+=arrow(240,260,330,260)
s+=card(720,165,290,170,'簇内注意力聚合',['中心作 Q，簇内 patch 作 K/V','位置编码只进入 V','每簇形成连续视觉 token','MLP → LLM 输入空间'],'green')
s+=arrow(615,260,720,260)
s+=text(45,495,'更细 θ ↑',20)+text(45,540,'更粗 θ ↓',20)
for row,n in [(480,12),(525,4)]:
 for j in range(n):s+=f'<rect x="{330+j*50}" y="{row}" width="35" height="30" rx="7" fill="{["#b8d6ee","#d7bee8","#b9dccb","#eecfa5"][j%4]}"/>'
s+=text(45,585,'token 数由内容与阈值共同决定；聚合不是无损编码，每簇也未必等于一个物体。',15)
save('divt','DiVT：把重复 patch 组织成更紧凑的视觉单元','示意颜色表示特征相近，不是原文分割标签；图中 token 数不是实验统计。',s,'依据原论文 Fig.3 / Algorithm1 / §3 重绘；省略投影矩阵与训练数据。')
# Alliance loop with explicit prune branch.
s=card(40,155,245,150,'可选：无标签选队',['模型池 → 任务一致性评分','选择 3 个异构 VLM','不是根据真值选最好代理'],'blue')
s+=card(390,155,310,150,'感知：线索 → 视频块',['每代理先随机看 4 帧','事件分块 + CLIP 线索检索','从相关块采 16 帧'],'green')
s+=arrow(285,230,390,230)
s+=card(820,155,335,150,'行动：回答与理由',['每代理基于自己的帧作答','全体一致 → 总结回答','一致性不保证正确'],'purple')
s+=arrow(700,230,820,230)
s+=card(820,420,335,135,'不一致：互评与淘汰',['自己与同伴分别打分','淘汰最低总分者','剩余代理重写感知线索'],'orange')
s+=arrow(990,305,990,420,'有分歧')
s+='<path d="M820 485 H545 V305" stroke="#6e8a83" stroke-width="2" fill="none" marker-end="url(#arrow)" stroke-dasharray="7 6"/>'
s+=text(45,575,'最多 3 轮（初始 3 代理）；最后剩 1 代理并不等于多人共同证实。',15)
save('a4vl','A4VL：先找证据，再回答，再按分歧重新看','action 指推理动作；外部视频内容与字幕不能授予代理新权限。',s,'依据原论文 Fig.2 / §2 重绘；未展开事件边界检测和模型内部结构。')
# PCE explicit verification point.
s=card(40,155,250,160,'观测变量 X',['中心化与 PCE 签名','基与阶数必须匹配分布','ζ 与观测如何耦合需核验'],'blue')
s+=card(390,155,300,160,'候选方向与残差',['多项式回归 Xj ~ Xi','提取残差系数签名','比较所谓独立性 / 污染度'],'purple')
s+=arrow(290,235,390,235)
s+=card(810,155,340,160,'递归图结构搜索',['推测汇点 → 选择父节点','检查多父节点冗余','移除汇点并重复'],'green')
s+=arrow(690,235,810,235)
s+=card(810,415,340,140,'代理模型方差归因',['重估全局 PCE 展开','Sobol 指数 + bootstrap','不等于精确干预效应'],'green')
s+=arrow(980,315,980,415)
s+=card(50,415,610,140,'理论与实现边界',['独立噪声 / 有限矩 / 稀疏指纹是实质假设','小图合成实验不证明任意工业系统可识别','参考 ζ 若与数据独立随机配对，投影不能自动恢复指纹'],'orange')
save('pce-lingam','PCE-LiNGAM：用随机展开描述噪声，再研究方向','作者流程概述与待核验环节并列呈现；未声称本地证明或复现通过。',s,'依据原论文 Algorithm1 / §2 重绘；保留潜变量耦合这一关键未说明边界。')
# ET3 loop.
s=card(40,170,225,150,'输入图像 x',['可能为干净 / 对抗图','冻结模型参数'],'blue')
s+=card(365,170,305,150,'分类器 / CLIP',['图像 → 类别相似度 logits','代理标签：ImageNet21k','不通过 LVLM 本体优化'],'purple')
s+=arrow(265,245,365,245)
s+=card(800,170,350,150,'能量下降与预算投影',['E(x) = − log Σ exp(logit)','图像梯度步 → 投影回防御球','默认通常迭代 2 步'],'green')
s+=arrow(670,245,800,245)
s+='<path d="M975 320 V365 H150 V320" stroke="#6e8a83" stroke-width="2" fill="none" marker-end="url(#arrow)" stroke-dasharray="7 6"/>'
s+=card(800,435,350,120,'变换后的图像 → 下游任务',['零样本分类 / 描述 / VQA','同时测自适应攻击与干净性能'],'green')
s+=arrow(1080,320,1080,435)
s+=card(45,435,610,120,'定理适用条件',['二分类、局部线性、真类加权梯度占优、足够预算','不是所有 LVLM 的无条件认证防御'],'orange')
save('et3','ET3：降低代理能量，再检查是否真正更稳健','免训练仍有图像梯度计算；低能量本身不能证明输出正确。',s,'依据原论文 Fig.2 / 式1–2 / Theorem4.1 重绘；省略定量梯度比条件。')
# Explicit training stages in DevDet.
s=card(40,150,270,175,'准备：多域检测器',['多已见域真 / 假数据训练','挑出难假与易真样本','不是完全未知域零样本'],'blue')
s+=card(410,150,315,175,'阶段 1：训练 DevGen',['冻结检测器，学习图像残差','难假 → 更可识别','易真 → 保持真','交叉熵 + TV 正则'],'purple')
s+=arrow(310,235,410,235)
s+=card(825,150,330,175,'阶段 2：剂量自适应微调',['冻结 DevGen','难假特征学习稀疏字典 D','接近字典 → 更高显影剂量','微调检测器适应显影图'],'green')
s+=arrow(725,235,825,235)
s+=card(420,425,735,130,'推理：x → DoseDict 剂量 εa → x + εa G(x) → 检测',['固定阈值与混合域评价；AUC 排序好不等于单张分类一定准确','字典不匹配时减弱处理；不能保证每个未见域泛化无损'],'green')
save('devdet','DevDet：让多域输入共用更可靠的真假判断','训练与推理条件分开；增强检测器证据不等于恢复真实伪造过程。',s,'依据原论文 Fig.3 / §4 重绘；DoseDict 的 Norm 映射与采样阈值需实现核验。')
# T2LDM: GN training only.
s=card(40,155,250,155,'文本 + 噪声 RM',['CLIP 文本特征','RM：距离 / 强度双通道','水平 / 垂直方向角 DPE'],'blue')
s+=card(400,155,310,155,'DN 去噪网络',['条件 U-Net + 时间步','v 预测与 CFG','学习几何细节分布'],'green')
s+=arrow(290,230,400,230)
s+=card(825,155,330,155,'推理：仅迭代 DN',['噪声逐步恢复 Range Map','逆球面投影 → LiDAR','辅助 GN 不在推理路径'],'green')
s+=arrow(710,230,825,230)
s+=card(400,425,420,140,'GN：训练期重建辅助',['输入干净 RM + DN 噪声特征','重建细节 → 多尺度余弦对齐','前 100k 步更新，之后冻结'],'purple')
s+=arrow(555,310,555,425,'DN 多层特征',True)+arrow(820,470,710,290,'SCRG 训练监督',True)
s+=text(45,575,'训练期可见干净目标；推理不得输入干净 RM，否则造成信息泄漏。',15)
save('t2ldm','T2LDM：把几何细节教给去噪器，辅助网络不随推理走','DPE 缓解球面视野展开的方位混淆；检测框匹配率仍受评价检测器影响。',s,'依据原论文 Fig.3 / §4 重绘；省略 DDPM 采样内部层与损失日程。')
# SeDiR conditional reconstruction.
s=card(40,155,260,160,'正常点云 + 类别标签',['共享 FPS 中心','k/2, k, 2k 邻域编码','保留细节与整体几何'],'blue')
s+=card(400,155,310,160,'CFGT + C3L',['多尺度 GAP + ACT','同类拉近、异类分开','分类 / 对比 / 跨尺度损失'],'purple')
s+=arrow(300,235,400,235)
s+=card(825,155,330,160,'几何引导解码 GGD',['全局语义与局部特征','法向 / 曲率信息作为偏置','重建编码特征，不是点坐标'],'green')
s+=arrow(710,235,825,235)
s+=card(825,425,330,130,'异常评分',['原始与重建特征 L2 差','归一化 + 高斯滤波','对象级与点级分别评价'],'green')
s+=arrow(990,315,990,425)
s+=card(45,425,620,130,'适用边界',['仅正常样本训练，但使用类别监督','未见类别和工业生产部署需要另外验证','归一化范围、token 排序及几何偏置需对照实现'],'orange')
save('sedir','SeDiR：先分清是什么，再用正确先验重建','图展示作者条件重建思路；类别语义分离不意味着每个缺陷都无法重建。',s,'依据原论文 Fig.3–4 / §3 重绘；未展开局部解码张量与插值细节。')
# PL timeline and dual learning.
s=card(40,150,255,165,'共享 ViT 帧编码器',['无流程标签预训练','同一骨干服务两个分支','训练保留时间顺序监督'],'blue')
s+=card(400,150,330,165,'视频：PL 时间排序',['稀疏 8 帧 CLS','时间头输出列表分数 s','最大化真实顺序概率','不枚举 K! 排列'],'purple')
s+=card(400,405,330,165,'图像：局部对应与掩码',['当前帧 MIM，遮蔽 30%','前后 1.5–2.5s 帧作上下文','PL patch 拼图顺序'],'green')
s+=arrow(295,225,400,225)+arrow(165,315,400,475)
s+=card(850,260,300,170,'联合训练 → 冻结评估',['Lvid + LMIM + 0.4 Ljigsaw','下游线性探针 / kNN','训练需未来上下文','推理头按评价协议使用'],'orange')
s+=arrow(730,230,850,310)+arrow(730,480,850,385)
save('pl-stitch','PL-Stitch：从“画面有什么”走向“流程先后如何”','PL 分数组织相对顺序；方向敏感与真正理解因果流程仍是不同概念。',s,'依据原论文 Fig.3–4 / §3 重绘；输入置乱与位置编码处理需源码核验。')
# Style: actual 196-code bottleneck explicitly.
s=card(40,145,285,175,'训练 A：风格码本 + DiT',['同风格、不同内容图像对','1024 码字 / 64 维','每图 196 枚风格索引','风格条件通过文本分支注入'],'blue')
s+=card(440,145,310,175,'训练 B：风格 AR',['固定码本编码训练图','Qwen2-0.5B 架构从头训练','学习索引序列 next-token','不直接从一个数字恢复图片'],'purple')
s+=arrow(325,230,440,230)
s+=card(860,145,295,175,'用户输入：数值 code',['设置风格采样种子','固定模型与采样参数','不是跨平台通用风格编号'],'orange')
s+=card(440,425,310,135,'AR → 索引 → 风格 embedding',['高频索引抑制','查码本并解码风格','同 code 可搭配不同内容'],'green')
s+=arrow(1000,320,750,470)
s+=card(860,425,295,135,'内容文本 + 风格 → DiT',['生成一致风格的不同内容','像素噪声可独立变化','多样性与一致性有折中'],'green')
s+=arrow(750,490,860,490)
save('cotyle','CoTyle：一个 code 是入口，内部仍是一串风格索引','风格复现依赖码本、AR、DiT 与采样版本；不声称数据集之外绝对原创。',s,'依据原论文 Fig.3 / Algorithm1 重绘；损失符号与频率抑制细节见讲解核对点。')
# cryo: synthetic supervision and shared network; no GAN at real inference.
s=card(40,150,285,175,'模拟成对数据',['EMDB 密度 → 干净全角度 WBP','有限角投影 + CTF + GAN 噪声','形成 noisy / clean 配对体积'],'blue','训练数据包含显式干净目标')
s+=card(435,150,300,175,'共享 3D U-Net',['路径 A：原始 noisy patch','路径 B：旋转 + 再遮蔽频域','两条路径都预测干净目标'],'purple')
s+=arrow(325,235,435,235)
s+=card(850,150,305,175,'训练目标',['L = Lfidelity + 0.1 Lrecon','同一旋转对齐输入与目标','缺失信息依赖结构先验'],'orange')
s+=arrow(735,235,850,235)
s+=card(40,425,1115,130,'真实推理：倾转投影 → WBP → 切块 → 固定 U-Net → 拼接',['不重新拟合噪声 GAN；不需要真实干净体积作为输入','背景更平滑不等于分子结构全部真实；需独立验证未观测频带'],'green')
save('cryoderec','cryoDeRec：以模拟真值连接去噪和缺失楔补全','观测信息与学习先验分开：未采到的频率不是由测量唯一确定。',s,'依据原论文 Fig.2 / §3 重绘；省略成像参数，真实推理不含训练 GAN。')
# TCCA hierarchy and conditional gates.
s=card(40,145,270,150,'目标姿态 + 多参考图',['PoseNet → 多尺度 Fp','CLIP patch → SVD / 聚合','全局 CLS + 局部外观 Fa'],'blue')
s+=card(410,145,330,150,'三组 query 对齐语义',['Qc 读取当前噪声潜变量','Qp 读取姿态；Qa 读取外观','时间嵌入与内容交互'],'purple')
s+=arrow(310,220,410,220)
s+=card(850,145,305,150,'动态控制强度',['时间 base + 内容 residual','姿态：通道级 αp','外观：token 级 αa'],'orange')
s+=arrow(740,220,850,220)
s+=card(410,420,745,140,'每个去噪时刻：条件权重 → U-Net → 更新潜变量',['姿态特征加到下采样块；外观通过 cross-attention 注入','只有 base 权重互补；最终 αp / αa 不必和为 1','SVD 主方向不是已证明的纯姿态，投影维度需核验'],'green')
s+=arrow(1000,295,1000,420)
s+=arrow(410,490,375,490,'',True)+arrow(375,490,375,125,'下一步',True)+arrow(375,125,575,125,'',True)+arrow(575,125,575,145,'',True)
save('tcca-hand','TCCA：同一个时间步，不同手势需要不同控制','去噪状态、手势复杂度与纹理一起决定条件权重；不只是预设时间曲线。',s,'依据原论文 Fig.3 / §3 重绘；PIAE 式4的投影形状与符号另见讲解。')
# SVD: real dual stream spatial key-query transfer.
s=card(40,150,270,150,'参考图 → 图像编码器',['取得第三尺度 Fsty','SVD 谱指数加权 Φ(F)','不是只留下第一奇异值'],'purple')
s+=card(410,150,330,150,'PFB：第三尺度混合',['Fgen ← Φ(Fsty)','         + Fgen − Φ(Fgen)','替换主分量，保留其余残差'],'purple')
s+=arrow(310,225,410,225)
s+=card(40,420,270,140,'内容路径：同一文本',['冻结 Infinity2B','不注入参考风格','提供每尺度 Qcon / Kcon'],'blue')
s+=card(410,420,330,140,'SAC：尺度 3 → 12',['Qgen ← Qcon；Kgen ← Kcon','生成路径仍保留自己的 V','约束注意力空间关系'],'green')
s+=arrow(310,490,410,490)+arrow(575,300,575,420)
s+=card(850,270,305,160,'生成路径 → 解码输出',['文本保真与风格保真折中','不逐风格训练，但要双流推理','速度需区分微调摊销成本'],'orange')
s+=arrow(740,490,850,385)
save('svd-style','SVD 风格个性化：换风格分量，借内容路径稳结构','两个互补操作：PFB 改特征，SAC 改注意力；两者都发生在冻结模型推理。',s,'依据原论文 Fig.4 / 式5–7 重绘；省略逐尺度残差累积，hook 索引需实现核验。')
# Wavelet diagram with actual subband mosaic and bidirectional arrows.
s=card(40,150,290,145,'按功能跨层堆叠权重',['Wqkv / Wo / Wf1 / Wf2','层数 × 输入维 × 输出维','先建立源与目标的 shape 表'],'blue')
s+=card(430,150,310,145,'L2S：3D-DWT',['1 个低频 cA + 7 个细节 cD','保留匹配目标形状的低频','拆回较小网络 → 继续训练'],'green')
s+=arrow(330,220,430,220)
for i in range(2):
 for j in range(4):
  x=865+j*65;y=165+i*55;s+=f'<rect x="{x}" y="{y}" width="55" height="45" rx="5" fill="{"#73b69c" if i+j==0 else "#d9e2e9"}"/>'+text(x+6,y+27,'cA' if i+j==0 else 'cD',12)
s+=text(860,315,'只有全部子带保留才可逆',14)
s+=card(430,420,310,145,'S2L：3D-IDWT',['小模型权重作为 cA','7 个细节子带补零','合成大网络 → 继续训练'],'purple')
s+=card(40,420,290,145,'已有小模型权重',['作为低分辨率初始化','不是生成新训练知识','形状、边界及归一化需核验'],'blue')
s+=arrow(330,490,430,490)
s+=card(850,420,305,145,'免训练的是迁移算子',['目标仍需预训练 / 微调','源模型训练成本单独计入','不保证任意尺寸 / 架构兼容'],'orange')
s+=arrow(740,490,850,490)
save('bot-scaling','BoT：缩小取低频，扩大补零后合成','把参数看成信号是一种有效初始化假设；丢失高频后不再保持完整原函数。',s,'依据原论文 Fig.2 / §3 重绘；子带示意未对应实际内存布局，任意尺寸处理待核验。')
# Membership audit defense path and geometry interpretation.
s=card(40,150,285,170,'审计输入：三种来源',['真实训练成员','自然非成员','被微扰的非成员','训练历史不会被输入修改'],'blue')
s+=card(430,150,300,170,'两类统计证据',['S：原始成员推断分数','g：输入损失梯度范数','高置信 + 低梯度可能误导','白盒梯度权限是主要假设'],'purple')
s+=arrow(325,230,430,230)
s+=card(850,150,305,170,'AR-MIA 加权推断',['w = tanh(λ g)','成员分数 = w × S','阈值需 shadow 数据校准','不能仅凭梯度认定归属'],'green')
s+=arrow(730,230,850,230)
s+=card(40,430,690,125,'MFD 是另外一个条件检测问题',['先筛选被 MIA 判为成员的查询，再区分真成员与伪造成员','筛选后 AUC 不能当作全部查询上的端到端性能'],'orange')
s+=card(850,430,305,125,'边界：小扰动仍难识别',['局部定理不是全局保证','式9标签方向另见正文核对'],'red')
save('membership-audit','成员推断：审计器的置信证据也需要验证','几何量补充原始推断分数；结果是统计证据，不是训练数据归属的确定证明。',s,'依据原论文 §3 / Fig.5–7 重绘；省略扰动优化步骤，聚焦审计与防御路径。')
