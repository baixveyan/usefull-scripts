# 数据集下载与校验助手

按 JSON 清单下载公开 HTTPS 文件，支持 SHA-256 或 MD5 完整性核验。默认只预览；明确加 `--download` 才创建目录和下载。适合多个数据文件反复检查、网络恢复后跳过已完整下载的文件。

Python 3.10+ 标准库，无第三方依赖。版本 1.0.0；验证日期 2026-10-19。独立实现，发布许可证尚未确定。

## 使用

从仓库根目录运行：

```powershell
# 只预览，不联网、不创建输出目录
python datasets/download-helper/fetch.py datasets/download-helper/fashion-mnist.json --output D:\datasets\fashion-mnist\raw

# 开始下载；示例每个文件最多 100 MiB
python datasets/download-helper/fetch.py datasets/download-helper/fashion-mnist.json --output D:\datasets\fashion-mnist\raw --max-mib 100 --download

# 仅在你明确需要直连且网络允许时：本次进程忽略代理，不修改系统设置
python datasets/download-helper/fetch.py datasets/download-helper/fashion-mnist.json --output D:\datasets\fashion-mnist\raw --max-mib 100 --download --direct-network

python -m unittest discover -s datasets/download-helper -p "test_*.py" -v
```

Fashion-MNIST 清单固定 commit `b2617bb6d3ffa2e429640350f613e3291e10b141`，通过 GitHub 官方 Contents API 与 `Accept: application/vnd.github.raw+json` 取二进制内容。四文件真实下载已验证，见[报告](../fashion-mnist/verification.json)。公开 API 仍可能限流，本工具不自动重试或添加凭据；Raw 域名与 API 在不同网络下可达性可能不同。规模、许可与论文见[数据集指南](../fashion-mnist/README.md)。

## 自定义清单

```json
{
  "version": 1,
  "files": [
    {
      "name": "example.zip",
      "url": "https://example.com/example.zip",
      "algorithm": "sha256",
      "digest": "替换为官方64位十六进制SHA256"
    }
  ]
}
```

这里只是模板，不能直接下载。URL 必须来自你有权访问的可信发布方；不接受 URL 内账号密码。清单支持简单 ASCII 文件名，拒绝目录穿越、Windows 保留设备名、重复文件名及无效摘要。可选 `accept` 只允许 GitHub raw 内容类型或 application/octet-stream，不支持任意认证头。优先 SHA-256，只有上游仅给出 MD5 时才使用 MD5。

## 文件行为与限制

- 已有文件匹配时跳过；不匹配时保留原文件并报错，先检查或移走再重试。
- 下载写入随机 `.part` 文件，校验通过后通过硬链接发布；不会覆盖同时由其他进程创建的目标文件。失败清理本次临时文件。
- 输出磁盘需支持硬链接（如 NTFS）；不支持时明确失败，不退化为可能覆盖目标的写入。发布前后需要同一个输出目录所在文件系统。
- 不提供断点续传、自动解压、登录、验证码或私有仓库认证。失败后再次运行会重新下载未完成的单个文件。
- 超时是网络操作超时，不是完整任务总时限；每文件字节上限默认 1024 MiB。默认遵循系统网络设置；仅显式加 `--direct-network` 时在本进程忽略代理，永不修改持久设置。
- 工具允许 HTTPS 重定向；消费响应内容前会拒绝最终 HTTP 地址，但不承诺把清单变成不可信 URL 的网络隔离器。
- 返回码 0 成功/预览，1 下载或校验失败，2 清单或参数错误。错误日志不输出完整网络异常，避免泄露签名 URL。

## 验证范围

Windows / Python 3.13.5 下 7 项合成响应测试通过，覆盖下载、已有文件、错误摘要、字节限制、失败清理、并发创建不覆盖、清单拒绝、默认预览、Accept 头及 HTTPS 降级拒绝。另对固定版本 Fashion-MNIST 四文件完成真实直连 API 下载及结构检查；不代表任意站点或默认代理路径都已验证。
