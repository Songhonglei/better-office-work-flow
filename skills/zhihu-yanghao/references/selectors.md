# DOM 选择器与 ego-browser API 速查（zhihu-yanghao）

## 知乎关键选择器 / 按钮
| 目标 | 选择器 / 判定 | 说明 |
|---|---|---|
| 赞同按钮 | `button[aria-label*="赞同"]` | **⚠️ 8/11 实测旧 `button.VoteButton:not(.VoteButton--down)` / `button.VoteButton--up` 已失效**（知乎改版）；aria-label 形如 `"已赞同 1020 "` / `"赞同 307"`（**含尾空格必须 `trim()`**）；`.click()` 触发点赞 |
| 已赞同判定 | `b.classList.contains('is-active')`（class 含 `VoteButton is-active`） | 再点会**取消**点赞（toggle 行为）；点赞前必须判此跳过，否则把已赞取消。innerText 含「已赞同」也可但不如 class 稳 |
| ⚠️ 按钮 innerText 零宽字符 | `/赞同/.test(b.innerText)` 可命中，但 `b.innerText.trim()==='赞同 87'` 命中 0 | **8/12 实测**：innerText 实际为 `"\u200b 已赞同 87"`（前导零宽字符 `\u200b` + 空格）；**一律用 `aria-label` + `trim()` 做精确匹配**，绝不依赖 innerText 等值 |
| 回答容器 | `[data-zop]` | 每个含 `itemId`（JSON.parse 取），用于去重遍历前 5 |
| Draft.js 编辑器 | `.public-DraftEditor-content` | fillInput 目标；`\n\n` 分段保留段落 |
| 「写回答」按钮 | `button` 且 `innerText.includes('写回答')` | 文本前有零宽字符 `\u200b`，**不能**用 `===` |
| 「查看我的回答」按钮 | `button` 且 innerText 含「查看我的回答」 | 出现 = 该问题已答过，5 天内避开 |
| 「发布回答」按钮 | `button` 且 `innerText.trim() === '发布回答'` | 用 js click 才稳（8/7 实测 `Button--blue` 不稳定） |
| 发布成功标志 | URL 跳转 `/question/{qid}/answer/{aid}` | 约 5 秒后跳转；按钮变 disabled +「发布中…」 |
| 「编辑回答」按钮 | 回答页 `button` 含「编辑回答」 | 存在 = 回答已发布且可见 |
| 按时间排序菜单 | 找 `b.innerText.trim() === '默认排序'` 按钮，再点「按时间排序」 | 新回答默认排序靠后，验证可见性需切此 |
| 历史类话题 ID | `19551077`（机器学习是 `19559450`，别搞混） | 话题页入口 |
| 精华区 URL | `/topic/19551077/top-answers` | 带连字符；`/top_answers` 是 404 |
| 折叠验证 API | `/api/v4/answers/{aid}` 的 `is_collapsed` 字段 | 可靠；页面摘要默认只显示末尾段会误判 |

## ego-browser nodejs API 速查
> 这些全局函数在 `ego-browser nodejs` 运行时可用（无需 import）。

| API | 作用 |
|---|---|
| `useOrCreateTaskSpace(name)` | 创建 / 复用任务空间，返回 `{ id }` |
| `openOrReuseTab(url, { wait, timeout })` | 打开或复用标签页 |
| `wait(sec)` | 等待秒数（用于阅读模拟、点赞间隔、发布前等） |
| `js(codeString)` | 在页面执行 JS，返回结果（code 为字符串，建议字符串拼接避免模板插值） |
| `fillInput(selector, text)` | 向输入框 / 编辑器填值（直接 UTF-8 字符串） |
| `scrollBy(px)` | 滚动触发懒加载 |
| `pageInfo()` | 返回 `{ url, title }` |
| `serverFetch(url, headers?)` | 带 ego-browser 登录态的 fetch（可拿登录态 API） |
| `completeTaskSpace(name, { keep })` | 关闭任务空间（`keep:false` 清理） |
| `listTabs()` / `closeTab(id)` | 标签页管理 |
| `cliLog(str)` | 向 ego-browser 日志输出（脚本内用） |

## js 代码字符串写法建议
- 脚本文件（scripts/）内用**字符串拼接**组装 js 代码（避免 `${}` 被外壳展开）：
  ```js
  const r = await js('(() => {'
    + ' const b = document.querySelector("button.VoteButton:not(.VoteButton--down)");'
    + ' return b ? b.innerText.trim() : "";'
    + '})()')
  ```
- 若直接写 `ego-browser nodejs <<'EOF' ... EOF'`（单引号 EOF），可用模板字符串与 `${JSON.stringify(x)}` 注入参数。
