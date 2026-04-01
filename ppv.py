import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import aiohttp
from datetime import datetime
import re 

API_URL = "https://api.ppv.to/api/streams"

# 播放器需要的伪装头
CUSTOM_HEADERS = [
    '#EXTVLCOPT:http-origin=https://ppv.to',
    '#EXTVLCOPT:http-referrer=https://ppv.to/',
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0'
]

# ... (此处省略你代码中定义的 ALLOWED_CATEGORIES, CATEGORY_LOGOS 等字典以节省篇幅，请保持原样) ...

async def get_streams():
    """修复版 API 请求函数"""
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        # 模拟真实浏览器请求 API 的完整头部
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0',
            'Accept': 'application/json, text/plain, */*',
            'Origin': 'https://api.ppv.to',
            'Referer': 'https://api.ppv.to/',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            print(f"🌐 Fetching streams from {API_URL}")
            async with session.get(API_URL) as resp:
                print(f"🔍 Response status: {resp.status}")
                
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"❌ API Error: {resp.status}. Content: {error_text[:200]}")
                    return None
                
                # 核心修复：content_type=None 强制解析 JSON，即使服务器返回 text/html
                return await resp.json(content_type=None)
                
    except Exception as e:
        print(f"❌ Error in get_streams: {str(e)}")
        return None

# ... (check_m3u8_url, grab_m3u8_from_iframe 等函数保持你原来的逻辑) ...

# 注意：确保你的 main 函数里调用的逻辑与上面定义的变量一致
async def main():
    print("🚀 Starting PPV Stream Fetcher")
    data = await get_streams()
    
    # 兼容性检查：确保数据结构正确
    if not data or (isinstance(data, dict) and 'streams' not in data):
        print("❌ No valid data received from the API. Check headers or IP blocks.")
        return

    # 如果 API 返回的是列表格式（有些版本会直接返回列表），做个转换
    if isinstance(data, list):
        streams_data = data
    else:
        streams_data = data.get("streams", [])

    print(f"✅ Found {len(streams_data)} categories")
    
    # ... (后续处理逻辑保持不变) ...

if __name__ == "__main__":
    asyncio.run(main())
