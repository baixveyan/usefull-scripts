# 文件夹体积快照与变化比较

想知道“哪个子目录变大了”，但不想运行自动清理程序时使用。扫描文件元数据，生成顶层子目录体积、文件数和最大的若干文件；之后比较两份快照。

Python 3.10+ 标准库；独立实现，版本 1.0.0，验证日期 2026-10-19。无文件内容读取、上传、删除或移动行为。原创代码发布许可证尚未确定。

## 使用

从仓库根目录运行，路径和输出文件按实际情况修改：

```powershell
# 默认只向终端输出 JSON，不创建快照文件
python everyday/folder-snapshot/snapshot.py scan D:\Downloads --top 20

# 保存到扫描目录之外，输出已存在时拒绝覆盖
python everyday/folder-snapshot/snapshot.py scan D:\Downloads --exclude .git --output before.json

# 过一段时间后再保存，排除规则保持一致
python everyday/folder-snapshot/snapshot.py scan D:\Downloads --exclude .git --output after.json
python everyday/folder-snapshot/snapshot.py compare before.json after.json
```

`--exclude` 可重复，按任意层级的精确文件/目录名称排除；默认没有隐式排除。输出目录需事先存在。比较时扫描根和排除规则不同会报错，避免把不同范围误认为增长。

## 如何解读

`groups` 是每个顶层子目录的汇总，`root_files` 是根目录直接包含的文件。比较结果按字节增长从高到低列出目录；负数表示减少。文件名和路径会出现在报告中，请将快照保存在本地，分享前检查。

统计为逻辑文件长度，不是文件系统实际分配空间；硬链接按路径重复计数，稀疏文件和压缩文件也可能与磁盘占用不同。扫描期间变化的文件不构成原子快照，不保证每一条元数据来自同一时刻。

扫描根会解析用户指定路径；遍历内部条目时不跟随符号链接、Windows junction 或其他 reparse 条目，云盘占位文件可能因此跳过。程序不调用文件内容读取；云盘元数据访问行为仍取决于客户端。权限错误会记录在 `errors` 中并标记 `partial=true`，不把部分结果包装成完整扫描。

返回码：0 完整完成，1 部分扫描/比较含部分结果，2 参数、文件或输出错误。不要仅按大小判断文件是否可以删除。

## 验证

```powershell
python -m unittest discover -s everyday/folder-snapshot -p "test_*.py" -v
```

Windows / Python 3.13.5 合成目录测试覆盖汇总、最大文件、排除、不读取内容、增减比较、权限异常及拒绝覆盖输出。真实云盘、网络盘、junction 和稀疏文件尚未实机验证。
