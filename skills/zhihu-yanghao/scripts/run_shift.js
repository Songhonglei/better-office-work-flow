// run_shift.js — 知乎养号三班编排脚本（zhihu-yanghao v1.1.0）
// 用法（Bash 必须 dangerouslyDisableSandbox:true，且关闭沙箱开关）：
//   CONFIG=/path/config.json SHIFT=morning ego-browser nodejs < scripts/run_shift.js
//   SHIFT=noon QID=2021300214389043782 CONTENT_FILE=/tmp/a.txt ego-browser nodejs < scripts/run_shift.js
//
// 行为：读 config.json → 按 班次+日序号 轮转话题池取关键词 → 选未答过问题(QID 可覆盖)
//        → 前10随机3-5赞(差值自校正) → 若 answer=true 写/发布/验证1回答 → 按 interactions 做可选收藏/关注/评论
//
// env：
//   CONFIG      配置文件路径（默认 ../config.json，找不到回退 ../config.example.json）
//   SHIFT       morning|noon|evening（必填）
//   QID         指定问题 qid（可选，跳过自动选题）
//   CONTENT     回答正文（answer=true 时必填其一）
//   CONTENT_FILE 回答正文文件路径（优先于 CONTENT）
//   KW          覆盖轮转关键词（可选，逗号分隔）

(async () => {
  const fs = require('fs')
  const path = require('path')

  // ---------- 1. 加载配置 ----------
  function loadConfig() {
    const candidates = []
    if (process.env.CONFIG) candidates.push(process.env.CONFIG)
    candidates.push(path.join(__dirname, '..', 'config.json'))
    candidates.push(path.join(__dirname, '..', 'config.example.json'))
    for (const c of candidates) {
      try { return { path: c, data: JSON.parse(fs.readFileSync(c, 'utf8')) } } catch (e) {}
    }
    return null
  }
  const cfg = loadConfig()
  if (!cfg) { cliLog('ERROR: no config.json found (looked for CONFIG env, ../config.json, ../config.example.json)'); return }
  cliLog('CONFIG_LOADED: ' + cfg.path)

  const SHIFT = (process.env.SHIFT || '').toLowerCase()
  if (!['morning', 'noon', 'evening'].includes(SHIFT)) {
    cliLog('ERROR: set SHIFT=morning|noon|evening'); return
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
  let kw = process.env.KW
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

  let qid = process.env.QID
  let chosenTitle = ''
  if (!qid) {
    const limit = parseInt(process.env.LIMIT || '25', 10)
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

  // ---------- 5. 点赞（前10随机3–5，差值自校正） ----------
  cliLog('simulating read 90s (risk control)...')
  await wait(90)
  const interactions = shiftCfg.interactions || {}
  const likeMax = parseInt(interactions.like || '0', 10)

  if (likeMax > 0) {
    // 候选池：取前 10 个回答（知乎每条回答挂在 data-zop 节点上），已赞的排除
    const candidates = await js('(() => {'
      + ' const seen = new Set(); const arr = [];'
      + ' const nodes = document.querySelectorAll("[data-zop]");'
      + ' for (let i = 0; i < nodes.length; i++) {'
      + '   let zop; try { zop = JSON.parse(nodes[i].getAttribute("data-zop")); } catch (e) { continue; }'
      + '   if (!zop.itemId || seen.has(zop.itemId)) continue;'
      + '   seen.add(zop.itemId);'
      + '   if (arr.length >= 10) break;'
      + '   const b = nodes[i].querySelector("button[aria-label*=赞同]");'
      + '   arr.push({ itemId: zop.itemId, active: b ? b.classList.contains("is-active") : false });'
      + ' }'
      + ' return arr;'
      + '})()')
    cliLog('CANDIDATES_10: ' + JSON.stringify(candidates))

    // 从可赞候选里随机选 3–5 个（受 likeMax 上限约束），贴近真人随机行为、抗风控
    const likeable = candidates.filter(function (x) { return !x.active })
    let target = 3 + Math.floor(Math.random() * 3) // 3,4,5
    target = Math.min(target, likeMax, likeable.length)
    if (target < 0) target = 0
    const selected = likeable.slice().sort(function () { return Math.random() - 0.5 }).slice(0, target)
    cliLog('LIKE_PLAN: target=' + target + ' selected=' + JSON.stringify(selected.map(function (s) { return s.itemId })))

    const results = []
    for (let i = 0; i < selected.length; i++) {
      const itemId = selected[i].itemId
      const clicked = await js('((id) => {'
        + ' const nodes = document.querySelectorAll("[data-zop]");'
        + ' for (let i = 0; i < nodes.length; i++) {'
        + '   let zop; try { zop = JSON.parse(nodes[i].getAttribute("data-zop")); } catch (e) { continue; }'
        + '   if (zop.itemId === id) {'
        + '     const b = nodes[i].querySelector("button[aria-label*=赞同]");'
        + '     if (b) {'
        + '       if (b.classList.contains("is-active")) return "already_active";'
        + '       b.click(); return (b.getAttribute("aria-label")||"").trim();'
        + '     }'
        + '   }'
        + ' }'
        + ' return null;'
        + '})(' + JSON.stringify(itemId) + ')')
      results.push({ itemId: itemId, after: clicked })
      cliLog('liked ' + itemId + ' -> ' + clicked)
      if (i < selected.length - 1) { const gap = 35 + Math.floor(Math.random() * 45); await wait(gap) }
    }
    cliLog('LIKE_RESULT: ' + JSON.stringify(results))
  } else {
    cliLog('like disabled for this shift (like:0)')
  }

  // ---------- 6. 写回答（answer=true 时） ----------
  let aid = null
  if (shiftCfg.answer) {
    let content = process.env.CONTENT || ''
    if (process.env.CONTENT_FILE) content = fs.readFileSync(process.env.CONTENT_FILE, 'utf8')
    if (!content.trim()) {
      cliLog('WARN: answer=true but no CONTENT/CONTENT_FILE — skipping answer (do NOT publish empty)')
    } else {
      const opened = await js('(() => {'
        + ' const btns = Array.from(document.querySelectorAll("button"));'
        + ' const b = btns.find(function (x) { return x.innerText.indexOf("写回答") >= 0; });'
        + ' if (b) { b.click(); return true; }'
        + ' return false;'
        + '})()')
      cliLog('editor-opened: ' + opened)
      await wait(3)
      await fillInput('.public-DraftEditor-content', content)
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

  // ---------- 7. 验证未折叠 + API 真值 ----------
  if (aid) {
    const api = await serverFetch('https://www.zhihu.com/api/v4/answers/' + aid + '?include=content,is_collapsed,voteup_count,updated_time')
    const raw = (api || '').toString()
    const i1 = raw.indexOf('is_collapsed')
    cliLog('API_VERIFY is_collapsed=' + (i1 >= 0 ? raw.substr(i1, 24) : '?'))
    const i2 = raw.indexOf('updated_time')
    cliLog('API_VERIFY updated_time=' + (i2 >= 0 ? raw.substr(i2, 24) : '?'))
    const hasEscape = /\\u[0-9a-fA-F]{4}/.test(raw)
    cliLog('API_VERIFY content_has_unicode_escape=' + hasEscape + ' (false=OK, 见 8/4 乱码教训)')
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
    // 实验性：评论触发审核敏感，默认关闭。选择器可能随知乎改版失效，失败即跳过。
    const opened = await js('(() => {'
      + ' const btns = Array.from(document.querySelectorAll("button"));'
      + ' const b = btns.find(function (x) { return x.innerText.indexOf("添加评论") >= 0; });'
      + ' if (b) { b.click(); return true; }'
      + ' return false;'
      + '})()')
    cliLog('COMMENT_EDITOR_OPENED: ' + opened)
    if (opened) {
      await wait(3)
      const txt = process.env.COMMENT_TEXT || ''
      if (txt) {
        const filled = await (async () => {
          try {
            await fillInput('.CommentEditor-input, [contenteditable="true"][data-placeholder*="评论"]', txt)
            return true
          } catch (e) { return 'fill_failed:' + e.message }
        })()
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
        cliLog('COMMENT_SKIP: no COMMENT_TEXT provided')
      }
    }
  }

  cliLog('SHIFT_DONE: ' + SHIFT + ' qid=' + qid + (aid ? ' aid=' + aid : ''))
  await completeTaskSpace(space, { keep: false })
})()
