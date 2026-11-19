#!/usr/bin/env python3
"""Intenda V4 QA: V3 功能断言复跑 + 双模式主题断言（Playwright 无头）"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:4173/"
results = []
errors = []


def check(name, cond, extra=""):
    results.append((name, bool(cond), extra))
    print(("PASS " if cond else "FAIL ") + name + (f" [{extra}]" if extra and not cond else ""))


def css(page, sel, prop, nth=0):
    return page.evaluate(
        """([sel, prop, nth]) => {
          const el = document.querySelectorAll(sel)[nth];
          if (!el) return null;
          return getComputedStyle(el)[prop];
        }""",
        [sel, prop, nth],
    )


def visible(page, sel):
    return page.evaluate(
        """(sel) => {
          const el = document.querySelector(sel);
          if (!el) return false;
          const s = getComputedStyle(el);
          return s.display !== 'none' && s.visibility !== 'hidden';
        }""",
        sel,
    )


def nav(page, label):
    page.locator(".nav-item", has_text=label).first.click()
    page.wait_for_timeout(350)


with sync_playwright() as p:
    browser = p.chromium.launch()

    # ---------- 会话 A：默认夜间 + 主题切换 ----------
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(BASE)
    page.wait_for_selector(".hero")

    check("A1 默认主题为夜间", page.evaluate("document.documentElement.dataset.theme") == "night")
    check("A2 夜间 body 背景 #090A0C", css(page, "body", "backgroundColor") == "rgb(9, 10, 12)", css(page, "body", "backgroundColor"))
    check("A3 title 含 Intenda", "Intenda" in page.title())
    check("A4 夜间 hero 图可见且已加载", visible(page, ".hero-art.only-night") and page.evaluate("document.querySelector('.hero-art.only-night').naturalWidth") > 0)
    check("A5 日间 hero 图隐藏", not visible(page, ".hero-art.only-day"))
    check("A6 夜间 logo 可见、日间 logo 隐藏", visible(page, ".brand-logo.only-night") and not visible(page, ".brand-logo.only-day"))
    check("A7 强调蓝：新建委托按钮背景 #2563EB", css(page, ".new-delegate-btn", "backgroundColor") == "rgb(37, 99, 235)", css(page, ".new-delegate-btn", "backgroundColor"))
    check("A8 通知圆点为蓝 #2563EB", css(page, ".bell-dot", "backgroundColor") == "rgb(37, 99, 235)")
    check("A9 账户头像蓝底 #2563EB", css(page, ".account-avatar", "backgroundColor") == "rgb(37, 99, 235)")

    stats = page.locator(".stat-num").all_inner_texts()
    cards = page.locator(".decision-card").count()
    check("A10 简报四项统计齐全", len(stats) == 4, str(stats))
    check("A11 新邮件统计为 09", stats[0] == "09", stats[0] if stats else "")
    check("A12 待决策统计与决策卡数一致", len(stats) > 1 and int(stats[1]) == cards, f"stat={stats[1] if len(stats)>1 else '?'} cards={cards}")
    check("A13 决策卡图标位为 motif 素材图", page.locator(".decision-motif.only-night").count() >= 1 and visible(page, ".decision-motif.only-night"))

    pct1 = page.locator(".agent-row .agent-pct").first.inner_text()
    page.wait_for_timeout(3200)
    pct2 = page.locator(".agent-row .agent-pct").first.inner_text()
    check("A14 进行中任务进度实时推进", int(pct2.strip("%")) > int(pct1.strip("%")), f"{pct1}->{pct2}")

    # 决策联动
    page.locator(".decision-main").first.click()
    page.wait_for_timeout(300)
    check("A15 决策卡展开详情", page.locator(".decision-detail").count() == 1)
    page.locator(".decision-detail .btn-primary", has_text="批准发送").click()
    page.wait_for_timeout(600)
    check("A16 批准后决策卡移除", page.locator(".decision-card").count() == cards - 1)
    check("A17 已完成动态新增处理记录", "已按建议处理" in page.locator(".feed-item").first.inner_text())

    # 切换到日间
    page.locator(".theme-toggle").click()
    page.wait_for_timeout(300)
    check("A18 点击切换到日间", page.evaluate("document.documentElement.dataset.theme") == "day")
    check("A19 日间 body 背景 #F5F6F7", css(page, "body", "backgroundColor") == "rgb(245, 246, 247)", css(page, "body", "backgroundColor"))
    check("A20 日间侧栏为白 #FFFFFF", css(page, ".sidebar", "backgroundColor") == "rgb(255, 255, 255)")
    check("A21 日间 hero 图可见、日间 logo 可见", visible(page, ".hero-art.only-day") and visible(page, ".brand-logo.only-day") and not visible(page, ".brand-logo.only-night"))
    check("A22 localStorage 已存 day", page.evaluate("localStorage.getItem('intenda-theme')") == "day")
    page.reload()
    page.wait_for_selector(".hero")
    check("A23 刷新后保持日间", page.evaluate("document.documentElement.dataset.theme") == "day")

    # 日间五视图可打开
    for label, h1 in [("委托工作", "委托工作"), ("任务进度", "任务进度"), ("待审阅", "待审阅"), ("收件箱", "收件箱"), ("今日简报", "今日简报")]:
        nav(page, label)
        check(f"A24 日间视图可打开：{label}", page.locator(".view h1").first.inner_text() == h1)

    # 切回夜间并验证持久化
    page.locator(".theme-toggle").click()
    page.wait_for_timeout(200)
    page.reload()
    page.wait_for_selector(".hero")
    check("A25 切回夜间后刷新保持夜间", page.evaluate("document.documentElement.dataset.theme") == "night")
    ctx.close()

    # ---------- 会话 B：功能全流程（夜间） ----------
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(BASE)
    page.wait_for_selector(".hero")

    nav(page, "委托工作")
    check("B1 委托页缎带素材可见且加载", visible(page, ".intent-ribbon img.only-night") and page.evaluate("document.querySelector('.intent-ribbon img.only-night').naturalWidth") > 0)
    page.fill("#intent-input", "给设计评审参会人发纪要和下一步")
    page.keyboard.press("Enter")
    page.wait_for_selector(".plan-step")
    check("B2 委托生成执行计划（4 步）", page.locator(".plan-step").count() == 4)
    khaki_bg = css(page, ".pill-khaki", "backgroundColor")
    check("B3 卡其胶囊夜间底色 #2B2110", khaki_bg == "rgb(43, 33, 16)", str(khaki_bg))

    # 每一步问我：step gate
    page.locator(".autonomy-option", has_text="每一步问我").click()
    page.locator(".btn-primary", has_text="开始执行").click()
    page.wait_for_selector(".gate-panel", timeout=8000)
    check("B4 逐步授权停在步骤决策点", "需要你确认" in page.locator(".gate-panel").inner_text())
    check("B5 状态胶囊为停在决策点", "停在决策点" in page.locator(".pill-lg").inner_text())
    page.locator(".gate-panel .btn-primary", has_text="继续执行").click()
    page.wait_for_timeout(600)
    check("B6 确认后继续推进（决策点解除或进入下一步）", page.locator(".progress-pct").inner_text() != "0%")
    page.locator(".controls-panel .btn-dark", has_text="接管").click()
    page.wait_for_timeout(300)
    check("B7 接管后出现手动处理横幅", page.locator(".state-banner.manual").count() == 1)

    # 关键节点问我：tone gate -> 存入待审阅
    nav(page, "委托工作")
    page.locator(".chip", has_text="把本周会议邮件整理成待办").click()
    page.wait_for_selector(".plan-step")
    page.locator(".autonomy-option", has_text="关键节点问我").click()
    page.locator(".btn-primary", has_text="开始执行").click()
    page.wait_for_selector(".gate-panel", timeout=15000)
    check("B8 关键节点授权停在语气选择", "选择跟进方式" in page.locator(".gate-panel").inner_text())
    page.locator(".tone-card .btn-primary", has_text="用正式版继续").first.click()
    page.wait_for_selector(".result-panel", timeout=15000)
    check("B9 任务完成出现结果面板", "已产出的结果草稿" in page.locator(".result-panel").inner_text())
    page.locator(".result-panel .btn-ghost", has_text="存入待审阅").click()
    page.wait_for_timeout(300)
    check("B10 存入待审阅有确认横幅", "已存入「待审阅」" in page.locator(".result-panel").inner_text())
    nav(page, "待审阅")
    check("B11 新草稿流入审阅队列", page.locator(".queue-item").count() >= 4, str(page.locator(".queue-item").count()))

    # 审阅筛选与动作
    page.locator(".filter-pill", has_text="待批准").click()
    page.wait_for_timeout(300)
    check("B12 审阅筛选待批准可用", page.locator(".queue-item").count() >= 1)
    page.locator(".filter-pill", has_text="全部").click()
    page.wait_for_timeout(300)
    page.locator(".queue-item").first.click()
    page.wait_for_timeout(300)
    subj = page.locator(".detail-subject").inner_text()
    check("B13 审阅详情打开且有主题", len(subj) > 0)
    page.locator(".detail-actions .btn-primary", has_text="批准并发送").click()
    page.wait_for_timeout(400)
    check("B14 批准发送后状态为已发送", "已发送" in page.locator(".detail-panel").inner_text())
    page.locator(".queue-item").nth(1).click()
    page.wait_for_timeout(300)
    page.locator(".detail-actions .btn-dark", has_text="修改内容").click()
    page.wait_for_selector(".detail-panel textarea")
    page.fill(".detail-panel textarea", "修改后的正文内容，用于 QA 验证。")
    page.locator(".detail-panel .btn-primary", has_text="保存修改").click()
    page.wait_for_timeout(400)
    check("B15 编辑保存后状态为需修改", "需修改" in page.locator(".detail-panel").inner_text())

    # 全自动：send gate
    nav(page, "委托工作")
    page.locator(".chip", has_text="跟进上周没回复的客户询价").click()
    page.wait_for_selector(".plan-step")
    page.locator(".autonomy-option", has_text="全自动").click()
    page.locator(".btn-primary", has_text="开始执行").click()
    page.wait_for_selector(".gate-panel", timeout=20000)
    check("B16 全自动停在发送前确认", "发送前确认" in page.locator(".gate-panel").inner_text())
    page.locator(".gate-panel .btn-primary", has_text="确认发送").click()
    page.wait_for_selector(".result-panel", timeout=15000)
    check("B17 确认发送后结果为已发送", "已发送" in page.locator(".result-panel .pill").first.inner_text())

    # 收件箱全套
    nav(page, "收件箱")
    check("B18 收件箱邮件行数 9", page.locator(".mail-row").count() == 9, str(page.locator(".mail-row").count()))
    check("B19 初始未读圆点 4 个", page.locator(".mail-row .unread-dot").count() == 4, str(page.locator(".mail-row .unread-dot").count()))
    first_subject = page.locator(".mail-row .mail-subject").first.inner_text()
    page.locator(".mail-row").first.click()
    page.wait_for_timeout(300)
    check("B20 打开邮件阅读窗主题一致", page.locator(".read-subject").inner_text() == first_subject)
    check("B21 打开后未读圆点减少", page.locator(".mail-row .unread-dot").count() == 3)
    page.locator(".folder-item", has_text="未读邮件").click()
    page.wait_for_timeout(300)
    check("B22 未读文件夹只列未读", page.locator(".mail-row").count() == 3, str(page.locator(".mail-row").count()))
    page.locator(".folder-item", has_text="收件箱").first.click()
    page.wait_for_timeout(300)
    page.fill(".top-search input", "发票")
    page.wait_for_timeout(400)
    rows = page.locator(".mail-row").count()
    check("B23 顶栏搜索过滤邮件", 1 <= rows < 9, str(rows))
    page.fill(".top-search input", "")
    page.wait_for_timeout(400)
    page.locator(".mail-row").first.click()
    page.wait_for_timeout(300)
    page.locator(".read-actions .btn-dark", has_text="回复邮件").click()
    page.wait_for_selector(".composer textarea")
    page.fill(".composer textarea", "收到，我来跟进。")
    page.locator(".composer .btn-primary", has_text="发送").click()
    page.wait_for_timeout(300)
    check("B24 手动回复发送有确认横幅", "回复已发送" in page.locator(".read-pane").inner_text())
    page.locator(".agent-cta .btn-primary", has_text="开始委托").click()
    page.wait_for_timeout(400)
    check("B25 交给 Agent 跳转委托且预填意图", "跟进这封" in page.input_value("#intent-input"))

    check("B26 全程无页面错误", len(errors) == 0, "; ".join(errors[:3]))
    ctx.close()
    browser.close()

passed = sum(1 for _, ok, _ in results if ok)
print(f"\n==== {passed}/{len(results)} assertions passed ====")
sys.exit(0 if passed == len(results) else 1)
