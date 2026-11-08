# HTTP 与代理路径诊断

用少量 HEAD 请求比较系统网络路径和明确选择的进程内直连，帮助区分“本机代理不可用”和“目标站点返回错误”。不下载响应正文，不修改代理、证书、DNS 或系统设置。

Python 3.10+ 标准库，独立实现，版本 1.0.0，验证日期 2026-10-19。原创代码发布许可证尚未确定。

## 用法

```powershell
# 默认只检查系统网络路径
python everyday/network-check/diagnose.py https://api.github.com --timeout 5

# 明确比较直连，不保存或修改系统设置
python everyday/network-check/diagnose.py https://api.github.com --timeout 5 --compare-direct
```

每次最多 5 个 HTTP/HTTPS 地址，不接受 URL 内用户名密码。输出为 JSON，目标只显示协议、主机和端口，不输出路径、查询或完整错误文本。代理摘要显示主机、端口及是否有凭据，不输出用户名密码；分享报告前仍应检查本地网络地址。

## 如何判断

- system_path 失败、direct_path 成功：两种路径结果不同，可进一步检查代理；程序不会替你更改配置。
- 收到 403、401、405 等 HTTP 状态：说明收到 HTTP 响应，可能来自站点或代理，不应称为 DNS/连接失败。405 也可能只是站点不支持 HEAD。
- successful_status 只表示 HTTP 状态范围，不证明页面内容、登录状态或业务接口正确。
- 超时是单次网络操作的设置，不是严格的全流程总时限，系统 DNS 等步骤也可能延长等待。

返回 0：所有系统路径获得成功状态；1：至少一个系统路径失败，即使直连可用也保留该失败；2：输入无效。报告不上传到任何第三方，目标站点或代理仍会看到这次普通请求。

## 验证

```powershell
python -m unittest discover -s everyday/network-check -p "test_*.py" -v
```

合成测试覆盖只发 HEAD、不读正文、敏感字段脱敏、HTTP 错误与连接错误区分、显式直连对比和参数限制。真实网络复核结果以维护进度为准，不保证不同网络环境相同。

2026-10-19 当前执行环境的公开 GitHub API 复核：系统路径 ConnectionRefusedError，显式直连状态 200；程序按设计返回 1，以保留默认路径失败信息，没有修改网络配置。这不是对用户其他应用网络状态的结论。
