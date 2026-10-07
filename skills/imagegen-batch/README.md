# imagegen-batch

> 用 ImageGen 等文生图工具**安全地批量生成多张图片**。把「防覆盖 / 避水印 / 防塌脸」这三件事的处理顺序和判断标准固定下来。

## Features

- **三道防覆盖机制** —— 提示词唯一前缀 + 默认顺序发 + 生成后立刻 `mv` 重命名。文生图工具的文件名是「截断的提示词前缀 + 秒级时间戳」，同前缀 + 同一秒 = 静默互相覆盖，谁都不知道丢了图。
- **量水印，不猜** —— AI 水印固定压右下角。本 skill 给出一条「放大右下角 + 画坐标刻度」的量法，读出上沿的准确 y 值再裁，**不凭感觉裁**；并附 1536×1024 / 1408×704 两种尺寸的实测经验值。
- **留白相框可选** —— prompt 里写「四周留白」模型基本不遵守，要留白边只能用 `scripts/add_frame.py` 后期加。**默认不加框**，用户明确要求时才传 `--frame`；要加就用 `--line 0`（纯留白、不画黑线框）。
- **人物「标识包」防塌脸** —— 同组图里每个角色固定五个维度（脸型骨相 / 五官 / 发型 / 体态 / 标志物），跨图复用同一套措辞。只写「一个方脸一个瘦脸」会塌成同一张脸。
- **风格库** —— 已命名风格 `白纸速写`（`paper-sketch`）与 `水墨文艺风`（`ink-wash`），各带招牌配方、可复用后缀、调性变体和实测有效的分镜参考。以后只说名字，不必重述整段 prompt。
- **五条实测避坑** —— 转义拼中文会写错字、并行会撞 `ECONNRESET`、想让物件变小得改形状而不是给数值……每条都注明实测日期和当时踩的具体坑。

## 什么场景用它

| 场景 | 说明 |
|---|---|
| 公众号 / 博客 封面 + 正文插图 | 一张封面立主题，其余按小标题顺序各配一张 |
| 同风格系列图 | 需要多张图看起来像一套（同风格、同人物） |
| 卡片 / 长图 / 信息图素材 | 批量出图，统一尺寸与留白 |
| 单张图的重出与微调 | 改白边宽度、换比例、去水印不必重新生图 |

## Quick Start

```bash
# Install (clawhub)
clawhub install imagegen-batch

# Or clone the mono-repo; the skill lives in skills/imagegen-batch/
git clone https://github.com/Songhonglei/better-office-work-flow.git
```

## Usage

详细规则见 [SKILL.md](./SKILL.md)，风格档案见 [references/style-library.md](./references/style-library.md)。

触发示例：

- 「给这篇文章生成封面和 5 张插图」→ 分镜 + 批量生成 + 归档
- 「用白纸速写风格做一套」→ 直接调风格库里的 `paper-sketch` 配方
- 「图片右下角有水印」→ 量水印 → 按量裁 → 验真
- 「这几张图的人物长得一样」→ 上「标识包」重出

## 后期脚本

`scripts/add_frame.py`（依赖 Pillow）—— 裁水印（必做）+ 可选的留白边框。

```bash
python3 -m pip install Pillow          # 唯一依赖

S=scripts/add_frame.py

# 默认：只裁水印，不加框
python3 "$S" in.png out.png --crop-bottom 80
python3 "$S" in.png out.png --crop-bottom 70 --ratio 2.35        # 头条封面（2.35:1），再 sips -z 383 900

# 用户明确要求留白边时，才加 --frame
python3 "$S" in.png out.png --crop-bottom 80 --frame --line 0
python3 "$S" in.png out.png --crop-bottom 70 --frame --ratio 1 --pad 0.04 --line 0   # 方形次条封面
```

| 参数 | 默认 | 说明 |
|---|---|---|
| `--frame` | 关 | **加框总开关，默认不加**；用户要求留白边时才传 |
| `--pad` | 0.06 | 外侧白边，取**短边**的比例；5%~6% 观感最好 |
| `--gap` | 11 | 图像与线框之间的白隙（px）；`--line 0` 时它就是图像到外沿的留白 |
| `--line` | 3 | 线框粗细（px）；**传 0 = 只留白边不画线**（推荐） |
| `--crop-bottom` | 0 | 先裁掉底部 N px（去水印） |
| `--ratio` | — | 裁到指定比例，用二分拟合、不用手算；不加框时指图像本身，加框时指含框后的整体 |

> **加框会改变整体比例**，且 `pad` 依赖短边、短边又随裁切变化——手算必然错。要精确到目标比例请用脚本内置的 `fit_ratio()`。

## Install in your AI agent

| Agent | Install |
|---|---|
| WorkBuddy | 复制到 `~/.workbuddy/skills/` |
| Claude Code | 复制到 `~/.claude/skills/` |
| Cursor | 复制到 `.cursor/skills/` |
| OpenClaw | `clawhub install imagegen-batch` |

## License

MIT (see [LICENSE](./LICENSE))

## Author

Evan Song · [github.com/Songhonglei](https://github.com/Songhonglei)

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for the full version history.
