# 文件完整性：优先使用成熟工具

用途：下载数据集后校验文件、拷贝到移动硬盘前后核对内容、长期备份检查。校验只能发现内容差异，不会修复文件，也不能替代备份。

最后资料检查：2026-10-19。交付形式：中文指南，未复制或改造第三方源码。

## 选型

| 需求 | 建议 |
| --- | --- |
| Windows 单文件 SHA-256 比对 | 内置 PowerShell `Get-FileHash` |
| 多算法、跨平台、目录级核验 | [RHash 作者仓库](https://github.com/rhash/RHash) |
| 已有 hashdeep 清单与审计流程 | [hashdeep 作者仓库](https://github.com/jessek/hashdeep)，按其文档确认格式与构建方式 |

本轮深入核对 RHash README 和 COPYING：支持递归处理、计算和核验多种摘要，当前 master 声明 BSD Zero Clause（0BSD）许可。实际使用某个 release 时仍需检查该版本附带许可，不能把 master 的许可直接套到所有旧版本。

## 获取 RHash

从 [官方 Releases](https://github.com/rhash/RHash/releases) 选定版本，记录 release 标签、安装包来源与校验值。作者 README 另指向 [Windows 二进制发布目录](https://sourceforge.net/projects/rhash/files/rhash/)。本指南未下载或执行这些安装包，未取得当前固定 commit，不保证每个版本具有相同安装方式。

安装后先运行 `rhash --version` 与 `rhash --help`，记录版本并核对参数。目录清单生成时应保存到被扫描目录之外，避免把清单自身也纳入输入。恢复或核验时保留原有相对目录结构。

## 无需安装：Windows 单文件核验

在 PowerShell 里把路径与期望值替换成你实际需要的值。期望值必须来自可信发布渠道。

```powershell
$fileToCheck = 'D:\datasets\example\archive.zip'
$expectedSha256 = '替换为官方提供的64位十六进制SHA256'
if ($expectedSha256 -notmatch '^[0-9a-fA-F]{64}$') {
    throw '请先填写官方 SHA256，不能使用占位文本'
}
$actualSha256 = (Get-FileHash -LiteralPath $fileToCheck -Algorithm SHA256 -ErrorAction Stop).Hash
if ($actualSha256 -ne $expectedSha256) {
    throw '校验失败：先检查文件、版本和官方校验值，不要使用该文件'
}
Write-Output 'SHA256 matches'
```

`-LiteralPath` 按原样处理文件名中的方括号等字符。核验只读取目标文件，不改写文件内容。

## 本轮验证

本地用临时样例实测 `Get-FileHash` 与预期 SHA-256 的一致性及修改后的差异检测；这不等于 RHash 端到端验证。RHash 和 hashdeep 仅做上游资料选型，不提供未经核对的复杂命令。没有为成熟工具重复实现另一个校验引擎。

来源：[RHash README](https://github.com/rhash/RHash/blob/master/README.md)、[RHash COPYING](https://github.com/rhash/RHash/blob/master/COPYING)。
