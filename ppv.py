async def grab_m3u8_from_iframe(iframe_url):
    """
    增强版抓取：模拟点击 + 延长等待 + 自动尝试播放
    """
    async with async_playwright() as p:
        # 使用 Firefox，并设置较长的超时
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        m3u8_url = None

        # 监听所有网络请求
        async def handle_request(request):
            nonlocal m3u8_url
            url = request.url
            # 排除掉不需要的干扰项
            if ".m3u8" in url and "chunklist" not in url and not m3u8_url:
                m3u8_url = url
                print(f"🎯 成功捕获流地址: {m3u8_url}")

        page.on("request", handle_request)

        try:
            print(f"📺 正在深度分析: {iframe_url}")
            # 1. 增加页面加载超时到 60 秒
            await page.goto(iframe_url, wait_until="load", timeout=60000)
            
            # 2. 模拟点击屏幕中心，很多播放器需要点一下才加载流
            await asyncio.sleep(3)
            await page.mouse.click(400, 300) 
            print("🖱️ 已模拟点击播放按钮...")
            
            # 3. 延长等待时间到 10-15 秒，给播放器缓冲时间
            for _ in range(15):
                if m3u8_url: break
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"⚠️ 页面处理超时或出错: {str(e)}")
        finally:
            await browser.close()
            
        return m3u8_url
