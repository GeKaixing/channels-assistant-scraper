# 视频号助手数据采集 (Channels Assistant Scraper)

基于 Playwright 的视频号助手 (`channels.weixin.qq.com/platform`) 数据采集工具。
一键导出关注者趋势、视频日趋势、单篇视频明细到 Excel。

## 功能

- **关注者数据** — 每日净增、新增、取消关注、关注者总数趋势
- **视频日趋势** — 每日播放、点赞、评论、分享、新增关注
- **单篇视频** — 每篇视频的完播率、平均播放时长、互动数据
- **一键三表** — 一条命令输出 3 个独立 Excel 到桌面
- **跨平台** — macOS / Linux / Windows 自动识别桌面路径

## 安装

```bash
pip install playwright openpyxl
playwright install chromium
```

## 快速开始

### 1. 首次登录（扫码）

```bash
python3 templates/login_helper.py
```

打开浏览器 → 扫码登录 → 自动保存 session cookie 到 `assets/`

### 2. 一键导出三张表

```bash
python3 templates/scrape_all_three.py
```

输出到 `~/Desktop/视频号助手数据/`：

| 文件 | 内容 |
|------|------|
| `关注者数据.xlsx` | 7 日关注者趋势 |
| `视频日趋势.xlsx` | 7 日视频数据 |
| `单篇视频.xlsx` | 单篇视频明细（完播率、时长等） |

## 模板清单

| 文件 | 用途 |
|------|------|
| `login_helper.py` | 首次扫码登录，保存 session |
| `scrape_all_three.py` | **推荐** 一键三张表 → 3 个 Excel |
| `scrape_dashboard.py` | 首页概览 + 所有 API 响应 |
| `scrape_video_list.py` | 从 `post/post_list` API 获取视频列表 |
| `scrape_statistics.py` | 粉丝趋势 + 作品统计 API |
| `explore_platform.py` | 全平台探索（导航、DOM、API 端点） |
| `export_excel.py` | JSON dump 转多 Sheet Excel |

## 架构

```
channels.weixin.qq.com/platform
        │
        ├── 主页面（Vue SPA）
        │     └── 侧边栏通过 mouse.click() 导航
        │
        └── 数据中心（micro-app iframe）
              ├── micro/statistic/follower  → 关注者数据
              └── micro/statistic/post      → 视频数据 + 单篇视频
```

### 关键要点

1. **侧边栏必须用 mouse.click()** — Vue 侧边栏默认折叠，`dispatchEvent()` 和 `locator.click()` 无效。必须通过 `getBoundingClientRect()` 获取坐标后用 `page.mouse.click(x, y)`。

2. **数据中心在 iframe 里渲染** — 子页面在 `<micro-app>` iframe 中。通过 `page.frames` 查找并执行 JS。

3. **"下载表格"触发的是 API 调用** — 不会产生浏览器下载事件。点击后在 iframe 的 `innerText` 底部出现 TSV 数据，解析即可。

4. **不能直接 page.goto() 进入子页面** — Vue SPA 会重定向到 `/platform`。必须点击侧边栏导航。

5. **用 `wait_until='domcontentloaded'`** — `networkidle` 因为心跳 keepalive 会卡死。

## 已发现的 API 端点

所有 POST 到 `https://channels.weixin.qq.com/cgi-bin/mmfinderassistant-bin/`

| 端点 | 响应 | 数据 |
|------|------|------|
| `statistic/fans_trend` | JSON | add, reduce, netAdd, total 数组 |
| `statistic/new_post_total_data` | JSON | browse, like, comment, forward, fav |
| `statistic/get-product-statics` | JSON | exposeCnt, clickCnt, orderCnt |
| `statistic/get-finder-total-statics` | JSON | fansNum, supportPostProduct |
| `post/post_list` | JSON | 视频列表（播放、点赞、评论等） |
| `notification/notification_list` | JSON | 通知列表 |
| `shop/get_finder_ec_info_for_opening_page` | JSON | 小店信息、商户状态 |
| `auth/auth_data` | JSON | 用户信息（nickname, username） |

## 坑点

- **与微信小店登录独立** — `channels.weixin.qq.com` 和 `store.weixin.qq.com` 是不同的域，cookie 不通
- **Session 会过期** — 访问后检查 URL 是否包含 `/login`，过期了重新跑 `login_helper.py`
- **年份前缀** — TSV 数据行以当前年份开头（`2026/`、`2025/` 等），跨年时需要更新
- **JS chunk hash 随部署变化** — 文件名带 hash，不影响功能

## License

MIT
