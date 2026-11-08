# 数据划分分组交叉检查

检查训练集、验证集和测试集是否包含相同参与者、病人、家庭、设备或其他分组 ID。避免只检查行是否重复，却忽略同一来源跨越多个划分。

独立实现，Python 3.10+ 标准库；版本 1.0.0，验证日期 2026-10-19。仅做字符串分组 ID 的精确匹配，不是完整的数据泄漏检测器。原创代码发布许可证尚未确定。

## CSV 用法

准备各划分的 UTF-8 CSV，包含 `subject_id` 或你指定的列；其余列不会出现在报告中。

```powershell
python datasets/split-audit/audit.py --split train=D:\datasets\demo\train.csv --split test=D:\datasets\demo\test.csv --id-column subject_id
```

重复 `--split 名称=路径` 可检查验证集等任意多个划分，至少两个。路径含空格时给整个参数加引号，例如 `--split "train=D:\my datasets\train.csv"`。

## UCI HAR 用法

[UCI HAR 指南](../uci-har/README.md)中的数据包提供参与者编号文件，使用每行一个 ID 的模式：

```powershell
python datasets/split-audit/audit.py --format lines --split "train=D:\datasets\uci-har\extracted\UCI HAR Dataset\train\subject_train.txt" --split "test=D:\datasets\uci-har\extracted\UCI HAR Dataset\test\subject_test.txt"
```

2026-10-19 已对 UCI 官方包的真实参与者编号验证此模式，训练 21 组/7,352 行、测试 9 组/2,947 行，交叉为 0；你的解压路径仍需按实际目录调整。

## 输出与含义

输出 JSON 包含每个划分的行数、独立分组数，以及每两组之间重叠的分组数量。默认不输出具体 ID，也不改写源文件。

- 返回 0：分组 ID 无交叉。
- 返回 1：发现至少一对划分有交叉。
- 返回 2：文件、列、空 ID 或参数有误，不能据此判定无交叉。

分组内重复行不算跨划分错误。ID 去除两端空白，保留大小写与前导零；`001` 和 `1` 视为不同 ID。若来源编码不统一，应先按研究定义规范化，不能靠本工具猜测。

即使返回 0，也可能存在内容重复、时间泄漏、标签信息泄漏或不同 ID 指向同一主体。是否允许同一组出现在多个划分取决于研究任务；工具只提供可核查统计，不替你决定实验设计。内存主要随独立分组数量增长。

## 验证

```powershell
python -m unittest discover -s datasets/split-audit -p "test_*.py" -v
```

Windows / Python 3.13.5 的 6 项合成样例测试覆盖：无交叉、三划分成对统计、默认不暴露 ID、UTF-8 BOM、空白与前导零、逐行文件、异常 CSV、返回码。另有 [UCI HAR 真实公开数据复核](../uci-har/verification.json)；未读取用户私有研究数据。
