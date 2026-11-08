# UCI HAR：手机传感器活动识别

分类：科研数据集 / 时间序列。2026-10-19 已从官方 HTTPS 下载包并检查真实参与者划分，未训练模型；临时数据已删除，见[验证报告](verification.json)。

## 介绍与来源

30 位参与者的手机加速度计和陀螺仪记录，用于六类活动识别；共 10,299 个样本，提供 561 维特征及窗口化传感器数据。官方训练/测试按参与者划分。[UCI 官方页面](https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones)

## 下载与保存

1. 打开官方页面，使用 Download 按钮获取约 58.2 MB 的 ZIP，保留原始文件名与下载日期。
2. 建议原包存到 `D:\datasets\uci-har\raw`，解压副本存到 `D:\datasets\uci-har\extracted`。建议预留 1 GB，作为工作空间预算，非官方解压体积声明。
3. 找到含 train、test 目录的数据根；若下载包还包含一层 UCI HAR Dataset.zip，需要再解压一层。阅读包内 README、特征说明和标签映射后选特征或传感器窗口，不要把所有文件当作一张 CSV。

尚未取得作者发布的独立摘要或固定归档版本。本次下载的观测 SHA-256 记在验证报告中，它是本地测得值，不冒充官方摘要。可用 PowerShell `Get-FileHash -Algorithm SHA256 -LiteralPath '你的ZIP路径'` 做后续比对。通用下载助手要求预先有可信摘要，当前不为该动态入口生成自动下载清单。

## 许可、引用与复现

当前 UCI 页面声明 CC BY 4.0。引用数据集 DOI [10.24432/C54S4K](https://doi.org/10.24432/C54S4K)，并按论文要求引用 Anguita 等人在 ESANN 2013 的 *A Public Domain Dataset for Human Activity Recognition using Smartphones*。

训练时保留官方参与者划分，避免相邻窗口或同一参与者同时进入训练/测试造成结果偏高。将划分规则、特征版本、原包本地摘要写入自己的实验记录。本仓库仅保存指南，不保存数据。

已用[分组交叉检查工具](../split-audit/README.md)检查官方参与者文件：训练 7,352 行、21 位参与者，测试 2,947 行、9 位参与者，跨划分参与者交叉为 0。此结果不等于完整数据泄漏审计。

复核命令：`python maintenance/verify_uci_har.py --download --direct-network --date 2026-10-19`，日期改为实际检查日。命令明确联网、下载约 60 MB，仅读取指定 ZIP 成员，不执行包内代码、不向磁盘批量解压；保存元数据后删除临时数据。默认离线检查不会运行它。
