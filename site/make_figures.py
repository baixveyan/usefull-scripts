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
print('Wrote six original method figures')
