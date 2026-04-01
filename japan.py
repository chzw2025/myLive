import requests
import re

UPSTREAM_URL = "https://web.utako.moe/jp.m3u"
OUTPUT_FILE = "JapanTV.m3u8"
FORCED_GROUP_NAME = "JapanTV"
# 保持播放列表头部的 EPG 信息
TVG_HEADER = '#EXTM3U url-tvg="https://epg.freejptv.com/jp.xml,https://animenosekai.github.io/japanterebi-xmltv/guide.xml" tvg-shift=0'

def process_m3u(m3u_content):
    lines = m3u_content.strip().splitlines()
    output_lines = []
    
    # 状态机：标记当前是否正在处理一个有效的频道条目
    for i in range(len(lines)):
        line = lines[i].strip()
        
        if line.startswith("#EXTINF"):
            # 1. 排除掉包含 "Information" 的广告或说明频道
            if 'group-title="Information"' in line:
                continue
                
            # 2. 确保下一行是 URL 链接
            if i + 1 < len(lines):
                url_line = lines[i+1].strip()
                
                # --- 核心逻辑：只改分组名，保留图标和 ID ---
                # 使用正则寻找 group-title="..." 并替换它
                if 'group-title="' in line:
                    # 将原来的 group-title="Tokyo" 替换为 group-title="JapanTV"
                    new_line = re.sub(r'group-title="[^"]*"', f'group-title="{FORCED_GROUP_NAME}"', line)
                else:
                    # 如果原行没有分组，则在 #EXTINF 后插入分组
                    new_line = line.replace('#EXTINF:', f'#EXTINF group-title="{FORCED_GROUP_NAME}":')
                
                output_lines.append(new_line)
                output_lines.append(url_line)
                
    return output_lines

def main():
    print(f"🚀 Starting Sync from {UPSTREAM_URL}")
    try:
        # 增加超时处理，防止网络卡死
        response = requests.get(UPSTREAM_URL, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error fetching source: {e}")
        return

    # 处理抓取到的内容
    final_channels = process_m3u(response.text)

    if final_channels:
        # --- 关键改动：'w' 模式覆盖写入 ---
        # 这样每次运行都会清空旧的 us1001 链接，只保留当前源头里的 NL 链接
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(TVG_HEADER + "\n")
            # 将处理后的频道行合并写入
            f.write("\n".join(final_channels) + "\n")
            
        print(f"✅ Success! Updated {len(final_channels)//2} channels.")
        print(f"✨ All old domains (like us1001) have been removed.")
    else:
        print("⚠️ No valid channels found in source. Local file kept unchanged.")

if __name__ == "__main__":
    main()
