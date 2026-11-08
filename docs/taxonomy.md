# 分类与索引约定

以“用户想解决什么问题”为主分类，语言和文件形式独立标注。每项只设一个主分类，可有多个标签。新增分类须有实际条目，避免空目录堆积。

| 主分类 | 路径 | 建议子分类 |
| --- | --- | --- |
| 论文与数据集 | datasets/ | vision、nlp、audio、multimodal、tabular、time-series、scientific、tooling |
| 软件辅助 | app-helpers/ | translation、export、privacy、accessibility、workflow |
| 预约与提醒 | booking-helpers/ | tickets、courses、appointments、availability |
| 日常实用 | everyday/ | files、backup、media、network、system、productivity、gaming |


## 每项字段

- id：稳定英文标识；title：中文名称；path：仓库相对入口路径。
- category：上表的目录标识；subcategory：细分场景。
- type：guide、script、browser-extension、userscript、cli、desktop-app、web-app 中的一项。
- languages：实际使用语言列表，纯指南为 Markdown；不要以语言代替场景分类。
- tags：平台、用途等检索标签，例如 windows、translation、checksum。
- status：unreviewed（未审核）、documented（资料已核对）、tested（所述环境验证通过）、needs-maintenance、archived。
- source、upstream_license、upstream_ref、upstream_commit、checked_on、validation：可追溯信息；未知值用 null，不猜测。

收录新条目时，在对应主分类内创建 `<id>/README.md` 并更新根导航。项目增长后再创建分类 README。指南必须说明验证范围；documented 不代表命令已运行。

## 原有项目的归类计划

| 当前目录 | 主分类 / 子分类 | 当前处理 |
| --- | --- | --- |
| whatsapp_live_translator | app-helpers / translation | 原地保留，部分源码改进与模拟测试完成，GUI 待验证 |
| whatsapp_translator_desktop | app-helpers / translation | 本轮目录已不存在，停止导航 |
| whatsapp_translator_web | app-helpers / translation | 本轮目录已不存在，停止导航 |
| wows_assistant_next | everyday / gaming | 原地保留，未审核 |

这些项目须先审核功能、配置、凭据、依赖和许可证，再决定迁移、合并或收录。目录名不能作为功能或安全验证依据。
