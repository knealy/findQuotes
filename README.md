# Automated Quote-Finding App

A web application that scrapes quotes from the internet, generates beautiful designs, and allows users to download or share them.

## Features

- Web scraping for quotes based on user input
- Automated quote design generation
- Customizable design options
- Responsive web interface
- Social media sharing capabilities

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd QuoteApp
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

6. Run the application:
```bash
flask run
```

The application will be available at `http://localhost:5000`

## Project Structure

```
QuoteApp/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── scraper.py
│   ├── designer.py
│   └── static/
│       ├── css/
│       ├── js/
│       └── images/
├── templates/
├── migrations/
├── requirements.txt
├── config.py
└── run.py
```

## Usage

1. Enter a topic or subject in the search box
2. Choose design preferences (optional)
3. View generated quote designs
4. Download or share quotes to social media

## Deployment

The application can be deployed using Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 