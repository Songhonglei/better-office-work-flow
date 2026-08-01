---
name: xhs-image-note-release
version: 1.4.0
description: >
  小红书图文笔记自动发布技能。通过 ego-browser 自动化完成图片上传、标题填写、正文编辑、
  话题标签、发布等全流程。附带 25 种多样式风格卡片生成器，卡片主题、布局、插画、署名等参数均可自由配置。
  当用户要求发小红书、发布图文笔记、上传到小红书、小红书发帖或涉及小红书内容发布时触发此技能。
  前置依赖：ego-browser (ego-lite) 已安装且正在运行，小红书账号已登录。
bins: [ego-browser, node]
metadata:
  openclaw:
    requires:
      env:
        - IMAGE_DIR
        - IMAGES
        - TITLE
        - BODY
---

- **Version**: 1.4.0
- **License**: MIT
- **Author**: Evan Song · [github.com/Songhonglei](https://github.com/Songhonglei)
- **Repository**: https://github.com/Songhonglei/better-office-work-flow

# xhs-image-note-release

通过 ego-browser 自动化发布小红书图文笔记。覆盖从打开创作平台到发布成功的完整流程，包含图片批量上传、标题/正文填写、话题标签、一键发布等。附带 25 种多样式风格卡片生成器，卡片参数可自由配置。

## Dependencies

本技能依赖以下外部工具/技能，**必须在使用前安装并配置**：

| 依赖 | 类型 | 用途 | 安装方式 | 验证 |
|------|------|------|----------|------|
| **ego-browser** (ego-lite) | CLI 工具 + Skill | 浏览器自动化引擎，提供 CDP、snapshot、fillInput 等 API | 参考 [ego-browser skill](https://github.com/Songhonglei/better-office-work-flow) 安装 | `ego-browser --version` 能正常输出版本号 |
| **小红书账号** | 平台账号 | 需在 ego-lite 浏览器中已登录小红书 | 手动在 ego-lite 中登录 creator.xiaohongshu.com | 打开创作平台能看到发布按钮 |
| **Google Chrome / Chromium** | 系统浏览器 | 卡片生成器 (`card_generator.py`) 使用 Chrome headless 渲染 PNG | macOS: 从 [google.com/chrome](https://www.google.com/chrome/) 安装；Linux: `apt install chromium-browser` | 终端运行 `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version` 或 `chromium --version` |

> **特别提示（仅 WorkBuddy 环境）**：较新版本的 WorkBuddy 需先关闭沙箱功能（设置 → 关闭沙箱），否则运行 ego-browser 会被中断。这**不是本技能的依赖**——在终端或其他 Agent 中直接运行本技能无需任何沙箱相关操作。
>
> **ego-browser API**：本技能代码中使用的 `useOrCreateTaskSpace`、`openOrReuseTab`、`snapshotText`、`click`、`fillInput`、`typeText`、`pressKey`、`cdp`、`js`、`pageInfo`、`completeTaskSpace`、`captureScreenshot`、`wait`、`waitForNetworkIdle`、`cliLog` 均为 ego-browser 提供的 API，需先 `Skill("ego-browser")` 加载后使用。

## 前置条件

1. **ego-lite 已安装且运行中** — ego-browser CLI 依赖 ego-lite app 提供的浏览器环境
2. **小红书已登录** — ego-browser 继承用户登录态，需在 ego-lite 中手动登录小红书一次
3. **已加载 ego-browser 技能** — 先 `Skill("ego-browser")` 加载浏览器操作技能

> **特别提示（仅 WorkBuddy 环境）**：较新版本的 WorkBuddy 需先关闭沙箱功能（设置 → 关闭沙箱），否则运行 ego-browser 会被中断。这不是本技能的依赖，在终端或其他 Agent 中直接运行无需此操作。

## 核心流程（9 步）

```
创建 task space → 打开创作平台 → 等待 SPA 渲染(15s) → 进入图文发布页(自动兼容 tab/下拉)
→ 上传图片(CDP 批量) → 填标题 → 填正文 → 关闭话题弹窗
→ 调用 _onPublish() 发布 → 等待跳转确认 → 清理 task space
```

### 1. 创建 task space 并打开创作平台

```bash
ego-browser nodejs <<'EOF'
const task = await useOrCreateTaskSpace('publish xhs note')
await openOrReuseTab('https://creator.xiaohongshu.com/publish/publish', { wait: true, timeout: 25 })
// Vue SPA，必须等待 15 秒渲染
await wait(15)
EOF
```

**关键点**：小红书创作平台是 Vue SPA，`<div id="app">` 初始为空，`waitForNetworkIdle` 不够，必须 `await wait(15)`。

### 2. 进入图文发布页

创作平台支持两种入口进入图文编辑页，脚本会**自动兼容**两种 UI：

- **方式 A（顶部 tab）**：页面顶部有「上传视频 / 上传图文 / 写长文」tab 导航，点击「上传图文」
- **方式 B（下拉菜单）**：页面有「发布笔记」下拉按钮，点击展开后选「上传图文」

脚本逻辑：先试方式 A（按文本遍历点击），检查是否出现 `input.upload-input`；如果没有，回退到方式 B（snapshotText 匹配 ref 点击）。

```js
// 方式 A：点击顶部「上传图文」tab
const tabClicked = await js(`(() => {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false)
  let node
  while (node = walker.nextNode()) {
    if (node.textContent.trim() === '上传图文') {
      let element = node.parentElement
      for (let i = 0; i < 4; i++) {
        if (!element) break
        element.click()
        element.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }))
        element = element.parentElement
      }
      return true
    }
  }
  return false
})()`)
await wait(3)

// 检查是否已进入图文编辑页
if (!await js(`!!document.querySelector('input.upload-input')`)) {
  // 方式 B：回退到「发布笔记」下拉菜单
  const pageText = await snapshotText()
  const matchPublish = pageText.match(/发布笔记.*?\[ref=(\d+)/)
  if (matchPublish) {
    await click('@' + matchPublish[1])
    await wait(2)
    const text2 = await snapshotText()
    const matchUpload = text2.match(/上传图文.*?\[ref=(\d+)/)
    if (matchUpload) {
      await click('@' + matchUpload[1])
      await waitForNetworkIdle(5)
      await wait(3)
    }
  }
}
```

> **注意**：两种 UI 可能同时存在或随版本切换，脚本以 `input.upload-input` 是否出现为判断标准，自动选择可用入口。

### 3. 上传图片（CDP 批量）

**不能用** `uploadFile()` 传逗号分隔多文件路径（不生效）。**必须用 CDP**：

```js
const doc = await cdp('DOM.getDocument', {})
const inputNode = await cdp('DOM.querySelector', {
  nodeId: doc.root.nodeId,
  selector: 'input.upload-input'
})
await cdp('DOM.setFileInputFiles', {
  files: ['/abs/path/img1.png', '/abs/path/img2.png', ...],
  nodeId: inputNode.nodeId
})
await wait(8)  // 等待图片处理
```

- 图片推荐尺寸：1080x1440（3:4 竖屏）
- 最多 18 张

### 4. 填写标题

```js
await fillInput('css:input[placeholder="填写标题会有更多赞哦"]', '标题内容')
```

### 5. 填写正文

正文区域是 `contenteditable="true"` 的富文本编辑器：

```js
// 先 focus 编辑器
await js(`document.querySelector('[contenteditable="true"]').focus()`)
// 再用 typeText 输入（支持换行和 #话题标签）
await typeText('正文内容...\n\n#话题1 #话题2')
await wait(1)
// 按 Esc 关闭话题建议弹窗
await pressKey('Escape')
```

### 6. 触发发布

小红书的「发布」按钮封装为自定义 Web Component（`<xhs-publish-btn>`），常规选择器或坐标点击无法命中，需直接调用其暴露的发布方法：

```js
const host = document.querySelector('xhs-publish-btn')
// 检查状态
const disabled = host.getAttribute('submit-disabled')  // 'false' = 可点
const loading = host.getAttribute('submit-loading')     // 'false' = 未加载
// 触发发布
host._onPublish()
```

> 若需了解完整的失败方案对比与排查细节，参见 `references/publish-method.md`。

### 7. 等待发布完成

调用 `_onPublish()` 后按钮进入 loading，约 5-10 秒后页面会重置并出现 `published=true` URL 参数。验证：

```js
const info = await pageInfo()
if (info.url.includes('published=true') || info.url.includes('note-manage')) {
  cliLog('SUCCESS: 发布成功！')
}
```

### 8. 清理

```js
await completeTaskSpace(task.id, { keep: false })
```

## 快速复用

### 发布已有图片

修改 `scripts/publish_note.sh` 中的 4 个参数后直接运行：

```bash
IMAGE_DIR="/path/to/images"
IMAGES="img1.png,img2.png,img3.png"
TITLE="标题"
BODY='正文内容\n\n#话题1 #话题2'

bash ~/.workbuddy/skills/xhs-image-note-release/scripts/publish_note.sh
```

### 先用本技能生成卡片，再发布

本技能附带统一风格卡片生成器，位于 `references/card-generator/card_generator.py`。

```bash
python3 ~/.workbuddy/skills/xhs-image-note-release/references/card-generator/card_generator.py \
  --theme warm \
  --tag "人生随笔" \
  --lines "周五了\\n你还活着吗\\n去外面走走" \
  --subtitle "关于活着" \
  --page-number 1 \
  --total-pages 6 \
  --account "@雨夜心灯" \
  -o ./card.png

# 图文卡片：顶部简笔画 + 窄列居中文字 + 底部署名
python3 ~/.workbuddy/skills/xhs-image-note-release/references/card-generator/card_generator.py \
  --layout image-text \
  --illustration ./door.svg \
  --theme warm_illust \
  --lines "周五了。\\n把工牌摘下来，" \
  --account "@雨夜心灯" \
  -o ./illust-card.png
```

**25 种内置主题**（纯文字布局全部共用同一套布局；图文布局额外支持 `warm_illust`）：

| 分组 | 主题 key |
|------|---------|
| 年轻人风格 | `warm` 温暖哲思、`warm_illust` 温暖简笔哲思、`y2k` Y2K 千禧潮酷、`doodle` 手绘涂鸦、`pop` 渐变波普、`minimal` 极简日系 |
| 科技 / 商务 | `cyberpunk` 赛博科技、`apple` Apple 质感、`cowork` 轻科技、`bloomberg` Bloomberg 终端、`carbon` 暗色极简 |
| 文艺 / 复古 | `elegant` 极简优雅、`newspaper` 报纸杂志、`ink` 水墨卷轴、`steampunk` 蒸汽朋克、`palace` 故宫金红 |
| 生活 / 治愈 | `xhs` 小红书·简洁、`xhs_rich` 小红书·丰富、`morandi` 莫兰迪灰、`glass` 玻璃拟态、`fresh` 清新绿、`earthy` 大地原木、`dreamy` 紫梦幻、`macaron` 马卡龙、`vivid` 活力渐变 |

> 小红书风有两个模式：`xhs` = 简洁正式（白底 + 45° 极淡斜纹，呼吸感强，适合知识笔记）；`xhs_rich` = 丰富活泼（淡粉渐变底 + 手账圆点纹 + 毛玻璃光晕 + 三段波浪线，适合生活攻略）。

用 `--list-themes` 可随时打印完整清单。

**自定义参数**：

| 参数 | 说明 | 示例 |
|------|------|------|
| `--theme` | 主题风格 | `--theme y2k` |
| `--layout` | 布局：`text` 纯文字（默认）、`image-text` 图文 | `--layout image-text` |
| `--illustration` | image-text 布局的插画文件（`.svg` / `.png` / `.jpg`） | `--illustration ./door.svg` |
| `--image-text-width` | image-text 文字区宽度占比（0.5–0.8，默认 0.65） | `--image-text-width 0.7` |
| `--tag` | 顶部标签（仅 text 布局默认显示） | `--tag 人生随笔` |
| `--lines` | 主文案，用 `\\n` 分行 | `--lines "第一行\\n第二行"` |
| `--subtitle` | 副标题（短横线下方，仅 text 布局） | `--subtitle 关于自省` |
| `--page-number` / `--total-pages` | 页码（仅 text 布局） | `--page-number 2 --total-pages 6` |
| `--account` | 右下角账号（text）/ 底部署名（image-text） | `--account @雨夜心灯` |
| `--hide-page-number` | 隐藏页码 | 默认显示 |
| `--hide-account` | 隐藏账号 | 默认显示 |
| `--hide-tag` | 隐藏顶部标签 | 默认显示 |
| `--hide-subtitle` | 隐藏副标题 | 默认显示 |
| `--width` / `--height` | 输出尺寸 | 默认 `1080x1440` |

**图文布局（`--layout image-text`）说明**：

- 顶部居中展示插画，下方是窄列居中文字，再下方是短横线 + 账号署名。
- 文案宽度默认为卡片宽度的 65%，适合短句分行，营造留白和呼吸感。
- 不显示 tag、subtitle、页码，保持画面极简。
- 推荐主题：`warm_illust`（米白底、黑线稿、琥珀色点缀，与截图示例一致）。
- SVG 插画：建议插画本身以原点为中心、无多余留白；生成器会自动提取第一个 `<g>` 元素并居中放置。
- PNG/JPG 插画：建议使用已裁切好的插画图（去除背景文字），生成器会按最大 55% 宽度 / 32% 高度等比缩放。

生成后配合 `publish_note.sh` 发布即可。

## 注意事项

1. **沙箱（仅 WorkBuddy 环境）**：若在 WorkBuddy 中运行报错 `from the default agent sandbox`，请在设置中关闭沙箱后重试（见上文「特别提示」）
2. **SPA 渲染**：首次加载等 15 秒，不要用 `waitForNetworkIdle` 代替
3. **话题标签**：正文中的 `#话题` 自动被识别，输入后弹建议列表，按 `Escape` 关闭
4. **发布频率**：**严禁**短时间连续发多篇，可能触发风控；建议每次发布间隔至少 5 分钟
5. **权限设置**：发布前如需设置权限（公开/仅自己可见），在填正文后、点发布前操作
6. **标题特殊字符**：脚本中 TITLE 变量会插入 JS 单引号字符串，**严禁**包含单引号，否则会中断脚本
7. **正文特殊字符**：脚本中 BODY 变量会插入 JS 模板字符串，**严禁**包含反引号（``` ` ```）和 `${`，否则会中断脚本

## Resources

### scripts/
- `scripts/publish_note.sh` — 一键发布脚本，修改 4 个参数即可复用

### references/
- `references/publish-method.md` — 完整方法文档，含失败方案对比表和技术原理详解。**按需加载**：当需要了解发布按钮各失败方案的完整对比、或需要排查发布相关问题时阅读此文件；正常发布流程无需提前加载
