# 独立 MVU QA

施工基线：`ccd8162982e0eb23453da58a5925d6ac5ad57676`。验收日期：2026-10-26（Asia/Shanghai）。

## 自动化已通过

| 检查 | 结果 |
|---|---|
| 原始结构解析与正则 | Node 8/8 测试通过 |
| 两 Record 空初始值、0/100、100/100 | PASS；没有第三业务字段 |
| 最终整数值，非法增量/越界/小数/重复姓名 | PASS；拒绝整个非法快照，不钳值、不推算 |
| 唯一块、完整块、禁止嵌套 | PASS；重复/破损/status/affinity/wlog 嵌套均拒绝 |
| 已遇见完整快照与首次遇见顺序 | PASS；重排输出不重排列表，漏旧角色拒绝快照 |
| 缺块继承 | PASS；保留旧值并记录“本回合 hormone 输出缺失 / 上游输出契约失败” |
| role 与 is_user 消息形状 | PASS；role 缺失的真实消息形状可读，用户/系统均排除 |
| 修改、切 swipe、删除、切聊天 | PASS；重放当前原文，未来人物不残留 |
| 主面板单实例 | PASS；迁移最新回复底部，重复事件/重复执行构建包无多余面板 |
| 原生变量接口模拟 | PASS；机械写入 message.stat_data，保留 stat_data 外变量，停用清理5个监听 |
| 事件驱动 | PASS；无 setInterval、setTimeout、120ms 二刷或一秒轮询 |
| 背景失败 | PASS；强制阻断远程背景，CSS 渐变仍可读，四宽度截图均为失败兜底状态 |

## 响应式证据

Chromium 153，Playwright mobile emulation，viewport 高844px。每侧正文留8px，因此主面板有效宽度比 viewport 少16px。

| viewport | 面板宽 | 横向溢出 | 长姓名/铠甲换行 | 0与100进度宽 | 结果 |
|---:|---:|---|---|---|---|
| 320 | 304 | 无 | 正常 | 0 / 246px | PASS |
| 360 | 344 | 无 | 正常 | 0 / 286px | PASS |
| 390 | 374 | 无 | 正常 | 0 / 316px | PASS |
| 440 | 424 | 无 | 正常 | 0 / 366px | PASS |

证据：`evidence/browser-results.json` 与 `evidence/main-320.png`、`main-360.png`、`main-390.png`、`main-440.png`。已目视核对320px截图的中文显示、换行、边界值及深色兜底布局。测试专用中文字体由环境提供，不打包进运行时、不产生前端字体依赖。

## hormone 正则

固定宽匹配 `/<hormone>\s*([\s\S]*?)\s*<\/hormone>\s*/gi`。

- 大小写、跨行、CRLF、前后空白、0与100、长铠甲名完整匹配。
- 输出一个默认折叠的 details，小条标题为“♡ 荷尔蒙记录 · 本回合”；展开完整显示 `$1`。
- 原始 XML 在正常显示结果中消失；markdownOnly=true，promptOnly=false，placement=[2]，原始消息不变。
- 无脚本、状态更新、主背景、图片、iframe 或第二套 MVU。正则不会掩盖重复/漏块诊断。

## 执行命令与测试边界

`python3 modules/hormone-ledger/build.py`、`node --test modules/hormone-ledger/qa/runtime.test.js`、`python3 modules/hormone-ledger/qa/media.py`、`node modules/hormone-ledger/qa/browser.cjs` 均执行通过。浏览器可用 `HL_CHROMIUM_PATH` 指定已安装 Chromium，`HL_QA_FONT` 指定测试字体；两者只作用于 QA。

浏览器媒体使用固定提交的本地静态字节镜像，全部61页逐页解码；真实 jsDelivr 的63个 HEAD 请求另行全部通过，见 QA_MEDIA。未安装到任何现有卡体或世界书，未在真实 Android/SillyTavern 中对话；宿主真实事件时序、模型每回合完整输出契约、正则导入显示与正式背景视觉仍等待集成后实机验收。模拟通过不等于手机实机通过。

## 边界证明

所有新增文件均在 `modules/hormone-ledger/`。根 `worldbook/`、根 `dist/`、构建世界书脚本、原角色卡、docs 与 media 均无改动。可复核：

```sh
git diff --exit-code ccd8162982e0eb23453da58a5925d6ac5ad57676 HEAD -- worldbook dist scripts
git diff --name-only ccd8162982e0eb23453da58a5925d6ac5ad57676 HEAD
```

第一条为空；第二条仅模块路径。未运行世界书自动构建，未复制世界书到模块，未生成 Candidate JSON/PNG。模块自身 `dist/` 是独立脚本/正则输出，和受保护的仓库根 `dist/` 不同。
