# 本地维护命令

从 `D:\scripts` 运行，Python 3.10+，不需要 OpenAI API 或额外付费服务。

统一入口：`python maintenance/check_all.py`。仅运行本库明确列出的离线检查，不安装依赖、不启动 GUI、不读取业务数据库。Windows 额外运行 PowerShell 模拟构建，其他平台明确跳过此项。可用 `--list` 只看将执行的命令。

包含浏览器扩展的 JavaScript 检查：`python maintenance/check_all.py --with-javascript`，需要已有 Node，不需要 npm 包。默认命令不要求 Node；CI 另有 JavaScript 任务。

| 命令 | 行为 |
| --- | --- |
| `python maintenance/search_catalog.py 翻译` | 中文关键词搜索；只查索引，不扫描私人文件 |
| `python maintenance/search_catalog.py --category datasets --status tested` | 按分类和维护状态筛选 |
| `python maintenance/search_catalog.py --json` | UTF-8 JSON 输出全部条目 |
| `python maintenance/validate_catalog.py` | 只读检查字段、条目路径、简单入口链接 |
| `python maintenance/build_catalog.py` | 预览分类页差异，不写文件 |
| `python maintenance/build_catalog.py --write` | 仅重写带生成标记的 docs/catalog.md |
| `python maintenance/build_catalog.py --check` | 不同步时返回 1；索引无效时返回 2 |

生成页以 catalog.json 为唯一数据源。不要直接修改 docs/catalog.md；根 README 的介绍与精选入口仍由维护者编辑。

## 有实际逻辑变更时的回归

```powershell
python -m unittest discover -s booking-helpers/calendar-reminders -p "test_*.py" -v
python -m unittest discover -s datasets/download-helper -p "test_*.py" -v
python -m unittest discover -s datasets/split-audit -p "test_*.py" -v
python -m unittest discover -s everyday/folder-snapshot -p "test_*.py" -v
python -m unittest discover -s everyday/network-check -p "test_*.py" -v
python -m unittest discover -s maintenance -p "test_maintenance.py" -v
python -m unittest discover -s maintenance -p "test_discover.py" -v
python -m unittest discover -s whatsapp_live_translator -p "test_*.py" -v
powershell -NoProfile -File maintenance/test_whatsapp_build.ps1
```

这些测试使用合成文件、模拟响应和模拟构建，不需要运行真实 WhatsApp、访问聊天数据库或登录平台。第三方扩展、数据下载、真实翻译服务及日历通知仍按各项 README 的实际验证状态处理。

额外的本机控件测试：`python maintenance/test_whatsapp_ui.py`，依赖已安装的应用依赖，以隐藏 Tk、替换 Store/OCR、禁止网络与截图的方式检查控件。它不属于默认无依赖 CI。

明确联网的真实数据复核是独立命令：`verify_fashion_mnist.py` 和 `verify_uci_har.py`，均要求 `--download` 与 `--date`，可显式选择 `--direct-network`。它们下载公开数据，复核后删除临时文件，只留元数据；默认 `check_all.py` 不会运行它们。

`validate_catalog.py` 只覆盖简单 Markdown 行内链接，不验证外部链接、锚点和完整 Markdown 语法；不要将检查通过解释为全仓库安全或功能审核通过。

## 待发布 CI

[quality.yml](../.github/workflows/quality.yml)准备了 Windows/Ubuntu、Python 3.10/3.13 的离线检查矩阵，不需要聊天凭据和数据集。当前仅保存本地配置，尚未上传或在 GitHub 执行；只有本机 Windows/Python 3.13.5 结果可视为已实测。

Action 用法按 [checkout 官方仓库](https://github.com/actions/checkout)和 [setup-python 官方仓库](https://github.com/actions/setup-python)核对，当前使用其文档中的 v7 主版本标签。尚未锁定 commit；发布前应审核固定的 action 版本和仓库启用设置。
