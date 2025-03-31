from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_login import login_user, logout_user, current_user, login_required
import traceback

# Import the db instance and User model from app, not recreate them
from app import db
from app.models import User, Design

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            if not all([username, email, password]):
                flash('All fields are required')
                return render_template('auth/register.html')
                
            with current_app.app_context():
                if User.query.filter_by(username=username).first():
                    flash('Username already exists')
                    return render_template('auth/register.html')
                    
                if User.query.filter_by(email=email).first():
                    flash('Email already registered')
                    return render_template('auth/register.html')
                
                user = User(username=username, email=email)
                user.set_password(password)
                
                db.session.add(user)
                db.session.commit()
                
                current_app.logger.info(f"User registered: {username}")
                
                login_user(user)
                return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            flash('An error occurred during registration. Please try again.')
            return render_template('auth/register.html')
        
    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            remember_me = request.form.get('remember_me') == 'on'
            
            with current_app.app_context():
                user = User.query.filter_by(username=username).first()
                
                if not user or not user.check_password(password):
                    flash('Invalid username or password')
                    return render_template('auth/login.html')
                    
                login_user(user, remember=remember_me)
                return redirect(url_for('main.index'))
        except Exception as e:
            current_app.logger.error(f"Login error: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            flash('An error occurred during login. Please try again.')
            return render_template('auth/login.html')
        
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/account')
@login_required
def account():
    with current_app.app_context():
        user_designs = Design.query.filter_by(user_id=current_user.id).order_by(Design.created_at.desc()).all()
    return render_template('auth/account.html', user=current_user, designs=user_designs)

@bp.route('/designs')
@login_required
def my_designs():
    with current_app.app_context():
        user_designs = Design.query.filter_by(user_id=current_user.id).order_by(Design.created_at.desc()).all()
    return render_template('auth/designs.html', designs=user_designs)

@bp.route('/designs/<int:design_id>/delete', methods=['POST'])
@login_required
def delete_design(design_id):
    try:
        with current_app.app_context():
            design = Design.query.filter_by(id=design_id, user_id=current_user.id).first()
            
            if not design:
                return jsonify({'error': 'Design not found or not owned by you'}), 404
            
            # Delete from database
            db.session.delete(design)
            db.session.commit()
            
            return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Design delete error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/cloudinary', methods=['GET', 'POST'])
@login_required
def cloudinary_settings():
    if request.method == 'POST':
        try:
            # Handle the form submission for Cloudinary credentials
            cloud_name = request.form.get('cloud_name')
            api_key = request.form.get('api_key')
            api_secret = request.form.get('api_secret')
            
            if not all([cloud_name, api_key, api_secret]):
                flash('All Cloudinary credentials are required')
                return render_template('auth/cloudinary.html')
                
            # Update user's Cloudinary settings
            current_user.cloudinary_cloud_name = cloud_name
            current_user.cloudinary_api_key = api_key
            current_user.cloudinary_api_secret = api_secret
            current_user.cloudinary_connected = True
            
            db.session.commit()
            flash('Cloudinary account connected successfully')
            return redirect(url_for('auth.account'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Cloudinary settings error: {str(e)}")
            flash('An error occurred while saving your Cloudinary settings.')
            return render_template('auth/cloudinary.html')
        
    return render_template('auth/cloudinary.html') 