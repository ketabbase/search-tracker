from PIL import Image, ImageDraw, ImageFont
import os

def create_app_icon():
    # Create a 256x256 image with a white background
    size = 256
    image = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a circle
    circle_color = (41, 128, 185)  # Nice blue color
    draw.ellipse([20, 20, size-20, size-20], fill=circle_color)
    
    # Draw a magnifying glass
    glass_color = (255, 255, 255)  # White
    # Draw the circle part of the magnifying glass
    draw.ellipse([60, 60, size-60, size-60], outline=glass_color, width=8)
    # Draw the handle
    draw.line([(size-60, size-60), (size-20, size-20)], fill=glass_color, width=8)
    
    # Save as ICO file
    icon_path = 'app_icon.ico'
    image.save(icon_path, format='ICO', sizes=[(256, 256)])
    print(f"Icon created at: {os.path.abspath(icon_path)}")
    return icon_path

if __name__ == "__main__":
    create_app_icon() 