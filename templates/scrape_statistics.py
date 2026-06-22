"""
视频号助手 - 粉丝趋势数据采集
拦截 statistic/fans_trend 和 statistic/new_post_total_data API

跨平台兼容: macOS / Linux / Windows
"""

import os, sys, json, asyncio, tempfile
from playwright.async_api import async_playwright

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(SKILL_DIR, "..", "assets", "channels_sessions.json")


async def main():
    captured_api = {}

    async def on_response(response):
        url = response.url
        if "/statistic/" in url:
            try:
                body = await response.json()
                ep = url.split("mmfinderassistant-bin/")[-1].split("?")[0]
                captured_api[ep] = {"status": response.status, "data": body}
            except:
                pass

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            storage_state=STATE_PATH, viewport={"width": 1920, "height": 1080}
        )
        page = await ctx.new_page()
        page.on("response", on_response)

        await page.goto(
            "https://channels.weixin.qq.com/platform",
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        await asyncio.sleep(5)

        if "/login" in page.url:
            print("❌ 会话过期")
            await browser.close()
            return

        for ep, info in captured_api.items():
            print(f"\n=== {ep} ===")
            d = info["data"]
            data = d.get("data", {})
            if isinstance(data, dict):
                for k, v in data.items():
                    v_str = json.dumps(v, ensure_ascii=False)
                    if len(v_str) > 300:
                        v_str = v_str[:300] + "..."
                    print(f"  {k}: {v_str}")
            else:
                print(f"  data: {data}")

        fp = os.path.join(tempfile.gettempdir(), "statistic_data.json")
        with open(fp, "w") as f:
            json.dump(captured_api, f, ensure_ascii=False, indent=2)
        print(f"\n📄 {fp}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
