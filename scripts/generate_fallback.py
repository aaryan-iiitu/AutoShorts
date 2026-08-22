import os
import subprocess
from PIL import Image, ImageDraw
import random

def generate_fallback():
    # Ensure assets directory exists
    os.makedirs(os.path.join("assets", "video"), exist_ok=True)
    output_path = os.path.join("assets", "video", "fallback.mp4")
    temp_img = "assets/video/temp_bg.png"
    
    print("Generating background gradient with Pillow...")
    width, height = 1080, 1920
    img = Image.new("RGB", (width, height), color="#0f172a")
    draw = ImageDraw.Draw(img)
    
    # Create a subtle dark blue/purple gradient
    for y in range(height):
        r = int(15 + (25 - 15) * (y / height))
        g = int(23 + (35 - 23) * (y / height))
        b = int(42 + (65 - 42) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Add subtle static particles/stars
    random.seed(42)
    for _ in range(300):
        x = random.randint(0, width)
        y = random.randint(0, height)
        radius = random.uniform(0.5, 2.0)
        alpha = random.randint(20, 100)
        draw.ellipse([(x, y), (x+radius, y+radius)], fill=(200, 200, 255, alpha))
        
    img.save(temp_img)
    
    print("Animating background with FFmpeg (slow zoom)...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", "30",
        "-loop", "1",
        "-i", temp_img,
        "-vf", "zoompan=z='min(zoom+0.0005,1.5)':d=1800:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920",
        "-t", "60",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "28",
        "-pix_fmt", "yuv420p",
        output_path
    ]
    
    subprocess.run(cmd, check=True)
    
    # Clean up temp image
    if os.path.exists(temp_img):
        os.remove(temp_img)
        
    print(f"Successfully generated 60-second fallback video at {output_path}")

if __name__ == "__main__":
    generate_fallback()
