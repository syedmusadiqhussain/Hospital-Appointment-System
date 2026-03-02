from PIL import Image, ImageDraw, ImageFont
import os

os.makedirs("screenshots", exist_ok=True)

screens = [
    ("1_home.png", "#0F172A", "SehatBook — Home Page", "Find the right doctor\nBook in seconds"),
    ("2_doctors.png", "#0F172A", "SehatBook — Find Doctors", "Browse 500+ verified\nPakistani doctors"),
    ("3_chat.png", "#0F172A", "SehatBook — AI Chat", "Chat with SehatBot\nPowered by Gemini AI"),
]

for filename, bg, title, subtitle in screens:
    img = Image.new("RGB", (1280, 720), bg)
    draw = ImageDraw.Draw(img)
    # Header Bar
    draw.rectangle([0, 0, 1280, 80], fill="#0D9488")
    
    # Simple text rendering without custom font file (fallback to default)
    # Title
    draw.text((40, 25), "🩺 SehatBook", fill="white") 
    
    # Main Content
    # Approximate centering manually since default font size is small
    # We will draw a big box instead to represent UI
    draw.rectangle([100, 150, 1180, 650], fill="#1E293B", outline="#334155", width=2)
    
    # Text inside
    draw.text((400, 280), title, fill="#0D9488")
    draw.text((400, 320), subtitle, fill="#94A3B8")
    
    # Footer
    draw.rectangle([80, 580, 1200, 640], fill="#0D9488", outline="#14B8A6", width=2)
    draw.text((500, 600), "localhost:3000", fill="white")
    
    img.save(f"screenshots/{filename}")
    print(f"Created: screenshots/{filename}")

print("Screenshots ready!")
