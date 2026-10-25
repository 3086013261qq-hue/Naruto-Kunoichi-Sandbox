# Candidate2：最终卡 MVU 挂载返工

直接基线 `f007e0c030e70c9ec90c3149c61b4343675b5b1c`，日期2026-10-26（Asia/Shanghai）。本轮只修改现有模块挂载、最终装配与QA，不改业务模型或视觉。

## 上一张真实导入文件检查

读取用户此前的 `火影姬世界_正式实机测试_v1.0.json` 与同名PNG。两份PNG载荷chara/ccv3均与该JSON一致；MVU、MVU ZOD、变量状态栏三个原生脚本确实存在，type=script、enabled=true。状态栏内容与既有模块dist完全一致。因此“未装脚本”“PNG/JSON不一致”均不是这两份输入中的故障。

上一卡有195条：此前192条lore + 3条MVU集成；清理UpdateVariable与占位符的两个原生正则、变量更新规则和变量输出格式两条接线尚未补齐。本轮补齐这些接线，不把它们误判成已证实的显示故障原因。

## 可复现的两个挂载缺口

1. 原卡first_mes含`<opening>`；replay有意不把开场当正常事实源，但旧host在latest=null时直接移除面板，连空锁屏画廊也不显示。
2. 旧host第一次执行时若`.mes_text`尚不存在，直接移除面板并退出。楼层稍后出现或正文重绘且无后续数据事件时，没有挂回入口。

回归用上一卡真正嵌入的状态栏代码，在hidden srcdoc、type=module的角色脚本iframe中执行：开场已有DOM、正常回复DOM迟到两种情况下，旧版初始面板数均为0。Candidate2相同两种条件下均为1。父窗口提供模拟原生接口；未运行真实Android/SillyTavern，不能由此断言手机端所有原因已穷尽。

## 修复

- 无正常回复时，只允许开场承载原有空画廊。不开档、不读取开场业务事实、不写虚构Record。第一条正常回复后迁移原面板到最新正常AI楼。
- DOM挂载观察器只迁移现有节点，不读剧情、不调用replay、不更新Record。面板父节点正确时不重复append，停用时disconnect；无定时器与轮询。
- 保持原生脚本结构和三份组件；复用现有模块、Schema、背景、61页画廊与正则。没有第二套MVU。
- 在最终卡中装入三份启用脚本、荷尔蒙折叠正则、两份原生清理正则、post-history短保险、五个MVU接线条目。更新规则/输出格式明确只同步hormone，不引入第二个JSONPatch写入者。
- 最终装配直接读取当前HEAD的worldbook-ready，保留世界书名“火影姬世界书”。不运行任何世界书组装/返工脚本。

## 九项真实卡体检查

| 原生组件 | 最终卡内位置/状态 |
|---|---|
| MVU core | data.extensions.tavern_helper.scripts，MVU，enabled=true |
| MVU ZOD | 同上，MVU ZOD，enabled=true；恰好两个Record |
| 变量状态栏 | 同上，变量状态栏，enabled=true；内容等于修复后模块dist |
| initvar | character_book中关闭的[initvar]变量初始化勿开，两Record均为空 |
| 变量更新规则 | character_book中启用的[mvu_update]变量更新规则，depth=0 |
| 变量输出格式 | character_book中启用的[mvu_update]变量输出格式，depth=0 |
| 变量列表 | character_book中启用的变量列表，单数status_current_variable与原生宏 |
| 去除变量更新显示 | data.extensions.regex_scripts，enabled即disabled=false |
| 去除正文底部占位符/显示 | 同上原生清理正则；hormone另用原有小折叠条 |

常驻hormone完整快照契约与post_history_instructions短保险真实存在。JSON不是只指向模块的占位manifest，脚本/正则均为实际内容。原生结构同时对照咩咩全栈v1.0.0空模板与TavernHelper源代码的`src/panel/script/iframe.ts`、`src/iframe/predefine.js`；iframe会注入父窗口原生接口，测试也在此边界模拟。

## 自动化结果

- 原有runtime tests：8/8 PASS。
- 原有media QA：PASS，28+33=61页，固定提交、无重排、无重新解压。
- 原有320/360/390/440浏览器回归：PASS。
- 新增实际嵌入脚本iframe回归：PASS；开场、迟到DOM、正文重绘挂回、单实例、最新楼迁移、漏块保留37、停用清理均通过。
- 新增最终JSON/PNG独立读回：PASS；九项组件真实存在、脚本内容等于模块、三个正则启用、原始192条及其灯态完全一致。
- PNG全chunk CRC通过；ccv3与chara解码后都与最终JSON字节完全一致；旧封面的所有非卡体PNG块逐字节保留。

证据：`evidence/candidate2-mount.json`、`candidate2-integration.json`、两张`candidate2-*.png`，以及release下两份QA JSON。浏览器外部媒体被阻断，以排除网络加载影响并检查CSS fallback；不代表真实手机网络测试。

## 世界书冻结证明

最终卡内前192条逐条等于当前封版worldbook-ready；character_book除entries外的元数据也完全一致。最终197条只因在成卡接线层追加5条MVU条目，不是192条lore被修改或复制。

`worldbook/**`、根`dist/**`、build_worldbook.py、audit_worldbook_final.py、apply_worldbook_refinements.py相对基线diff为空。角色正文、姓名、发型、兽耳兽尾与蓝绿灯均通过原始条目整体相等得到保留，不另做lore业务审计。

## 交付与停止点

`release/火影姬世界_Candidate2_v1.0.json`与`release/火影姬世界_Candidate2_v1.0.png`供真实Android/SillyTavern导入。用户确认MVU实际出现前，不宣布实机通过、不封版、不继续其他内容。

复验：先build模块→npm test→media.py→build_final_card.py→package_candidate_png.py→candidate2-integration.py。已提交的Candidate2 PNG可作为自身重打包时的封面源，不需要重新生成图像。额外iframe测试执行`node modules/hormone-ledger/qa/candidate2-browser.cjs`；如提供`HL_PREVIOUS_CANDIDATE`可重现旧版失败。
