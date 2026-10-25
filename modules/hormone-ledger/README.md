# 火影姬 · 荷尔蒙档案（独立 MVU）

基线 `ccd8162982e0eb23453da58a5925d6ac5ad57676`。只交付模块、待组装片段与 QA；未写入世界书、根 dist 或角色卡。

## 数据与宿主

长期 Schema 恰好两个 Record。原始 assistant `message` / `mes` 中唯一顶层完整 `<hormone>` 是唯一事实源；模块不读取美化后的 DOM，不解析剧情，不推算变化。键存在表示已遇见。首次遇见顺序保存在 Record 插入顺序中。完整重放当前聊天的原始消息恢复顺序，故编辑、删除、切 swipe、切聊天不会残留未来数据。

正常回复缺块、重复、嵌套、越界、增量、重复姓名或遗漏旧角色时，拒绝整个无效快照并保留上一有效快照。诊断位于父窗口 `__hormoneLedger.diagnostics`，缺块精确记录“本回合 hormone 输出缺失 / 上游输出契约失败”。诊断只在内存，不是业务 Schema。空首轮块合法。

酒馆助手角色脚本入口为 `dist/hormone-ledger.js` 的完整内容。使用 `getLastMessageId / getChatMessages / getVariables / replaceVariables / eventOn / tavern_events`；消息的 `is_user` 或 `role` 均兼容，并排除系统消息。只把两个 Record 写到最新正常 assistant 消息的 `stat_data`，保留原有变量外壳；不得与第二个模型更新器同时写这两个字段。

面板保持单实例，挂在最新正常 assistant 的 `.mes_text` 底部；事件只迁移原节点。监听完成渲染、编辑、swipe、删除、换聊天事件。串行队列与版本令牌取消陈旧异步工作；无定时器、二刷或轮询。脚本停用清理监听器和面板。尚无正常回复时，开场楼层只挂现有空画廊，既不解析开场事实也不建角色档案。MutationObserver 只负责楼层DOM迟到或重绘后的原节点挂回，不重放、不解析正文、不补算数值。普通 0 楼如有正常快照允许挂，依本项目每正常回复契约执行。

## 原生结构与待组装

已读取咩咩全栈 v1.0.0 的 MVU 总则、变量写法、MVU_ZOD.js、状态栏脚本、变量列表与输出格式。保留原生核心 import、ZOD 注册、`stat_data` 消息变量外壳、单数 `status_current_variable` 与原生宏。用户本轮要求覆盖母版的逐楼面板、严格 role 判断、钳值与 JSONPatch 输出方案，详见 integration manifest。

`integration/` 提供核心脚本、ZOD、关闭的空初始值、变量列表、常驻蓝灯 hormone 契约和 post-history 短保险。状态栏脚本与显示正则在模块自己的 `dist/`。这些均未安装；最终组装方按清单导入文件内容，并确定不冲突的世界书 order。不得将模板中的 JSONPatch 更新格式再作为这两个 Record 的事实源。无需 affinity_format 或第二套变量更新格式。

## 媒体与显示

`build.py` 只读取两份权威 manifest，生成 `src/media.js` 和模块 `dist/`；不扫描、排序、解压或改写媒体。所有媒体使用已确认含 61 页及背景的固定 SHA `b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27`。只保留当前显示页和相邻 ±1 预加载；进入档案释放画廊图片。页码是浏览器本地 UI 偏好，不是第三个业务字段。存储不可用时仍可使用。

中央轻触解锁，位移超过12px取消轻触，水平位移至少36px且大于垂直位移1.25倍时翻页；滑动后产生的 click 不解锁。键盘左右键翻页，Enter/Space 进入。无第二业务页。背景失败由 CSS 渐变兜底。

## 验证

运行 `python3 modules/hormone-ledger/build.py`，在模块目录运行 `npm test`、`node qa/browser.cjs`、`python3 qa/media.py`。浏览器测试需要环境提供 Playwright 与 Chromium，不新增运行时依赖。QA 报告区分自动化模拟与真实 Android/SillyTavern 待验收；未宣称最终集成或手机实机已通过。

Candidate2集成返工见 `qa/QA_CANDIDATE2.md`。最终卡生成使用现有 `scripts/build_final_card.py`，随后 `scripts/package_candidate_png.py` 只替换PNG元数据。最终卡保留封版192条lore及其灯态，额外追加5条MVU接线条目；模块本身仍不是另一份世界书。
