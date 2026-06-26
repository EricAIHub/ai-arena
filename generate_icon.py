"""生成 AI Arena 应用图标（icon.ico）

使用 Pillow 创建一个简单的闪电+圆形图标。
如果 Pillow 不可用，则跳过（打包时 icon 参数设为 None）。
"""
import sys
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow 未安装，尝试安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "--quiet"])
    from PIL import Image, ImageDraw, ImageFont

import os

def create_icon():
    sizes = [256, 128, 64, 48, 32, 16]
    images = []
    
    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 背景圆（深色）
        margin = max(1, size // 16)
        draw.ellipse(
            [margin, margin, size - margin - 1, size - margin - 1],
            fill=(15, 15, 23, 255),  # 深蓝黑 #0f0f17
            outline=(99, 102, 241, 255),  # 靛蓝边框 #6366f1
            width=max(1, size // 32),
        )
        
        # 闪电符号 ⚡（用多边形绘制）
        cx, cy = size // 2, size // 2
        s = size * 0.35  # 闪电大小比例
        
        # 闪电形状（简化的多边形）
        lightning = [
            (cx - s * 0.15, cy - s * 0.9),   # 上左
            (cx + s * 0.45, cy - s * 0.9),   # 上右
            (cx + s * 0.05, cy - s * 0.05),  # 中间右
            (cx + s * 0.55, cy - s * 0.05),  # 中右
            (cx - s * 0.15, cy + s * 0.95),  # 下左
            (cx + s * 0.15, cy + s * 0.1),   # 中间左
            (cx - s * 0.35, cy + s * 0.1),   # 中左
        ]
        
        # 缩放和定位
        draw.polygon(lightning, fill=(250, 204, 21, 255))  # 金黄 #facc15
        
        # 剑的符号（简化为一条线+护手）
        # 在闪电右侧画一个小剑
        sword_x = cx + s * 0.35
        sword_y = cy - s * 0.6
        sword_len = s * 0.8
        
        # 剑身
        draw.line(
            [(sword_x, sword_y), (sword_x, sword_y + sword_len)],
            fill=(200, 200, 220, 255),
            width=max(1, size // 40),
        )
        # 护手
        guard_w = s * 0.25
        draw.line(
            [(sword_x - guard_w, sword_y + sword_len * 0.2), 
             (sword_x + guard_w, sword_y + sword_len * 0.2)],
            fill=(200, 200, 220, 255),
            width=max(1, size // 48),
        )
        
        images.append(img)
    
    # 保存为 .ico
    out_path = os.path.join(os.path.dirname(__file__), 'static', 'icon.ico')
    images[0].save(
        out_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"✅ 图标已生成: {out_path}")

if __name__ == "__main__":
    create_icon()
