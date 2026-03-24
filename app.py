"""
Flask Web Application
PM2.5 Estimation System - Main Application

Author: PM2.5 Estimation System
"""

from flask import Flask, render_template, request, jsonify, url_for, send_file, redirect, session
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import traceback
import json
import numpy as np
from functools import wraps
import uuid
import sqlite3
import re

# Import our custom modules
from image_analysis import ImageAnalyzer
from pm25_estimator import PM25Estimator
from visualization import PM25Visualizer
from pdf_generator import generate_report_pdf


# Custom JSON Encoder to handle numpy types
class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that can handle numpy data types."""
    def default(self, obj):
        if isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


# Initialize Flask app
app = Flask(__name__)
app.json_encoder = NumpyEncoder
app.config['SECRET_KEY'] = 'pm25-estimation-secret-key-2026'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['RESULTS_FOLDER'] = 'static/results'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tif', 'tiff', 'bmp'}

# Simple credential gate for demo/admin access
ADMIN_EMAIL = 'admin@gmail.com'
ADMIN_PASSWORD = '160904'

# Ensure required directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)

REPORT_HISTORY_FILE = 'data/report_history.json'
USERS_DB_FILE = 'data/users.db'


def get_db_connection():
    """Create a sqlite connection with dict-like row access."""
    conn = sqlite3.connect(USERS_DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_user_db():
    """Initialize users table used for authentication."""
    conn = get_db_connection()
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        '''
    )
    conn.commit()
    conn.close()


def is_valid_email(email):
    """Basic email format check for server-side validation."""
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return bool(re.match(pattern, email))


def get_user_by_email(email):
    """Fetch a user by email."""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return user


def create_user(username, email, password):
    """Create a new user with a securely hashed password."""
    password_hash = generate_password_hash(password)
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)',
            (username, email, password_hash, datetime.now().isoformat())
        )
        conn.commit()
    finally:
        conn.close()


def allowed_file(filename):
    """Check if uploaded file has allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def is_logged_in():
    """Check whether the current session is authenticated."""
    return bool(session.get('authenticated'))


def login_required(require_json=False):
    """Protect routes that require authentication."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if is_logged_in():
                return func(*args, **kwargs)

            if require_json:
                return jsonify({'error': 'Authentication required'}), 401

            return redirect(url_for('login'))
        return wrapper
    return decorator


def get_risk_measures(aqi_category):
    """Return safety suggestions based on AQI category."""
    measures = {
        'Good': [
            'Continue normal outdoor activity.',
            'Maintain routine air-quality monitoring.',
            'Use green transport options to keep emissions low.'
        ],
        'Moderate': [
            'Sensitive groups should reduce prolonged outdoor exertion.',
            'Keep indoor ventilation balanced during peak traffic hours.',
            'Use masks when traveling through high-traffic corridors.'
        ],
        'Unhealthy for Sensitive Groups': [
            'Children, elderly, and respiratory patients should limit outdoor time.',
            'Use N95 masks when outdoors for longer duration.',
            'Prefer indoor exercise and close windows near busy roads.'
        ],
        'Unhealthy': [
            'Reduce all non-essential outdoor activities.',
            'Use air purifiers indoors where possible.',
            'Follow mask use and hydration precautions strictly.'
        ],
        'Very Unhealthy': [
            'Avoid outdoor exposure except for urgent needs.',
            'Run air purifiers continuously in occupied rooms.',
            'Schools/offices should limit outdoor sessions.'
        ],
        'Hazardous': [
            'Stay indoors and avoid travel unless critical.',
            'Use high-filtration masks for any outdoor movement.',
            'Issue public health alerts and emergency mitigation steps.'
        ]
    }
    return measures.get(aqi_category, [
        'Follow local advisory and minimize outdoor exposure when uncertain.'
    ])


def load_report_history():
    """Load stored report rows from disk."""
    if not os.path.exists(REPORT_HISTORY_FILE):
        return []

    try:
        with open(REPORT_HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def save_report_history(rows):
    """Persist report rows to disk."""
    with open(REPORT_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2)


def append_report_row(row):
    """Append a report row and keep only recent records."""
    rows = load_report_history()
    rows.append(row)
    # Keep recent 200 reports to prevent unbounded growth.
    rows = rows[-200:]
    save_report_history(rows)


def get_report_row(report_id):
    """Find a report row by report id."""
    rows = load_report_history()
    for row in reversed(rows):
        if row.get('report_id') == report_id:
            return row
    return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Render login page and authenticate users."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            return render_template('login.html', error='Email and password are required.')

        if not is_valid_email(email):
            return render_template('login.html', error='Please enter a valid email address.')

        user = get_user_by_email(email)
        if user and check_password_hash(user['password_hash'], password):
            session['authenticated'] = True
            session['user_email'] = user['email']
            session['username'] = user['username']
            return redirect(url_for('home'))

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['authenticated'] = True
            session['user_email'] = ADMIN_EMAIL
            session['username'] = 'Admin'
            return redirect(url_for('home'))

        return render_template('login.html', error='Invalid email or password.')

    if is_logged_in():
        return redirect(url_for('home'))

    success_message = request.args.get('success')
    return render_template('login.html', success=success_message)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Render signup page and register a new user."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not username or not email or not password:
            return render_template('signup.html', error='All fields are required.', form_data={'username': username, 'email': email})

        if not is_valid_email(email):
            return render_template('signup.html', error='Please enter a valid email address.', form_data={'username': username, 'email': email})

        if get_user_by_email(email):
            return render_template('signup.html', error='An account with this email already exists.', form_data={'username': username, 'email': email})

        try:
            create_user(username, email, password)
        except sqlite3.IntegrityError:
            return render_template('signup.html', error='An account with this email already exists.', form_data={'username': username, 'email': email})

        return redirect(url_for('login', success='Account created successfully. Please login.'))

    if is_logged_in():
        return redirect(url_for('home'))

    return render_template('signup.html', form_data={'username': '', 'email': ''})


@app.route('/api/signup', methods=['POST'])
def signup_api():
    """JSON API for client-side signup requests."""
    data = request.get_json(silent=True) or {}
    username = str(data.get('username', '')).strip()
    email = str(data.get('email', '')).strip().lower()
    password = str(data.get('password', ''))

    if not username or not email or not password:
        return jsonify({'success': False, 'error': 'All fields are required.'}), 400

    if not is_valid_email(email):
        return jsonify({'success': False, 'error': 'Please provide a valid email address.'}), 400

    if get_user_by_email(email):
        return jsonify({'success': False, 'error': 'Email is already registered.'}), 409

    try:
        create_user(username, email, password)
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Email is already registered.'}), 409

    return jsonify({'success': True, 'message': 'Signup successful. Please login.'}), 201


@app.route('/logout')
def logout():
    """Clear user session and return to login screen."""
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@login_required()
def home():
    """Render dashboard home page."""
    return render_template('dashboard.html', page='home', user_email=session.get('user_email', ADMIN_EMAIL))


@app.route('/analysis')
@login_required()
def analysis():
    """Render analysis workspace page."""
    return render_template(
        'dashboard.html',
        page='analysis',
        user_email=session.get('user_email', ADMIN_EMAIL),
        analysis_data=session.get('last_analysis')
    )


@app.route('/account')
@login_required()
def account():
    """Render account page."""
    return render_template('dashboard.html', page='account', user_email=session.get('user_email', ADMIN_EMAIL))


@app.route('/report')
@login_required()
def report():
    """Render report page."""
    last_analysis = session.get('last_analysis')
    risk_measures = []
    if last_analysis and last_analysis.get('aqi_category'):
        risk_measures = get_risk_measures(last_analysis['aqi_category'])

    report_rows = sorted(
        load_report_history(),
        key=lambda r: r.get('created_at', ''),
        reverse=True
    )

    return render_template(
        'dashboard.html',
        page='report',
        user_email=session.get('user_email', ADMIN_EMAIL),
        analysis_data=last_analysis,
        risk_measures=risk_measures,
        report_rows=report_rows
    )


@app.route('/analyze', methods=['POST'])
@login_required(require_json=True)
def analyze():
    """
    Handle image upload and perform PM2.5 analysis.
    """
    try:
        # Check if file was uploaded
        if 'satellite_image' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['satellite_image']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload an image file.'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        print(f"✓ Image saved: {filepath}")
        
        # Step 1: Analyze image to extract atmospheric features
        print("Analyzing atmospheric features...")
        analyzer = ImageAnalyzer(filepath)
        features = analyzer.analyze()
        print(f"✓ Features extracted: {features}")
        
        # Step 2: Estimate PM2.5 from features
        print("Estimating PM2.5 concentration...")
        estimator = PM25Estimator()
        estimation_results = estimator.estimate_with_confidence(features)
        pm25_value = estimation_results['pm25']
        print(f"✓ PM2.5 estimated: {pm25_value} µg/m³")
        
        # Step 3: Create visualizations
        print("Generating visualizations...")
        
        # Ensure results folder exists
        os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
        print(f"✓ Results folder verified: {app.config['RESULTS_FOLDER']}")
        
        visualizer = PM25Visualizer(app.config['RESULTS_FOLDER'])
        
        # Generate all visualizations
        vis_timestamp = timestamp
        
        # Create heatmap
        heatmap_filename = f'heatmap_{vis_timestamp}.png'
        heatmap_path = visualizer.create_heatmap(filepath, pm25_value, heatmap_filename)
        if os.path.exists(heatmap_path):
            print(f"✓ Heatmap created and verified: {heatmap_path}")
        else:
            print(f"✗ WARNING: Heatmap file not found at {heatmap_path}")
        
        # Create before/after
        before_after_filename = f'before_after_{vis_timestamp}.png'
        before_after_path = visualizer.create_before_after(filepath, before_after_filename)
        if os.path.exists(before_after_path):
            print(f"✓ Before/After created and verified: {before_after_path}")
        else:
            print(f"✗ WARNING: Before/After file not found at {before_after_path}")
        
        # Create dehazed
        dehazed_filename = f'dehazed_{vis_timestamp}.png'
        dehazed_path = visualizer.create_dehazed(filepath, dehazed_filename)
        if os.path.exists(dehazed_path):
            print(f"✓ Dehazed image created and verified: {dehazed_path}")
        else:
            print(f"✗ WARNING: Dehazed file not found at {dehazed_path}")
        
        # Create timeseries
        timeseries_filename = f'timeseries_{vis_timestamp}.png'
        timeseries_path = visualizer.create_timeseries_graph(pm25_value, output_name=timeseries_filename)
        if os.path.exists(timeseries_path):
            print(f"✓ Time series created and verified: {timeseries_path}")
        else:
            print(f"✗ WARNING: Timeseries file not found at {timeseries_path}")
        
        # Create features chart
        features_filename = f'features_{vis_timestamp}.png'
        features_chart_path = visualizer.create_feature_chart(features, output_name=features_filename)
        if os.path.exists(features_chart_path):
            print(f"✓ Feature chart created and verified: {features_chart_path}")
        else:
            print(f"✗ WARNING: Feature chart file not found at {features_chart_path}")
        
        # Prepare response with all results
        response_data = {
            'success': True,
            'pm25': float(pm25_value),
            'confidence': float(estimation_results['confidence']),
            'aqi_category': estimation_results['aqi_category'],
            'aqi_color': estimation_results['aqi_color'],
            'health_advice': estimation_results['health_advice'],
            'features': {
                'haze_score': float(round(features['haze_score'], 2)),
                'turbidity': float(round(features['turbidity'], 2)),
                'visibility': float(round(features['visibility'], 2)),
                'contrast': float(round(features['contrast'], 2)),
                'brightness': float(round(features['brightness'], 2)),
                'saturation': float(round(features['saturation'], 2))
            },
            'images': {
                'original': url_for('static', filename=f'uploads/{unique_filename}'),
                'heatmap': url_for('static', filename=f'results/{heatmap_filename}'),
                'dehazed': url_for('static', filename=f'results/{dehazed_filename}'),
                'before_after': url_for('static', filename=f'results/{before_after_filename}'),
                'timeseries': url_for('static', filename=f'results/{timeseries_filename}'),
                'features_chart': url_for('static', filename=f'results/{features_filename}')
            },
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Keep latest analysis in session for report page and PDF download.
        session['last_analysis'] = response_data

        # Save report row for report table history.
        report_id = f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        report_row = {
            'report_id': report_id,
            'report_name': f"PM25_Report_{vis_timestamp}",
            'image_name': filename,
            'date': response_data['timestamp'],
            'pm25': float(round(pm25_value, 2)),
            'status': 'Completed',
            'created_at': datetime.now().isoformat(),
            'analysis_data': response_data
        }
        append_report_row(report_row)
        response_data['report_id'] = report_id
        
        print("✓ Analysis complete!")
        return jsonify(response_data)
    
    except Exception as e:
        print(f"✗ Error during analysis: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'error': f'Analysis failed: {str(e)}',
            'details': traceback.format_exc()
        }), 500


@app.route('/about')
@login_required(require_json=True)
def about():
    """Return information about the system."""
    info = {
        'title': 'PM2.5 Estimation System',
        'version': '1.0.0',
        'description': 'High-Resolution PM2.5 Estimation from Satellite Images Using Image Processing',
        'author': 'Final Year Engineering Project',
        'features': [
            'Image-based PM2.5 estimation (no ML training required)',
            'Real-time atmospheric feature extraction',
            'Multiple visualization outputs',
            'AQI category classification',
            'Historical trend analysis'
        ],
        'technology': {
            'backend': 'Flask + Python',
            'image_processing': 'OpenCV + NumPy',
            'visualization': 'Matplotlib + Seaborn',
            'frontend': 'HTML + CSS + JavaScript'
        }
    }
    return jsonify(info)


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/download_report', methods=['POST'])
@login_required(require_json=True)
def download_report():
    """
    Generate and download a PDF report of analysis results.
    
    Expects JSON body with analysis_data containing:
    - pm25: PM2.5 value
    - features: atmospheric features dict
    - images: dict with image URLs
    - timestamp: analysis timestamp
    - aqi_category: AQI category
    - confidence: confidence level
    - health_advice: health advice text
    """
    try:
        # Accept explicit payload, fallback to latest session report.
        data = request.get_json(silent=True)
        if not data:
            data = session.get('last_analysis')

        if not data:
            return jsonify({'error': 'No report data available. Run analysis first.'}), 400
        
        # Generate PDF report
        print("Generating PDF report...")
        pdf_buffer = generate_report_pdf(data)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"PM25_Analysis_Report_{timestamp}.pdf"
        
        print(f"✓ PDF generated: {filename}")
        
        # Return PDF as file download
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        print(f"✗ Error generating PDF: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'error': f'PDF generation failed: {str(e)}',
            'details': traceback.format_exc()
        }), 500


@app.route('/download_report/<report_id>')
@login_required()
def download_report_by_id(report_id):
    """Generate and download PDF for a specific report row."""
    row = get_report_row(report_id)
    if not row:
        return jsonify({'error': 'Report not found'}), 404

    try:
        pdf_buffer = generate_report_pdf(row['analysis_data'])
        filename = f"{row.get('report_name', report_id)}.pdf"
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"✗ Error generating report by id: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500


init_user_db()


if __name__ == '__main__':
    print("=" * 60)
    print("PM2.5 ESTIMATION SYSTEM")
    print("High-Resolution PM2.5 Estimation from Satellite Images")
    print("=" * 60)
    print("\nStarting Flask application...")
    print("Server will be available at: http://127.0.0.1:5000")
    print("Press CTRL+C to stop the server\n")
    print("=" * 60)
    
    # Run Flask app
    app.run(debug=True, host='127.0.0.1', port=5000)
