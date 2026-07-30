#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WorkBuddy Token Usage Analyzer — Neon Dashboard Edition
生成科技炫酷风格的 HTML 报告，含动态粒子背景、渐变发光、交互式图表。
"""

import sqlite3
import json
import os
import argparse
from datetime import datetime, timedelta
from collections import defaultdict, Counter

DB_PATH = os.path.expanduser("~/.workbuddy/workbuddy.db")

MODEL_LABELS = {
    "auto": "🤖 自动选择",
    "balanced-model": "⚖️ 平衡模型",
    "hy3": "🌊 Hy3",
    "deepseek-v4-pro": "🐋 DeepSeek V4 Pro",
    "deepseek-v4-flash": "⚡ DeepSeek V4 Flash",
    "kimi-k2.6": "🌙 Kimi K2.6",
    "glm-5.2": "🧠 GLM-5.2",
}

def get_model_label(model: str) -> str:
    if model is None:
        return "❓ 未知"
    if model.startswith("custom-local:"):
        return "🔧 " + model.replace("custom-local:", "")
    return MODEL_LABELS.get(model, f"📦 {model}")

def parse_credit(credit_json_str: str) -> dict:
    if not credit_json_str:
        return {}
    try:
        return json.loads(credit_json_str)
    except json.JSONDecodeError:
        return {}

def format_tokens(tokens: int) -> str:
    """将 token 数量格式化为人类可读形式
    0 → 0
    <1KB → 1 KB
    1KB–1MB → xxx KB (保留1位小数)
    1MB–1GB → xxx MB (保留1位小数)
    >=1GB → xxx GB (保留1位小数)
    """
    if tokens == 0:
        return "0"
    if tokens < 1024:
        return "1 KB"
    elif tokens < 1024 * 1024:
        return f"{tokens / 1024:.1f} KB"
    elif tokens < 1024 * 1024 * 1024:
        return f"{tokens / (1024 * 1024):.1f} MB"
    else:
        return f"{tokens / (1024 * 1024 * 1024):.1f} GB"

def ms_to_date_str(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d")

class TokenAnalyzer:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = None
        self._connect()

    def _connect(self):
        if not os.path.exists(self.db_path):
            print(f"❌ 数据库文件不存在: {self.db_path}")
            return
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        if self.conn:
            self.conn.close()

    def get_sessions_with_usage(self, days: int = 30) -> list:
        if not self.conn:
            return []
        cutoff_ms = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        rows = self.conn.execute('''
            SELECT s.id, s.title, s.model, s.created_at, s.is_background_automation, s.mode,
                   su.used, su.size, su.credit_json
            FROM sessions s
            LEFT JOIN session_usage su ON s.id = su.session_id
            WHERE s.created_at >= ? AND s.status != 'Deleted'
            ORDER BY s.created_at DESC
        ''', (cutoff_ms,)).fetchall()

        sessions = []
        for row in rows:
            credit_details = parse_credit(row["credit_json"] or "")
            credit_total = sum(credit_details.values()) if credit_details else 0.0
            sessions.append({
                "session_id": row["id"],
                "title": row["title"] or "(无标题)",
                "model": row["model"] or "unknown",
                "date": ms_to_date_str(row["created_at"]),
                "is_automation": bool(row["is_background_automation"]),
                "mode": row["mode"] or "unknown",
                "used_tokens": row["used"] or 0,
                "credit_total": round(credit_total, 2),
                "credit_details": credit_details,
            })
        return sessions

    def summarize(self, sessions: list):
        daily = defaultdict(lambda: {"credit": 0.0, "tokens": 0, "count": 0, "models": Counter()})
        models = defaultdict(lambda: {"credit": 0.0, "tokens": 0, "count": 0})
        for s in sessions:
            d = s["date"]
            daily[d]["credit"] += s["credit_total"]
            daily[d]["tokens"] += s["used_tokens"]
            daily[d]["count"] += 1
            daily[d]["models"][s["model"]] += 1
            m = s["model"]
            models[m]["credit"] += s["credit_total"]
            models[m]["tokens"] += s["used_tokens"]
            models[m]["count"] += 1
        for m in models:
            models[m]["avg"] = round(models[m]["credit"] / models[m]["count"], 2)
            models[m]["credit"] = round(models[m]["credit"], 2)
        daily = dict(sorted(daily.items(), reverse=True))
        models = dict(sorted(models.items(), key=lambda x: x[1]["credit"], reverse=True))
        top = sorted(sessions, key=lambda x: x["credit_total"], reverse=True)
        return daily, models, top

    def generate_suggestions(self, sessions: list, models: dict, daily: dict) -> list:
        suggestions = []
        total_credit = sum(s["credit_total"] for s in sessions)
        total_sessions = len(sessions)
        automation_sessions = [s for s in sessions if s["is_automation"]]

        if models:
            top_model = list(models.keys())[0]
            top_data = models[top_model]
            top_label = get_model_label(top_model)
            if top_model in ["deepseek-v4-pro", "kimi-k2.6"]:
                suggestions.append({
                    "priority": "high",
                    "category": "模型选择",
                    "title": f"Top 消耗模型 {top_label} 占主导",
                    "detail": f"累计 {top_data['credit']:.2f} credits，平均每次 {top_data['avg']:.2f}。非关键任务建议切换轻量模型。",
                    "action": "总结/分类/简单提取任务使用 deepseek-v4-flash 或 auto 模式"
                })

            custom_models = {k: v for k, v in models.items() if k.startswith("custom-local:")}
            if custom_models:
                suggestions.append({
                    "priority": "medium",
                    "category": "自定义模型",
                    "title": f"检测到 {len(custom_models)} 个自定义模型",
                    "detail": "自定义模型计费方式可能不同，建议确认是否按需加载。",
                    "action": "自定义模型用于特定场景，通用任务使用平台内置模型"
                })

        if automation_sessions and total_credit > 0:
            auto_credit = sum(s["credit_total"] for s in automation_sessions)
            auto_pct = auto_credit / total_credit * 100
            if auto_pct > 30:
                suggestions.append({
                    "priority": "high",
                    "category": "自动化优化",
                    "title": f"自动化任务占 {auto_pct:.1f}% 消耗",
                    "detail": f"自动化会话 {len(automation_sessions)} 个，累计 {auto_credit:.2f} credits。",
                    "action": "检查自动化 prompt 是否过长，精简指令或降低执行频率"
                })

        long_sessions = [s for s in sessions if s["used_tokens"] > 500000]
        if long_sessions:
            suggestions.append({
                "priority": "high",
                "category": "上下文管理",
                "title": f"发现 {len(long_sessions)} 个超长上下文会话",
                "detail": "这些会话 used_tokens > 500K，可能携带大量历史消息。",
                "action": "定期开启新会话，避免单一会话累积过多上下文"
            })

        if daily:
            max_day = max(daily.items(), key=lambda x: x[1]["credit"])
            avg = sum(d["credit"] for d in daily.values()) / len(daily)
            if max_day[1]["credit"] > avg * 2:
                suggestions.append({
                    "priority": "medium",
                    "category": "使用模式",
                    "title": f"日期 {max_day[0]} 消耗异常高",
                    "detail": f"该日消耗 {max_day[1]['credit']:.2f} credits，是平均值的 {max_day[1]['credit']/avg:.1f} 倍。",
                    "action": "回顾当天操作，是否有批量任务或调试反复重试"
                })

        suggestions.append({
            "priority": "medium",
            "category": "通用优化",
            "title": "使用更短的 Prompt",
            "detail": "精简提示词，删除冗余指令和示例。",
            "action": "将复杂任务拆分为多个小任务，避免单 prompt 过长"
        })

        suggestions.append({
            "priority": "medium",
            "category": "通用优化",
            "title": "善用 '继续' 而非重复请求",
            "detail": "长输出任务使用 '继续' 续接，而非重新发送完整请求。",
            "action": "对于长文生成，使用分段续写策略"
        })

        return suggestions

    def build_html(self, sessions: list, daily: dict, models: dict, top: list,
                   suggestions: list, days: int, top_n: int) -> str:
        total_credit = sum(s["credit_total"] for s in sessions)
        total_tokens = sum(s["used_tokens"] for s in sessions)
        total_sessions = len(sessions)
        auto_count = sum(1 for s in sessions if s["is_automation"])
        active_days = len(daily)
        avg_credit = round(total_credit / total_sessions, 2) if total_sessions else 0
        auto_pct = round(auto_count / total_sessions * 100, 1) if total_sessions else 0
        total_tokens_fmt = format_tokens(total_tokens)

        # Model table rows
        model_rows = ""
        for m, d in models.items():
            label = get_model_label(m)
            is_custom = m.startswith("custom-local:")
            tag_class = "custom" if is_custom else ("auto" if m == "auto" else "pro")
            model_rows += f'''                            <tr>
                                <td><span class="model-tag {tag_class}">{label}</span></td>
                                <td>{d["credit"]:.2f}</td>
                                <td>{d["count"]}</td>
                                <td>{d["avg"]:.2f}</td>
                            </tr>\n'''

        # Top table rows
        top_rows = ""
        max_credit = top[0]["credit_total"] if top else 1
        for i, t in enumerate(top[:top_n], 1):
            rank_class = f"rank-{i}" if i <= 3 else "rank-other"
            model_label = get_model_label(t["model"])
            is_custom = t["model"].startswith("custom-local:")
            tag_class = "custom" if is_custom else ("auto" if t["model"] == "auto" else "pro")
            type_badge = '<span class="type-badge type-auto">自动</span>' if t["is_automation"] else '<span class="type-badge type-manual">手动</span>'
            pct = t["credit_total"] / max_credit * 100 if max_credit else 0
            title = t["title"][:30] if len(t["title"]) <= 30 else t["title"][:27] + "..."
            top_rows += f'''                            <tr>
                                <td><span class="rank-badge {rank_class}">{i}</span></td>
                                <td title="{t["title"]}">{title}</td>
                                <td><span class="model-tag {tag_class}">{model_label}</span></td>
                                <td>{type_badge}</td>
                                <td>
                                    {t["credit_total"]:.2f}
                                    <div class="credit-bar"><div class="credit-bar-fill" style="width:{pct:.1f}%"></div></div>
                                </td>
                                <td>{format_tokens(t["used_tokens"])}</td>
                            </tr>\n'''

        # Suggestions HTML
        sug_html = ""
        for i, sug in enumerate(suggestions, 1):
            p_class = sug["priority"]
            sug_html += f'''            <div class="suggestion {p_class}">
                <div class="sug-header">
                    <span class="sug-priority {p_class}">{p_class.upper()}</span>
                    <h4>{i}. {sug["category"]} — {sug["title"]}</h4>
                </div>
                <p>{sug["detail"]}</p>
                <div class="action">✅ {sug["action"]}</div>
            </div>\n'''

        # Data JSON for JS
        data = {
            "daily": {k: {"credit": round(v["credit"], 2), "tokens": v["tokens"], "count": v["count"]} for k, v in daily.items()},
            "models": {k: {"credit": v["credit"], "count": v["count"], "avg": v["avg"]} for k, v in models.items()},
            "model_labels": MODEL_LABELS,
        }
        data_json = json.dumps(data, ensure_ascii=False)

        # Read template
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wb_token_report_template.html")
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Replace placeholders
        replacements = {
            "{GENERATED_AT}": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "{DAYS}": str(days),
            "{TOTAL_CREDIT}": str(int(total_credit)),
            "{AVG_CREDIT}": str(avg_credit),
            "{TOTAL_TOKENS}": str(total_tokens),
            "{TOTAL_TOKENS_FMT}": total_tokens_fmt,
            "{TOTAL_SESSIONS}": str(total_sessions),
            "{ACTIVE_DAYS}": str(active_days),
            "{AUTO_COUNT}": str(auto_count),
            "{AUTO_PCT}": str(auto_pct),
            "{TOP_N}": str(top_n),
            "{MODEL_TABLE_ROWS}": model_rows,
            "{TOP_TABLE_ROWS}": top_rows,
            "{SUGGESTIONS_HTML}": sug_html,
            "{DATA_JSON}": data_json,
        }
        for key, val in replacements.items():
            html = html.replace(key, val)

        return html


def main():
    parser = argparse.ArgumentParser(description="WorkBuddy Token Analyzer — Neon Dashboard")
    parser.add_argument("--days", type=int, default=30, help="分析最近 N 天 (默认: 30)")
    parser.add_argument("--top", type=int, default=15, help="Top N 消耗任务 (默认: 15)")
    parser.add_argument("--export", type=str, default=None, help="导出 HTML 到指定路径")
    parser.add_argument("--db", type=str, default=DB_PATH, help="数据库路径")
    parser.add_argument("--no-open", action="store_true", help="不自动打开浏览器")
    args = parser.parse_args()

    analyzer = TokenAnalyzer(args.db)
    if not analyzer.conn:
        return

    try:
        sessions = analyzer.get_sessions_with_usage(args.days)
        if not sessions:
            print("⚠️ 该时间段内无数据")
            return

        daily, models, top = analyzer.summarize(sessions)
        suggestions = analyzer.generate_suggestions(sessions, models, daily)

        output_path = args.export or os.path.join(os.path.dirname(os.path.abspath(__file__)), f"wb_token_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        html = analyzer.build_html(sessions, daily, models, top, suggestions, args.days, args.top)

        output_dir = os.path.dirname(os.path.abspath(output_path))
        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ Neon Dashboard 报告已生成: {output_path}")

        if not args.no_open:
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(output_path)}")
    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
