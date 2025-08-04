from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
import os
import colorsys
import random
from PIL.ImageColor import getrgb

class DaftPunkTextEffect:
    def __init__(self, width=800, height=600):
        """Initialize with canvas dimensions"""
        self.width = width
        self.height = height
        self.canvas = Image.new('RGB', (width, height), 'black')
        
    def load_texture(self, texture_path="texture.png"):
        """Load and process the texture background"""
        try:
            if os.path.exists(texture_path):
                texture = Image.open(texture_path).convert('RGB')
                # Resize to canvas size
                texture = texture.resize((self.width, self.height), Image.Resampling.LANCZOS)
            else:
                # Generate a noise texture if file doesn't exist
                texture = self.generate_noise_texture()
            
            # Apply hue/saturation adjustment (make it very dark)
            enhancer = ImageEnhance.Brightness(texture)
            texture = enhancer.enhance(0.2)  # Very dark like -80 lightness
            
            return texture
        except Exception as e:
            print(f"Error loading texture: {e}")
            return self.generate_noise_texture()
    
    def generate_noise_texture(self):
        """Generate a noise texture similar to the tutorial's texture"""
        # Create noise pattern
        noise_array = np.random.randint(0, 256, (self.height, self.width, 3), dtype=np.uint8)
        texture = Image.fromarray(noise_array)
        
        # Apply blur to make it smoother
        texture = texture.filter(ImageFilter.GaussianBlur(radius=2))
        return texture
    
    def create_radial_gradient(self, center_x, center_y, radius, inner_color=(255,255,255,255), outer_color=(0,0,0,0)):
        """Create a radial gradient"""
        gradient = Image.new('RGBA', (self.width, self.height), outer_color)
        draw = ImageDraw.Draw(gradient)
        
        # Draw concentric circles for gradient effect
        steps = 50
        for i in range(steps):
            alpha = int(255 * (1 - i/steps))
            current_radius = radius * i / steps
            color = (*inner_color[:3], alpha)
            
            bbox = [
                center_x - current_radius, center_y - current_radius,
                center_x + current_radius, center_y + current_radius
            ]
            draw.ellipse(bbox, fill=color)
        
        return gradient
    
    def create_clouds_layer(self):
        """Create a clouds-like layer using noise"""
        # Generate cloud-like pattern using multiple noise layers
        clouds = Image.new('L', (self.width, self.height))
        
        # Create multiple octaves of noise
        for octave in range(4):
            scale = 2 ** octave
            noise_width = self.width // scale
            noise_height = self.height // scale
            
            # Generate noise at this scale
            noise = np.random.randint(0, 256, (noise_height, noise_width), dtype=np.uint8)
            noise_img = Image.fromarray(noise, 'L')
            
            # Resize and blend
            noise_img = noise_img.resize((self.width, self.height), Image.Resampling.LANCZOS)
            
            if octave == 0:
                clouds = noise_img
            else:
                # Blend with previous octaves
                clouds = Image.blend(clouds, noise_img, 0.5)
        
        # Apply blur
        clouds = clouds.filter(ImageFilter.GaussianBlur(radius=1))
        return clouds.convert('RGB')
    
    def setup_background(self, texture_path=None):
        """Setup pure black background"""
        # Pure black background as specified
        background = Image.new('RGB', (self.width, self.height), 'black')
        return background
    
    def load_font(self, font_path="Daft Font.TTF", size=80):
        """Load the font or fallback to default"""
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
            else:
                print(f"Font file {font_path} not found, using default font")
                return ImageFont.load_default()
        except Exception as e:
            print(f"Error loading font: {e}")
            return ImageFont.load_default()
    
    def create_chrome_text_with_bevel(self, text, font, x, y):
        """Create chrome text with heavy bevel and emboss effects like the tutorial"""
        # Create a larger canvas for effects
        effect_padding = 80
        text_canvas = Image.new('RGBA', 
                               (self.width + effect_padding*2, self.height + effect_padding*2), 
                               (0,0,0,0))
        draw = ImageDraw.Draw(text_canvas)
        
        # Adjust position for padding
        text_x = x + effect_padding
        text_y = y + effect_padding
        
        # Create main drop shadow (black, as per tutorial: -30 angle, 5 distance)
        shadow_offset_x = 3  # Approximating -30 degree angle
        shadow_offset_y = 5
        draw.text((text_x + shadow_offset_x, text_y + shadow_offset_y), text, 
                 fill=(0, 0, 0, 200), font=font)
        
        # Inner glow (black, as per tutorial)
        inner_glow_color = (0, 0, 0, 70)  # 70% opacity black
        for offset in range(1, 5):  # Size 4
            for dx in [-offset, 0, offset]:
                for dy in [-offset, 0, offset]:
                    if dx != 0 or dy != 0:
                        draw.text((text_x + dx, text_y + dy), text, 
                                fill=inner_glow_color, font=font)
        
        # Base chrome color (medium gray)
        base_chrome = (140, 140, 140, 255)
        draw.text((text_x, text_y), text, fill=base_chrome, font=font)
        
        # Bevel and Emboss effects (as per tutorial: 20% depth, 10px size)
        # Top highlight (white, screen mode, 100% opacity)
        top_highlights = [
            (0, -3, (255, 255, 255, 120)),  # Main top highlight
            (0, -2, (240, 240, 240, 100)),  # Secondary highlight
            (-1, -2, (220, 220, 220, 80)),  # Left highlight
        ]
        
        for offset_x, offset_y, color in top_highlights:
            draw.text((text_x + offset_x, text_y + offset_y), text, fill=color, font=font)
        
        # Bottom shadow (multiply black, 80% opacity as per tutorial)
        bottom_shadows = [
            (1, 3, (0, 0, 0, 80)),     # Main bottom shadow
            (0, 2, (40, 40, 40, 60)),  # Mid shadow
            (2, 2, (20, 20, 20, 40)),  # Side shadow
        ]
        
        for offset_x, offset_y, color in bottom_shadows:
            draw.text((text_x + offset_x, text_y + offset_y), text, fill=color, font=font)
        
        # Satin effect (dark blue multiply, as per tutorial)
        satin_color = (20, 30, 80, 100)  # Dark navy blue
        for offset in range(1, 3):
            draw.text((text_x + offset, text_y + offset), text, fill=satin_color, font=font)
        
        # Add very subtle color hints only at edges (much less than before)
        edge_colors = [
            (-1, 0, (100, 255, 200, 30)),   # Cyan hint on left
            (1, 0, (200, 100, 255, 30)),    # Purple hint on right  
            (0, -1, (255, 200, 100, 25)),   # Orange hint on top
        ]
        
        for offset_x, offset_y, color in edge_colors:
            draw.text((text_x + offset_x, text_y + offset_y), text, fill=color, font=font)
        
        # # Final chrome highlight pass
        # final_chrome = (180, 180, 180, 255)
        # draw.text((text_x, text_y), text, fill=final_chrome, font=font)
        
        # Very bright top edge highlight
        draw.text((text_x, text_y - 1), text, fill=(255, 255, 255, 140), font=font)
        
        # Crop back to original size
        text_canvas = text_canvas.crop((effect_padding, effect_padding, 
                                      self.width + effect_padding, self.height + effect_padding))
        
        return text_canvas
    
    def create_colored_shadow_layer(self, text, font, text_x, text_y):
        """Create the colored shadow layer as per tutorial (3 layers of text)"""
        shadow_canvas = Image.new('RGBA', (self.width, self.height), (0,0,0,0))
        draw = ImageDraw.Draw(shadow_canvas)
        
        # Shadow layer 2: Black shadow (3 pixels down, 3 pixels right as per tutorial)
        shadow_x = text_x + 3
        shadow_y = text_y + 3
        draw.text((shadow_x, shadow_y), text, fill=(0, 0, 0, 255), font=font)
        
        return shadow_canvas
    
    def create_rainbow_colored_layer(self, text, font, text_x, text_y):
        """Create the third layer with rainbow colors and effects"""
        rainbow_canvas = Image.new('RGBA', (self.width, self.height), (0,0,0,0))
        
        # Create rainbow gradient
        rainbow_gradient = Image.new('RGB', (self.width, self.height))
        for x in range(self.width):
            hue = x / self.width
            rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            color = tuple(int(c * 255) for c in rgb)
            for y in range(self.height):
                rainbow_gradient.putpixel((x, y), color)
        
        # Create text mask
        text_mask = Image.new('L', (self.width, self.height), 0)
        mask_draw = ImageDraw.Draw(text_mask)
        
        # Position for third layer (3 pixels right, 3 pixels down from shadow)
        rainbow_x = text_x + 6  # 3 from main + 3 more
        rainbow_y = text_y + 6  # 3 from main + 3 more
        mask_draw.text((rainbow_x, rainbow_y), text, fill=255, font=font)
        
        # Apply rainbow to text shape
        rainbow_canvas.paste(rainbow_gradient, mask=text_mask)
        
        # Add outer glow (white, overlay mode, as per tutorial)
        glow_canvas = Image.new('RGBA', (self.width, self.height), (0,0,0,0))
        glow_draw = ImageDraw.Draw(glow_canvas)
        
        # Outer glow with white color, size 5
        glow_color = (255, 255, 255, 100)
        for offset in range(1, 6):  # Size 5
            for dx in [-offset, 0, offset]:
                for dy in [-offset, 0, offset]:
                    if dx != 0 or dy != 0:
                        glow_draw.text((rainbow_x + dx, rainbow_y + dy), text, 
                                     fill=glow_color, font=font)
        
        # Inner glow (white, overlay mode, size 5)
        inner_glow_color = (255, 255, 255, 100)
        for offset in range(1, 6):
            for dx in [-offset, 0, offset]:
                for dy in [-offset, 0, offset]:
                    if dx != 0 or dy != 0:
                        glow_draw.text((rainbow_x + dx, rainbow_y + dy), text, 
                                     fill=inner_glow_color, font=font)
        
        # Combine rainbow text with glows
        result_canvas = Image.alpha_composite(glow_canvas, rainbow_canvas.convert('RGBA'))
        
        return result_canvas
    
    def add_subtle_lighting(self):
        """Add subtle lighting effects instead of stars"""
        lighting_layer = Image.new('RGBA', (self.width, self.height), (0,0,0,0))
        
        # Add very subtle light spots for ambiance
        light_positions = [
            (self.width * 0.2, self.height * 0.3, 30),
            (self.width * 0.8, self.height * 0.7, 25),
            (self.width * 0.6, self.height * 0.2, 20),
        ]
        
        for x, y, radius in light_positions:
            # Create subtle white light spot
            light_gradient = self.create_radial_gradient(
                int(x), int(y), radius,
                inner_color=(255, 255, 255, 15),
                outer_color=(255, 255, 255, 0)
            )
            lighting_layer = Image.alpha_composite(lighting_layer, light_gradient)
        
        return lighting_layer
    

    
    def create_daft_punk_effect(self, text="daft punk", font_path="Daft Font.TTF", 
                               texture_path="texture.png", output_path="daft_punk_effect.png"):
        """Main function to create the complete Daft Punk text effect"""
        
        print("Creating Daft Punk text effect...")
        
        # Step 1: Create pure black background
        print("Setting up black background...")
        background = self.setup_background()
        
        # Step 2: Load font and calculate text position
        print("Creating chrome text with heavy bevel effects...")
        font = self.load_font(font_path, size=100)
        
        # Calculate text position (center)
        temp_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = (self.width - text_width) // 2
        text_y = (self.height - text_height) // 2
        
        # Step 3: Create the 3 text layers as per tutorial
        
        # Layer 1: Main chrome text with all effects
        main_chrome_text = self.create_chrome_text_with_bevel(text, font, text_x, text_y)
        
        # Layer 2: Black shadow layer (offset)
        print("Creating black shadow layer...")
        black_shadow = self.create_colored_shadow_layer(text, font, text_x, text_y)
        
        # Layer 3: Rainbow colored layer with effects (further offset)
        print("Creating rainbow colored layer...")
        rainbow_layer = self.create_rainbow_colored_layer(text, font, text_x, text_y)
        
        # Step 4: Combine all layers in proper order (as per tutorial)
        print("Combining layers...")
        result = background.convert('RGBA')
        
        # Layer order from bottom to top:
        # 1. Rainbow layer (bottom/back)
        rainbow_reduced = rainbow_layer.copy()
        # Erase/mask parts of rainbow as mentioned in tutorial
        rainbow_alpha = rainbow_reduced.split()[-1]
        rainbow_alpha = ImageEnhance.Brightness(rainbow_alpha).enhance(0.7)  # Reduce some brightness
        rainbow_reduced.putalpha(rainbow_alpha)
        result = Image.alpha_composite(result, rainbow_reduced)
        
        # 2. Black shadow layer (middle)
        result = Image.alpha_composite(result, black_shadow)
        
        # 3. Main chrome text (top)
        result = Image.alpha_composite(result, main_chrome_text)
        
        # Final adjustments - enhance contrast and colors
        result = result.convert('RGB')
        enhancer = ImageEnhance.Contrast(result)
        result = enhancer.enhance(1.2)
        
        enhancer = ImageEnhance.Color(result)
        result = enhancer.enhance(1.3)
        
        # Save result
        result.save(output_path, 'PNG', quality=95)
        print(f"Daft Punk effect saved as: {output_path}")
        
        return result

def main():
    """Main function to run the script"""
    print("Daft Punk Text Effect Generator")
    print("=" * 40)
    
    # Get user input
    # text = input("Enter text (default: 'daft punk'): ").strip() or "daft punk"
    # text = 'stop starting\nstart finishing\nstart stoppping'
    text = 'stop starting\nstart finishing'
    
    # Check for required files
    font_path = "Daft Font.TTF"
    texture_path = "texture.png"
    brush_path = "brush.abr"  # Not used in PIL version but mentioned for reference
    
    print(f"\nLooking for files:")
    print(f"Font: {font_path} - {'Found' if os.path.exists(font_path) else 'Not found (will use default)'}")
    print(f"Texture: {texture_path} - {'Found' if os.path.exists(texture_path) else 'Not found (will generate)'}")
    
    # Create the effect
    effect_generator = DaftPunkTextEffect(width=1000, height=600)
    result = effect_generator.create_daft_punk_effect(
        text=text,
        font_path=font_path,
        texture_path=texture_path,
        output_path="daft_punk_effect.png"
    )
    
    print("\nEffect generation complete!")
    print("Output saved as: daft_punk_effect.png")

if __name__ == "__main__":
    # Install required packages if not available
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        print("Required packages not found. Please install:")
        print("pip install Pillow numpy")
        sys.exit(1)
    
    main()
