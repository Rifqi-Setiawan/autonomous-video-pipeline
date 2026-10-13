"""Automated Thumbnail Engine.
Generates dead-center high-impact hook cards for Frame-0 video insertion (0.35s).
"""

import os
import logging
from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("thumbnail_engine")

class ThumbnailEngine:
    """Generates high-contrast vertical hook cards with typography hierarchy."""
    def __init__(self, font_path: str = "./assets/fonts/Anton.ttf"):
        self.font_path = font_path

    def _create_vignette(self, width: int, height: int) -> Image.Image:
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        center_y = height // 2
        band_radius = 520

        for y in range(height):
            dist = abs(y - center_y)
            if dist < band_radius:
                factor = 1.0 - (dist / band_radius) ** 1.5
                alpha = int(185 * factor)
                draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))

        return overlay

    def generate(
        self,
        base_image_path: str,
        hook_text: str,
        output_path: str,
        width: int = 1080,
        height: int = 1920
    ) -> str:
        """Draws dynamic 2-tone centered text on background canvas."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        if os.path.exists(base_image_path):
            img = Image.open(base_image_path).convert("RGBA").resize((width, height))
        else:
            img = Image.new("RGBA", (width, height), (20, 20, 25, 255))

        vignette = self._create_vignette(width, height)
        img = Image.alpha_composite(img, vignette)

        draw = ImageDraw.Draw(img)
        lines = [line.strip() for line in hook_text.split("/") if line.strip()]

        font_size = 90
        try:
            font = ImageFont.truetype(self.font_path, font_size) if os.path.exists(self.font_path) else ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        # Calculate total text block height for perfect dead-center positioning
        line_heights = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_heights.append(bbox[3] - bbox[1])

        total_h = sum(line_heights) + (len(lines) - 1) * 20
        curr_y = (height - total_h) // 2

        for idx, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            line_x = (width - line_w) // 2

            # 2-Tone Color Hierarchy: Line 1 White, Line 2 Electric Yellow
            color = (255, 255, 255) if idx == 0 else (255, 230, 0)

            # Drop shadow
            draw.text((line_x + 6, curr_y + 6), line, font=font, fill=(0, 0, 0, 200))
            # Black outline
            for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
                draw.text((line_x + dx, curr_y + dy), line, font=font, fill=(0, 0, 0, 255))
            # Main text
            draw.text((line_x, curr_y), line, font=font, fill=color)

            curr_y += line_heights[idx] + 20

        img.convert("RGB").save(output_path, "JPEG", quality=95)
        logger.info(f"Rendered thumbnail card: {output_path}")
        return output_path
