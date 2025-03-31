from app import create_app, db
from app.models import User

app = create_app()

def init_database():
    """Initialize the database with fresh tables and sample data if needed"""
    with app.app_context():
        print("Creating all database tables...")
        db.create_all()
        
        # Create a demo user if needed
        if User.query.count() == 0:
            print("Creating a demo user...")
            demo_user = User(username="demo", email="demo@example.com")
            demo_user.set_password("password")
            db.session.add(demo_user)
            db.session.commit()
            print("Demo user created!")

if __name__ == "__main__":
    init_database() 