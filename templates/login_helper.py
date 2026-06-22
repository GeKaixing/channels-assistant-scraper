"""
视频号助手 登录助手
打开 headless=false 浏览器 → 扫码登录 → 检测到 URL 变化后自动保存 session

跨平台兼容: macOS / Linux / Windows
"""

import os, sys, json, time
from playwright.sync_api import sync_playwright

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(SKILL_DIR, '..', 'assets', 'channels_sessions.json')


def main():
    print("=== 视频号助手 登录 ===")
    print(f"会话将保存到: {STATE_PATH}")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(
            viewport={"width": 1400, "height": 900},
        )
        page = ctx.new_page()
        page.goto("https://channels.weixin.qq.com/platform", wait_until="domcontentloaded")
        print("✅ 浏览器已打开，请在窗口中扫码登录...")
        print("   检测到跳转后自动保存并关闭...")

        # 轮询等待 URL 变化（扫码登录后 URL 会变为 /platform）
        start_url = page.url
        for i in range(120):
            current = page.url
            if current != start_url:
                print(f"\n✅ 检测到跳转: {current}")
                break
            time.sleep(1)
        else:
            print("\n⚠️ 超时，尝试保存当前会话...")

        time.sleep(1)
        ctx.storage_state(path=STATE_PATH)

        with open(STATE_PATH) as f:
            state = json.load(f)
        cookies = state.get("cookies", [])
        channels_cookies = [c for c in cookies if "channels.weixin.qq.com" in c.get("domain", "")]
        print(f"   cookie: {len(channels_cookies)} 个来自 channels.weixin.qq.com (共 {len(cookies)})")

        browser.close()

    if not channels_cookies:
        print("❌ 未获取到 cookie，登录可能未完成")
        sys.exit(1)

    print("✅ 登录完成")


if __name__ == "__main__":
    main()
