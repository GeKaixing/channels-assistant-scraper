"""
视频号助手 - 首页 Dashboard 数据采集
从 /platform 首页采集概览数据（视频数、关注者、昨日数据）

跨平台兼容: macOS / Linux / Windows
"""

import os, sys, json, asyncio, tempfile
from playwright.async_api import async_playwright

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(SKILL_DIR, "..", "assets", "channels_sessions.json")


def get_desktop_path(sub_dir=None):
    home = os.path.expanduser("~")
    if sys.platform == "darwin":
        base = os.path.join(home, "Desktop")
    elif sys.platform == "win32":
        base = os.path.join(home, "Desktop")
    else:
        base = os.environ.get("XDG_DESKTOP_DIR", os.path.join(home, "Desktop"))
    if not os.path.exists(base):
        base = home
    return os.path.join(base, sub_dir) if sub_dir else base


async def main():
    captured_api = {}

    async def on_response(response):
        url = response.url
        if "/mmfinderassistant-bin/" in url:
            try:
                body = await response.json()
                endpoint = url.split("mmfinderassistant-bin/")[-1].split("?")[0]
                captured_api[endpoint] = {
                    "status": response.status,
                    "data": body,
                }
            except:
                pass

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            storage_state=STATE_PATH,
            viewport={"width": 1920, "height": 1080},
        )
        page = await ctx.new_page()
        page.on("response", on_response)

        await page.goto(
            "https://channels.weixin.qq.com/platform",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        await asyncio.sleep(5)

        final_url = page.url
        if "/login" in final_url:
            print("❌ 会话过期，请重新登录")
            await browser.close()
            return

        # DOM 数据
        text = await page.evaluate('document.body.innerText || ""')
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # 解析概览数据
        dashboard = {"url": final_url}
        for i, l in enumerate(lines):
            if "视频号ID:" in l and i + 1 < len(lines):
                dashboard["finder_id"] = lines[i + 1]
            if "视频" in l and l.endswith("视频"):
                dashboard["video_count"] = l.replace("视频", "")
            if "关注者" in l:
                dashboard["followers"] = l.replace("关注者", "")

        # 昨日数据
        if "昨日数据" in lines:
            idx = lines.index("昨日数据")
            yesterday = {}
            for i in range(idx + 1, min(idx + 10, len(lines))):
                if lines[i] in ("净增关注", "新增播放", "新增评论", "新增"):
                    key = lines[i]
                    if i + 1 < len(lines):
                        yesterday[key] = lines[i + 1]
            dashboard["yesterday"] = yesterday

        print(f"\n=== 首页概览 ===")
        for k, v in dashboard.items():
            if k != "yesterday":
                print(f"  {k}: {v}")
        if "yesterday" in dashboard:
            print(f"  昨日数据:")
            for k, v in dashboard["yesterday"].items():
                print(f"    {k}: {v}")

        # 保存到临时目录（调试用，不污染桌面）
        out_dir = tempfile.gettempdir()
        os.makedirs(out_dir, exist_ok=True)

        # 1. DOM 数据
        dom_fp = os.path.join(out_dir, "dashboard_dom.json")
        with open(dom_fp, "w") as f:
            json.dump({"lines": lines, "parsed": dashboard}, f, ensure_ascii=False, indent=2)
        print(f"\n📄 {dom_fp}")

        # 2. API 数据
        api_fp = os.path.join(out_dir, "dashboard_api.json")
        clean_api = {}
        for ep, info in captured_api.items():
            clean_api[ep] = {
                "status": info["status"],
                "data": info["data"],
            }
        with open(api_fp, "w") as f:
            json.dump(clean_api, f, ensure_ascii=False, indent=2)
        print(f"📄 {api_fp}")
        print(f"\n✅ 共捕获 {len(captured_api)} 个 API 端点")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
