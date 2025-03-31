from app import create_app
from flask_migrate import migrate, upgrade

app = create_app()

with app.app_context():
    # Create a migration for the model changes
    migrate(message="Add Cloudinary fields to User model")
    
    # Apply the migration
    upgrade()
    
    print("Applied migration for Cloudinary fields") 