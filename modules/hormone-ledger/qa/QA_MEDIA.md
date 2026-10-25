# 媒体与锁屏 QA

权威输入：`media/mvu/media-manifest.v1.json`、`media/mvu/lockscreen/manifest.json`，均只读。

固定 SHA：`b4b11c5efbbc99e1b7d92d79f32b937cfabd2f27`。未使用 @main，没有重新扫描、重排、下载 ZIP 或运行时解压。

| 内容 | 验证结果 |
|---|---|
| 卷一277699 | manifest 中28页，00001～00028；全部存在并可解码 |
| 卷二474873 | manifest 中33页，00001～00033；全部存在并可解码 |
| 总页数 | 61，路径唯一且61个文件SHA256均不同，无漏页/重页 |
| 固定提交 | 61页、背景与manifest均在媒体SHA中存在 |
| 真实CDN可达 | 61页 + 背景 + manifest 共63/63 HEAD 200，证据在 evidence/cdn-results.json |
| 浏览器解码 | 每个320/360/390/440宽度下均逐页打开61页，通过 |
| 页序 | 直接展开 manifest.books[].pages，不 sort、不猜序 |
| 跨卷 | 第28页向下一页进入总第29页（474873/00001.webp），通过 |
| 居留图片 | 画廊DOM仅1个 img，离屏预加载最多2个，始终只在当前±1范围 |
| 初始请求 | 首屏仅当前页和存在的1个相邻页，共2张 |
| 图片完整显示 | object-fit:contain、object-position:center center；无cover裁图、无拉伸 |
| 滑动/轻触隔离 | 水平36px阈值、12px取消点击；翻页后合成click不会解锁；中央真实touch tap可解锁 |
| 页码记忆 | 第29页释放后新建画廊仍返回第29页，通过 |
| 锁屏加载失败 | 阻断请求可显示文字占位，不影响中央进入逻辑 |
| 背景文件 | 真实142996460_p0_master1200.webp可解码，CDN HEAD 200 |
| 背景布局 | cover、center center、no-repeat，固定深色渐变；失败纯CSS兜底 |
| 额外资源 | 无运行时ZIP、JSZip、Base64、视频、音乐、头像或全量预下载 |

QA 脚本遍历全部图片仅用于验收；生产运行时不执行遍历。首次翻阅已请求的页面可由浏览器HTTP缓存复用，不是主动预下载。释放当前画廊时取消其src与预加载引用；浏览器自身缓存不受应用管理。

自动化用静态镜像检查实际WebP字节与交互，真实CDN逐URL检查可达性；网络速度、Android浏览器手势与实际酒馆嵌入仍待用户集成后验收。未将图片内容重新制作为交付素材。
