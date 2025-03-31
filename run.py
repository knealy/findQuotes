from app import create_app, db
from app.models import User, Quote, Design

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Quote': Quote,
        'Design': Design
    }

if __name__ == '__main__':
    app.run(debug=True) 