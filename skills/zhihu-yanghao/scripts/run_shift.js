// run_shift.js — 知乎养号三班编排脚本（zhihu-yanghao v1.1.0）
// 用法（Bash 必须 dangerouslyDisableSandbox:true，且关闭沙箱开关）：
//   先把参数写到 /tmp/zhihu_shift_params.json（见底部 schema），再：
//   ego-browser nodejs < scripts/run_shift.js
//   兼容旧式 env 传参（其他机器若 ego-browser 透传 env 仍可用）：
//   SHIFT=morning QID=xxx CONTENT_FILE=xxx ego-browser nodejs < scripts/run_shift.js
//
// 行为：读配置 → 按 班次+日序号 轮转话题池取关键词 → 选未答过问题(QID 可覆盖)
//        → 前10候选随机选3-5点赞(自然化) → 若 answer=true 写/发布/验证1回答 → 按 interactions 做可选收藏/关注/评论
//
// 参数优先级：env（SHIFT/CONFIG/QID/CONTENT/CONTENT_FILE/KW/LIMIT/COMMENT_TEXT）> /tmp/zhihu_shift_params.json
// 注：部分 ego-browser 构建不向 nodejs 运行时透传 shell env，故参数文件为可靠路径。

(async () => {
  const fs = require('fs')
  const path = require('path')

  // ---------- 0. 参数加载（env 优先，回退参数文件） ----------
  function loadParams() {
    const p = {}
    if (process.env.SHIFT) p.shift = process.env.SHIFT
    if (process.env.CONFIG) p.configPath = process.env.CONFIG
    if (process.env.QID) p.qid = process.env.QID
    if (process.env.CONTENT) p.content = process.env.CONTENT
    if (process.env.CONTENT_FILE) p.contentFile = process.env.CONTENT_FILE
    if (process.env.KW) p.kw = process.env.KW
    if (process.env.LIMIT) p.limit = process.env.LIMIT
    if (process.env.COMMENT_TEXT) p.commentText = process.env.COMMENT_TEXT
    const file = '/tmp/zhihu_shift_params.json'
    if (!p.shift) {
      try {
        const f = JSON.parse(fs.readFileSync(file, 'utf8'))
        for (const k of ['shift', 'configPath', 'qid', 'content', 'contentFile', 'kw', 'limit', 'commentText']) {
          if (f[k] != null && p[k] == null) p[k] = f[k]
        }
        cliLog('PARAMS_FROM_FILE: ' + file)
      } catch (e) {
        cliLog('PARAMS_FILE_MISSING: ' + file + ' (' + e.message + ')')
      }
    }
    return p
  }
  const P = loadParams()

  // ---------- 1. 加载配置 ----------
  function loadConfig() {
    const candidates = []
    if (P.configPath) candidates.push(P.configPath)
    if (process.env.CONFIG) candidates.push(process.env.CONFIG)
    candidates.push('/tmp/zhihu_config.json')
    candidates.push(path.join(process.cwd(), 'config.json'))
    candidates.push(path.join(process.cwd(), 'config.example.json'))
    candidates.push('/Users/songhonglei/.workbuddy/skills/zhihu-yanghao/config.json')
    candidates.push('/Users/songhonglei/.workbuddy/skills/zhihu-yanghao/config.example.json')
    for (const c of candidates) {
      if (!c) continue
      try { return { path: c, data: JSON.parse(fs.readFileSync(c, 'utf8')) } } catch (e) {}
    }
    return null
  }
  const cfg = loadConfig()
  if (!cfg) { cliLog('ERROR: no config.json found'); return }
  cliLog('CONFIG_LOADED: ' + cfg.path)

  const SHIFT = (P.shift || '').toLowerCase()
  if (!['morning', 'noon', 'evening'].includes(SHIFT)) {
    cliLog('ERROR: set SHIFT=morning|noon|evening (or shift in params file)'); return
  }
  const shiftCfg = (cfg.data.shifts || {})[SHIFT]
  if (!shiftCfg || shiftCfg.enabled === false) {
    cliLog('SHIFT_DISABLED: ' + SHIFT + ' (set enabled:true in config to run)'); return
  }
  cliLog('SHIFT: ' + SHIFT + ' answer=' + !!shiftCfg.answer)

  // ---------- 2. 话题轮转（全局池 + 日序号偏移） ----------
  function dayOfYear(d) {
    const start = new Date(d.getFullYear(), 0, 0)
    const diff = d - start
    return Math.floor(diff / 86400000)
  }
  const pool = (cfg.data.topic_pool || []).filter(Boolean)
  let kw = P.kw
  if (!kw && pool.length) {
    const offsets = { morning: 0, noon: 1, evening: 2 }
    const n = pool.length
    const base = dayOfYear(new Date()) + offsets[SHIFT]
    const pick = [pool[base % n], pool[(base + 1) % n], pool[(base + 2) % n]].filter(Boolean)
    kw = pick.join(',')
  }
  cliLog('ROTATED_KW: ' + kw)

  // ---------- 3. 选题（QID 未指定时自动选） ----------
  async function pickQuestion(keywords, limit) {
    const space = 'zhihu-pick'
    const task = await useOrCreateTaskSpace(space)
    await openOrReuseTab('https://www.zhihu.com/hot', { wait: true, timeout: 20 })
    await wait(5)
    const kws = keywords.split(',').map(function (s) { return s.trim() }).filter(Boolean)
    const hot = await js('(() => {'
      + ' const items = Array.from(document.querySelectorAll(".HotItem"));'
      + ' const out = [];'
      + ' for (let i = 0; i < items.length && i < ' + limit + '; i++) {'
      + '   const el = items[i];'
      + '   const a = el.querySelector("a");'
      + '   const titleEl = el.querySelector(".HotItem-title") || a;'
      + '   const metrics = el.querySelector(".HotItem-metrics");'
      + '   out.push({ i: i, title: titleEl ? titleEl.innerText.trim() : "", href: a ? a.getAttribute("href") : "", metrics: metrics ? metrics.innerText.trim() : "" });'
      + ' }'
      + ' return out.filter(function (x) { return x.title; });'
      + '})()')
    const hit = hot.filter(function (x) { return kws.some(function (k) { return x.title.indexOf(k) >= 0; }); })
    cliLog('HOT_TOTAL: ' + hot.length + ' KEYWORD_HITS: ' + hit.length)
    cliLog('HITS: ' + JSON.stringify(hit.map(function (x) { return x.title + ' [' + x.metrics + ']'; }), null, 2))
    let chosen = null
    for (let i = 0; i < hit.length; i++) {
      const m = (hit[i].href || '').match(/question\/(\d+)/)
      if (m) { chosen = { qid: m[1], title: hit[i].title }; break }
    }
    if (!chosen) {
      for (let i = 0; i < hot.length; i++) {
        const m = (hot[i].href || '').match(/question\/(\d+)/)
        if (m) { chosen = { qid: m[1], title: hot[i].title }; break }
      }
    }
    await completeTaskSpace(space, { keep: false })
    return chosen
  }

  let qid = P.qid
  let chosenTitle = ''
  if (!qid) {
    const limit = parseInt(P.limit || '25', 10)
    const c = await pickQuestion(kw, limit)
    if (!c) { cliLog('ERROR: no candidate question found for KW=' + kw); return }
    qid = c.qid; chosenTitle = c.title
    cliLog('PICKED qid=' + qid + ' title=' + chosenTitle)
  } else {
    cliLog('QID_OVERRIDE: ' + qid)
  }

  const space = 'zhihu-shift-' + SHIFT + '-' + qid
  const task = await useOrCreateTaskSpace(space)
  const url = 'https://www.zhihu.com/question/' + qid
  await openOrReuseTab(url, { wait: true, timeout: 20 })
  await wait(4)

  // ---------- 4. 已答过跳过 ----------
  const answered = await js('(() => {'
    + ' const btns = Array.from(document.querySelectorAll("button"));'
    + ' return btns.some(function (b) { return b.innerText.indexOf("查看我的回答") >= 0; });'
    + '})()')
  cliLog('already-answered: ' + answered)
  if (answered) {
    cliLog('SKIP: question already answered, pick another')
    await completeTaskSpace(space, { keep: false })
    return
  }

  // ---------- 5. 点赞：前 pool 个候选里随机选 min~max 个（自然化，避免每次固定点赞前 N 被风控） ----------
  cliLog('simulating read 90s (risk control)...')
  await wait(90)
  const interactions = shiftCfg.interactions || {}

  // like spec 兼容：旧式整数 N（=固定 N 个） / 新式对象 {pool,min,max}
  function parseLikeSpec(raw) {
    if (raw == null) return null
    if (typeof raw === 'number') return { pool: raw, min: raw, max: raw }
    if (typeof raw === 'object') {
      const pool = parseInt(raw.pool, 10)
      let min = parseInt(raw.min, 10)
      let max = parseInt(raw.max, 10)
      if (isNaN(pool)) return null
      if (isNaN(min)) min = pool
      if (isNaN(max)) max = pool
      if (min > max) { const t = min; min = max; max = t }
      return { pool: pool, min: min, max: max }
    }
    return null
  }
  const likeSpec = parseLikeSpec(interactions.like)

  if (likeSpec) {
    const before = await js('(() => {'
      + ' const seen = new Set(); const arr = [];'
      + ' const nodes = document.querySelectorAll("[data-zop]");'
      + ' for (let i = 0; i < nodes.length; i++) {'
      + '   let zop; try { zop = JSON.parse(nodes[i].getAttribute("data-zop")); } catch (e) { continue; }'
      + '   if (!zop.itemId || seen.has(zop.itemId)) continue;'
      + '   seen.add(zop.itemId);'
      + '   if (arr.length >= ' + likeSpec.pool + ') break;'
      + '   const b = nodes[i].querySelector("button[aria-label*=赞同]");'
      + '   arr.push({ itemId: zop.itemId, voteText: b ? b.innerText.trim() : "" });'
      + ' }'
      + ' return arr;'
      + '})()')
    cliLog('CANDIDATE_POOL(' + likeSpec.pool + '): ' + before.length + ' answers collected')
    const n = before.length
    const minC = Math.min(likeSpec.min, n)
    const maxC = Math.min(likeSpec.max, n)
    const count = n === 0 ? 0 : (minC + Math.floor(Math.random() * (maxC - minC + 1)))
    cliLog('RANDOM_LIKE_COUNT: ' + count + ' (min=' + likeSpec.min + ' max=' + likeSpec.max + ' avail=' + n + ')')
    const shuffled = before.slice()
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      const t = shuffled[i]; shuffled[i] = shuffled[j]; shuffled[j] = t
    }
    const picks = shuffled.slice(0, count)
    cliLog('PICKED_ITEMIDS: ' + JSON.stringify(picks.map(function (x) { return x.itemId; })))
    const results = []
    for (let i = 0; i < picks.length; i++) {
      const itemId = picks[i].itemId
      const vt = picks[i].voteText
      if (vt.indexOf('已赞同') >= 0) { results.push({ itemId: itemId, action: 'skip_already_liked' }); cliLog('skip already-liked ' + itemId); continue }
      const clicked = await js('((id) => {'
        + ' const nodes = document.querySelectorAll("[data-zop]");'
        + ' for (let i = 0; i < nodes.length; i++) {'
        + '   let zop; try { zop = JSON.parse(nodes[i].getAttribute("data-zop")); } catch (e) { continue; }'
        + '   if (zop.itemId === id) {'
        + '     const b = nodes[i].querySelector("button[aria-label*=赞同]");'
        + '     if (b) { b.click(); return b.innerText.trim(); }'
        + '   }'
        + ' }'
        + ' return null;'
        + '})(' + JSON.stringify(itemId) + ')')
      results.push({ itemId: itemId, after: clicked })
      cliLog('liked ' + itemId + ' -> ' + clicked)
      if (i < picks.length - 1) { const gap = 35 + Math.floor(Math.random() * 45); await wait(gap) }
    }
    cliLog('LIKE_RESULT: ' + JSON.stringify(results))
  } else {
    cliLog('like disabled for this shift (interactions.like = 0/null)')
  }

  // ---------- 6. 写回答（answer=true 时） ----------
  let aid = null
  if (shiftCfg.answer) {
    let content = P.content || ''
    if (P.contentFile) content = fs.readFileSync(P.contentFile, 'utf8')
    if (!content.trim()) {
      cliLog('WARN: answer=true but no content — skipping answer (do NOT publish empty)')
    } else {
      const opened = await js('(() => {'
        + ' const btns = Array.from(document.querySelectorAll("button"));'
        + ' const b = btns.find(function (x) { return x.innerText.indexOf("写回答") >= 0; });'
        + ' if (b) { b.click(); return true; }'
        + ' return false;'
        + '})()')
      cliLog('editor-opened: ' + opened)
      await wait(3)
      await js('((text) => {'
        + ' const editor = document.querySelector(".public-DraftEditor-content");'
        + ' if (!editor) return false;'
        + ' editor.focus();'
        + ' const range = document.createRange();'
        + ' range.selectNodeContents(editor);'
        + ' range.collapse(false);'
        + ' const sel = window.getSelection();'
        + ' sel.removeAllRanges();'
        + ' sel.addRange(range);'
        + ' const dt = new DataTransfer();'
        + ' dt.setData("text/plain", text);'
        + ' editor.dispatchEvent(new ClipboardEvent("paste", { clipboardData: dt, bubbles: true, cancelable: true, composed: true }));'
        + ' return true;'
        + '})(' + JSON.stringify(content) + ')')
      await wait(2)
      cliLog('risk-control wait 60s before publish...')
      await wait(60)
      const pub = await js('(() => {'
        + ' const btns = Array.from(document.querySelectorAll("button"));'
        + ' const b = btns.find(function (x) { return x.innerText.trim() === "发布回答"; });'
        + ' if (b) { b.click(); return true; }'
        + ' return false;'
        + '})()')
      cliLog('publish-clicked: ' + pub)
      await wait(8)
      const info = await pageInfo()
      cliLog('after-publish-url: ' + info.url)
      const m = info.url.match(/answer\/(\d+)/)
      if (m) {
        aid = m[1]
        cliLog('PUBLISHED aid=' + aid)
      } else {
        cliLog('WARN: url did not jump to /answer/{aid} — possible publish stuck (see risk-control: do NOT retry)')
      }
    }
  } else {
    cliLog('answer disabled for this shift')
  }

  // ---------- 7. 验证未折叠（带 retry：刚发布的 answer 索引可能滞后返回 404） ----------
  if (aid) {
    let collapsed = '?'
    let raw = ''
    const MAX_TRIES = 5
    for (let attempt = 1; attempt <= MAX_TRIES; attempt++) {
      try {
        raw = (await serverFetch('https://www.zhihu.com/api/v4/answers/' + aid) || '').toString()
        const i1 = raw.indexOf('is_collapsed')
        if (i1 >= 0) {
          collapsed = raw.substr(i1, 24)
          cliLog('API_VERIFY attempt ' + attempt + ' is_collapsed=' + collapsed)
          break
        }
        cliLog('API_VERIFY attempt ' + attempt + ': is_collapsed not in body yet (index lag), retrying...')
      } catch (e) {
        cliLog('API_VERIFY attempt ' + attempt + ' ERR: ' + (e && e.message ? e.message : String(e)))
      }
      if (attempt < MAX_TRIES) {
        const gap = 10 + Math.floor(Math.random() * 6) // 10-15s 随机间隔，等索引跟上
        cliLog('API_VERIFY wait ' + gap + 's before retry')
        await wait(gap)
      }
    }
    cliLog('API_VERIFY_FINAL is_collapsed=' + collapsed)
  }

  // ---------- 8. 可选互动：收藏 / 关注问题 / 评论 ----------
  if (interactions.collect) {
    const done = await js('(() => {'
      + ' const btns = Array.from(document.querySelectorAll("button"));'
      + ' const b = btns.find(function (x) { return x.innerText.indexOf("收藏") >= 0; });'
      + ' if (!b) return "no_button";'
      + ' if (b.innerText.indexOf("已收藏") >= 0) return "already";'
      + ' b.click(); return "clicked";'
      + '})()')
    cliLog('COLLECT: ' + done)
    await wait(3)
  }
  if (interactions.follow) {
    const done = await js('(() => {'
      + ' const btns = Array.from(document.querySelectorAll("button"));'
      + ' const b = btns.find(function (x) { return x.innerText.indexOf("关注问题") >= 0; });'
      + ' if (!b) return "no_button";'
      + ' if (b.innerText.indexOf("取消关注") >= 0) return "already";'
      + ' b.click(); return "clicked";'
      + '})()')
    cliLog('FOLLOW_QUESTION: ' + done)
    await wait(3)
  }
  if (interactions.comment) {
    const opened = await js('(() => {'
      + ' const btns = Array.from(document.querySelectorAll("button"));'
      + ' const b = btns.find(function (x) { return x.innerText.indexOf("添加评论") >= 0; });'
      + ' if (b) { b.click(); return true; }'
      + ' return false;'
      + '})()')
    cliLog('COMMENT_EDITOR_OPENED: ' + opened)
    if (opened) {
      await wait(3)
      const txt = P.commentText || ''
      if (txt) {
        let filled = 'no_text'
        try {
          await fillInput('.CommentEditor-input, [contenteditable="true"][data-placeholder*="评论"]', txt)
          filled = true
        } catch (e) { filled = 'fill_failed:' + e.message }
        cliLog('COMMENT_FILLED: ' + filled)
        if (filled === true) {
          const sent = await js('(() => {'
            + ' const btns = Array.from(document.querySelectorAll("button"));'
            + ' const b = btns.find(function (x) { return x.innerText.trim() === "发布" || x.innerText.trim() === "发送"; });'
            + ' if (b) { b.click(); return true; }'
            + ' return false;'
            + '})()')
          cliLog('COMMENT_SENT: ' + sent)
          await wait(3)
        }
      } else {
        cliLog('COMMENT_SKIP: no commentText provided')
      }
    }
  }

  cliLog('SHIFT_DONE: ' + SHIFT + ' qid=' + qid + (aid ? ' aid=' + aid : ''))
  await completeTaskSpace(space, { keep: false })
})()

// 参数文件 schema（/tmp/zhihu_shift_params.json）：
// {
//   "shift": "morning|noon|evening",
//   "qid": "2070982459156424668",          // 可选，跳过自动选题
//   "contentFile": "/abs/answer.txt",       // answer=true 时必填其一
//   "content": "回答正文...",                // 或直接内联
//   "configPath": "/abs/config.json",       // 可选
//   "kw": "历史,神话",                       // 可选，覆盖轮转
//   "limit": 25,                            // 可选
//   "commentText": "评论内容"               // 可选，comment=true 时
// }
