# 软件辅助：翻译

| 项目 | 入口 | 当前状态 |
| --- | --- | --- |
| WhatsApp 多会话翻译侧栏 | [原项目](../../whatsapp_live_translator/README.md) | 模块、隐藏控件和合成端点验证已进行；真实聊天与发布仍待验收 |

## WhatsApp 侧栏审查（2026-10-19）

先阅读本地源文件、依赖清单和打包脚本，再做模块与隐藏 Tk 控件测试。另用合成句子核对端点。未截图、未读取真实数据库、未发送聊天文本、未执行 EXE。

### 已确认的实现

- Windows 专用：依赖 Win32/DWM、Tkinter、Pillow、NumPy 和 RapidOCR。
- 初次审查发现原翻译函数会从 Google 自动回退到 MyMemory。本轮源码已改为独立 translation_service.py：默认禁用，只发送到用户明确启用的单个服务，失败不回退。已有 EXE 未重打包，仍是旧行为。
- `Store` 使用 `data/chats.db`；构造时及正常退出时执行消息表 DELETE。联系人、语言设置和头像继续保存。
- SQL DELETE 不构成安全擦除；异常退出也不保证立即清理。数据库和头像不应公开上传。
- 原文仍通过 URL 查询参数发送；本轮已把翻译错误替换为不含请求 URL/原文的通用提示。

### 优先改进项

1. 已加入每次启动默认关闭的在线翻译开关、明确外发提示与确认。GUI 交互仍待手动验证。
2. 已抽成独立模块，允许 Google/MyMemory 单服务选择；切换后重新启用。4 项模拟网络测试通过，未外发真实文本。
3. 仅用合成英文句子进行本机进程内直连检查：MyMemory 返回非空中文结果，Google 请求失败。默认服务选择调整为 MyMemory，在线开关仍默认关闭；这不是长期可用性或条款/额度审核承诺，详见[端点检查记录](service-verification.json)。
4. 已增加最多 2 个并发、共 10 个任务的有界执行器，支持排队取消和异步退出等待。旧会话不能改发新服务，含对应测试；GUI 仍待实测。
5. 已修复构建脚本删除整个 dist 的问题：现在只清理 build，保留 dist/data，且明确指定构建、输出与 spec 路径。已通过模拟构建器测试，未构建真实 EXE。后续仍建议将用户数据迁到用户目录。
6. 确认原始代码权属和许可证、固定可复现依赖版本，再制作干净的发布包。

本轮新增根 `.gitignore` 排除上述运行数据和构建产物，不删除任何本地文件。忽略规则不会从已有 Git 历史移除文件；尚未完成历史与凭据全面审计。另有 4 项隐藏 Tk 控件测试通过，仍不代表真实聊天与视觉布局已验收。

构建回归检查：从仓库根目录运行 `powershell -NoProfile -File maintenance/test_whatsapp_build.ps1`。此测试仅在工作区创建合成文件并模拟 Python 命令，不接触真实数据库或执行 EXE。构建路径参数参考 [PyInstaller 官方文档](https://pyinstaller.org/en/stable/usage.html)。

## 原有目录变化

本次检查发现 whatsapp_translator_desktop 和 whatsapp_translator_web 已不在工作目录，取消其导航；不重建、不推断删除原因。现存项目继续原地维护。
