from flask import Blueprint, render_template, request, jsonify, send_from_directory, current_app, url_for
from app.scraper import QuoteScraper
from app.designer import QuoteDesigner
from app.models import Quote, Design
from app import db
import os
from werkzeug.utils import secure_filename
import time
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from dotenv import load_dotenv

bp = Blueprint('main', __name__)
scraper = QuoteScraper()
designer = QuoteDesigner()

# Load environment variables
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/search', methods=['POST'])
def search_quotes():
    topic = request.form.get('topic', '')
    
    try:
        # Try to scrape quotes from the web
        quotes = scraper.search_quotes(topic)
        
        # If no quotes found or scraping failed, use fallback quotes
        if not quotes:
            quotes = get_fallback_quotes(topic)
            
        return jsonify(quotes)
    except Exception as e:
        print(f"Error searching quotes: {str(e)}")
        # Return fallback quotes on error
        return jsonify(get_fallback_quotes(topic))

def get_fallback_quotes(topic):
    """Return a set of fallback quotes when web scraping fails."""
    fallback_quotes = [
        {"text": "The greatest glory in living lies not in never falling, but in rising every time we fall.", "author": "Nelson Mandela"},
        {"text": "The way to get started is to quit talking and begin doing.", "author": "Walt Disney"},
        {"text": "Your time is limited, so don't waste it living someone else's life.", "author": "Steve Jobs"},
        {"text": "If life were predictable it would cease to be life, and be without flavor.", "author": "Eleanor Roosevelt"},
        {"text": "Life is what happens when you're busy making other plans.", "author": "John Lennon"},
        {"text": "Spread love everywhere you go. Let no one ever come to you without leaving happier.", "author": "Mother Teresa"},
        {"text": "When you reach the end of your rope, tie a knot in it and hang on.", "author": "Franklin D. Roosevelt"},
        {"text": "Always remember that you are absolutely unique. Just like everyone else.", "author": "Margaret Mead"},
        {"text": "Don't judge each day by the harvest you reap but by the seeds that you plant.", "author": "Robert Louis Stevenson"},
        {"text": "The future belongs to those who believe in the beauty of their dreams.", "author": "Eleanor Roosevelt"},
        {"text": "Tell me and I forget. Teach me and I remember. Involve me and I learn.", "author": "Benjamin Franklin"},
        {"text": "The best and most beautiful things in the world cannot be seen or even touched — they must be felt with the heart.", "author": "Helen Keller"},
        {"text": "It is during our darkest moments that we must focus to see the light.", "author": "Aristotle"},
        {"text": "Whoever is happy will make others happy too.", "author": "Anne Frank"},
        {"text": "Do not go where the path may lead, go instead where there is no path and leave a trail.", "author": "Ralph Waldo Emerson"}
    ]
    return fallback_quotes

@bp.route('/design', methods=['POST'])
def create_design():
    try:
        # Handle both form-data and JSON requests
        if request.is_json:
            data = request.json
            quote = data.get('quote', '')
            author = data.get('author', '')
            font_style = data.get('font_style', 'arial')
            
            # Font size can be string or number
            font_size_raw = data.get('font_size', 'medium')
            if isinstance(font_size_raw, str) and not font_size_raw.isdigit():
                font_size_map = {
                    'small': 30,
                    'medium': 40,
                    'large': 50
                }
                font_size = font_size_map.get(font_size_raw, 40)
            else:
                font_size = int(font_size_raw)
            
            font_color = data.get('font_color', '#000000')
            background = data.get('background', {'type': 'color', 'color': '#ffffff'})
        else:
            # Handle form submission (old method)
            quote = request.form.get('quote', '')
            author = request.form.get('author', '')
            font_style = request.form.get('font_style', 'arial')
            
            # Font size handling
            font_size_text = request.form.get('font_size', 'medium')
            font_size_map = {
                'small': 30,
                'medium': 40,
                'large': 50
            }
            font_size = font_size_map.get(font_size_text, 40)
            
            font_color = request.form.get('font_color', '#000000')
            background = {'type': 'color', 'color': request.form.get('background_color', '#ffffff')}
        
        # Make sure quote is a string
        if not isinstance(quote, str):
            quote = str(quote)
        
        # Generate the design
        design_id = designer.create_design(
            quote=quote,
            author=author,
            font_style=font_style,
            font_size=font_size,
            font_color=font_color,
            background=background
        )
        
        # Return the design information
        image_url = url_for('static', filename=f'designs/{design_id}.png')
        return jsonify({
            'success': True,
            'design_id': design_id,
            'image_url': image_url
        })
        
    except Exception as e:
        print(f"Error creating design: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/download/<design_id>', methods=['GET'])
def download_design(design_id):
    try:
        # Find the image file
        design_path = os.path.join(current_app.static_folder, 'designs', f'{design_id}.png')
        
        if not os.path.exists(design_path):
            return jsonify({'error': 'Design not found'}), 404
        
        # Get the directory and filename
        directory = os.path.dirname(design_path)
        filename = os.path.basename(design_path)
        
        # Return the file as an attachment for download
        # Use download_name instead of attachment_filename for newer Flask versions
        return send_from_directory(
            directory,
            filename,
            as_attachment=True,
            download_name=f'quote-design-{design_id}.png'
        )
    except Exception as e:
        print(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_base_url():
    """Get the base URL for sharing"""
    return current_app.config['BASE_URL']

@bp.route('/share/<design_id>', methods=['GET'])
def share_design(design_id):
    try:
        design_path = os.path.join(current_app.static_folder, 'designs', f'{design_id}.png')
        
        if not os.path.exists(design_path):
            return jsonify({'error': 'Design not found'}), 404
        
        try:
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                design_path,
                public_id=f"quotes/{design_id}",
                overwrite=True
            )
            
            image_url = upload_result['secure_url']
            
            # Use request.host_url for development
            base_url = request.host_url.rstrip('/')
            share_url = f"{base_url}/s/{design_id}"
            
            print(f"Generated share URL: {share_url}")
            print(f"Cloudinary image URL: {image_url}")
            
            return jsonify({
                'success': True,
                'image_url': image_url,
                'share_url': share_url
            })
            
        except Exception as cloud_error:
            print(f"Cloudinary upload error: {str(cloud_error)}")
            return jsonify({
                'error': 'Failed to upload image to cloud storage',
                'details': str(cloud_error)
            }), 500
            
    except Exception as e:
        print(f"Share error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/s/<design_id>', methods=['GET'])
def view_share(design_id):
    """Render the share page with proper meta tags"""
    try:
        # Get the Cloudinary URL
        cloudinary_url = cloudinary.utils.cloudinary_url(f"quotes/{design_id}")[0]
        if cloudinary_url.startswith('http:'):
            cloudinary_url = cloudinary_url.replace('http:', 'https:', 1)
            
        # Use request.host_url for development
        base_url = request.host_url.rstrip('/')
        share_url = f"{base_url}/s/{design_id}"
        
        print(f"Rendering share page for: {share_url}")
        print(f"With image URL: {cloudinary_url}")
        
        return render_template('share.html', 
                             image_url=cloudinary_url,
                             share_url=share_url)
    except Exception as e:
        print(f"Share page error: {str(e)}")
        return str(e), 500

@bp.route('/upload-background', methods=['POST'])
def upload_background():
    if 'background_image' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['background_image']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        # Generate a secure filename to prevent security issues
        filename = secure_filename(file.filename)
        # Add a timestamp to make it unique
        unique_filename = f"{int(time.time())}_{filename}"
        
        # Create upload folder if it doesn't exist
        upload_folder = os.path.join(current_app.static_folder, 'backgrounds')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Return the path for use in the frontend
        return jsonify({
            'success': True,
            'background_url': url_for('static', filename=f'backgrounds/{unique_filename}')
        })
    
    return jsonify({'error': 'File type not allowed'}), 400

def allowed_file(filename):
    # Only allow certain file types for security
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS 

@bp.route('/test-meta/<design_id>')
def test_meta(design_id):
    """Test route to verify meta tags"""
    try:
        # Use the stored Cloudinary URL if available
        if hasattr(current_app, 'design_urls') and design_id in current_app.design_urls:
            cloudinary_url = current_app.design_urls[design_id]
        else:
            # Fallback to constructing the URL
            cloudinary_url = f"https://res.cloudinary.com/dtah9fnes/image/upload/v{int(time.time())}/quotes/{design_id}.png"
            
        base_url = "https://0f12-68-44-48-193.ngrok-free.app"
        share_url = f"{base_url}/s/{design_id}"
        
        return f"""
        <h1>Meta Tags Test</h1>
        <p>Share URL: {share_url}</p>
        <p>Image URL: {cloudinary_url}</p>
        <img src="{cloudinary_url}" style="max-width: 500px">
        <p>Try these tools to debug:</p>
        <ul>
            <li><a href="https://cards-dev.twitter.com/validator?url={share_url}" target="_blank">Twitter Card Validator</a></li>
            <li><a href="https://developers.facebook.com/tools/debug/?q={share_url}" target="_blank">Facebook Debugger</a></li>
        </ul>
        <hr>
        <h2>Meta Tags Preview:</h2>
        <pre>
&lt;meta name="twitter:card" content="summary_large_image"/&gt;
&lt;meta name="twitter:title" content="Quote Design"/&gt;
&lt;meta name="twitter:description" content="Check out this quote design"/&gt;
&lt;meta name="twitter:image" content="{cloudinary_url}"/&gt;
        </pre>
        """
    except Exception as e:
        return str(e) 

@bp.route('/upload-split-image', methods=['POST'])
def upload_split_image():
    if 'split_image' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['split_image']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        try:
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(file)
            return jsonify({
                'success': True,
                'image_url': upload_result['secure_url']
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File type not allowed'}), 400 

@bp.route('/generate_preview', methods=['POST'])
def generate_preview():
    quote_text = request.form['quote']
    author = request.form['author']
    background_type = request.form['background_type']
    quote_bg_color = request.form['quote_bg_color']
    font_color = request.form['font_color']
    
    if background_type == 'split':
        split_image = request.files['split_image']
        image_position = request.form['image_position']
        
        # Save uploaded image temporarily
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_split.png')
        split_image.save(temp_path)
        
        # Generate the design
        final_image = create_split_design(
            quote_text,
            author,
            temp_path,
            image_position,
            quote_bg_color,
            font_color
        )
        
        # Clean up temp file
        os.remove(temp_path)
    else:
        final_image = create_basic_design(
            quote_text,
            author,
            quote_bg_color,
            font_color
        )

    # Save the preview image
    preview_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'preview.png')
    final_image.save(preview_path, 'PNG')
    
    return jsonify({'success': True}) 