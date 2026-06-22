# Channels Assistant Scraper (视频号助手数据采集)

Playwright-powered data scraper for WeChat Channels management backend (`channels.weixin.qq.com/platform`).
Extracts follower trends, video performance metrics, and per-video analytics into clean Excel files.

## Features

- **关注者数据** — Daily fan trend (net add, new follows, unfollows, total count)
- **视频日趋势** — Daily video metrics (plays, likes, comments, shares, follows)
- **单篇视频** — Per-video breakdown (play rate, avg watch time, engagement)
- **One-shot export** — Single command outputs 3 separate Excel files to Desktop
- **Cross-platform** — macOS / Linux / Windows (auto-detects Desktop path)

## Prerequisites

```bash
pip install playwright openpyxl
playwright install chromium
```

## Quick Start

### 1. Login (one-time)

```bash
python3 templates/login_helper.py
```

Opens a browser for QR scan → auto-saves session cookie.

### 2. Export all three tables

```bash
python3 templates/scrape_all_three.py
```

Outputs to `~/Desktop/视频号助手数据/`:

| File | Contents |
|------|----------|
| `关注者数据.xlsx` | 7-day follower trend |
| `视频日趋势.xlsx` | 7-day video metrics |
| `单篇视频.xlsx` | Per-video detail (play rate, duration, etc.) |

## Templates

| File | Purpose |
|------|---------|
| `login_helper.py` | QR scan login, saves session to `assets/` |
| `scrape_all_three.py` | **One-shot**: all 3 tables → 3 Excel files |
| `scrape_dashboard.py` | Dashboard overview + all API responses |
| `scrape_video_list.py` | Video list from `post/post_list` API |
| `scrape_statistics.py` | Fans trend + post total stat APIs |
| `explore_platform.py` | Full platform reconnaissance (nav, DOM, APIs) |
| `export_excel.py` | Convert saved JSON dump to multi-sheet Excel |

## Architecture

```
channels.weixin.qq.com/platform
        │
        ├── Main page (Vue SPA)
        │     └── Sidebar navigation via mouse.click()
        │
        └── Data center pages (micro-app iframes)
              ├── micro/statistic/follower  → 关注者数据
              └── micro/statistic/post      → 视频数据 + 单篇视频
```

### Key Technical Notes

1. **Sidebar requires mouse.click()** — The Vue sidebar is collapsed by default. `dispatchEvent()` and `locator.click()` don't work. Always use `page.mouse.click()` with `getBoundingClientRect()` coordinates.

2. **Data center renders in iframes** — Sub-pages live inside `<micro-app>` iframes. Query via `page.frames` and evaluate JS inside the target frame.

3. **"下载表格" triggers API, not file download** — These buttons populate TSV data at the bottom of the iframe's `innerText`. Click them and parse the tab-separated rows.

4. **No direct URL navigation** — Vue SPA redirects unmatched routes. Always navigate via sidebar clicks.

5. **Use `wait_until='domcontentloaded'`** — `networkidle` hangs due to keepalive heartbeat endpoint.

## API Endpoints (Discovered)

All POST to `https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/`

| Endpoint | Response | Data |
|----------|----------|------|
| `statistic/fans_trend` | JSON | add, reduce, netAdd, total arrays |
| `statistic/new_post_total_data` | JSON | browse, like, comment, forward, fav |
| `statistic/get-product-statics` | JSON | exposeCnt, clickCnt, orderCnt |
| `statistic/get-finder-total-statics` | JSON | fansNum, supportPostProduct |
| `post/post_list` | JSON | Video list with engagement stats |
| `notification/notification_list` | JSON | Notifications list |
| `shop/get_finder_ec_info_for_opening_page` | JSON | Shop info, merchant status |
| `auth/auth_data` | JSON | User profile (nickname, username) |

## Pitfalls

- **Separate login from 微信小店** — `channels.weixin.qq.com` != `store.weixin.qq.com`. Different cookies, different domains.
- **Session expires** — Check URL for `/login` after navigation. Re-run `login_helper.py` to refresh.
- **Year prefix** — TSV data rows start with the current year (`2026/`, `2025/`, etc.). Hard-coded year check in extraction code; update if the calendar year changes.
- **Chunk hash changes** — JS bundle filenames change with each deploy.

## License

MIT
