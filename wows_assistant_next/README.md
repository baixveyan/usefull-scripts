# WoWS Assistant Next

一个独立设计、从零实现的《战舰世界》视觉辅助与自动化实验项目。

本项目不会逐文件、逐模块复刻 `main.dist`。旧程序只用于了解可行的功能方向，例如窗口截图、界面识别、OCR、战斗状态判断和输入自动化。新项目采用自己的架构、数据格式、算法和测试体系，不依赖旧程序的服务器、登录系统、加密资源或第三方私有插件。

## 项目边界

### 采用

- Windows 窗口截图
- OpenCV、OCR、ONNX/PyTorch 视觉识别
- 可解释的任务状态机
- 可配置的策略系统
- Windows 标准输入接口
- 离线截图回放和模拟执行

### 不采用

- 不读取、修改或注入游戏进程内存
- 不修改游戏文件
- 不连接旧程序的登录、心跳或代码下载服务器
- 不加载旧程序中的未知 EXE/DLL
- 不复用加密 `.jf` 代码包
- 不把 1920×1080 固定坐标写死在业务逻辑中
- 不在未验证状态下直接发送连续游戏输入

## 核心设计

程序分为六个相互隔离的层：

```text
窗口与截图 Capture
        ↓
视觉感知 Perception
        ↓
世界状态 World State
        ↓
任务状态机 Task FSM
        ↓
策略决策 Policy
        ↓
安全执行 Action Executor
```

每层只通过明确的数据对象通信。截图、识别结果、状态变化、决策和实际动作都可以记录与回放。

### 1. Capture：窗口与截图

- 枚举并选择游戏窗口
- 获取客户区尺寸、DPI 和缩放比例
- 全屏或局部区域截图
- 截图时间戳和帧编号
- 支持真实窗口、图片目录和录屏三种数据源

### 2. Perception：视觉感知

- UI 锚点定位，不依赖绝对坐标
- 模板匹配
- OCR 文本识别
- ONNX/PyTorch 检测与分割
- 小地图、准星、目标信息和消耗品状态识别
- 每个结果包含置信度与来源

### 3. World State：统一世界状态

- 港口、排队、加载、战斗、结算等场景状态
- 己方舰船速度、航向和武器状态
- 可见目标、距离和运动趋势
- 小地图对象和占领区状态
- 对多帧结果进行滤波，避免单帧误识别触发动作

### 4. Task FSM：任务状态机

- 将界面流程与战斗决策分开
- 每个状态定义进入条件、退出条件、超时和恢复方式
- 状态迁移必须有连续多帧证据
- 支持暂停、恢复、单步和紧急停止

### 5. Policy：策略决策

- 输入只读世界状态，输出“动作意图”
- 导航、目标选择、主炮、鱼雷和消耗品策略相互独立
- 支持规则策略、评分策略及后续模型策略
- 所有决策附带原因、置信度和有效期

### 6. Action Executor：安全执行

- 默认 Dry Run，只记录不执行
- 执行动作前再次检查前台窗口和当前状态
- 按键限速、动作去重和超时取消
- 鼠标位置、按键和持续时间完全配置化
- 全局紧急停止热键

## 新的任务拆分

### 阶段 0：工程初始化

- [x] 确定独立项目目录与架构
- [x] 创建 Python 包、测试、配置、资源和工具目录
- [x] 创建 `pyproject.toml`、日志配置和启动入口
- [x] 增加环境自检命令
- [x] 固化 CPU 与 GPU 依赖版本

验收：项目可以安装为开发包，环境自检能报告 Python、GPU、截图和模型运行状态。

### 阶段 1：离线数据与回放框架

- [x] 定义帧、识别结果、世界状态和动作意图数据结构
- [x] 支持从图片目录读取帧
- [x] 建立截图样本清单和标注格式
- [x] 实现识别结果与动作日志回放

验收：不启动游戏也能运行完整处理管线。

### 阶段 2：游戏窗口与截图

- [x] 发现并选择游戏窗口
- [x] DPI/客户区坐标校准
- [x] 高效截取窗口客户区
- [x] FPS 控制与性能统计
- [x] 窗口丢失、最小化和尺寸变化处理

验收：持续截图稳定，窗口移动、缩放后仍能正确定位客户区。

### 阶段 3：场景识别

- [x] 建立 UI 锚点与相对坐标系统
- [x] 港口、排队、加载、战斗、结算分类
- [x] OCR 通用封装
- [x] 多帧置信度滤波

验收：离线验证集的主要场景识别达到约定准确率，错误结果可视化。

### 阶段 4：只读监控器

- [x] 展示当前场景与置信度
- [x] 展示识别框和 OCR 结果
- [x] 保存调试截图和性能数据
- [x] 建立 PyQt5 调试界面

验收：程序只观察、不发送输入，能长时间稳定运行。

### 阶段 5：界面任务状态机

- [x] 港口准备状态
- [x] 开始匹配与加载等待
- [x] 战斗结束与结算识别
- [x] 返回港口、循环次数、超时恢复
- [x] 模拟执行器测试

验收：使用截图回放和模拟执行器完成完整任务闭环。

### 阶段 6：受控输入执行

- [x] Windows 标准鼠标执行器
- [x] Dry Run/真实执行双模式
- [x] 前台窗口保护和 F12 紧急停止
- [x] 单击节流与 JSONL 审计日志

验收：只在测试窗口中验证输入；未显式启用时绝不操作游戏。

### 阶段 7：战斗信息感知

- [ ] 速度与航向识别
- [ ] 武器类型、装填状态和消耗品识别
- [ ] 目标距离与锁定状态识别
- [ ] 小地图检测和坐标映射
- [ ] ONNX 模型结构分析与自有数据集设计

验收：在离线战斗截图集上输出结构化、带置信度的世界状态。

### 阶段 8：建议模式

- [ ] 导航建议
- [ ] 目标优先级建议
- [ ] 主炮提前量建议
- [ ] 鱼雷投放窗口建议
- [ ] 消耗品使用建议

验收：只显示建议和原因，不自动执行战斗动作。

### 阶段 9：策略实验

- [ ] 基于规则的基线策略
- [ ] 基于评分的多目标选择
- [ ] 航线规划与避障
- [ ] 多帧目标运动估计
- [ ] 仿真和回放评估指标

验收：策略可以离线重复评测，改动前后有量化对比。

### 阶段 10：有限自动化与稳定性

- [ ] 对低风险、可验证动作逐项开放执行
- [ ] 识别不确定时自动降级或停止
- [ ] 长时间运行和异常恢复测试
- [ ] 配置迁移、版本管理和打包

验收：任何实际动作都可追溯、可禁用并有明确安全条件。

## 推荐目录结构

```text
wows_assistant_next/
├─ README.md
├─ pyproject.toml
├─ requirements.txt
├─ requirements-gpu.txt
├─ config/
│  ├─ default.yaml
│  └─ logging.yaml
├─ src/wows_assistant/
│  ├─ capture/
│  ├─ perception/
│  ├─ state/
│  ├─ tasks/
│  ├─ policies/
│  ├─ actions/
│  ├─ ui/
│  └─ diagnostics/
├─ assets/
│  ├─ templates/
│  └─ models/
├─ datasets/
│  ├─ manifests/
│  └─ samples/
├─ tests/
│  ├─ unit/
│  ├─ replay/
│  └─ fixtures/
├─ tools/
└─ outputs/
```

`datasets/samples`、模型文件、运行日志和调试截图不应提交到版本库，后续通过 `.gitignore` 管理。

## 开发顺序

严格按照以下顺序推进：

1. 工程骨架和环境自检。
2. 离线数据结构和回放。
3. 窗口截图。
4. 只读视觉识别。
5. 状态机和模拟执行。
6. 安全输入层。
7. 战斗感知与建议模式。
8. 在充分测试后评估有限自动化。

这能保证大多数开发和测试不依赖实时游戏，也能显著降低误输入和不可复现问题。

## 当前环境

- Conda：`scripts`
- Python：3.11.0
- PyTorch：2.11.0+cu130
- torchvision：0.26.0+cu130
- torchaudio：2.11.0+cu130
- CUDA Runtime：13.0（随 PyTorch wheel 安装）
- ONNX Runtime：1.29 GPU，复用 PyTorch `torch/lib` 中的 CUDA 13 与 cuDNN 9 DLL
- GPU：NVIDIA GeForce RTX 4060 Laptop GPU
- 系统 NVIDIA 驱动保持不变

## 下一步

阶段 0 至阶段 6 已完成。下一步是对港口受控启动流程进行实际验证。

环境自检命令：

```powershell
conda run -n scripts wows-assistant doctor
```

离线数据工具：

```powershell
conda run -n scripts wows-assistant validate-manifest datasets/manifests/example.yaml
conda run -n scripts wows-assistant replay-summary outputs/events.jsonl
```

只读窗口与截图工具：

```powershell
conda run -n scripts wows-assistant list-windows --title "战舰世界"
conda run -n scripts wows-assistant capture-once --title "战舰世界"
```

默认使用不激活窗口的 `printwindow` 后端。`screen` 后端只有在游戏本身处于前台时才允许运行，以避免把覆盖在游戏之上的桌面或其他应用误当作游戏截图。

离线场景分析：

```powershell
conda run -n scripts wows-assistant analyze-image outputs/captures/game-validation.png --annotated outputs/debug/port-analysis.png

# 更改画质、分辨率或 UI 缩放后的港口回归检查（不会操作游戏）
conda run -n scripts wows-assistant validate-port-image outputs/captures/low-quality-validation.png --ship "那不勒斯" --mode "联合作战"
```

启动只读监控器：

```powershell
conda run -n scripts wows-assistant monitor-ui --title "战舰世界"
```

启动图形控制面板（选择舰船和战斗模式后，点击“开始”才会运行）：

```powershell
conda run -n scripts wows-assistant launcher-ui
```

也可双击项目根目录的 `启动助手UI.bat`。当选择的模式与港口当前模式不同时，程序会点击当前模式所在的“更改战斗模式”位置，再从菜单选择目标模式；当前已经正确时不会重复点击。
舰船和模式右侧的“添加”按钮可保存新项目，下次打开 UI 仍会保留。也可直接在可编辑下拉框中输入完整名称；点击“开始”时会自动保存。名称必须与游戏界面中 OCR 可见的文字一致。

UI 默认启用“连续作战”。该模式会取消并锁定“战后回港”：每局结束后每 5 秒识别一次结算页，发现“继续战斗”按钮后直接点击，然后进入下一局的匹配、开局确认和导航，不再返回港口或重新选船/模式。支持半角感叹号、全角感叹号和无感叹号三种按钮文字。任何一步验证失败或等待超时都会终止循环；也可按 F12 或点击 UI 停止。CLI 可使用 `port-test --continuous` 启用同样的循环。

运行纯 Dry Run 任务闭环：

```powershell
conda run -n scripts wows-assistant simulate-task tests/fixtures/scenarios/full_cycle.yaml
```

模拟器产生的 `mouse_click` 只是带语义目标的动作意图；`DryRunExecutor` 会将其记录为 `executed: false`，不会调用任何 Windows 输入接口。

港口流程预检与实际运行：

```powershell
# 只定位，不点击
conda run -n scripts wows-assistant port-test --ship "那不勒斯" --mode "联合作战"

# 显式允许受控点击；F12 可紧急停止
conda run -n scripts wows-assistant port-test --ship "那不勒斯" --mode "联合作战" --confirm-live-input

# 只验证选船与模式，不加入战斗
conda run -n scripts wows-assistant port-test --ship "那不勒斯" --mode "联合作战" --select-only --confirm-live-input

# 结算页动作（实际点击需显式确认）
conda run -n scripts wows-assistant result-test --action return_port --confirm-live-input
conda run -n scripts wows-assistant result-test --action continue_battle --confirm-live-input
```

实际流程只负责选择舰船、确认模式、点击加入战斗并等待进入战斗。识别进入战斗后立即停止，不控制舰船。

启用 `--navigate-map-center` 时，开局后先在普通战斗画面中定位右下小地图，拟合射程/探测圆并在圆心附近确认白色己方标记。己方坐标只由小地图确定，不再依赖大地图箭头。随后对 X、Y 两轴同时做中心对称，得到斜对角目标格。程序按 `M` 后必须根据长网格线或“自动驾驶控制/战术地图模式”文字确认大地图已打开，才会使用大地图边界换算点击坐标。为降低格子中心被岛屿覆盖导致导航无效的概率，程序会依次尝试目标格四个向内缩进的角点与中心点，共 5 个点。无法可靠定位时拒绝点击。
地图导航步骤本身不会额外降低挡位。连续作战每次点击“继续战斗”进入新一局后，如启用了自动导航，都会重新等待正式开战、定位己方坐标并执行一次大地图导航。
连续作战等待结算期间，每隔 5 秒交替发送一次 `W`、`S`。若 OCR 检测到“战舰已被…摧毁”，或在左下舰船状态区检测到 `0/当前血量`，程序会停止发送航速键、只按一次 `Esc` 离开已击沉战斗，并继续每 5 秒检测和点击“继续战斗”。
如果大地图/小地图交叉确认失败，程序会先确保关闭战术地图，将失败原因写入 `observations.jsonl`，等待 10 秒后重新开图、截图和校准。最多尝试 3 次；连续 3 次失败时返回 `navigation_failed` 并停止当前连续作战循环，不执行地图点击或航速操作。
小地图白色标记的宽松确认距离按当前分辨率线性缩放，只用于验证射程圆圆心的真实性；最终己方坐标使用圆心，避免舰名/距离文字粘连使白色连通域质心偏移。

战术地图与小地图边界会在每次开图后根据长网格线动态校准，箭头尺寸、轮廓面积和映射误差阈值均按当前客户区分辨率缩放。动态网格被 HUD 或岛屿遮挡时，16:9 画面可使用窗口比例估计作为备选，但仍必须通过大地图/小地图箭头交叉验证才会点击。非 16:9 画面若动态校准失败则直接停止，不使用可能错位的比例回退。每次运行的 `observations.jsonl` 会记录两个地图边界和校准来源，标注图也会显示边界与校准方式。

地图导航只会在 OCR 明确看到“战斗开始”，或右上角比赛计时器已经低于 `20:00` 时执行。无法确认正式开战时会继续等待并最终超时，不再使用固定等待 40 秒后自动点击的回退逻辑。

进入战斗 HUD 后，实时阶段检测只对右上角计时器小区域执行局部 OCR，计时器从 `20:00` 开始下降后即可确认正式开战，避免每轮扫描完整战斗画面。“战斗开始”文字仍由离线判定器支持，但不作为实时轮询的必要条件。

实际控制流程优先使用 `PrintWindow` 截取游戏客户区。如果 DirectX 渲染导致其返回黑屏，程序会在实时输入已获明确允许时将目标游戏置于前台，并自动回退到屏幕客户区截图；若游戏不在前台或两种截图方式均失败，仍会拒绝识别和点击。

OCR 模型在进程内按 GPU/CPU 模式缓存，避免重复初始化。默认使用 CUDA；固定计时器区域通过前台屏幕小区域直接截图，并跳过文本检测与方向分类，只运行文字识别。

只读监控器使用 `PrintWindow` 连续截图时，部分 DirectX 游戏会因强制重绘而闪烁；它不是每次截图都必然发生。实际状态流程采用约 5 秒一次的低频截图，并在任务结束后停止采集。
