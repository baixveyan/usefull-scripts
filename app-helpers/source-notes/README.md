# 来源笔记浏览器扩展

浏览论文数据集、工具项目或活动说明时，记录当前页面标题和 URL，手动补充版本、许可证和备注，导出 Markdown 草稿。适合为这个仓库收集来源，也可用于个人研究笔记。

独立实现，Manifest V3，JavaScript/HTML/CSS，无 npm 依赖、后端或 API Key。版本 1.0.0，验证日期 2026-10-19。原创代码发布许可证尚未确定。

## 本地加载

Chrome 打开 `chrome://extensions`，Edge 打开 `edge://extensions`，进入开发者模式后“加载已解压的扩展程序”，选择本目录。源码尚未提交浏览器商店，也未在真实浏览器中完成安装验证。

点击扩展图标，检查自动读取的标题和地址，补充字段，查看预览再导出。默认删除 URL 查询参数与片段，避免把登录信息带进笔记；确需版本或检索参数时手动勾选保留并检查。含用户名密码的 URL 会被拒绝。

草稿只保留在当前弹窗，关闭后丢失，需及时导出。文件会进入浏览器的下载流程，不会自动写进本仓库或修改 catalog.json。所有条目先标为“采集草稿，未验证”，后续仍需人工或 Agent 核对。

## 权限与数据

只声明 activeTab，不声明永久站点权限、content scripts、后台任务或网络请求。点击时读取当前标签页的标题和 URL，不读取正文；导出的笔记可能包含你手填的私人信息，请自行选择保存位置和分享范围。

权限设计依据 [Chrome activeTab 官方说明](https://developer.chrome.com/docs/extensions/develop/concepts/activeTab)。浏览器内部页面可能无法读取，支持手动填写来源。

## 验证

```powershell
node app-helpers/source-notes/test_format.mjs
node app-helpers/source-notes/test_popup.mjs
```

本机 Node 18.19.0 上 6 项格式逻辑与 3 项模拟弹窗测试通过：默认去参数、显式保留、拒绝危险协议和凭据、文本转义、有效日期/分类、草稿状态及模拟下载。不需要安装 npm 包。Manifest、HTML 与模块语法检查通过；实际扩展权限弹窗、标签页读取和下载交互待真实浏览器验证，不能把这些测试当作完整浏览器验收。

本机沙箱阻止 `node --test` 派生子进程，因此示例直接执行测试模块，仍使用 Node 内置 test runner 输出 TAP；不是跳过测试。待发布 CI 单独配置 Node 24，尚未在线执行。
