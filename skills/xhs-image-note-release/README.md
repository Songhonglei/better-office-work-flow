# xhs-image-note-release

> 通过 ego-browser 自动化发布小红书图文笔记，核心解决 closed Shadow DOM 发布按钮无法点击的问题。

## Features

- 全自动 9 步流程：打开创作平台 → 上传图片 → 填标题/正文 → 发布 → 清理
- CDP 批量上传图片（绕过 uploadFile 逗号分隔不生效的坑）
- **穿透 closed Shadow DOM 点击发布按钮**（`_onPublish()` 方法调用）
- 附带一键发布脚本，改 4 个参数即可复用
- **内置卡片生成器**，24 种主题、统一小红书金句卡布局、支持自定义页码/账号等参数
- 完整技术文档含 5 种失败方案对比表

## Card Themes (24)

所有主题共用同一套布局（顶部标签 + 引号 / 中间大字 / 底部副标题 + 页码 + 账号），改布局一次全生效。

<table>
<tr>
<td align="center"><img src="assets/themes/warm.jpg" width="230"><br><code>warm</code><br>温暖哲思</td>
<td align="center"><img src="assets/themes/y2k.jpg" width="230"><br><code>y2k</code><br>Y2K 千禧潮酷</td>
<td align="center"><img src="assets/themes/doodle.jpg" width="230"><br><code>doodle</code><br>手绘涂鸦</td>
</tr>
<tr>
<td align="center"><img src="assets/themes/pop.jpg" width="230"><br><code>pop</code><br>渐变波普</td>
<td align="center"><img src="assets/themes/minimal.jpg" width="230"><br><code>minimal</code><br>极简日系</td>
<td align="center"><img src="assets/themes/cyberpunk.jpg" width="230"><br><code>cyberpunk</code><br>赛博科技</td>
</tr>
<tr>
<td align="center"><img src="assets/themes/elegant.jpg" width="230"><br><code>elegant</code><br>极简优雅</td>
<td align="center"><img src="assets/themes/apple.jpg" width="230"><br><code>apple</code><br>Apple 质感</td>
<td align="center"><img src="assets/themes/cowork.jpg" width="230"><br><code>cowork</code><br>轻科技</td>
</tr>
<tr>
<td align="center"><img src="assets/themes/newspaper.jpg" width="230"><br><code>newspaper</code><br>报纸杂志</td>
<td align="center"><img src="assets/themes/bloomberg.jpg" width="230"><br><code>bloomberg</code><br>Bloomberg 终端</td>
<td align="center"><img src="assets/themes/ink.jpg" width="230"><br><code>ink</code><br>水墨卷轴</td>
</tr>
<tr>
<td align="center"><img src="assets/themes/steampunk.jpg" width="230"><br><code>steampunk</code><br>蒸汽朋克</td>
<td align="center"><img src="assets/themes/xhs.jpg" width="230"><br><code>xhs</code><br>小红书·简洁</td>
<td align="center"><img src="assets/themes/xhs_rich.jpg" width="230"><br><code>xhs_rich</code><br>小红书·丰富</td>
</tr>
<tr>
<td align="center"><img src="assets/themes/morandi.jpg" width="230"><br><code>morandi</code><br>莫兰迪灰</td>
<td align="center"><img src="assets/themes/glass.jpg" width="230"><br><code>glass</code><br>玻璃拟态</td>
<td align="center"><img src="assets/themes/palace.jpg" width="230"><br><code>palace</code><br>故宫金红</td>
</tr>
<tr>
<td align="center"><img src="assets/themes/fresh.jpg" width="230"><br><code>fresh</code><br>清新绿</td>
<td align="center"><img src="assets/themes/earthy.jpg" width="230"><br><code>earthy</code><br>大地原木</td>
<td align="center"><img src="assets/themes/dreamy.jpg" width="230"><br><code>dreamy</code><br>紫梦幻</td>
</tr>
<tr>
<td align="center"><img src="assets/themes/macaron.jpg" width="230"><br><code>macaron</code><br>马卡龙</td>
<td align="center"><img src="assets/themes/carbon.jpg" width="230"><br><code>carbon</code><br>暗色极简</td>
<td align="center"><img src="assets/themes/vivid.jpg" width="230"><br><code>vivid</code><br>活力渐变</td>
</tr>
</table>

```bash
# 生成单张卡片
python3 references/card-generator/card_generator.py \
  --theme xhs_rich \
  --tag "人生随笔" \
  --lines "周五了\n你还活着吗\n去外面走走" \
  --subtitle "关于活着" \
  --page-number 1 --total-pages 6 \
  --account "@雨夜心灯" \
  -o card.png

# 查看全部主题清单
python3 references/card-generator/card_generator.py --list-themes
```

## Dependencies

| 依赖 | 类型 | 安装方式 |
|------|------|----------|
| **ego-browser** (ego-lite) | CLI 工具 + Skill | `bash ~/.workbuddy/skills/ego-browser/scripts/install.sh` |
| **小红书账号** | 平台账号 | 在 ego-lite 中手动登录 creator.xiaohongshu.com |
| **WorkBuddy 沙箱关闭** | 环境配置 | WorkBuddy 设置 → 关闭沙箱 |

> 详见 [SKILL.md](./SKILL.md) 的 Dependencies 章节。

## Quick Start

```bash
# 从本仓库安装
git clone https://github.com/Songhonglei/better-office-work-flow.git
cp -r better-office-work-flow/skills/xhs-image-note-release ~/.workbuddy/skills/
```

## Usage

详细使用方法见 [SKILL.md](./SKILL.md)。

## Install in your AI agent

| Agent | Install |
|---|---|
| OpenClaw | `clawhub install xhs-image-note-release` |
| Claude Code | Manual: copy to `~/.claude/skills/` |
| Cursor | Manual: copy to `.cursor/skills/` |
| WorkBuddy | Manual: copy to `~/.workbuddy/skills/` |

## License

MIT (see repo [LICENSE](../../LICENSE))

## Author

Evan Song · [github.com/Songhonglei](https://github.com/Songhonglei)

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for the full version history.
