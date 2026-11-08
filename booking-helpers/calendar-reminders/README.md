# 离线日历提醒生成器

把开售、选课、报名或预约时间写进 CSV，一次生成包含多条事件的 `.ics`，由你手动导入日历。完全离线、无第三方依赖，不登录平台、不自动下单或提交报名。

版本：1.0.0；最后验证：2026-10-19。Python 3.10+，Windows 已运行自动测试；其他系统未实机验证。独立实现，格式依据 [RFC 5545](https://www.rfc-editor.org/rfc/rfc5545.html)。当前尚未确定本仓库原创代码的发布许可证。

## 使用

复制并编辑 [examples.csv](examples.csv)，其中时间与链接均为演示，不代表真实活动。使用 Excel 保存时选择 CSV UTF-8。

```powershell
# 从 D:\scripts 运行：先预览，不生成文件
python booking-helpers/calendar-reminders/reminders.py booking-helpers/calendar-reminders/examples.csv --dry-run

# 写入一个尚不存在的文件，不覆盖原文件
python booking-helpers/calendar-reminders/reminders.py booking-helpers/calendar-reminders/examples.csv --output reminders.ics

# 执行自动测试
python -m unittest discover -s booking-helpers/calendar-reminders -p "test_*.py"
```

创建输出文件的父目录后再运行。返回码：0 成功，2 输入或文件错误。

| 字段 | 要求 |
| --- | --- |
| id | 必填；每行唯一，建议长期固定 |
| title | 必填；事件标题 |
| start | 必填；带 UTC 偏移的 ISO 时间，例如 2026-11-01T12:00:00+08:00 |
| duration_minutes | 可选；默认 15，范围 1–10080 |
| remind_minutes | 可选；用分号分隔提前分钟数，如 60;10;0；空白表示不添加提醒 |
| url | 可选；HTTP/HTTPS 官方入口，不会自动打开 |
| description | 可选；备注；逗号、换行按 CSV 标准加引号 |

北京时间用 `+08:00`，不要省略偏移；工具会转为 UTC 存储，日历显示时间取决于客户端设置。有夏令时的地区请确认事件当天的偏移。

## 导入与限制

在所用日历的“导入文件”功能中选择生成文件，核对显示的本地时间和提醒设置。不同客户端可能忽略文件中的提醒，导入后先创建一条近期测试事件确认；本轮没有连接真实日历验证通知。手机系统权限、勿扰模式和同步延迟也会影响提醒。

同一 id 生成稳定 UID，但不同日历客户端不保证重复导入会更新已有事件。修改后导入前先处理旧事件，以免重复提醒。开售时间变化需手动更新 CSV，工具不会监测网页。

支持中文、UTF-8 折行、文本转义和多个提醒。输入异常会在写入前失败；文件已存在时拒绝覆盖。日历文件包含你填的标题和备注，导入云日历可能上传这些内容。
