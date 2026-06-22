"""
视频号助手 - 视频列表采集
拦截 post/post_list API 获取视频列表（标题、时间、播放、点赞、评论、转发）

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
        if "/mmfinderassistant-bin/" in url:
            try:
                body = await response.json()
                endpoint = url.split("mmfinderassistant-bin/")[-1].split("?")[0]
                captured_api[endpoint] = {"status": response.status, "data": body}
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

        # 提取 post_list 数据
        posts = []
        if "post/post_list" in captured_api:
            data = captured_api["post/post_list"]["data"]
            post_list = data.get("data", {}).get("list", [])
            for p in post_list:
                posts.append({
                    "title": p.get("commentList", [{}])[0].get("content", "")
                            if p.get("commentList") else "",
                    "objectId": p.get("objectId", ""),
                    "createTime": p.get("createTime", 0),
                    "likeCount": p.get("likeCount", 0),
                    "commentCount": p.get("commentCount", 0),
                    "readCount": p.get("readCount", 0),
                    "forwardCount": p.get("forwardCount", 0),
                    "favCount": p.get("favCount", 0),
                })

            from datetime import datetime
            print(f"\n=== 视频列表 ({len(posts)} 条) ===")
            for p in posts:
                ts = datetime.fromtimestamp(p["createTime"]).strftime("%Y-%m-%d %H:%M")
                title = (p["title"] or "无标题")[:40]
                print(f"  [{ts}] {title}")
                print(f"    播放{p['readCount']} 点赞{p['likeCount']} 评论{p['commentCount']} 转发{p['forwardCount']} 收藏{p['favCount']}")

        # 保存到临时目录（不污染桌面）
        out_dir = tempfile.gettempdir()
        fp = os.path.join(out_dir, "video_list_api.json")
        with open(fp, "w") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print(f"\n📄 {fp}")

        await browser.close()

    print(f"✅ 共 {len(posts)} 条视频")


if __name__ == "__main__":
    asyncio.run(main())
