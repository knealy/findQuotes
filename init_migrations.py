from app import create_app, db
from app.models import User, Quote, Design

app = create_app()

with app.app_context():
    # Import Flask-Migrate command functions
    from flask_migrate import init, migrate, upgrade
    
    # Initialize migrations repository
    init()
    
    # Create a migration for the current model structure
    migrate(message="Add Cloudinary fields to User model")
    
    # Apply the migration
    upgrade()
    
    print("Migration setup complete!") 