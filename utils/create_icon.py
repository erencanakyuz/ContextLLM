#!/usr/bin/env python3
"""
Create a simple icon for the ContextLLM application
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """Create a simple icon for the ContextLLM application"""
    
    # Create a new image with RGBA mode (for transparency)
    size = (256, 256)
    img = Image.new("RGBA", size, (70, 130, 180, 255))  # type: ignore[arg-type]
    
    # Create a drawing object
    draw = ImageDraw.Draw(img)
    
    # Draw a document-like shape
    margin = 30
    doc_width = size[0] - 2 * margin
    doc_height = size[1] - 2 * margin
    
    # Main document rectangle
    doc_rect = [margin, margin, margin + doc_width, margin + doc_height]
    draw.rectangle(doc_rect, fill=(255, 255, 255, 255), outline=(50, 50, 50, 255), width=3)
    
    # Draw folded corner
    corner_size = 40
    corner_points = [
        (margin + doc_width - corner_size, margin),
        (margin + doc_width, margin + corner_size),
        (margin + doc_width, margin),
    ]
    draw.polygon(corner_points, fill=(240, 240, 240, 255))
    
    # Draw text lines to represent content
    line_color = (100, 100, 100, 255)
    line_width = 2
    
    # Horizontal lines
    for i in range(5):
        y = margin + 60 + i * 25
        start_x = margin + 20
        end_x = margin + doc_width - 20
        if i == 4:  # Last line shorter
            end_x = margin + doc_width - 80
        draw.line([(start_x, y), (end_x, y)], fill=line_color, width=line_width)
    
    # Add a small "+" symbol in the corner to represent aggregation
    plus_x = margin + doc_width - 60
    plus_y = margin + doc_height - 60
    plus_size = 15
    
    # Draw plus sign
    draw.line([(plus_x - plus_size, plus_y), (plus_x + plus_size, plus_y)], 
              fill=(70, 130, 180, 255), width=4)
    draw.line([(plus_x, plus_y - plus_size), (plus_x, plus_y + plus_size)], 
              fill=(70, 130, 180, 255), width=4)
    
    # Create multiple sizes for the icon
    sizes = [(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)]
    images = []
    
    for size in sizes:
        if size != (256, 256):
            resized = img.resize(size, Image.Resampling.LANCZOS)
            images.append(resized)
        else:
            images.append(img)
    
    # Save as ICO file
    icon_path = "icon.ico"
    images[0].save(icon_path, format='ICO', sizes=[(img.size[0], img.size[1]) for img in images])
    
    print(f"Icon created successfully: {icon_path}")
    return icon_path

if __name__ == "__main__":
    create_icon()