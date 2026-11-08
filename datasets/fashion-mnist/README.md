# Fashion-MNIST：下载与完整性校验

最后资料核对：2026-10-19。类型：独立编写的中文指南，不包含上游代码或数据。

## 适合什么场景

用于快速跑通图像分类、聚类和模型训练流程。包含 60,000 张训练图像与 10,000 张测试图像，均为 28×28 灰度服饰图片，共 10 类。适合基线和教学实验，不能代表所有真实视觉任务。

- [作者官方仓库](https://github.com/zalandoresearch/fashion-mnist)
- [论文：Fashion-MNIST: a Novel Image Dataset for Benchmarking Machine Learning Algorithms](https://arxiv.org/abs/1708.07747)
- [上游许可证：MIT，Zalando SE](https://github.com/zalandoresearch/fashion-mnist/blob/master/LICENSE)

本指南使用官方仓库 `data/fashion`，已固定 commit `b2617bb6d3ffa2e429640350f613e3291e10b141`。四文件经 GitHub 官方 Contents API 真实下载并校验通过，详见[验证报告](verification.json)。下表 MD5 来自作者，只用于完整性比对，不作为对抗恶意篡改的安全证明。

## 下载入口与存放地址

无需申请账号即可获取该仓库公开的数据。推荐存到 `D:\datasets\fashion-mnist\raw`，与源码分开。路径可自行修改。四个 gzip 文件合计约 30 MB；若保留解压副本，建议至少预留 100 MB。文件内部为 IDX 二进制格式，并非 PNG 文件夹。

| 文件 | 内容 | 上游 MD5 |
| --- | --- | --- |
| train-images-idx3-ubyte.gz | 训练图像 | 8d4fb7e6c68d591d4c3dfef9ec88bf0d |
| train-labels-idx1-ubyte.gz | 训练标签 | 25c81989df183df01b3e8a0aad5dffbe |
| t10k-images-idx3-ubyte.gz | 测试图像 | bef4ecab320f06d8554ea6380940ec79 |
| t10k-labels-idx1-ubyte.gz | 测试标签 | bb300cfdad3c16e7a12a480ee83cd310 |

[直接浏览官方数据目录](https://github.com/zalandoresearch/fashion-mnist/tree/master/data/fashion)。文件页使用 Raw 下载，避免把 HTML 页面误存成数据。

## PowerShell 下载示例

优先使用[通用清单下载助手](../download-helper/README.md)：附固定版本的四文件 API 清单，默认预览，需要 `--download` 才执行。2026-10-19 本机经明确指定的 `--direct-network` 方式完成真实下载，未更改持久代理设置。下面的独立 PowerShell/Raw 域名路径仅做语法检查，网络可达性与 API 路径可能不同。

Windows PowerShell 5.1 或 PowerShell 7，无额外包。先测试小文件，确认本机可访问 GitHub。以下示例检查已有文件、校验下载并使用临时文件，不会静默覆盖校验失败的已有文件。不提供断点续传。

```powershell
$ErrorActionPreference = 'Stop'
$datasetDir = 'D:\datasets\fashion-mnist\raw'
$sourceBase = 'https://raw.githubusercontent.com/zalandoresearch/fashion-mnist/b2617bb6d3ffa2e429640350f613e3291e10b141/data/fashion'
$expected = [ordered]@{
    't10k-labels-idx1-ubyte.gz' = 'bb300cfdad3c16e7a12a480ee83cd310'
    'train-labels-idx1-ubyte.gz' = '25c81989df183df01b3e8a0aad5dffbe'
    't10k-images-idx3-ubyte.gz' = 'bef4ecab320f06d8554ea6380940ec79'
    'train-images-idx3-ubyte.gz' = '8d4fb7e6c68d591d4c3dfef9ec88bf0d'
}
New-Item -ItemType Directory -Path $datasetDir -Force | Out-Null
foreach ($fileName in $expected.Keys) {
    $target = Join-Path $datasetDir $fileName
    if (Test-Path -LiteralPath $target) {
        if ((Get-FileHash -LiteralPath $target -Algorithm MD5).Hash -ne $expected[$fileName]) {
            throw "Existing file has unexpected checksum: $target. Inspect or move it before retrying."
        }
        Write-Output "Verified, skipping: $target"
        continue
    }
    $temporary = Join-Path $datasetDir ([guid]::NewGuid().ToString() + '.part')
    try {
        Invoke-WebRequest -UseBasicParsing -Uri "$sourceBase/$fileName" -OutFile $temporary -TimeoutSec 120
        if ((Get-FileHash -LiteralPath $temporary -Algorithm MD5).Hash -ne $expected[$fileName]) {
            throw "Downloaded file checksum failed: $fileName"
        }
        Move-Item -LiteralPath $temporary -Destination $target -ErrorAction Stop
        Write-Output "Downloaded and verified: $target"
    }
    finally {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -LiteralPath $temporary
        }
    }
}
```

以上路径固定在已记录 commit；更新版本时先重新核对作者摘要和真实下载结果，不要只替换哈希让检查通过。

## 使用与排错

- 标签 0–9 依次表示：T 恤/上衣、裤子、套头衫、连衣裙、外套、凉鞋、衬衫、运动鞋、包、短靴。
- 下载失败时先检查代理和官方地址可达性；不要关闭证书验证。
- 校验失败可能是文件截断、错误网页或上游变化；先确认来源，不要直接改校验值让程序通过。
- 训练库可能使用独立缓存目录。手动下载到此目录不代表框架自动识别；接入时按所用框架官方加载接口配置。
- 发表研究时引用上述论文，作者为 Han Xiao、Kashif Rasul、Roland Vollgraf，2017，arXiv:1708.07747。

## 本次验证范围

已真实下载四个 gzip 文件，均匹配作者 MD5；另记录本地 SHA-256，检查 gzip 可解压、IDX 标头、60,000/10,000 条记录、图像 28×28 与标签 0–9 的数量。临时数据已删除，未进行模型训练。默认代理及 Raw 域名路径当时失败，官方 API 的进程内直连成功；不保证其他网络环境同样可用。

完整复核命令：`python maintenance/verify_fashion_mnist.py --download --direct-network --date 2026-10-19`。该命令约下载 30 MB 后删除临时数据，重写此目录的验证报告，日期请改为实际复核日期；不属于默认离线测试。
