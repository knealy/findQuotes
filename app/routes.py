from flask import Blueprint, render_template, request, jsonify, send_from_directory, current_app, url_for, session
from flask_login import current_user, login_required
from app.scraper import QuoteScraper
from app.designer import QuoteDesigner
from app.models import Quote, Design, User
from app import db
import os
from werkzeug.utils import secure_filename
import time
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from dotenv import load_dotenv
import random

bp = Blueprint('main', __name__)
scraper = QuoteScraper()
designer = QuoteDesigner()

# Load environment variables
load_dotenv()

# Optional Cloudinary configuration from environment (will be overridden by user credentials when available)
cloudinary_env_configured = False
cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
api_key = os.getenv('CLOUDINARY_API_KEY')
api_secret = os.getenv('CLOUDINARY_API_SECRET')

if all([cloud_name, api_key, api_secret]):
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret
    )
    cloudinary_env_configured = True

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/search', methods=['POST'])
def search_quotes():
    topic = request.form.get('topic', '')
    max_quotes = request.form.get('max_quotes', 10)
    news_ratio = request.form.get('news_ratio', 40)
    
    try:
        # Convert max_quotes to integer with a reasonable limit
        try:
            max_quotes = int(max_quotes)
            max_quotes = min(max(max_quotes, 5), 30)  # Between 5 and 30
        except (ValueError, TypeError):
            max_quotes = 10
            
        # Convert news_ratio to integer percentage
        try:
            news_ratio = int(news_ratio)
            
            # IMPORTANT FIX: Invert the news ratio if coming from slider
            # If slider is 100%, we want 100% news; if slider is 0%, we want 0% news
            news_ratio_decimal = news_ratio / 100.0  # Convert percentage to decimal
            
            print(f"News ratio received: {news_ratio}%, decimal: {news_ratio_decimal}")
        except (ValueError, TypeError):
            news_ratio_decimal = 0.4  # Default to 40%
            print("Using default news ratio: 40%")
        
        # Try to scrape quotes from the web
        quotes = scraper.search_quotes(topic, max_quotes=max_quotes, news_ratio=news_ratio_decimal)
        
        # If no quotes found or scraping failed, use fallback quotes
        if not quotes:
            quotes = get_fallback_quotes(topic)[:max_quotes]
            
        return jsonify(quotes)
    except Exception as e:
        print(f"Error searching quotes: {str(e)}")
        # Return fallback quotes on error
        return jsonify(get_fallback_quotes(topic)[:max_quotes])

def get_fallback_quotes(topic):
    """Return a set of fallback quotes when web scraping fails."""
    fallback_quotes = [
        {"text": "The greatest glory in living lies not in never falling, but in rising every time we fall.", "author": "Nelson Mandela", "source": "Fallback"},
        {"text": "The way to get started is to quit talking and begin doing.", "author": "Walt Disney", "source": "Fallback"},
        {"text": "Your time is limited, so don't waste it living someone else's life.", "author": "Steve Jobs", "source": "Fallback"},
        {"text": "If life were predictable it would cease to be life, and be without flavor.", "author": "Eleanor Roosevelt", "source": "Fallback"},
        {"text": "Life is what happens when you're busy making other plans.", "author": "John Lennon", "source": "Fallback"},
        {"text": "Spread love everywhere you go. Let no one ever come to you without leaving happier.", "author": "Mother Teresa", "source": "Fallback"},
        {"text": "When you reach the end of your rope, tie a knot in it and hang on.", "author": "Franklin D. Roosevelt", "source": "Fallback"},
        {"text": "Always remember that you are absolutely unique. Just like everyone else.", "author": "Margaret Mead", "source": "Fallback"},
        {"text": "Don't judge each day by the harvest you reap but by the seeds that you plant.", "author": "Robert Louis Stevenson", "source": "Fallback"},
        {"text": "The future belongs to those who believe in the beauty of their dreams.", "author": "Eleanor Roosevelt", "source": "Fallback"},
        {"text": "Tell me and I forget. Teach me and I remember. Involve me and I learn.", "author": "Benjamin Franklin", "source": "Fallback"},
        {"text": "The best and most beautiful things in the world cannot be seen or even touched — they must be felt with the heart.", "author": "Helen Keller", "source": "Fallback"},
        {"text": "It is during our darkest moments that we must focus to see the light.", "author": "Aristotle", "source": "Fallback"},
        {"text": "Whoever is happy will make others happy too.", "author": "Anne Frank", "source": "Fallback"},
        {"text": "Do not go where the path may lead, go instead where there is no path and leave a trail.", "author": "Ralph Waldo Emerson", "source": "Fallback"}
    ]
    
    # Add some news-like fallback quotes to ensure we have a mix
    news_fallback_quotes = [
        {"text": f"Recent studies show that regular {topic} practices can improve overall wellbeing.", "author": "Health Magazine", "source": "Recent News"},
        {"text": f"Experts are concerned about the impact of {topic} on economic growth.", "author": "Financial Times", "source": "Recent News"},
        {"text": f"New research reveals unexpected benefits of {topic} for cognitive health.", "author": "Science Daily", "source": "Recent News"},
        {"text": f"Global trends in {topic} are shifting dramatically, according to industry experts.", "author": "Business Insider", "source": "Web Search"},
        {"text": f"The future of {topic} remains uncertain as new technologies emerge.", "author": "Tech Review", "source": "Web Search"}
    ]
    
    # Combine both types
    combined_fallback = fallback_quotes + news_fallback_quotes
    random.shuffle(combined_fallback)
    return combined_fallback

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
            # Use user's Cloudinary account if logged in and connected
            if current_user.is_authenticated and current_user.cloudinary_connected:
                # Configure Cloudinary with user's credentials
                cloudinary.config(
                    cloud_name=current_user.cloudinary_cloud_name,
                    api_key=current_user.cloudinary_api_key,
                    api_secret=current_user.cloudinary_api_secret
                )
                
                # Upload to user's Cloudinary account
                upload_result = cloudinary.uploader.upload(
                    design_path,
                    public_id=f"user_{current_user.id}/quotes/{design_id}",
                    overwrite=True
                )
                
                # Check if design already exists in user's collection
                existing_design = Design.query.filter_by(
                    user_id=current_user.id,
                    design_id=design_id
                ).first()
                
                if existing_design:
                    # Update existing design
                    existing_design.cloudinary_url = upload_result['secure_url']
                    db.session.commit()
                    
                    return jsonify({
                        'success': True,
                        'image_url': upload_result['secure_url'],
                        'share_url': f"{request.host_url.rstrip('/')}/s/{design_id}",
                        'saved_to_account': True,
                        'message': 'Design updated in your Cloudinary account!'
                    })
                else:
                    # Create new design entry
                    new_design = Design(
                        user_id=current_user.id,
                        design_id=design_id,
                        cloudinary_url=upload_result['secure_url'],
                        title=f"Quote Design {design_id}"
                    )
                    db.session.add(new_design)
                    db.session.commit()
                    
                    return jsonify({
                        'success': True,
                        'image_url': upload_result['secure_url'],
                        'share_url': f"{request.host_url.rstrip('/')}/s/{design_id}",
                        'saved_to_account': True,
                        'message': 'Design saved to your Cloudinary account!'
                    })
            
            # If no user or user has no Cloudinary connection, check if app has Cloudinary config
            cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
            api_key = os.getenv('CLOUDINARY_API_KEY')
            api_secret = os.getenv('CLOUDINARY_API_SECRET')
            
            if all([cloud_name, api_key, api_secret]):
                # Use app's Cloudinary config
                cloudinary.config(
                    cloud_name=cloud_name,
                    api_key=api_key,
                    api_secret=api_secret
                )
                
                upload_result = cloudinary.uploader.upload(
                    design_path,
                    public_id=f"quotes/{design_id}",
                    overwrite=True
                )
                
                image_url = upload_result['secure_url']
                share_url = f"{request.host_url.rstrip('/')}/s/{design_id}"
                
                return jsonify({
                    'success': True,
                    'image_url': image_url,
                    'share_url': share_url,
                    'saved_to_account': False,
                    'message': 'Your design has been shared to our cloud storage. To save to your personal account, connect Cloudinary in your profile.'
                })
            else:
                # No Cloudinary credentials available
                return jsonify({
                    'success': True,
                    'image_url': url_for('static', filename=f'designs/{design_id}.png', _external=True),
                    'share_url': f"{request.host_url.rstrip('/')}/s/{design_id}",
                    'saved_to_account': False,
                    'message': 'Your design has been saved locally. To enable cloud storage, connect Cloudinary in your profile settings.'
                })
            
        except Exception as cloud_error:
            print(f"Cloudinary upload error: {str(cloud_error)}")
            return jsonify({
                'success': False,
                'error': f'Cloud storage error: {str(cloud_error)}',
                'details': 'There was a problem uploading your design to cloud storage.'
            }), 500
            
    except Exception as e:
        print(f"Share error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/s/<design_id>', methods=['GET'])
def view_share(design_id):
    """Render the share page with proper meta tags"""
    try:
        # First check if any user has saved this design to Cloudinary
        design = Design.query.filter_by(design_id=design_id).first()
        
        if design and design.cloudinary_url:
            # Use the already saved Cloudinary URL
            cloudinary_url = design.cloudinary_url
        else:
            # Try to get from environment Cloudinary
            try:
                if cloudinary_env_configured:
                    cloudinary_url = cloudinary.utils.cloudinary_url(f"quotes/{design_id}")[0]
                    if cloudinary_url.startswith('http:'):
                        cloudinary_url = cloudinary_url.replace('http:', 'https:', 1)
                else:
                    # Use local image path
                    cloudinary_url = url_for('static', filename=f'designs/{design_id}.png', _external=True)
            except:
                # Fallback to local image
                cloudinary_url = url_for('static', filename=f'designs/{design_id}.png', _external=True)
            
        # Use request.host_url for share URL
        share_url = f"{request.host_url.rstrip('/')}/s/{design_id}"
        
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
        try:
            # Try to use Cloudinary if available
            use_cloudinary = False
            
            # Check if user has Cloudinary connected
            if current_user.is_authenticated and current_user.cloudinary_connected:
                # Configure with user credentials
                cloudinary.config(
                    cloud_name=current_user.cloudinary_cloud_name,
                    api_key=current_user.cloudinary_api_key,
                    api_secret=current_user.cloudinary_api_secret
                )
                use_cloudinary = True
            elif cloudinary_env_configured:
                # Environment variables are already configured
                use_cloudinary = True
            
            if use_cloudinary:
                # Upload to Cloudinary
                upload_result = cloudinary.uploader.upload(file)
                return jsonify({
                    'success': True,
                    'background_url': upload_result['secure_url']
                })
            else:
                # Fallback to local storage
                filename = secure_filename(file.filename)
                unique_filename = f"{int(time.time())}_{filename}"
                
                upload_folder = os.path.join(current_app.static_folder, 'backgrounds')
                os.makedirs(upload_folder, exist_ok=True)
                
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                
                return jsonify({
                    'success': True,
                    'background_url': url_for('static', filename=f'backgrounds/{unique_filename}')
                })
                
        except Exception as e:
            return jsonify({'error': f'Upload failed: {str(e)}'}), 500
    
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
            # Try to use Cloudinary if available
            use_cloudinary = False
            
            # Check if user has Cloudinary connected
            if current_user.is_authenticated and current_user.cloudinary_connected:
                # Configure with user credentials
                cloudinary.config(
                    cloud_name=current_user.cloudinary_cloud_name,
                    api_key=current_user.cloudinary_api_key,
                    api_secret=current_user.cloudinary_api_secret
                )
                use_cloudinary = True
            elif cloudinary_env_configured:
                # Environment variables are already configured
                use_cloudinary = True
            
            if use_cloudinary:
                # Upload to Cloudinary
                upload_result = cloudinary.uploader.upload(file)
                return jsonify({
                    'success': True,
                    'image_url': upload_result['secure_url']
                })
            else:
                # Fallback to local storage
                filename = secure_filename(file.filename)
                unique_filename = f"{int(time.time())}_{filename}"
                
                upload_folder = os.path.join(current_app.static_folder, 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                
                return jsonify({
                    'success': True,
                    'image_url': url_for('static', filename=f'uploads/{unique_filename}')
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

@bp.route('/connect-cloudinary', methods=['POST'])
def connect_cloudinary():
    """Connect user's Cloudinary account"""
    if 'user_id' not in session:
        return jsonify({'error': 'You must be logged in to connect your account'}), 401
        
    try:
        # Get Cloudinary credentials from form
        cloud_name = request.form.get('cloud_name')
        api_key = request.form.get('api_key')
        api_secret = request.form.get('api_secret')
        
        if not all([cloud_name, api_key, api_secret]):
            return jsonify({'error': 'All Cloudinary credentials are required'}), 400
            
        # Test the connection
        test_config = cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Try a simple API call to verify credentials
        account_info = cloudinary.api.account_info()
        
        # If successful, save to user's profile
        user = User.query.get(session['user_id'])
        user.cloudinary_cloud_name = cloud_name
        user.cloudinary_api_key = api_key
        user.cloudinary_api_secret = api_secret  # In production, encrypt this!
        user.cloudinary_connected = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Successfully connected to Cloudinary account'
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to connect Cloudinary account',
            'details': str(e)
        }), 500 