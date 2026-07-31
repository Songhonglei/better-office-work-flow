#!/bin/bash
set -euo pipefail
# ============================================================
# 小红书图文笔记自动发布脚本
# 依赖：ego-browser (ego-lite) 已安装且正在运行
# 用法：修改下方参数后 bash publish_note.sh
# ============================================================

export PATH="$HOME/.local/bin:$PATH"

# ---- 参数配置（按需修改）----
IMAGE_DIR=""                        # 图片所在目录（绝对路径）
IMAGES=""                           # 图片文件名，逗号分隔
TITLE=""                            # 笔记标题（严禁包含单引号）
BODY=''                             # 笔记正文（支持 \n 换行和 #话题标签；严禁包含反引号和 ${）
# ---- 参数配置结束 ----

# 参数校验
if [ -z "$IMAGE_DIR" ] || [ -z "$IMAGES" ] || [ -z "$TITLE" ] || [ -z "$BODY" ]; then
  echo "ERROR: 请先填写 IMAGE_DIR, IMAGES, TITLE, BODY 四个参数"
  exit 1
fi

# 检查 ego-browser 是否可用
if ! command -v ego-browser &>/dev/null; then
  echo "ERROR: ego-browser 未安装或不在 PATH 中"
  echo "请先安装 ego-lite: sh ~/.workbuddy/skills/ego-browser/scripts/install.sh"
  exit 1
fi

# 检查 TITLE 不含单引号
if echo "$TITLE" | grep -q "'"; then
  echo "ERROR: TITLE 含单引号，会导致脚本注入，请移除单引号后重试"
  exit 1
fi

# 检查 BODY 不含反引号或 ${
if echo "$BODY" | grep -q '`' || echo "$BODY" | grep -q '${'; then
  echo "ERROR: BODY 含反引号或 \${，会导致脚本注入，请移除后重试"
  exit 1
fi

# 通过环境变量传递参数，避免 shell 注入风险
export IMAGE_DIR IMAGES TITLE BODY

# 将逗号分隔的图片名转为数组（用于显示统计）
IFS=',' read -ra IMG_ARRAY <<< "$IMAGES"

echo "=========================================="
echo "小红书图文笔记自动发布"
echo "  图片目录: $IMAGE_DIR"
echo "  图片数量: ${#IMG_ARRAY[@]}"
echo "  标题: $TITLE"
echo "=========================================="
echo ""

# 使用 <<'EOF' 阻止 shell 展开，所有变量通过 process.env 读取
ego-browser nodejs <<'EOF'
// 从环境变量安全读取参数（避免 shell 注入）
const imageDir = process.env.IMAGE_DIR
const images = process.env.IMAGES.split(',').map(s => s.trim()).filter(Boolean)
const filePaths = images.map(img => imageDir + '/' + img)
const title = process.env.TITLE
const body = process.env.BODY

// ===== 第1步：创建/复用 task space =====
const task = await useOrCreateTaskSpace('publish xhs note')
cliLog('task space: ' + task.id)

// ===== 第2步：打开小红书创作平台 =====
await openOrReuseTab('https://creator.xiaohongshu.com/publish/publish', { wait: true, timeout: 25 })

// Vue SPA，需要等待 15 秒渲染
cliLog('waiting for SPA to render...')
await wait(15)

// 验证登录状态
const loginCheck = await js(`(() => {
  const text = document.body ? document.body.innerText : ''
  if (text.includes('登录') && !text.includes('发布')) return { loggedIn: false }
  return { loggedIn: true }
})()`)
cliLog('Login status: ' + JSON.stringify(loginCheck))

if (!loginCheck.loggedIn) {
  cliLog('ERROR: 未登录小红书，请先在 ego-lite 中登录')
  await completeTaskSpace(task.id, { keep: true })
  process.exit(1)
}

// ===== 第3步：进入图文发布页 =====
const pageText = await snapshotText()

// 尝试点击"发布笔记"展开下拉菜单
const matchPublish = pageText.match(/发布笔记.*?\[ref=(\d+)/)
if (matchPublish) {
  await click('@' + matchPublish[1], { label: 'click 发布笔记 dropdown' })
  await wait(2)

  const text2 = await snapshotText()
  const matchUpload = text2.match(/上传图文.*?\[ref=(\d+)/)
  if (matchUpload) {
    await click('@' + matchUpload[1], { label: 'click 上传图文' })
    await waitForNetworkIdle(5)
    await wait(3)
  }
}

// ===== 第4步：上传图片（CDP 批量设置 file input）=====
cliLog('Uploading ' + filePaths.length + ' files...')

const doc = await cdp('DOM.getDocument', {})
const inputNode = await cdp('DOM.querySelector', {
  nodeId: doc.root.nodeId,
  selector: 'input.upload-input'
})

if (!inputNode || !inputNode.nodeId) {
  cliLog('ERROR: 找不到图片上传 input，页面可能未正确加载')
  await completeTaskSpace(task.id, { keep: true })
  process.exit(1)
}

await cdp('DOM.setFileInputFiles', {
  files: filePaths,
  nodeId: inputNode.nodeId
})
cliLog('Files uploaded via CDP')

// 等待图片上传和处理
await wait(8)

// ===== 第5步：填写标题 =====
cliLog('Filling title...')
await fillInput('css:input[placeholder="填写标题会有更多赞哦"]', title, { label: 'fill title' })
await wait(1)

// ===== 第6步：填写正文 =====
cliLog('Filling body text...')

await js(`document.querySelector('[contenteditable="true"]')?.focus()`)
await wait(0.5)

await typeText(body, { label: 'type body text' })
await wait(1)

// 按 Esc 关闭话题建议弹窗
await pressKey('Escape')
await wait(1)

// ===== 第7步：点击发布按钮 =====
// 关键：小红书发布按钮在 <xhs-publish-btn> 的 closed Shadow DOM 内
// 常规方法全部无效，直接调用组件内部方法 _onPublish()
cliLog('Triggering publish via _onPublish()...')
const publishResult = await js(`(() => {
  const host = document.querySelector('xhs-publish-btn')
  if (!host) return { error: 'no xhs-publish-btn found' }
  if (typeof host._onPublish !== 'function') return { error: 'no _onPublish method' }

  const submitDisabled = host.getAttribute('submit-disabled')
  const submitLoading = host.getAttribute('submit-loading')

  if (submitDisabled === 'true') {
    return { error: 'publish button is disabled', submitDisabled, submitLoading }
  }

  host._onPublish()
  return { triggered: true, submitDisabled, submitLoading }
})()`)
cliLog('Publish result: ' + JSON.stringify(publishResult, null, 2))

if (publishResult.error) {
  cliLog('ERROR: ' + publishResult.error)
  await completeTaskSpace(task.id, { keep: true })
  process.exit(1)
}

// ===== 第8步：等待发布完成 =====
cliLog('Waiting for publish to complete...')
await wait(10)

const info = await pageInfo()
cliLog('URL after publish: ' + info.url)

if (info.url.includes('note-manage')) {
  cliLog('SUCCESS: 笔记发布成功！')
} else {
  await wait(5)
  const info2 = await pageInfo()
  if (info2.url.includes('note-manage')) {
    cliLog('SUCCESS: 笔记发布成功！')
  } else {
    cliLog('WARNING: 发布状态不确定，请手动检查小红书笔记管理页')
  }
}

// 截图存档
const shot = await captureScreenshot()
cliLog('Final screenshot: ' + shot)

// ===== 第9步：清理 =====
await completeTaskSpace(task.id, { keep: false })
cliLog('Task completed, space cleaned up')
EOF

echo ""
echo "=========================================="
echo "发布流程结束"
echo "=========================================="
