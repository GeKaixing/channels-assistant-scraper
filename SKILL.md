---
name: channels-assistant-scraper
category: social-media
description: 基于 Playwright 采集视频号助手 channels.weixin.qq.com/platform 的结构化数据。覆盖首页概览、内容管理、互动管理、直播、带货中心、数据中心、设置等功能。
platforms: [macos, linux, windows]
---

# 视频号助手 Scraper

基于 Playwright 采集 `https://channels.weixin.qq.com/platform`（视频号助手）的结构化数据。
覆盖首页概览、内容管理、互动管理、直播、带货中心、数据中心、设置等功能。
与微信小店 `store.weixin.qq.com` 独立，使用不同的 cookie 登录。

## 用户偏好

- **仅输出 Excel 到桌面** — 不保留中间 TXT/JSON 文件。所有结果直接到 `~/Desktop/视频号助手数据/<名称>.xlsx`
- **优先用平台自带的"下载表格"按钮** — 关注者数据、视频数据、单篇视频在 micro-app iframe 里都有。点击后解析 TSV 数据，比只靠 API 拦截更完整
- **直接执行不展示代码** — 直接跑脚本出 Excel，不在回复中贴代码

## 安装要求

- Python 3.9+ + `playwright`
- Playwright Chromium: `playwright install chromium`
- 视频号助手登录 session（见下方）

## Session 与登录

视频号助手使用 **cookie 会话认证**，2 个 cookie（`sessionid` + `wxuin`）。
登录状态保存在 `assets/channels_sessions.json`（Playwright `storage_state` 格式）。

**与微信小店独立** — 不能用 `weixin_store_state.json`，不同域、不同 cookie。

### 登录流程

运行 `templates/login_helper.py`：

1. 打开 headless=false 的 Chromium 浏览器到 `https://channels.weixin.qq.com/platform`
2. 等待扫码后 URL 变化，自动保存 cookie
3. 关闭浏览器

### Session 过期检测

导航后检查 URL 是否包含 `/login`：

```python
if '/login' in page.url:
    print('SESSION EXPIRED - 请重新扫码登录')
```

平台有两层结构：
1. **主页面**：普通 Vue SPA（无 micro-app）
2. **数据中心子页面**：在 `<micro-app>` iframe 中渲染（如 `micro/statistic/follower`、`micro/statistic/post`）
   - iframe 有自己的 JS bundle 和 DOM，通过 `page.frames` 定位
   - 数据提取必须指向正确的 iframe，不是主页

## 平台导航结构

侧边栏**默认折叠**（只有图标，文字隐藏）。点击一级菜单展开子项。

### 导航方式

```python
# 第1步：点击一级菜单（如 数据中心）展开子项
await page.mouse.click(x, y)
await asyncio.sleep(2)

# 第2步：点击子项（如 关注者数据）
await page.mouse.click(x2, y2)
await asyncio.sleep(5)

# 第3步：数据在 micro-app iframe 中加载
for f in page.frames:
    if 'micro/statistic/follower' in f.url:
        text = await f.evaluate('document.body.innerText or ""')
        break
```

**`dispatchEvent()` 和 `locator.click()` 对侧边栏无效。必须用 `page.mouse.click()` 坐标点击。**

### 获取坐标

```python
coords = await page.evaluate("""() => {
    const all = document.querySelectorAll('a, li, span, div');
    for (const el of all) {
        if (el.textContent.trim() === '数据中心' && el.offsetParent !== null) {
            const r = el.getBoundingClientRect();
            return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
        }
    }
    return null;
}""")
```

### 侧边栏菜单树

| 一级 | 子项 | 说明 |
|-----|------|------|
| 首页 | — | 概览仪表盘 |
| 内容管理 | 视频/图文/音乐/音频/草稿箱/主页/活动 | 内容发布和管理 |
| 互动管理 | — | 评论、私信、弹幕 |
| 直播 | — | 直播管理 |
| 收入与服务 | — | 收入和增值服务 |
| 带货中心 | — | 电商带货 |
| 数据中心 | 关注者数据/视频数据/图文数据/直播数据/带货数据 | 数据分析 |
| 设置 | — | 账号设置 |
| 通知中心 | — | 通知列表 |

URL 始终是 `https://channels.weixin.qq.com/platform`，Vue SPA 内部路由。

## 已发现的 API 端点

全部 POST，base: `https://channels.weixin.qq.com`，前缀: `/cgi-bin/mmfinderassistant-bin/`

| 端点 | 状态 | 说明 | 关键数据 |
|------|------|------|----------|
| `post/post_list` | 201 | 视频列表 | 标题、创建时间、播放/点赞/评论/转发/收藏数 |
| `statistic/fans_trend` | 201 | 粉丝趋势 | add, reduce, netAdd, total 按来源 |
| `statistic/new_post_total_data` | 201 | 作品数据 | browse, like, comment, forward, fav |
| `shop/get_finder_ec_info_for_opening_page` | 201 | 小店信息 | 商户/带货者状态、小店名、appid |
| `vip/get-user-member-service-status` | 201 | 会员服务 | 开通条件、状态、价格区间 |
| `notification/notification_list` | 200 | 通知列表 | 标题、内容、时间 |
| `collection/get_collection_list` | 201 | 合集列表 | id, name, cover |
| `statistic/get-finder-total-statics` | 201 | 概览统计 | fansNum, supportPostProduct |
| `statistic/get-product-statics` | 201 | 商品统计 | exposeCnt, clickCnt, orderCnt |
| `auth/auth_data` | 200 | 用户信息 | nickname, username |

## 数据提取策略

### DOM 提取（首页概览）

```python
text = await page.evaluate('document.body.innerText or ""')
```

### API 拦截（结构化数据）

```python
async def on_response(response):
    url = response.url
    if '/mmfinderassistant-bin/' in url:
        try:
            body = await response.json()
            captured[url] = body
        except:
            pass
page.on('response', on_response)
```

### 点击"下载表格"提取 TSV（推荐）

"下载表格"按钮触发的是 API 请求，不会产生浏览器下载事件。
点击后在 iframe 的 `innerText` 底部出现制表符分隔的 TSV 数据：

```python
for f in page.frames:
    if 'micro/statistic/follower' in f.url:
        await f.evaluate("""() => {
            const all = document.querySelectorAll('button, a, span, div');
            for (const el of all) {
                if (el.textContent.trim() === '下载表格') { el.click(); return; }
            }
        }""")
        await asyncio.sleep(3)
        text = await f.evaluate('document.body.innerText or ""')
        for l in text.split('\n'):
            if l.startswith('2026/'):
                cols = l.split('\t')
                # cols[0]=日期, cols[1]=净增, cols[2]=新增, cols[3]=取消, cols[4]=总数
        break
```

### 单篇视频 tab 切换

视频数据页面有"全部视频"和"单篇视频"两个 tab：

```python
# 在 micro/statistic/post iframe 中先点 tab
await f.evaluate("""() => {
    const all = document.querySelectorAll('span, a, div, li');
    for (const el of all) {
        if (el.textContent.trim() === '单篇视频' && el.offsetParent !== null) {
            el.click(); return true;
        }
    }
    return false;
}""")
await asyncio.sleep(5)
# 再点下载表格
```

## 模板

| 文件 | 说明 |
|------|------|
| `templates/login_helper.py` | 首次登录（扫码后自动保存 session） |
| `templates/scrape_all_three.py` | **一键三张表**：关注者数据+视频趋势+单篇视频 → 3 个 Excel |
| `templates/scrape_dashboard.py` | 首页概览 + 所有 API 响应 |
| `templates/scrape_video_list.py` | 视频列表（通过 API 拦截） |
| `templates/scrape_statistics.py` | 粉丝趋势 + 作品统计 |
| `templates/explore_platform.py` | 全平台探索（导航、DOM、API 端点） |
| `templates/export_excel.py` | JSON dump 转多 Sheet Excel |

## 坑点

1. **与微信小店登录分离** — `channels.weixin.qq.com` != `store.weixin.qq.com`，不同 cookie、不同域
2. **数据中心在 iframe 里** — 通过 `page.frames` 查找 micro-app iframe 来操作 DOM
3. **侧边栏必须用 mouse.click()** — `dispatchEvent` 和 `locator.click` 无效。通过 `getBoundingClientRect` 获取坐标后 `page.mouse.click(x, y)`
4. **不能直接 page.goto()** — Vue SPA 会把不匹配的路由重定向到 `/platform`，必须点击侧边栏导航
5. **"下载表格"是 API 不是浏览器下载** — 点击后数据出现在 iframe innerText 底部，用 API 拦截或 DOM 提取
6. **wait_for_load_state('networkidle') 会卡住** — 心跳 keepalive 导致 networkidle 永远达不到；用 `wait_until='domcontentloaded'` + `asyncio.sleep()`
7. **Session 过期** — URL 含 `/login` 即为过期，重新扫码
8. **API 参数带随机值** — `_rid`、`_pageUrl`、`_aid` 等由前端自动生成
9. **视频数和关注者数在 DOM 中可见** — 首页显示"视频585"、"关注者285"
10. **JS chunk hash 随部署变化** — 不影响功能
