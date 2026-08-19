(async () => {
  const qid = process.env.QID
  if (!qid) { cliLog('ERROR: set QID env var'); return }
  const space = 'zhihu-like-' + qid
  const task = await useOrCreateTaskSpace(space)
  const url = 'https://www.zhihu.com/question/' + qid
  await openOrReuseTab(url, { wait: true, timeout: 20 })
  await wait(4)

  const answered = await js('(() => {'
    + ' const btns = Array.from(document.querySelectorAll("button"));'
    + ' return btns.some(function(b){ return b.innerText.indexOf("查看我的回答") >= 0; });'
    + '})()')
  cliLog('already-answered: ' + answered)
  if (answered) {
    cliLog('SKIP: question already answered, pick another')
    await completeTaskSpace(space, { keep: false })
    return
  }

  cliLog('simulating read 90s (risk control)...')
  await wait(90)

  // 候选池：前 10 个回答，已赞排除，再从中随机选 3–5 个点赞（抗风控）
  const candidates = await js('(() => {'
    + ' const seen = new Set(); const arr = [];'
    + ' const nodes = document.querySelectorAll("[data-zop]");'
    + ' for (let i=0;i<nodes.length;i++){'
    + '   let zop; try { zop = JSON.parse(nodes[i].getAttribute("data-zop")); } catch(e){ continue; }'
    + '   if (!zop.itemId || seen.has(zop.itemId)) continue;'
    + '   seen.add(zop.itemId);'
    + '   if (arr.length >= 10) break;'
    + '   const b = nodes[i].querySelector("button[aria-label*=赞同]");'
    + '   arr.push({ itemId: zop.itemId, active: b ? b.classList.contains("is-active") : false });'
    + ' }'
    + ' return arr;'
    + '})()')
  cliLog('CANDIDATES_10: ' + JSON.stringify(candidates))

  const likeable = candidates.filter(function (x) { return !x.active })
  let target = 3 + Math.floor(Math.random() * 3) // 3,4,5
  target = Math.min(target, likeable.length)
  if (target < 0) target = 0
  const selected = likeable.slice().sort(function () { return Math.random() - 0.5 }).slice(0, target)
  cliLog('LIKE_PLAN: target=' + target + ' selected=' + JSON.stringify(selected.map(function (s) { return s.itemId })))

  const results = []
  for (let i=0;i<selected.length;i++){
    const itemId = selected[i].itemId
    const clicked = await js('((id) => {'
      + ' const nodes = document.querySelectorAll("[data-zop]");'
      + ' for (let i=0;i<nodes.length;i++){'
      + '   let zop; try { zop = JSON.parse(nodes[i].getAttribute("data-zop")); } catch(e){ continue; }'
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
    if (i < selected.length - 1) { const gap = 35 + Math.floor(Math.random()*45); await wait(gap) }
  }
  cliLog('LIKE_RESULT: ' + JSON.stringify(results, null, 2))
  await completeTaskSpace(space, { keep: false })
})()
