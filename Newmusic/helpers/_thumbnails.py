import os
import aiohttp
import textwrap
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from Newmusic import config
from Newmusic.helpers import Track

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Thumbnail:
    def __init__(self):
        self.size = (1280, 720)
        self.session: aiohttp.ClientSession | None = None
        
        
        title_font_path = os.path.join(BASE_DIR, "..", "helpers", "Raleway-Bold.ttf")
        info_font_path = os.path.join(BASE_DIR, "..", "helpers", "Inter-Light.ttf")

        try:
            self.font_title = ImageFont.truetype(title_font_path, 40)
            self.font_info = ImageFont.truetype(info_font_path, 28)
            self.font_time = ImageFont.truetype(info_font_path, 22)
            self.font_credit = ImageFont.truetype(info_font_path, 26)
        except:
            
            self.font_title = ImageFont.load_default()
            self.font_info = ImageFont.load_default()
            self.font_time = ImageFont.load_default()
            self.font_credit = ImageFont.load_default()

    def _wrap_text(self, text, font, max_width):
        """စာသားရှည်ရင် ဘောင်အကျယ်အလိုက် ဖြတ်ပေးမယ့် function"""
        avg_char_width = font.getlength('x') if hasattr(font, 'getlength') else 10
        chars_per_line = int(max_width / avg_char_width)
        wrapper = textwrap.TextWrapper(width=chars_per_line, break_long_words=True)
        return wrapper.wrap(text=text)

    async def start(self) -> None:
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()

    async def save_thumb(self, output_path: str, url: str) -> bool:
        if not url or not url.startswith("http"):
            return False
        try:
            if not self.session or self.session.closed:
                await self.start()
            async with self.session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    with open(output_path, "wb") as f:
                        f.write(await resp.read())
                    return True
        except:
            return False
        return False

    async def generate(self, song: Track) -> str:
        try:
            os.makedirs("cache", exist_ok=True)
            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}.png"
            
            if os.path.exists(output):
                return output

            success = await self.save_thumb(temp, song.thumbnail)
            
            if success and os.path.exists(temp):
                raw_cover = Image.open(temp).convert("RGBA")
            else:
                raw_cover = Image.new("RGBA", (300, 300), (30, 30, 30, 255))

            
            bg = ImageOps.fit(raw_cover, self.size, method=Image.Resampling.LANCZOS)
            bg = bg.filter(ImageFilter.GaussianBlur(50))
            bg = ImageEnhance.Brightness(bg).enhance(0.7)
            draw = ImageDraw.Draw(bg)

            
            player_w, player_h = 850, 500
            px, py = (self.size[0] - player_w) // 2, (self.size[1] - player_h) // 2
            draw.rounded_rectangle((px, py, px + player_w, py + player_h), 30, fill=(15, 15, 15, 230))

            
            c_size = 320
            cx, cy = px + 40, py + 40
            cover_img = ImageOps.fit(raw_cover, (c_size, c_size), method=Image.Resampling.LANCZOS)
            mask = Image.new("L", (c_size, c_size), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, c_size, c_size), 25, fill=255)
            cover_img.putalpha(mask)
            
            draw.rounded_rectangle((cx-3, cy-3, cx+c_size+3, cy+c_size+3), 28, outline=(255, 200, 50), width=4)
            bg.paste(cover_img, (cx, cy), cover_img)

            
            tx, ty = cx + c_size + 40, cy + 20
            details = "If you want to create your own music bot\nplease contact the developer mentioned in\nthe credit below."
            draw.text((tx, ty), details, font=self.font_time, fill=(255, 255, 0), spacing=8)
            draw.text((tx, ty + 140), "Now Playing", font=self.font_info, fill=(255, 255, 0))

            
            max_text_width = player_w - c_size - 100 
            wrapped_title = self._wrap_text(song.title, self.font_title, max_text_width)
            
            current_y = ty + 185
            
            for line in wrapped_title[:2]:
                draw.text((tx, current_y), line, font=self.font_title, fill=(255, 255, 255))
                current_y += 50 
            # ---------------------------------------------------

            # Progress Bar
            bar_w, bx, by = player_w - 80, px + 40, py + player_h - 110
            draw.rounded_rectangle((bx, by, bx + bar_w, by + 8), 4, fill=(60, 60, 60))
            draw.rounded_rectangle((bx, by, bx + (bar_w * 0.4), by + 8), 4, fill=(255, 200, 50))
            draw.ellipse((bx + (bar_w * 0.4) - 8, by - 4, bx + (bar_w * 0.4) + 8, by + 12), fill=(255, 200, 50))

            # Time Labels
            draw.text((bx, by + 20), "1:24", font=self.font_time, fill=(255, 255, 255))
            draw.text((bx + bar_w, by + 20), "3:45", font=self.font_time, fill="white", anchor="ra")

            # Playback Controls (Symbols)
            ctrl_y = by + 50
            draw.text((self.size[0]//2 - 100, ctrl_y), "<<", font=self.font_title, fill=(255, 255, 255), anchor="ma")
            draw.text((self.size[0]//2, ctrl_y), "||", font=self.font_title, fill=(255, 255, 255), anchor="ma")
            draw.text((self.size[0]//2 + 100, ctrl_y), ">>", font=self.font_title, fill=(255, 255, 255), anchor="ma")

            # Credit Text
            draw.text((self.size[0]//2, self.size[1] - 40), "Credit by @HANTHAR999", font=self.font_credit, fill=(255, 255, 255), anchor="ma")

            bg.save(output, "PNG")
            if os.path.exists(temp): os.remove(temp)
            return output

        except Exception as e:
            print(f"Error generating thumb: {e}")
            return config.DEFAULT_THUMB
