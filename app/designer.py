from PIL import Image, ImageDraw, ImageFont
import os
import random
from typing import Dict, Tuple
import textwrap
from flask import current_app, send_from_directory, jsonify, url_for, request
import time

class QuoteDesigner:
    def __init__(self):
        self.fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app/static/fonts')
        self.backgrounds_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app/static/backgrounds')
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app/static/uploads')
        
        # Ensure directories exist
        os.makedirs(self.fonts_dir, exist_ok=True)
        os.makedirs(self.backgrounds_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Default fonts and colors
        self.fonts = {
            'elegant': 'PlayfairDisplay-Regular.ttf',
            'modern': 'Roboto-Regular.ttf',
            'classic': 'TimesNewRoman.ttf'
        }
        
        self.colors = {
            'dark': '#1a1a1a',
            'light': '#ffffff',
            'accent': '#ff6b6b'
        }
    
    def create_design(self, quote: str, author: str, 
                     font_style: str = 'elegant',
                     font_size: int = 40,
                     font_color: str = '#000000',
                     background: Dict[str, str] = {'type': 'color', 'color': '#ffffff'}) -> str:
        # Convert quote to string if it's not already
        if not isinstance(quote, str):
            quote = str(quote)
        
        # Extract only the text within quotation marks
        if '"' in quote:
            start = quote.find('"')
            end = quote.rfind('"')
            if start != -1 and end != -1 and end > start:
                quote = quote[start:end+1]
        
        # Clean up the quote text
        quote = quote.strip()
        
        # Remove the author attribution completely
        if f"- {author}" in quote:
            quote = quote.replace(f"- {author}", "").strip()
        if f"– {author}" in quote:  # Handle en dash
            quote = quote.replace(f"– {author}", "").strip()
        if f"— {author}" in quote:  # Handle em dash
            quote = quote.replace(f"— {author}", "").strip()
        if author in quote:  # Remove just the author name if it appears
            quote = quote.replace(author, "").strip()
        
        # Now wrap the cleaned quote text
        wrapped_text = textwrap.fill(quote, width=30)
        
        # Create image
        img_width, img_height = 800, 800  # Square image for better social media sharing
        
        # Check if split design is enabled
        split_enabled = background.get('split_enabled', False)
        
        # Handle different background types
        if background['type'] == 'color':
            # Solid color background
            img = Image.new('RGB', (img_width, img_height), color=background['color'])
        
        elif background['type'] == 'gradient':
            # Create gradient background
            img = self.create_gradient_background(
                img_width, 
                img_height, 
                background['color1'], 
                background['color2'], 
                background['direction']
            )
        
        elif background['type'] == 'image' and 'url' in background:
            # Image background
            try:
                # Extract filename from URL
                image_path = os.path.join(
                    current_app.root_path, 
                    'static', 
                    background['url'].split('/static/')[1]
                )
                bg_img = Image.open(image_path).convert('RGB')
                
                # Resize to fit
                bg_img = bg_img.resize((img_width, img_height), Image.LANCZOS)
                img = bg_img
                
                # Add slight overlay for better text visibility
                overlay = Image.new('RGB', (img_width, img_height), color='#000000')
                img = Image.blend(img, overlay, 0.2)
                
            except Exception as e:
                # Fallback to white background if image can't be loaded
                print(f"Error loading background image: {e}")
                img = Image.new('RGB', (img_width, img_height), color='#ffffff')
        else:
            # Default white background
            img = Image.new('RGB', (img_width, img_height), color='#ffffff')
        
        # If split design is enabled, process the split image
        if split_enabled and 'split_image' in background:
            try:
                split_image_url = background['split_image']
                split_position = background.get('split_position', 'top')
                
                # Get the split image
                if split_image_url.startswith('http'):
                    # Download remote image
                    import requests
                    from io import BytesIO
                    response = requests.get(split_image_url)
                    split_img = Image.open(BytesIO(response.content))
                else:
                    # Load local image
                    image_path = os.path.join(
                        current_app.root_path, 
                        'static', 
                        split_image_url.split('/static/')[1]
                    )
                    split_img = Image.open(image_path)
                
                # Resize the split image to fit half the design height
                split_height = img_height // 2
                split_img = split_img.resize((img_width, split_height), Image.LANCZOS)
                
                # Place the split image at the top or bottom half
                if split_position == 'top':
                    img.paste(split_img, (0, 0))
                else:  # bottom
                    img.paste(split_img, (0, split_height))
            except Exception as e:
                print(f"Error processing split image: {str(e)}")
                # Continue with the base background if split image fails
        
        # Draw the quote text
        draw = ImageDraw.Draw(img)
        
        # Get font
        font_map = {
            'arial': 'arial.ttf',
            'times': 'times.ttc',
            'courier': 'courier.ttc',
            'geneva': 'geneva.ttf',
            'helvetica': 'helvetica.ttc',
            'monaco': 'monaco.ttf'
        }
        
        # Use default font if specified font doesn't exist
        try:
            font_file = font_map.get(font_style, 'arial.ttf')
            font_path = os.path.join(current_app.static_folder, 'fonts', font_file)
            
            # Check if font exists
            if os.path.exists(font_path):
                quote_font = ImageFont.truetype(font_path, font_size)
                author_font = ImageFont.truetype(font_path, font_size // 2)
            else:
                # Try system fonts as fallback
                quote_font = ImageFont.truetype('Arial', font_size)
                author_font = ImageFont.truetype('Arial', font_size // 2)
        except Exception as e:
            print(f"Font error: {str(e)}")
            # Last resort - use default font
            quote_font = ImageFont.load_default()
            author_font = ImageFont.load_default()
        
        # Calculate text size and position
        quote_bbox = draw.textbbox((0, 0), wrapped_text, font=quote_font)
        quote_width = quote_bbox[2] - quote_bbox[0]
        quote_height = quote_bbox[3] - quote_bbox[1]
        
        author_text = f"- {author}"
        author_bbox = draw.textbbox((0, 0), author_text, font=author_font)
        author_width = author_bbox[2] - author_bbox[0]
        author_height = author_bbox[3] - author_bbox[1]
        
        # Adjust text position if split design is enabled
        if split_enabled:
            split_position = background.get('split_position', 'top')
            if split_position == 'top':
                quote_y = (img_height // 2) + 50  # Text starts below the middle
            else:
                quote_y = (img_height // 4)  # Text starts at 1/4 from the top
        else:
            # Center the quote if no split design
            quote_y = (img_height - quote_height - author_height - 20) // 2
        
        # Center the quote
        quote_x = (img_width - quote_width) // 2
        
        # Position author below quote
        author_x = (img_width - author_width) // 2
        author_y = quote_y + quote_height + 20
        
        # Draw the texts
        draw.text((quote_x, quote_y), wrapped_text, font=quote_font, fill=font_color)
        draw.text((author_x, author_y), author_text, font=author_font, fill=font_color)
        
        # Save the image
        os.makedirs(os.path.join(current_app.static_folder, 'designs'), exist_ok=True)
        design_id = f"design_{int(time.time())}"
        image_filename = f"{design_id}.png"
        image_path = os.path.join(current_app.static_folder, 'designs', image_filename)
        img.save(image_path)
        
        return design_id
    
    def create_gradient_background(self, width, height, color1, color2, direction):
        """Create a gradient background image."""
        base = Image.new('RGB', (width, height), color1)
        top = Image.new('RGB', (width, height), color2)
        
        mask = Image.new('L', (width, height))
        mask_data = []
        
        if direction == 'horizontal':
            for y in range(height):
                for x in range(width):
                    mask_data.append(int(255 * (x / width)))
        elif direction == 'vertical':
            for y in range(height):
                for x in range(width):
                    mask_data.append(int(255 * (y / height)))
        else:  # diagonal
            for y in range(height):
                for x in range(width):
                    mask_data.append(int(255 * ((x + y) / (width + height))))
        
        mask.putdata(mask_data)
        final = Image.composite(top, base, mask)
        return final
    
    def create_split_design(self, quote_text, author, split_image_path, image_position, quote_bg_color, font_color):
        # Create base image with standard dimensions
        width = 1080
        height = 1080
        
        # Create the split sections
        split_height = height // 2
        
        # Load and resize the uploaded split image
        split_img = Image.open(split_image_path)
        split_img = split_img.resize((width, split_height), Image.LANCZOS)
        
        # Create the final image
        final_img = Image.new('RGB', (width, height), quote_bg_color)
        
        # Position the split image based on user selection
        if image_position == 'top':
            final_img.paste(split_img, (0, 0))
            quote_y_position = height // 2 + 100
        else:  # bottom
            final_img.paste(split_img, (0, split_height))
            quote_y_position = height // 4
        
        # Add text
        draw = ImageDraw.Draw(final_img)
        
        # Load font
        font_path = os.path.join('app', 'static', 'fonts', 'Roboto-Regular.ttf')
        quote_font = ImageFont.truetype(font_path, 60)
        author_font = ImageFont.truetype(font_path, 40)
        
        # Calculate text positions
        quote_lines = textwrap.wrap(quote_text, width=30)
        total_quote_height = len(quote_lines) * quote_font.getsize(quote_lines[0])[1]
        
        current_y = quote_y_position
        
        # Draw quote text
        for line in quote_lines:
            text_width = quote_font.getsize(line)[0]
            x_position = (width - text_width) // 2
            draw.text((x_position, current_y), line, font=quote_font, fill=font_color)
            current_y += quote_font.getsize(line)[1]
        
        # Draw author
        author_text = f"- {author}"
        author_width = author_font.getsize(author_text)[0]
        author_x = (width - author_width) // 2
        author_y = current_y + 20
        draw.text((author_x, author_y), author_text, font=author_font, fill=font_color)
        
        return final_img
    
    def create_split_design_with_url(self, quote_text, author, split_img, image_position, 
                                   quote_bg_color, font_color, font_style='arial', font_size=40):
        """Create a split design with an image on top/bottom and text on the opposite side"""
        # Create base image with standard dimensions - square for social media
        width = 800
        height = 800
        
        # Create the split sections
        split_height = height // 2
        
        # Resize the image to fit half the design
        split_img = split_img.resize((width, split_height), Image.LANCZOS)
        
        # Create the final image with the quote background color
        final_img = Image.new('RGB', (width, height), quote_bg_color)
        
        # Position the split image based on user selection
        if image_position == 'top':
            final_img.paste(split_img, (0, 0))
            quote_y_position = height // 2 + 50  # Text starts 50px below middle
        else:  # bottom
            final_img.paste(split_img, (0, split_height))
            quote_y_position = height // 4  # Text starts 1/4 from the top
        
        # Add text
        draw = ImageDraw.Draw(final_img)
        
        # Load font
        try:
            font_map = {
                'arial': 'arial.ttf',
                'times': 'times.ttc',
                'courier': 'courier.ttc',
                'geneva': 'geneva.ttf',
                'helvetica': 'helvetica.ttc', 
                'monaco': 'monaco.ttf'
            }
            font_file = font_map.get(font_style, 'arial.ttf')
            font_path = os.path.join(current_app.static_folder, 'fonts', font_file)
            
            if os.path.exists(font_path):
                quote_font = ImageFont.truetype(font_path, font_size)
                author_font = ImageFont.truetype(font_path, font_size // 2)
            else:
                quote_font = ImageFont.truetype('Arial', font_size)
                author_font = ImageFont.truetype('Arial', font_size // 2)
        except Exception as e:
            print(f"Font error: {str(e)}")
            quote_font = ImageFont.load_default()
            author_font = ImageFont.load_default()
        
        # Wrap the quote text for better presentation
        wrapped_text = textwrap.fill(quote_text, width=30)
        
        # Draw quote text
        quote_bbox = draw.textbbox((0, 0), wrapped_text, font=quote_font)
        quote_width = quote_bbox[2] - quote_bbox[0]
        text_x = (width - quote_width) // 2
        draw.text((text_x, quote_y_position), wrapped_text, font=quote_font, fill=font_color)
        
        # Draw author text
        author_text = f"- {author}"
        author_bbox = draw.textbbox((0, 0), author_text, font=author_font)
        author_width = author_bbox[2] - author_bbox[0]
        author_x = (width - author_width) // 2
        
        # Position author below quote
        author_y = quote_y_position + quote_bbox[3] - quote_bbox[1] + 20
        draw.text((author_x, author_y), author_text, font=author_font, fill=font_color)
        
        # Save the image with a unique design ID
        design_id = f"design_{int(time.time())}"
        image_filename = f"{design_id}.png"
        image_path = os.path.join(current_app.static_folder, 'designs', image_filename)
        final_img.save(image_path)
        
        return design_id
    
    def get_random_design(self, quote: str, author: str) -> str:
        font_style = random.choice(list(self.fonts.keys()))
        font_size = random.randint(30, 60)
        background_color = random.choice(list(self.colors.values()))
        
        return self.create_design(quote, author, font_style, font_size, self.colors['dark'], {'type': 'color', 'color': background_color}) 