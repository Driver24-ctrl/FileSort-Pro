"""
Icon Creation Script for FileSort Pro
Creates application icons in all required sizes for Microsoft Store
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_app_icon():
    """Create application icon in all required sizes"""
    
    # Icon design parameters
    base_size = 1024
    background_color = (46, 125, 50)  # Green background
    accent_color = (255, 255, 255)   # White accent
    icon_color = (33, 150, 243)      # Blue icon
    
    # Create base icon
    img = Image.new('RGBA', (base_size, base_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw background circle
    margin = base_size // 20
    draw.ellipse([margin, margin, base_size - margin, base_size - margin], 
                 fill=background_color, outline=accent_color, width=base_size//50)
    
    # Draw file icon
    file_size = base_size // 3
    file_x = (base_size - file_size) // 2
    file_y = (base_size - file_size) // 2 - base_size // 20
    
    # File body
    file_body = [
        (file_x, file_y),
        (file_x + file_size, file_y),
        (file_x + file_size, file_y + file_size),
        (file_x + file_size//4, file_y + file_size),
        (file_x, file_y + file_size - file_size//4)
    ]
    draw.polygon(file_body, fill=accent_color)
    
    # File corner fold
    fold_size = file_size // 4
    fold_points = [
        (file_x + file_size - fold_size, file_y),
        (file_x + file_size, file_y),
        (file_x + file_size, file_y + fold_size),
        (file_x + file_size - fold_size, file_y + fold_size)
    ]
    draw.polygon(fold_points, fill=icon_color)
    
    # Draw sorting arrows
    arrow_size = file_size // 6
    arrow_y = file_y + file_size + base_size // 20
    
    # Left arrow (up)
    left_arrow_x = file_x + file_size // 4
    arrow_points = [
        (left_arrow_x, arrow_y),
        (left_arrow_x - arrow_size//2, arrow_y + arrow_size),
        (left_arrow_x + arrow_size//2, arrow_y + arrow_size)
    ]
    draw.polygon(arrow_points, fill=icon_color)
    
    # Right arrow (down)
    right_arrow_x = file_x + file_size * 3 // 4
    arrow_points = [
        (right_arrow_x, arrow_y + arrow_size),
        (right_arrow_x - arrow_size//2, arrow_y),
        (right_arrow_x + arrow_size//2, arrow_y)
    ]
    draw.polygon(arrow_points, fill=icon_color)
    
    # Create icons directory
    os.makedirs("icons", exist_ok=True)
    
    # Required sizes for Microsoft Store
    sizes = [16, 24, 32, 48, 64, 96, 128, 256, 512, 1024]
    
    for size in sizes:
        # Resize image
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Save as PNG
        filename = f"icons/icon_{size}x{size}.png"
        resized.save(filename)
        print(f"Created {filename}")
        
        # Also save as ICO for Windows
        if size in [16, 32, 48, 64, 128, 256]:
            ico_filename = f"icons/icon_{size}x{size}.ico"
            resized.save(ico_filename, format='ICO')
            print(f"Created {ico_filename}")
    
    # Create main icon.ico for the application
    main_icon = img.resize((256, 256), Image.Resampling.LANCZOS)
    main_icon.save("icon.ico", format='ICO')
    print("Created main icon.ico")
    
    print("\n✅ All icons created successfully!")
    print("Icons saved in 'icons' directory")
    print("Main icon saved as 'icon.ico'")

def create_store_assets():
    """Create additional store assets"""
    
    # Create store logo (square)
    store_logo = Image.new('RGBA', (300, 300), (0, 0, 0, 0))
    draw = ImageDraw.Draw(store_logo)
    
    # Draw simplified version
    margin = 20
    draw.ellipse([margin, margin, 300 - margin, 300 - margin], 
                 fill=(46, 125, 50), outline=(255, 255, 255), width=3)
    
    # Add file icon
    file_size = 100
    file_x = (300 - file_size) // 2
    file_y = (300 - file_size) // 2 - 10
    
    # File body
    file_body = [
        (file_x, file_y),
        (file_x + file_size, file_y),
        (file_x + file_size, file_y + file_size),
        (file_x + file_size//4, file_y + file_size),
        (file_x, file_y + file_size - file_size//4)
    ]
    draw.polygon(file_body, fill=(255, 255, 255))
    
    # Save store logo
    store_logo.save("store_logo.png")
    print("Created store_logo.png")
    
    # Create wide tile
    wide_tile = Image.new('RGBA', (310, 150), (0, 0, 0, 0))
    draw = ImageDraw.Draw(wide_tile)
    
    # Draw background
    draw.rectangle([0, 0, 310, 150], fill=(46, 125, 50))
    
    # Add text
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    draw.text((20, 60), "FileSort Pro", fill=(255, 255, 255), font=font)
    
    wide_tile.save("wide_tile.png")
    print("Created wide_tile.png")

if __name__ == "__main__":
    print("Creating FileSort Pro application icons...")
    print("=" * 50)
    
    try:
        create_app_icon()
        create_store_assets()
        print("\n🎉 All assets created successfully!")
        print("\nNext steps:")
        print("1. Review the icons in the 'icons' directory")
        print("2. Use 'icon.ico' as your main application icon")
        print("3. Use the PNG files for Microsoft Store submission")
        print("4. Consider professional design if needed")
        
    except ImportError:
        print("❌ PIL (Pillow) not found. Installing...")
        import subprocess
        import sys
        subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"])
        print("✅ PIL installed. Please run the script again.")
        
    except Exception as e:
        print(f"❌ Error creating icons: {e}")
        print("Please install Pillow: pip install Pillow")
