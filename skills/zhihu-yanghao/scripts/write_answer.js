(async () => {
  const qid = process.env.QID
  let content = process.env.CONTENT || ''
  if (process.env.CONTENT_FILE) {
    const fs = require('fs')
    content = fs.readFileSync(process.env.CONTENT_FILE, 'utf8')
  }
  if (!qid || !content.trim()) { cliLog('ERROR: set QID and CONTENT (or CONTENT_FILE)'); return }

  const space = 'zhihu-answer-' + qid
  const task = await useOrCreateTaskSpace(space)
  const url = 'https://www.zhihu.com/question/' + qid
  await openOrReuseTab(url, { wait: true, timeout: 20 })
  await wait(3)

  const opened = await js('(() => {'
    + ' const btns = Array.from(document.querySelectorAll("button"));'
    + ' const b = btns.find(function(x){ return x.innerText.indexOf("写回答") >= 0; });'
    + ' if (b) { b.click(); return true; }'
    + ' return false;'
    + '})()')
  cliLog('editor-opened: ' + opened)
  await wait(3)

  // 直接 UTF-8 中文，勿用 String.raw；content 内用空行分段（fillInput 保留段落）
  await fillInput('.public-DraftEditor-content', content)
  await wait(2)

  cliLog('risk-control wait 60s before publish...')
  await wait(60)

  const pub = await js('(() => {'
    + ' const btns = Array.from(document.querySelectorAll("button"));'
    + ' const b = btns.find(function(x){ return x.innerText.trim() === "发布回答"; });'
    + ' if (b) { b.click(); return true; }'
    + ' return false;'
    + '})()')
  cliLog('publish-clicked: ' + pub)
  await wait(8)

  const info = await pageInfo()
  cliLog('after-publish-url: ' + info.url)
  const m = info.url.match(/answer\/(\d+)/)
  if (m) {
    const aid = m[1]
    cliLog('PUBLISHED aid=' + aid)
    cliLog('verify with: AID=' + aid + ' QID=' + qid + ' ego-browser nodejs < scripts/verify_fold.js')
  } else {
    cliLog('WARN: url did not jump to /answer/{aid} — possible publish stuck (see risk-control: do NOT retry)')
  }
  await completeTaskSpace(space, { keep: false })
})()
