# findQuotes

![findQuotes Logo](app/static/images/logo.png)

A full-featured web application that scrapes quotes from the internet, generates beautiful designs, and allows users to download or share them.

## Features

- **Quote Search**: Search for quotes on any topic from various sources
  - Famous historical quotes from reputable websites
  - Recent news quotes from current events
  - Adjustable ratio between famous and news quotes
  
- **Quote Design**: Create beautiful visual quotes
  - Multiple font styles and sizes
  - Custom color selection
  - Background options (solid color, gradient, or image)
  - Split-design functionality

- **User Accounts**: Personal user profiles to save and manage quotes
  - Register and login functionality
  - Password security
  - Personal design library
  
- **Cloudinary Integration**: Cloud storage for designs
  - Connect your personal Cloudinary account
  - Save designs directly to your cloud library
  - Private cloud storage for each user
  
- **Dark Mode**: Toggle between light and dark themes
  - Consistent across all pages
  - Remembers user preference
  
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Technical Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Bootstrap 5, JavaScript, CSS
- **Authentication**: Flask-Login
- **Web Scraping**: BeautifulSoup4, Requests
- **Image Processing**: Pillow
- **Cloud Storage**: Cloudinary API

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- A Cloudinary account (optional, but recommended)

### Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/yourusername/findQuotes.git
cd findQuotes
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

4. Set up the database:
```bash
python init_db.py
```

5. Run the application:
```bash
python -m flask run
```

The application will be available at `http://127.0.0.1:5000`

## Configuration

### Optional: App-level Cloudinary Setup

If you want to provide a default Cloudinary account for users who haven't connected their own, create a `.env` file with your Cloudinary credentials:

CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
SECRET_KEY=your_flask_secret_key

### User-level Cloudinary Setup

Each user can connect their own Cloudinary account through their profile settings:

1. Sign up for a free Cloudinary account at [cloudinary.com](https://cloudinary.com)
2. Log into findQuotes
3. Go to your account page
4. Click "Connect Cloudinary"
5. Enter your Cloud Name, API Key, and API Secret
6. Click "Save Cloudinary Settings"

## Usage

### Finding Quotes

1. Enter a topic in the search box
2. Adjust the news ratio slider (100% news to 0% famous quotes)
3. Click "Search"
4. Select a quote from the results

### Designing Quotes

1. Choose font style, size, and color
2. Select background type (color, gradient, or image)
3. Configure any additional options (split design, etc.)
4. Click "Generate Design"

### Saving and Sharing

1. Click "Download" to save the design to your device
2. Click "Save to Cloud" to upload the design to your Cloudinary account
3. Access your saved designs through your account page

## Development

### Project Structure

```
findQuotes/
├── app/
│   ├── __init__.py        # Application factory and initialization
│   ├── models.py          # Database models
│   ├── routes.py          # Main routes and endpoints
│   ├── auth.py            # Authentication routes
│   ├── scraper.py         # Quote scraping functionality
│   ├── designer.py        # Quote design generation
│   ├── static/            # Static assets (CSS, JS, images)
│   └── templates/         # HTML templates
├── migrations/            # Database migrations
├── requirements.txt       # Python dependencies
├── config.py              # Application configuration
├── init_db.py             # Database initialization script
└── run.py                 # Application entry point
```

### Adding New Features

- **New Quote Sources**: Add new websites to the `sources` list in `app/scraper.py`
- **New Design Options**: Extend the `create_design` method in `app/designer.py`
- **User Preferences**: Add fields to the `User` model in `app/models.py`

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Quote data provided by various public websites
- Design inspiration from popular quote sharing platforms
- Cloud storage powered by Cloudinary 