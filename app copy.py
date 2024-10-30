from collections import defaultdict
from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
import os
import json
from dotenv import load_dotenv
from flask_mail import Mail, Message

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # Your email
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # Your email password
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')  # Sender's email

# Initialize Flask-Mail
mail = Mail(app)

# Connect to the SQLite database
def get_db_connection():
    try:
        conn = sqlite3.connect('news.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

# Create the database schema if it doesn't exist
def create_table():
    try:
        conn = get_db_connection()
        if conn:
            # Create the tblNews table if not exists
            conn.execute('''CREATE TABLE IF NOT EXISTS tblNews (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            addDate TEXT NOT NULL,
                            news_title TEXT NOT NULL,
                            news_image TEXT,
                            news_summary TEXT,
                            news_url TEXT NOT NULL,
                            show TEXT DEFAULT 'yes')''')

            # Create the tblmgz table for the AI News Magazine
            conn.execute('''CREATE TABLE IF NOT EXISTS tblmgz (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            add_date TEXT NOT NULL,
                            news_title TEXT NOT NULL,
                            news_image TEXT,
                            news_summary TEXT,
                            news_url TEXT NOT NULL,
                            news_location TEXT NOT NULL)''')

            conn.commit()
        else:
            print("Failed to create database connection.")
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")
    finally:
        if conn:
            conn.close()

# Route for the homepage (index)
@app.route('/')
def index():
    # Load titles from config.json
    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            home_title = config.get('home_title', 'News Room')
            home_subtitle = config.get('home_subtitle', 'We bring the latest AI News, up to date')
    except FileNotFoundError:
        home_title = 'News Room'
        home_subtitle = 'We bring the latest AI News, up to date'

    return render_template('index.html', home_title=home_title, home_subtitle=home_subtitle)

# Route for the AI magazine page
@app.route('/ai-magazine')
def ai_magazine():
    conn = get_db_connection()
    top_news, second_news, sidebar_news, magazine_date = None, [], [], 'N/A'

    try:
        # Fetch the news categorized by location
        top_news = conn.execute("SELECT * FROM tblmgz WHERE news_location = 'Top News'").fetchone()
        second_news = conn.execute("SELECT * FROM tblmgz WHERE news_location = 'Second News'").fetchall()
        sidebar_news = conn.execute("SELECT * FROM tblmgz WHERE news_location = 'Sidebar List'").fetchall()

        # Fetch the date from the first news entry in tblmgz (if available)
        first_news = conn.execute("SELECT add_date FROM tblmgz ORDER BY add_date LIMIT 1").fetchone()
        if first_news:
            # Convert the date string to a datetime object
            date_obj = datetime.strptime(first_news['add_date'], "%Y-%m-%d")
            # Format the date to the desired format (e.g., 'Wed October 16, 2024')
            magazine_date = date_obj.strftime("%a %B %d, %Y")
        else:
            magazine_date = 'N/A'

        # Load titles from config.json
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            department_name = config.get('department_name', 'Computer Science Department')
            magazine_title = config.get('magazine_title', 'AI Magazine')
            news_subtitle = config.get('news_subtitle', 'AI Latest News')

    except sqlite3.Error as e:
        print(f"Error fetching AI Magazine news: {e}")
        top_news, second_news, sidebar_news, magazine_date = None, [], [], 'N/A'
        department_name, magazine_title, news_subtitle = 'N/A', 'N/A', 'N/A'

    except FileNotFoundError:
        print("Error: config.json not found.")
        department_name, magazine_title, news_subtitle = 'Computer Science Department', 'AI Magazine', 'AI Latest News'

    finally:
        if conn:
            conn.close()

    # Render the aimgz.html template with dynamic data
    return render_template('aimgz.html', 
                           top_news=top_news, 
                           second_news=second_news, 
                           sidebar_news=sidebar_news,
                           magazine_date=magazine_date,
                           department_name=department_name,
                           magazine_title=magazine_title,
                           news_subtitle=news_subtitle)

@app.route('/control', methods=['GET', 'POST'])
def control():
    # Load current values
    department_name = "Computer Science Department"
    magazine_title = "AI Magazine"
    news_subtitle = "AI Latest News"
    home_title = "News Room"
    home_subtitle = "We bring the latest AI News, up to date"

    if request.method == 'POST':
        # Get the updated titles from the form
        department_name = request.form.get('department_name')
        magazine_title = request.form.get('magazine_title')
        news_subtitle = request.form.get('news_subtitle')
        home_title = request.form.get('home_title')
        home_subtitle = request.form.get('home_subtitle')

        # Save titles to a file (or database)
        with open('config.json', 'w') as config_file:
            json.dump({
                'department_name': department_name,
                'magazine_title': magazine_title,
                'news_subtitle': news_subtitle,
                'home_title': home_title,
                'home_subtitle': home_subtitle
            }, config_file)

        # Check if files are part of the request
        if 'logo_image' in request.files:
            logo_image = request.files['logo_image']

            # Save the new logo image to the static/images folder
            if logo_image.filename != '':
                logo_path = os.path.join('static/images', 'new_logo.png')
                logo_image.save(logo_path)

        # Show success message after upload
        return render_template('control.html', message="Updated successfully!", 
                               department_name=department_name,
                               magazine_title=magazine_title,
                               news_subtitle=news_subtitle,
                               home_title=home_title,
                               home_subtitle=home_subtitle)

    # Load existing values
    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            department_name = config.get('department_name', department_name)
            magazine_title = config.get('magazine_title', magazine_title)
            news_subtitle = config.get('news_subtitle', news_subtitle)
            home_title = config.get('home_title', home_title)
            home_subtitle = config.get('home_subtitle', home_subtitle)
    except FileNotFoundError:
        pass

    return render_template('control.html', 
                           department_name=department_name, 
                           magazine_title=magazine_title, 
                           news_subtitle=news_subtitle,
                           home_title=home_title,
                           home_subtitle=home_subtitle)

# Create the necessary tables
if __name__ == '__main__':
    create_table()  # Ensure the table is created before running the app
    app.run(debug=True)
