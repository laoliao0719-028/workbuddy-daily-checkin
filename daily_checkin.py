#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WorkBuddy 每日自动签到（无头版，供 GitHub Actions 调用）"""
import json
import os
import sys
import requests

API_HOST = "https://copilot.tencent.com"
CHECKIN_URL = API_HOST + "/v2/billing/meter/daily-checkin"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

def load_accounts():
    raw = os.environ.get("WORKBUDDY_ACCOUNTS", "").strip()
    if raw:
        try:
            return json.loads(raw).get("accounts", [])
        except Exception as e:
            print("[E] WORKBUDDY_ACCOUNTS 不是合法 JSON: %s" % e, file=sys.stderr)
    for path in ("accounts.json", "签到token.json"):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f).get("accounts", [])
            except Exception as e:
                print("[E] 读取 %s 失败: %s" % (path, e), file=sys.stderr)
    return []

def build_headers(token):
    return {
        "Authorization": "Bearer %s" % token,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": UA,
        "Origin": API_HOST,
        "Referer": API_HOST + "/",
    }

def classify(resp):
    try:
        data = resp.json()
    except Exception:
        data = {}
    code = data.get("code")
    msg = str(data.get("msg", ""))
    if resp.status_code == 200 and ("成功" in msg or code in (0, 200)):
        return "ok", (msg or "签到成功")
    if code == 10001 or "已签到" in msg or "请明天" in msg:
        return "already", (msg or "今日已签")
    if any(k in msg for k in ("失效", "过期", "无效", "expired", "invalid")):
        return "expired", (msg or "Token 失效")
    if resp.status_code == 200:
        return "already", (msg or "今日已签(推断)")
    return "failed", "HTTP %s %s" % (resp.status_code, msg or resp.text[:120])

def do_checkin(acct):
    name = acct.get("name", "?")
    token = acct.get("token", "")
    if not token:
        return "failed", "缺少 token"
    try:
        resp = requests.post(CHECKIN_URL, headers=build_headers(token), json={}, timeout=25)
    except Exception as e:
        return "failed", "网络错误: %s" % e
    return classify(resp)

def push(title, content):
    token = os.environ.get("PUSHPLUS_TOKEN")
    if token:
        try:
            requests.post("http://www.pushplus.plus/send", json={"token": token, "title": title, "content": content}, timeout=15)
        except Exception:
            pass
    key = os.environ.get("SERVERCHAN_KEY")
    if key:
        try:
            requests.post("https://sctapi.ftqq.com/%s.send" % key, data={"title": title, "desp": content}, timeout=15)
        except Exception:
            pass

def mask(name):
    s = str(name)
    if len(s) == 11 and s.isdigit():
        return s[:3] + "****" + s[7:]
    if len(s) > 4:
        return s[:2] + "***" + s[-2:]
    return s

def main():
    accounts = load_accounts()
    if not accounts:
        print("[E] 没有可用账号，请配置 WORKBUDDY_ACCOUNTS 或本地 accounts.json")
        sys.exit(1)
    print("=== 开始签到，共 %d 个账号 ===" % len(accounts))
    lines = []
    summary = {"ok": 0, "already": 0, "expired": 0, "failed": 0}
    for acct in accounts:
        name = acct.get("name", "?")
        status, detail = do_checkin(acct)
        summary[status] += 1
        icon = {"ok": "✅", "already": "🟢", "expired": "⚠️", "failed": "❌"}[status]
        print("%s %s: %s" % (icon, mask(name), detail))
        lines.append("%s %s: %s" % (icon, name, detail))
    total = ("签到完成 | 成功 %d / 已签 %d / 失效 %d / 失败 %d" % (summary["ok"], summary["already"], summary["expired"], summary["failed"]))
    print(total)
    lines.append(total)
    push("WorkBuddy 签到", "\n".join(lines))

if __name__ == "__main__":
    main()
