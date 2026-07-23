#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""invoice_forward.py — 邮箱发票自动转发（配置驱动，无人值守）

流程：IMAP 扫描收件箱主题含关键词的邮件 → 下载 PDF 附件解析 →
     命中抬头规则（默认全部）→ SMTP 标准化转发（主题/正文模板 + 原始 PDF）。

子命令：
  check                体检：配置 / 凭证 / 依赖 / IMAP / SMTP 逐项验证（setup 后必跑）
  scan  [--days N]     干跑预览：列出候选、解析结果、将执行的动作（不发送、不写状态）
  run   [--days N]     正式执行：转发命中发票 + 写去重状态 + 生成报告
  parse <pdf路径>      调试：查看单个 PDF 的字段提取结果

配置：默认 ~/.workbuddy/invoice-forward/config.json（--config 或环境变量
      INVOICE_FORWARD_CONFIG 覆盖）。模板见 references/config.example.json。
凭证：授权码存独立 secrets 文件（默认 ~/.workbuddy/secrets/invoice-forward.env，
      chmod 600），字段 MAIL_USER / MAIL_AUTH_CODE。绝不写入 config 或 skill 包。
去重：state 文件按 Message-ID + 发票号双重去重（QQ 邮箱 IMAP UID 跨会话会重排，
      不可用 UID/序号做去重键）。
依赖：pdfplumber（主，视觉顺序提取）与 pymupdf/fitz（兜底），至少其一。
"""
import argparse
import collections
import datetime
import imaplib
import json
import os
import re
import smtplib
import sys
from email import message_from_bytes
from email.header import Header, decode_header, make_header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

__version__ = "1.0.0"

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.workbuddy/invoice-forward/config.json")
DEFAULTS = {
    "account": {
        "imap_host": "imap.qq.com", "imap_port": 993,
        "smtp_host": "smtp.qq.com", "smtp_port": 465,
        "secrets_file": "~/.workbuddy/secrets/invoice-forward.env",
    },
    "scan": {"days": 7, "subject_keywords": ["发票"], "folder": "INBOX"},
    "rule": {"buyer_whitelist": []},
    "forward": {
        "to": [],
        "subject_tpl": "{item} {amount} {date}",
        "body_tpl": "发票号码：{invoice_no}\n开票日期：{date}\n购买方（抬头）：{buyer}\n"
                    "销售方：{seller}\n物品：{item}\n价税合计：{amount}",
    },
    "state_file": "~/.workbuddy/invoice-forward/processed.json",
}


# ---------- 配置与凭证 ----------

def _merge(base, override):
    out = dict(base)
    for k, v in (override or {}).items():
        out[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def load_config(path):
    if not os.path.exists(path):
        sys.exit("未找到配置文件 %s\n参照 references/config.example.json 创建，"
                 "或让 WorkBuddy 按 SKILL.md 的 setup 流程引导生成。" % path)
    try:
        cfg = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        sys.exit("配置文件 JSON 解析失败：%s" % e)
    return _merge(DEFAULTS, cfg), path


def load_cred(secrets_path):
    p = os.path.expanduser(secrets_path)
    if not os.path.exists(p):
        sys.exit("未找到凭证文件 %s（需含 MAIL_USER / MAIL_AUTH_CODE，权限 600）" % p)
    try:
        with open(p, encoding="utf-8") as fp:
            kv = dict(l.split("=", 1) for l in fp if "=" in l and not l.startswith("#"))
    except OSError as e:
        sys.exit("凭证文件 %s 读取失败：%s（检查文件权限）" % (p, e))
    user = (kv.get("MAIL_USER") or "").strip()
    code = (kv.get("MAIL_AUTH_CODE") or "").strip()
    if not user or not code:
        sys.exit("凭证文件 %s 缺少 MAIL_USER 或 MAIL_AUTH_CODE" % p)
    return user, code


# ---------- 发票 PDF 解析 ----------

def dhead(s):
    if not s:
        return ""
    try:
        return str(make_header(decode_header(s)))
    except Exception:
        return s


def pdf_text(data: bytes) -> str:
    """pdfplumber 按视觉顺序提取（发票标签和值同行）；fitz 是内容流顺序，
    OFD 转换的发票会把标签和值拆到两个文本块导致正则失配，仅作兜底。"""
    try:
        import io
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return "\n".join((p.extract_text() or "") for p in pdf.pages)
    except ImportError:
        pass
    except Exception:
        return ""
    try:
        import fitz
        with fitz.open(stream=data, filetype="pdf") as doc:
            return "\n".join(pg.get_text() for pg in doc)
    except Exception:
        return ""


# 在「单位词 / xx.xx 金额 / ¥ / x% 税率」前截断。\b 保护商品名里的套装/批次等词
_UNIT = r"(?:台|个|件|份|本|张|套|箱|袋|瓶|只|副|双|次|项|批|组)"
_CUT = re.compile(r"\s+(?=" + _UNIT + r"\b|\d+\.\d{2}\b|[¥￥]|\d+(?:\.\d+)?%)")
# 商品名续行排除：表头/金额/合计类行
_BAD = re.compile(r"项目名称|价税|备注|开票人|合计|规格|税额|税率|\d+\.\d{2}|[¥￥]")


def extract(text: str) -> dict:
    """从发票全文提取转发所需字段。"""
    f = {"item": "", "amount": "", "date": "", "invoice_no": "", "seller": "", "buyer": ""}
    m = re.search(r"名称[:：]\s*([^\s]+)", text)          # 购买方名称（购/销同模板，第一个）
    if m:
        f["buyer"] = m.group(1)
    m = re.search(r"销售方\s*名称[:：]\s*([^\s]+)", text)     # 销售方名称
    if m:
        f["seller"] = m.group(1)
    lines = text.split("\n")
    for i, l in enumerate(lines):
        m = re.search(r"\*[^*\n]+\*\s*(.+)", l)           # *税收分类*商品名 行
        if m:
            item = _CUT.split(m.group(1).strip(), maxsplit=1)[0].strip()
            nl = lines[i + 1].strip() if i + 1 < len(lines) else ""  # 型号常折到下一行
            if nl and not _BAD.search(nl) and len(nl) <= 30:
                item = (item + " " + nl).strip()
            f["item"] = item
            break
    m = re.search(r"（小写）\s*[¥￥]?\s*([\d,]+\.\d{2})", text)
    if m:
        f["amount"] = m.group(1).replace(",", "")
    m = re.search(r"开票日期[:：]\s*(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)", text)
    if m:
        f["date"] = re.sub(r"\s+", "", m.group(1))
    m = re.search(r"发票号码[:：]\s*(\d{12,30})", text)
    if m:
        f["invoice_no"] = m.group(1)
    return f


def find_pdf(msg):
    """在 MIME 树里找 PDF 附件：文件名 / content-type / %PDF 魔数三重判定。"""
    for part in msg.walk():
        payload = part.get_payload(decode=True) or b""
        fn = dhead(part.get_filename() or "")
        if payload and (fn.lower().endswith(".pdf")
                        or "pdf" in part.get_content_type().lower()
                        or payload[:4] == b"%PDF"):
            return payload, fn or "invoice.pdf"
    return b"", ""


# ---------- IMAP ----------

def imap_scan(user, code, cfg, days):
    """单连接完成 登录→SINCE 搜索→批量取主题过滤。
    返回 (imap连接, 候选列表[(uid, msgid, subject)], 近 days 天邮件总数)。
    连接保持打开供 imap_fetch_pdf 复用，调用方负责 logout。"""
    acc = cfg["account"]
    imap = imaplib.IMAP4_SSL(acc["imap_host"], acc["imap_port"], timeout=30)
    imap.login(user, code)
    imap.select(cfg["scan"]["folder"])
    since = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%d-%b-%Y")
    # UID SEARCH 条件必须分开传；整串带括号 "(SINCE ...)" 会被 QQ 服务器静默忽略返回全部
    _, data = imap.uid("SEARCH", None, "SINCE", since)
    uids = data[0].split() if data and data[0] else []
    cand = []
    if uids:
        _, data = imap.uid("FETCH", b",".join(uids),
                           "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM MESSAGE-ID)])")
        kws = cfg["scan"]["subject_keywords"]
        exclude = {a.lower() for a in cfg["forward"]["to"]}  # 防自转发循环
        for part in data:
            if not isinstance(part, tuple):
                continue
            m_uid = re.search(rb"UID (\d+)", part[0])  # 某些服务器可能不带 UID，跳过而非崩溃
            if not m_uid:
                continue
            uid = m_uid.group(1).decode()
            msg = message_from_bytes(part[1])
            subj, frm = dhead(msg.get("Subject")), dhead(msg.get("From"))
            msgid = dhead(msg.get("Message-ID")) or (frm + "|" + subj)
            frm_addr = (re.search(r"[\w.\-]+@[\w.\-]+", frm) or [None])[0]
            if any(k in subj for k in kws) and (frm_addr or "").lower() not in exclude:
                cand.append((uid, msgid, subj))
    return imap, cand, len(uids)


def imap_fetch_pdf(imap, uid):
    _, data = imap.uid("FETCH", uid, "(RFC822)")
    return find_pdf(message_from_bytes(data[0][1]))


# ---------- 转发 ----------

def render(tpl, fields):
    """模板渲染，缺失字段渲染为空串而不是报错。"""
    return tpl.format_map(collections.defaultdict(str, fields))


class SmtpSession:
    """惰性建立的单 SMTP 连接，供逐封发送复用。"""

    def __init__(self, user, code, cfg):
        self.user, self.code, self.cfg, self.conn = user, code, cfg, None

    def send(self, subject, body, pdf, fname):
        if self.conn is None:
            acc = self.cfg["account"]
            self.conn = smtplib.SMTP_SSL(acc["smtp_host"], acc["smtp_port"], timeout=30)
            self.conn.login(self.user, self.code)
        m = MIMEMultipart()
        m["From"] = self.user
        m["To"] = ", ".join(self.cfg["forward"]["to"])
        m["Subject"] = Header(subject, "utf-8")
        m.attach(MIMEText(body, "plain", "utf-8"))
        att = MIMEApplication(pdf, _subtype="pdf")
        att.add_header("Content-Disposition", "attachment", filename=("utf-8", "", fname))
        m.attach(att)
        self.conn.send_message(m)

    def close(self):
        if self.conn:
            try:
                self.conn.quit()
            except Exception:
                pass


# ---------- 状态 ----------

def load_state(path):
    p = os.path.expanduser(path)
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_state(path, state):
    p = os.path.expanduser(path)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fp:
            json.dump(state, fp, ensure_ascii=False, indent=2)
    except OSError as e:
        # 状态写失败必须响亮失败——静默吞掉会导致下次运行重复转发
        sys.exit("状态文件 %s 写入失败：%s（为防重复转发，本次中止）" % (p, e))


def buyer_hit(cfg, fields, text):
    """抬头白名单判定。已提取到购买方时按名称精确比对（允许互为子串，吸收空格差异），
    避免备注栏出现同名公司造成误判；仅当购买方提取失败时才用全文本兜底。"""
    wl = cfg["rule"]["buyer_whitelist"]
    if not wl:
        return True
    buyer = fields.get("buyer", "")
    if buyer:
        return any(name == buyer or name in buyer or buyer in name for name in wl)
    return any(name in text for name in wl)


# ---------- 主流程 ----------

def process(cfg, days, do_send):
    # 防线：无任何 PDF 解析库时直接退出（否则会发出字段全空的转发邮件）
    try:
        import pdfplumber  # noqa
    except ImportError:
        try:
            import fitz  # noqa
        except ImportError:
            sys.exit("缺少 PDF 解析库，请先执行：python3 %s check --install-deps" % os.path.basename(__file__))
    user, code = load_cred(cfg["account"]["secrets_file"])
    state = load_state(cfg["state_file"])
    print("[连接] 正在登录 %s 并扫描近 %d 天邮件…" % (cfg["account"]["imap_host"], days))
    imap, cand, total = imap_scan(user, code, cfg, days)
    print("[扫描] 近 %d 天收件箱 %d 封，发票候选 %d 封" % (days, total, len(cand)))

    todo = [(u, k, s) for u, k, s in cand if k not in state]
    print("[待办] 未处理 %d 封（其余 %d 封已去重跳过）" % (len(todo), len(cand) - len(todo)))

    sent, skipped, no_pdf, failed = [], [], [], []
    smtp = SmtpSession(user, code, cfg) if do_send else None
    for uid, key, subj in todo:
        pdf, fname = imap_fetch_pdf(imap, uid)
        if not pdf:
            no_pdf.append(subj)
            state[key] = {"status": "no_pdf", "subject": subj}
            continue
        text = pdf_text(pdf)
        f = extract(text)
        if not buyer_hit(cfg, f, text):
            skipped.append(subj)
            state[key] = {"status": "skipped", "subject": subj}
            continue
        if f["invoice_no"] and f["invoice_no"] in state.get("_nos", []):
            skipped.append(subj + "（发票号重复）")
            state[key] = {"status": "dup_invoice", "subject": subj}
            continue
        item = f["item"] or re.sub(r"^(转发|Fw)[:：]\s*", "", subj)  # 提取失败回退原主题
        f["item"] = item
        subject = " ".join(render(cfg["forward"]["subject_tpl"], f).split())
        body = render(cfg["forward"]["body_tpl"], f)
        if do_send:
            try:
                smtp.send(subject, body, pdf, fname)
            except Exception as e:
                failed.append((subject, str(e)[:100]))  # 不写状态，下轮自动重试
                continue
            sent.append(subject)
            state[key] = {"status": "sent", "subject": subject}
            save_state(cfg["state_file"], state)  # 每发一封即落盘：中途崩溃重跑也不会重发
        else:
            sent.append(subject + "（预览未发送）")
        if f["invoice_no"]:
            # 同轮内按发票号去重：scan 预览与 run 真实发送必须一致，
            # 否则预览会漏报重复（同一发票被不同邮件多次投递时）。
            state.setdefault("_nos", []).append(f["invoice_no"])
    imap.logout()
    if smtp:
        smtp.close()

    if do_send:
        save_state(cfg["state_file"], state)  # 落盘 skipped/no_pdf/dup 条目

    summary = "[完成] %s %d / 跳过 %d / 无PDF待人工 %d%s" % (
        "已发送" if do_send else "将发送", len(sent), len(skipped), len(no_pdf),
        " / 发送失败 %d" % len(failed) if failed else "")
    print(summary)
    for s in sent:
        print("  ✅", s)
    for s in skipped:
        print("  ⚪ 跳过:", s)
    for s in no_pdf:
        print("  ⚠️ 无PDF:", s)
    for s, err in failed:
        print("  ❌ 发送失败: %s（%s）" % (s, err))

    if do_send:
        now = datetime.datetime.now()
        report = os.path.join(os.path.dirname(os.path.expanduser(cfg["state_file"])),
                              f"报告_{now:%Y%m%d}.md")
        try:
            with open(report, "w", encoding="utf-8") as fp:
                fp.write(f"# 发票转发报告 {now:%Y-%m-%d %H:%M}\n\n- 范围：近 {days} 天；候选 {len(cand)} 封\n- {summary}\n")
                fp.write("\n".join("- ✅ " + s for s in sent))
                fp.write("\n".join("\n- ⚠️ 无PDF: " + s for s in no_pdf))
                fp.write("\n".join("\n- ❌ 发送失败: %s（%s）" % (s, err) for s, err in failed))
            print("[报告]", report)
        except OSError as e:
            # 转发本身已成功，报告写失败只告警不中止
            print("[警告] 报告文件写入失败：%s（不影响本次转发结果）" % e)


def cmd_check(cfg, install_deps=False):
    ok = True

    def step(name, fn):
        nonlocal ok
        try:
            detail = fn()
            print("✓ %s：%s" % (name, detail or "正常"))
        except Exception as e:
            ok = False
            print("✗ %s：%s" % (name, e))

    step("配置文件", lambda: "已加载")
    step("转发收件人", lambda: ", ".join(cfg["forward"]["to"]) or "未配置！请在 config.json 的 forward.to 填写")

    def _deps():
        try:
            import pdfplumber  # noqa
            return "pdfplumber 可用（首选）"
        except ImportError:
            pass
        try:
            import fitz  # noqa
            return "仅 fitz 可用（pdfplumber 缺失，建议：pip install pdfplumber）"
        except ImportError:
            pass
        if not install_deps:
            raise RuntimeError("缺少 pdfplumber/pymupdf；重跑 check --install-deps 可自动安装到当前 Python 环境")
        import subprocess
        print("  … 正在自动安装 pdfplumber pymupdf（pip，当前 Python 环境）")
        try:
            r = subprocess.run([sys.executable, "-m", "pip", "install", "pdfplumber", "pymupdf"],
                               capture_output=True, text=True, timeout=600)
        except Exception as e:
            raise RuntimeError("自动安装执行异常（pip 不可用或超时）：%s" % e)
        if r.returncode != 0:
            raise RuntimeError("自动安装失败：" + (r.stderr or r.stdout)[-300:])
        import importlib
        importlib.invalidate_caches()
        import pdfplumber  # noqa
        return "已自动安装 pdfplumber + pymupdf"
    step("PDF 解析依赖", _deps)
    user, code = None, None

    def _cred():
        nonlocal user, code
        user, code = load_cred(cfg["account"]["secrets_file"])
        return "%s（授权码已读取）" % user
    step("凭证文件", _cred)

    def _imap():
        acc = cfg["account"]
        m = imaplib.IMAP4_SSL(acc["imap_host"], acc["imap_port"], timeout=15)
        m.login(user, code)
        _, d = m.select(cfg["scan"]["folder"], readonly=True)
        m.logout()
        return "登录成功，%s 共 %s 封" % (cfg["scan"]["folder"], d[0].decode())
    step("IMAP 登录", _imap)

    def _smtp():
        acc = cfg["account"]
        s = smtplib.SMTP_SSL(acc["smtp_host"], acc["smtp_port"], timeout=15)
        s.login(user, code)
        s.quit()
        return "登录成功"
    step("SMTP 登录", _smtp)

    print("\n%s" % ("体检通过，可以执行 scan 预览 / run 正式转发" if ok
                    else "体检未通过，请按上面 ✗ 项修复后重跑 check"))
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser(description="邮箱发票自动转发 v%s" % __version__)
    ap.add_argument("--config", default=os.environ.get("INVOICE_FORWARD_CONFIG", DEFAULT_CONFIG_PATH))
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("check")
    sp.add_argument("--install-deps", action="store_true",
                    help="缺少 PDF 解析库时自动 pip 安装到当前 Python 环境")
    for name in ("scan", "run"):
        sp = sub.add_parser(name)
        sp.add_argument("--days", type=int, default=None)
    sp = sub.add_parser("parse")
    sp.add_argument("pdf")
    args = ap.parse_args()

    cfg, _ = load_config(args.config)
    if args.cmd == "check":
        cmd_check(cfg, install_deps=args.install_deps)
    elif args.cmd == "parse":
        try:
            with open(args.pdf, "rb") as fp:
                data = fp.read()
        except OSError as e:
            sys.exit("无法读取 PDF 文件 %s：%s" % (args.pdf, e))
        print(json.dumps(extract(pdf_text(data)), ensure_ascii=False, indent=2))
    else:
        days = args.days or cfg["scan"]["days"]
        if not cfg["forward"]["to"]:
            sys.exit("config.json 的 forward.to 未配置收件人")
        process(cfg, days, do_send=(args.cmd == "run"))


if __name__ == "__main__":
    main()
