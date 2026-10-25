# Candidate3 纯 UI 导航 QA

直接基线：35b03b6099c690819d14a53967f4437a2f427ac6。

只修改现有 gallery/UI/CSS：锁屏底部左右真实 button（44×44px，半透明，边界 disabled，不循环），以及 header 内“‹ 锁屏”按钮。导航 pointer 事件停止冒泡，click 停止冒泡并翻页；手势逻辑保持原状。返回时切换已有节点 hidden，并 show(gallery.index) 恢复当前图片与相邻预加载，不重建 UI 或重复注册监听。

自动化：
- candidate3-navigation.cjs：320/360/390/440px 全部 PASS。1/61、3/61、61/61；按钮不进入 MVU；左右手势；中央进入；17/61 返回图片实际解码；三次重复往返；返回后翻页与再次进入；状态保留；44px 触控；页码不遮挡；无横向溢出；单实例。
- candidate3-mount.cjs：最终 JSON 内真实嵌入脚本在 hidden srcdoc module iframe 中运行，开场挂载、迟到 DOM、正文重绘、最新楼迁移、漏块保留和停用清理均 PASS。原生宿主接口为模拟，不是 Android 实机。
- runtime.test.js：8/8 PASS。
- candidate3-integration.py：最终卡除“变量状态栏”脚本 content 外与 Candidate2 全量相等；三脚本、三正则及九项集成真实存在；PNG chara/ccv3 payload 与 JSON 字节一致；受保护的 worldbook、根 dist、media、integration、schema、runtime、host 无差异。
- package_candidate_png.py：所有 chunk CRC PASS，保留 Candidate2 封面非卡体块，两个 payload 均等于 Candidate3 JSON。

浏览器使用本地 Chromium 153，图片请求由固定仓库内实际图片响应；不代表手机网络验收。导航截图和 JSON 证据位于 qa/evidence/candidate3-*。

复验命令：npm test（模块目录）；HL_CHROMIUM_PATH=<chromium> node modules/hormone-ledger/qa/candidate3-navigation.cjs；相同环境运行 candidate3-mount.cjs；python3 modules/hormone-ledger/qa/candidate3-integration.py。

等待用户真实 Android/SillyTavern 导入验收，未宣称实机通过。
