"""
视频号助手 - 导航菜单探索
访问平台首页，记录完整页面结构、导航菜单、API 端点响应数据

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
    print("=== 视频号助手 - 平台探索 ===")
    captured_api = {}

    async def on_response(response):
        url = response.url
        if "/mmfinderassistant-bin/" in url:
            try:
                body = await response.json()
                ep = url.split("mmfinderassistant-bin/")[-1].split("?")[0]
                captured_api[ep] = {"status": response.status, "data": body}
            except:
                ep = url.split("mmfinderassistant-bin/")[-1].split("?")[0]
                captured_api[ep] = {"status": response.status, "data": "(non-json)"}

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

        if "/login" in page.url:
            print("❌ 会话过期")
            await browser.close()
            return

        print(f"URL: {page.url}")

        # 导航菜单提取
        nav = await page.evaluate("""() => {
            const items = document.querySelectorAll('[class*=\"menu__name\"], [class*=\"nav-item\"], [class*=\"sidebar\"] a, [class*=\"side-bar\"] a');
            const names = [];
            for (const el of items) {
                const t = el.textContent.trim();
                if (t && !names.includes(t) && t.length < 20) names.push(t);
            }
            return names;
        }""")
        if nav:
            print(f"\n=== 导航菜单 ({len(nav)} 项) ===")
            for n in nav:
                print(f"  {n}")

        # 页面文本
        text = await page.evaluate('document.body.innerText || ""')
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        print(f"\n=== 页面文本 ({len(lines)} 行) ===")
        for l in lines:
            print(f"  {l}")

        # 框架
        frames = page.frames
        print(f"\n=== 框架 ({len(frames)}) ===")
        for i, f in enumerate(frames):
            print(f"  [{i}] {f.url[:120]}")

        # API 端点
        print(f"\n=== API 端点 ({len(captured_api)}) ===")
        for ep, info in sorted(captured_api.items()):
            status_icon = "✅" if info["status"] == 200 else "⚠️"
            body_preview = json.dumps(info["data"], ensure_ascii=False)[:200] if isinstance(info["data"], dict) else str(info["data"])[:200]
            print(f"  {status_icon} {info['status']} {ep}")
            print(f"      {body_preview}")

        # 保存到临时目录（不污染桌面）
        out_dir = tempfile.gettempdir()
        os.makedirs(out_dir, exist_ok=True)
        fp = os.path.join(out_dir, "platform_explore.json")
        with open(fp, "w") as f:
            json.dump({
                "url": page.url,
                "nav": nav,
                "lines": lines,
                "api": captured_api,
            }, f, ensure_ascii=False, indent=2)
        print(f"\n📄 {fp}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
