#!/usr/bin/env python3
"""Extract sample architecture diagram images from the AWS PDF."""

import fitz
from PIL import Image
import io
from pathlib import Path

def extract_samples():
    """Extract sample images to visualize the architecture diagrams."""
    doc = fitz.open("aws_architecture_diagram.pdf")
    output_dir = Path("aws_diagram_samples")
    output_dir.mkdir(exist_ok=True)
    
    # Extract a few sample images from page 1 (the large architecture diagrams)
    page = doc[0]
    images = page.get_images(full=True)
    
    print(f"Total images on page 1: {len(images)}")
    print("\nExtracting sample architecture diagrams...\n")
    
    for idx, img_info in enumerate(images[:4]):  # First 4 images (likely the main diagrams)
        xref = img_info[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]
        
        pil_image = Image.open(io.BytesIO(image_bytes))
        width, height = pil_image.size
        
        output_file = output_dir / f"diagram_{idx+1}_{width}x{height}.{image_ext}"
        with open(output_file, "wb") as f:
            f.write(image_bytes)
        
        print(f"✅ Extracted Diagram {idx+1}:")
        print(f"   Size: {width}x{height} pixels")
        print(f"   Format: {image_ext.upper()}")
        print(f"   Mode: {pil_image.mode}")
        print(f"   Saved to: {output_file}")
        print()
    
    doc.close()
    print(f"Sample diagrams saved to: {output_dir.absolute()}")

if __name__ == "__main__":
    extract_samples()

