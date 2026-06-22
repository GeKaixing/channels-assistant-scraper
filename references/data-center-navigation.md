# 数据中心导航 & 数据提取

## 侧边栏展开路径

```
首页                     (无需展开)
内容管理                 (展开 → 视频/图文/音乐/音频/草稿箱/主页/活动)
  └─ 视频
  └─ 图文
  └─ 音乐
  └─ 音频
  └─ 草稿箱
  └─ 主页
  └─ 活动
互动管理                 (点击即切换)
直播                    (点击即切换)
收入与服务               (点击即切换)
带货中心                 (点击即切换)
数据中心                (展开 → 关注者数据/视频数据/图文数据/直播数据/带货数据)
  └─ 关注者数据          iframe: micro/statistic/follower
  └─ 视频数据            iframe: micro/statistic/post
  └─ 图文数据            iframe: (待确认)
  └─ 直播数据            iframe: (待确认)
  └─ 带货数据            iframe: (待确认)
设置                    (点击即切换)
通知中心                 (点击即切换)
```

## 关键点击坐标计算

```python
async def get_click_coords(page, text):
    """获取元素的点击坐标"""
    coords = await page.evaluate(f"""() => {{
        const all = document.querySelectorAll('a, li, span, div');
        for (const el of all) {{
            if (el.textContent.trim() === '{text}' && el.offsetParent !== null) {{
                const r = el.getBoundingClientRect();
                return {{x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)}};
            }}
        }}
        return null;
    }}""")
    return coords

# 使用
dc = await get_click_coords(page, '数据中心')
await page.mouse.click(dc['x'], dc['y'])
await asyncio.sleep(2)

sub = await get_click_coords(page, '关注者数据')
await page.mouse.click(sub['x'], sub['y'])
await asyncio.sleep(5)
```

## 数据提取模式

### 1. 从 iframe 提取 DOM 文本
```python
for f in page.frames:
    if 'micro/statistic/follower' in f.url:
        text = await f.evaluate('document.body.innerText or ""')
        break
```

### 2. 点击"下载表格"提取 TSV 数据（推荐）
"下载表格"按钮触发的是 API 请求，不会产生浏览器下载事件。
数据以 TSV（tab-separated values）格式出现在 iframe 正文末尾。

```python
for f in page.frames:
    if 'micro/statistic/follower' in f.url:
        await f.evaluate("""() => {
            const all = document.querySelectorAll('button, a, span, div');
            for (const el of all) {
                if (el.textContent.trim() === '下载表格' && el.offsetParent !== null) {
                    el.click(); return;
                }
            }
        }""")
        await asyncio.sleep(3)
        text = await f.evaluate('document.body.innerText or ""')
        for l in text.split("\\n"):
            if l.startswith("2026/"):
                cols = l.split("\\t")
                # cols[0]=date, cols[1]=净增, cols[2]=新增, cols[3]=取消, cols[4]=总数
        break
```

### 3. 单篇视频 tab 切换
视频数据页面有"全部视频"和"单篇视频"两个 tab：
```python
# 在 micro/statistic/post iframe 中先点击 tab
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

### 4. API 拦截（备选）
```python
page.on('response', lambda r: asyncio.ensure_future(capture_api(r)))

async def capture_api(response):
    url = response.url
    if '/statistic/' in url:
        try:
            body = await response.json()
            # process body
        except:
            pass
```

## 已知数据字段

### 关注者数据 (micro/statistic/follower)
- 关注者总数 (fansNum)
- 净增关注, 新增关注, 取消关注
- 趋势数据 (近7天/近30天/自定义)
- 关注者画像 (性别/年龄/地域 etc.)

### 视频数据 (micro/statistic/post)
- 视频播放量, 点赞, 评论, 转发, 收藏
- 视频发布列表
- 单篇数据

### 商品数据 (via API `statistic/get-product-statics`)
- 曝光量 (exposeCnt)
- 点击量 (clickCnt)
- 订单数 (orderCnt)
