# 小红书图文笔记自动发布方法

> 通过 ego-browser 自动化发布小红书图文笔记的完整技术文档

## 一、整体流程（9 步）

```
创建 task space → 打开创作平台 → 等待 SPA 渲染
→ 上传图片（CDP 批量）→ 填标题 → 填正文 → 关闭弹窗
→ 调用 _onPublish() 发布 → 等待跳转确认 → 清理 task space
```

## 二、各步骤技术要点

### 1. 环境准备

- ego-lite 必须在前台运行
- WorkBuddy 沙箱必须关闭（沙箱会导致 ego-browser 进程被 SIGKILL，exit 137）
- ego-browser 继承用户登录态，小红书需已在 ego-lite 中登录
- 检测沙箱：如果报错包含 `from the default agent sandbox`，说明沙箱未关闭

### 2. 打开创作平台

```
URL: https://creator.xiaohongshu.com/publish/publish
```

小红书创作平台是 **Vue SPA**，`<div id="app">` 初始为空，需要等待 **15 秒** 才能完成渲染。

- `waitForNetworkIdle(5)` 不够：网络空闲时 DOM 可能还没渲染
- 必须显式 `await wait(15)` 
- 然后用 `js()` 检查 `document.getElementById('app').childElementCount` 确认渲染完成

### 3. 进入图文发布页

页面加载后显示「发布笔记」下拉按钮。需要两步点击：

1. 点击「发布笔记」展开下拉菜单
2. 点击「上传图文」进入图文编辑器

用 `snapshotText()` 获取语义快照，正则匹配 ref 编号后 `click('@N')`。

### 4. 上传图片（关键坑点）

小红书的图片上传 `<input type="file">` 的 class 是 `upload-input`。

**不能用** `uploadFile()` 传逗号分隔的多文件路径（不生效，只上传第一张或无反应）。

**正确做法**：用 CDP（Chrome DevTools Protocol）批量设置：

```js
const doc = await cdp('DOM.getDocument', {})
const inputNode = await cdp('DOM.querySelector', {
  nodeId: doc.root.nodeId,
  selector: 'input.upload-input'
})
await cdp('DOM.setFileInputFiles', {
  files: ['/path/to/card_01.png', '/path/to/card_02.png', ...],
  nodeId: inputNode.nodeId
})
```

上传后等待 **8 秒** 让图片处理完成（生成缩略图、上传到 CDN）。

- 图片推荐尺寸：1080x1440（3:4 竖屏）
- 最多 18 张
- 文件路径必须是绝对路径

### 5. 填写标题

```js
await fillInput('css:input[placeholder="填写标题会有更多赞哦"]', '标题内容')
```

标题限制 20 字符，超出会被截断。

### 6. 填写正文

正文区域是 `contenteditable="true"` 的富文本编辑器，不是 `<textarea>` 或 `<input>`：

```js
// 先 focus 编辑器
await js(`document.querySelector('[contenteditable="true"]').focus()`)
// 再用 typeText 输入（支持 \n 换行和 #话题标签）
await typeText('正文内容...\n\n#话题1 #话题2')
```

输入完成后按 `Escape` 关闭话题建议弹窗（输入 `#` 后小红书会弹出话题建议列表）。

### 7. 点击发布按钮（最关键的坑点）

#### 问题分析

小红书的「发布」按钮被封装在 **`<xhs-publish-btn>`** 自定义 Web Component 中，该组件使用 **closed Shadow DOM**：

```html
<xhs-publish-btn submit-text="发布" submit-disabled="false" submit-loading="false">
  #shadow-root (closed)    ← closed 意味着 host.shadowRoot 返回 null
    <div class="publish-page-publish-btn">
      <button class="ce-btn bg-red">发布</button>
    </div>
</xhs-publish-btn>
```

#### 失败的方法（全部无效）

| 方法 | 结果 | 原因 |
|---|---|---|
| `document.querySelector('button.ce-btn.bg-red')` | 找不到 | 按钮在 shadow DOM 内，主文档查询不到 |
| `host.shadowRoot.querySelector(...)` | `shadowRoot` 为 `null` | closed shadow DOM 不暴露 shadowRoot 属性 |
| `click('@N')` via snapshotText | 无 ref 可用 | snapshotText 不穿透 shadow DOM |
| `cdp('DOM.performSearch', {includeUserAgentShadowDOM: true})` | 找到节点但 nodeId=0 | closed shadow DOM 的节点无法被 CDP 操作 |
| `cdp('DOM.enable') + DOM.performSearch` | 同上 | 即使启用 DOM agent 也无法穿透 closed shadow |
| `cdp('Input.dispatchMouseEvent', {x, y})` | 不触发 Vue 事件 | 坐标点击不触发 Vue 的事件绑定 |
| `host.click()` | 点击的是宿主元素 | 宿主没有绑定 click 事件，内部按钮未触发 |

#### 成功的方法

**直接调用组件暴露的内部方法 `_onPublish()`**：

```js
const host = document.querySelector('xhs-publish-btn')

// 检查按钮状态
const submitDisabled = host.getAttribute('submit-disabled')  // 'false' = 可点
const submitLoading = host.getAttribute('submit-loading')     // 'false' = 未在加载

if (submitDisabled === 'true') {
  // 按钮被禁用，可能标题或正文为空
  throw new Error('Publish button is disabled')
}

// 直接调用内部发布方法
host._onPublish()
```

**原理**：`<xhs-publish-btn>` 是一个 Web Component（自定义元素），其原型链上暴露了 `_onPublish` 和 `_onSave` 方法。这些方法绑定在组件实例上，通过 `host._onPublish()` 可以直接调用，绕过 Shadow DOM 的封装。

**发现方法**：通过 `Object.getOwnPropertyNames(Object.getPrototypeOf(host))` 列出组件原型上的所有方法名，发现 `_onPublish`、`_onSave` 等内部方法。

#### 验证发布状态

- 按钮进入 loading：`host.getAttribute('submit-loading')` 变为 `'true'`
- 发布成功：页面约 5-10 秒后跳转到 `https://creator.xiaohongshu.com/publish/note-manage`
- 检查方式：`pageInfo().url.includes('note-manage')`

### 8. 清理

```js
await completeTaskSpace(task.id, { keep: false })
```

## 三、注意事项

1. **沙箱限制**：WorkBuddy 的 Bash 工具即使在"完全访问"模式下，ego-browser 仍可能检测到 macOS sandbox。如果报错 `from the default agent sandbox`，需要在 WorkBuddy 设置中关闭沙箱。
2. **SPA 渲染**：小红书创作平台首次加载需要 15 秒，不要用 `waitForNetworkIdle` 代替。
3. **话题标签**：正文中的 `#话题` 会自动被小红书识别为话题标签，输入后会弹出建议列表，按 `Escape` 关闭。
4. **图片尺寸**：推荐 1080x1440（3:4 竖屏），最多 18 张。
5. **发布频率**：不要短时间内连续发布多篇，可能触发风控。
6. **标题字数**：小红书标题限制 20 字符。
7. **正文字数**：小红书正文限制 1000 字符。
