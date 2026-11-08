# ClearURLs：清理分享链接的跟踪参数

分类：软件辅助 / 隐私。资料检查：2026-10-19；通过 GitLab 公开 API 读取固定 commit 的 README、LICENSE、PRIVACY 和 manifest，未安装或执行扩展。

## 官方来源

[ClearURLs 作者 GitLab 项目](https://gitlab.com/ClearURLs/ClearUrls)提供 URL 跟踪元素清理功能。本轮固定 commit `6d904144eca14f71789180da4fe43f3c402be153`，manifest 声明版本 1.27.3、Manifest V2。源文档摘要和元数据见[核对记录](source-review.json)。

作者 README 指向 [Firefox 商店](https://addons.mozilla.org/firefox/addon/clearurls/)和 [Edge 商店](https://microsoftedge.microsoft.com/addons/detail/mdkdmaickkfdekbjdoojfalpbkgaddei)。这些是源文档中的入口，本轮未安装验证；实际商店版本可能与源码不同，Manifest V2 的安装兼容性也须按当前浏览器核查。

该 commit 的 LICENSE 为 GNU LGPL 第 3 版，README 另列第三方组件许可。这里不复制或改造扩展代码，不将上游许可作为整个实用工具库的统一许可。

## 权限与网络行为

manifest 声明 `<all_urls>`、webRequest、webRequestBlocking、storage、unlimitedStorage、contextMenus、webNavigation、tabs 和 downloads。它是覆盖浏览活动的扩展，不是只处理你粘贴的一段文本；安装前核对浏览器实际显示的授权。

作者 PRIVACY 文档说明会联网更新规则和相关摘要，提供自定义更新地址。该说明是上游声明，不代表本仓库完成了全源码或网络流量审计。权限用途可查[作者权限文档](https://docs.clearurls.xyz/latest/permissions/)。

## 实际使用前检查

- 先在普通公开文章链接上测试，确认清理前后正文相同。
- 涉及支付、登录、报名、签名下载和邀请码时，保留原始链接。部分参数可能承担真实功能，不应按“看起来杂乱”全部删除。
- 原始 URL 可能包含访问凭据；不要把真实登录链接粘贴到公开在线清洗网站或仓库问题区。
- 自动清理引起页面异常时暂停该扩展并恢复原始 URL。排错记录只用脱敏示例。

本仓库选择整理作者项目而非再造一套规则引擎。当前状态为资料已核对；后续仍需核对实际浏览器版本、商店权限并用合成链接验证功能参数，不作为已经运行验证的推荐。
