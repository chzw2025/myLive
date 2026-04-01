import asyncio
import requests
import re
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from datetime import datetime

# 1. 严格使用你确认正确的 API 地址
API_URL = "https://api.ppv.to/api/streams"
OUTPUT_FILE = "PPVLand.m3u8"

# 播放器需要的伪装头
CUSTOM_HEADERS = [
    '#EXTVLCOPT:http-origin=https://ppv.to',
    '#EXTVLCOPT:http-referrer=https://ppv.to/',
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# 允许的分类（根据 API 返回内容过滤）
ALLOWED_CATEGORIES = ["Boxing", "MMA", "Wrestling", "Football", "Basketball", "Baseball", "Hockey", "Other"]

def get_streams():
    """
    参考成功案例：使用 requests 强制获取 JSON。
    即使服务器返回 text/html，requests.json() 也能硬解出来。
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://ppv.to",
        "Referer": "https://ppv.to/"
    }
    
    try:
        print(f"🌐 正在请求 API: {API_URL}")
        # requests 默认处理重定向非常稳健
        response = requests.get(API_URL, headers=headers, timeout=20)
        
        print(f"🔍 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 关键：requests 会自动处理编码，并尝试将内容解析为 JSON
            return response.json()
        else:
            print(f"❌ API 请求失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ get_streams 运行异常: {str(e)}")
        return None

async def grab_m3u8_from_iframe(iframe_url):
    """
    使用 Playwright 进入 iframe 页面抓取真实的 .m3u8 链接
    """
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0"
        )
        page = await context.new_page()
        
        m3u8_url = None

        # 监听网络请求，寻找 m3u8
        async def handle_request(request):
            nonlocal m3u8_url
            url = request.url
            if ".m3u8" in url and not m3u8_url:
                if "chunklist" not in url: # 过滤掉切片列表，只要主索引
                    m3u8_url = url
                    print(f"✅ 抓到直播流: {m3u8_url}")

        page.on("request", handle_request)

        try:
            print(f"📺 正在分析页面: {iframe_url}")
            await page.goto(iframe_url, wait_until="networkidle", timeout=45000)
            await asyncio.sleep(5) # 额外等待，确保播放器加载
        except Exception as e:
            print(f"⚠️ 页面加载异常: {str(e)}")
        finally:
            await browser.close()
            
        return m3u8_url

async def main():
    print(f"🚀 PPV 抓取程序启动 | 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 获取原始 API 数据
    data = get_streams()
    if not data or "streams" not in data:
        print("❌ 无法获取有效的 API 数据，程序退出。")
        return

    m3u8_lines = ["#EXTM3U"]
    total_found = 0

    # 遍历分类和流
    for cat_obj in data.get("streams", []):
        category = cat_obj.get("category", "Uncategorized")
        
        # 如果你想过滤分类，可以取消下面注释
        # if category not in ALLOWED_CATEGORIES: continue

        for stream in cat_obj.get("streams", []):
            name = stream.get("name", "Unknown Event")
            iframe_url = stream.get("iframe", "")
            logo = stream.get("poster") or stream.get("logo") or ""

            if not iframe_url:
                continue

            # 开始抓取真正的流地址
            real_stream_url = await grab_m3u8_from_iframe(iframe_url)
            
            if real_stream_url:
                # 构建 M3U 标准格式
                m3u8_lines.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{category}",{name}')
                # 插入 VLC/播放器需要的 Headers
                for h in CUSTOM_HEADERS:
                    m3u8_lines.append(h)
                m3u8_lines.append(real_stream_url)
                total_found += 1

    # 保存文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u8_lines))
    
    print(f"🎉 处理完成！共抓取到 {total_found} 个有效频道，已保存至 {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
