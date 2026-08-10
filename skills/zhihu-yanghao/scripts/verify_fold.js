(async () => {
  const aid = process.env.AID
  if (!aid) { cliLog('ERROR: set AID env var'); return }
  const qid = process.env.QID
  const space = 'zhihu-verify-' + aid
  const task = await useOrCreateTaskSpace(space)

  if (qid) {
    const target = 'https://www.zhihu.com/question/' + qid + '/answer/' + aid
    await openOrReuseTab(target, { wait: true, timeout: 20 })
    await wait(4)
    const page = await js('(() => {'
      + ' const btns = Array.from(document.querySelectorAll("button"));'
      + ' const hasEdit = btns.some(function(b){ return b.innerText.indexOf("编辑回答") >= 0; });'
      + ' const body = document.body.innerText;'
      + ' const hasFoldTip = body.indexOf("被折叠") >= 0 || body.indexOf("已折叠") >= 0;'
      + ' const rc = document.querySelector(".RichContent-inner");'
      + ' const snippet = rc ? rc.innerText.trim().slice(0, 60) : "";'
      + ' return { hasEdit: hasEdit, hasFoldTip: hasFoldTip, snippet: snippet };'
      + '})()')
    cliLog('PAGE_VERIFY: ' + JSON.stringify(page))
  } else {
    cliLog('no QID provided, skipping page check (API check only)')
  }

  let apiInfo = 'n/a'
  try {
    const api = await serverFetch('https://www.zhihu.com/api/v4/answers/' + aid)
    const raw = (api || '').toString()
    const i1 = raw.indexOf('is_collapsed')
    const i2 = raw.indexOf('isFolded')
    apiInfo = JSON.stringify({
      is_collapsed: i1 >= 0 ? raw.substr(i1, 24) : '?',
      isFolded: i2 >= 0 ? raw.substr(i2, 18) : '?'
    })
  } catch (e) {
    apiInfo = 'API_ERR: ' + e.message
  }
  cliLog('API_VERIFY: ' + apiInfo)
  await completeTaskSpace(space, { keep: false })
})()
