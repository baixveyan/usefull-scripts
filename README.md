# 日常与科研实用工具库

主动发现值得使用的工具，整理成能理解、能复现、能维护的中文指南与实用程序。支持脚本、浏览器扩展及纯文档。

## 已整理

| 场景 | 条目 | 状态 |
| --- | --- | --- |
| 科研数据集 | [Fashion-MNIST 下载与完整性校验](datasets/fashion-mnist/README.md) | 固定版本四文件真实下载、MD5 与 IDX 检查通过 |
| 科研数据集 / 下载工具 | [清单下载与校验助手](datasets/download-helper/README.md) | 7 项合成测试及 Fashion-MNIST 四文件真实验证通过 |
| 科研数据集 / 下载工具 | [Go Hugging Face 下载器选型](datasets/huggingface-downloader/README.md) | 固定来源、版本与许可证已核对；未运行 |
| 科研数据集 / 实验检查 | [数据划分分组交叉检查](datasets/split-audit/README.md) | 6 项合成测试及真实 UCI 参与者划分检查通过 |
| 科研数据集 / 时间序列 | [UCI HAR](datasets/uci-har/README.md) | 官方包真实下载及参与者划分检查通过 |
| 科研数据集 / 科学研究 | [MIMIC-IV 3.1 申请指引](datasets/mimic-iv/README.md) | 受控访问流程已整理；未申请/下载 |
| 软件辅助 / 翻译 | [WhatsApp 侧栏审查与改进计划](app-helpers/translation/README.md) | 已修复打包清理与翻译外发控制；模拟测试通过，GUI 待验证 |
| 软件辅助 / 导出 | [SingleFile 网页归档](app-helpers/web-archive/README.md) | 作者资料已核对；未安装实测 |
| 软件辅助 / 工作流 | [来源笔记浏览器扩展](app-helpers/source-notes/README.md) | 9 项逻辑与模拟弹窗测试通过；真实安装待验证 |
| 软件辅助 / 工作流 | [GitHub/GitLab 候选采集器](app-helpers/tool-discovery/README.md) | 5 项模拟测试及两站真实元数据采集通过 |
| 软件辅助 / 隐私 | [ClearURLs 来源与验收](app-helpers/link-cleaning/README.md) | 固定 GitLab 版本、许可与权限已核对；未安装 |
| 预约与提醒 | [离线日历提醒生成器](booking-helpers/calendar-reminders/README.md) | 7 项自动测试通过；客户端通知待验证 |
| 日常实用 / 效率 | [163 邮箱只读检查与归档](everyday/mail-watch/README.md) | TLS认证、只读收件与本地副本；定时运行待到点验收 |
| 日常实用 / 文件 | [RHash 选型与完整性核验](everyday/file-integrity/README.md) | 内置校验样例已测试；RHash 本体未运行 |
| 日常实用 / 文件 | [文件夹体积快照与变化比较](everyday/folder-snapshot/README.md) | 5 项合成目录测试通过；不自动清理 |
| 日常实用 / 网络 | [HTTP 与代理路径诊断](everyday/network-check/README.md) | 5 项模拟测试与真实公开 HEAD 检查通过 |

机器可读索引：[catalog.json](catalog.json)。维护记录：[maintenance/progress.md](maintenance/progress.md)。

按细分场景浏览：[完整分类导航](docs/catalog.md)。本地质量检查：`python maintenance/validate_catalog.py`。

当天成果、实际复核和未验收项：[2026-10-19 建设记录](maintenance/reports/2026-10-19.md)。

本地搜索：`python maintenance/search_catalog.py 翻译`，或用 `--category datasets`、`--status tested` 筛选；加 `--json` 输出结构化结果。分类页从索引生成：更新 `catalog.json` 后执行 `python maintenance/build_catalog.py --write`，用 `--check` 检查同步状态。所有命令从本仓库根目录运行。

分类采用“使用场景 → 细分领域”，并以语言、平台、交付形式作为标签，详见[分类规范](docs/taxonomy.md)。每日北京时间 23:00 分批推进，有可用额度和高价值任务时继续；每批保存进度，遇到用量或运行限制时停止并留待后续恢复。

## 已有项目

以下原有项目保留原路径。WhatsApp 已完成部分源码改进和模拟验证，GUI 与真实服务仍待验证；战舰世界项目尚未按新标准审核。

- [WhatsApp 实时翻译](whatsapp_live_translator/README.md)
- [战舰世界辅助项目](wows_assistant_next/README.md)

## 收录方向

- 论文数据集：介绍、申请下载入口、存放路径和校验。
- 软件辅助：翻译、格式转换、导出、浏览器扩展。
- 预约辅助：开售与余量提醒、平台允许的自动化。
- 日常工具：文件整理、备份、媒体处理及其他高价值场景。

优先贡献使用指南、稳定性和可复现性，不以搬运数量为目标。引用和改造须遵守各上游许可；当前未给整个目录授予统一许可证，原有项目与外部材料的权利分别核查。

贡献前请阅读[贡献规范](CONTRIBUTING.md)；维护命令与回归范围见[维护说明](maintenance/README.md)。
