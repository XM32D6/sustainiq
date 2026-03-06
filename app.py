"""
app.py — Flask Backend for Enterprise Sustainability Dashboard
Handles CSV upload, data processing, and serving analytics to frontend.
"""

import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
from werkzeug.utils import secure_filename
from ai_analysis import run_ai_analysis
from chatbot import ask_chatbot
from simulation import run_simulation

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
ALLOWED_EXTENSIONS = {'csv'}


def allowed_file(filename):
    """Check if the uploaded file is a CSV."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_dataset(filepath):
    """
    Core analytics engine.
    Reads CSV and computes all KPIs, trends, and insights.
    Returns a structured dict that will be sent to the frontend as JSON.
    """
    df = pd.read_csv(filepath)

    # ── Normalize column names (strip spaces, lowercase) ──────────────────
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

    # ── Detect which columns exist in the uploaded file ───────────────────
    energy_col  = next((c for c in df.columns if 'electricity' in c or 'energy' in c), None)
    water_col   = next((c for c in df.columns if 'water' in c), None)
    waste_col   = next((c for c in df.columns if 'waste' in c), None)
    dept_col    = next((c for c in df.columns if 'dept' in c or 'department' in c), None)
    date_col    = next((c for c in df.columns if 'date' in c or 'time' in c), None)

    results = {}

    # ── KPI Totals ─────────────────────────────────────────────────────────
    results['total_energy']  = round(float(df[energy_col].sum()), 2)  if energy_col  else 0
    results['total_water']   = round(float(df[water_col].sum()),  2)  if water_col   else 0
    results['total_waste']   = round(float(df[waste_col].sum()),  2)  if waste_col   else 0

    # ── Trend (compare first half vs second half of dataset) ──────────────
    def calc_trend(col):
        if col is None:
            return 0
        mid = len(df) // 2
        first_half  = df[col].iloc[:mid].mean()
        second_half = df[col].iloc[mid:].mean()
        if first_half == 0:
            return 0
        return round(((second_half - first_half) / first_half) * 100, 1)

    results['energy_trend'] = calc_trend(energy_col)
    results['water_trend']  = calc_trend(water_col)
    results['waste_trend']  = calc_trend(waste_col)

    # ── Time Series for Line Chart ─────────────────────────────────────────
    if date_col and energy_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        ts = df[[date_col, energy_col]].dropna()
        ts = ts.sort_values(date_col)
        results['energy_labels'] = ts[date_col].dt.strftime('%b %d').tolist()
        results['energy_values'] = ts[energy_col].round(2).tolist()
    else:
        results['energy_labels'] = list(range(1, len(df) + 1))
        results['energy_values'] = df[energy_col].round(2).tolist() if energy_col else []

    # ── Department Bar Chart ───────────────────────────────────────────────
    if dept_col and water_col:
        dept_water = df.groupby(dept_col)[water_col].sum().reset_index()
        results['dept_labels'] = dept_water[dept_col].tolist()
        results['dept_water']  = dept_water[water_col].round(2).tolist()
    elif water_col:
        # Fallback: show raw water data as simple indexed chart
        results['dept_labels'] = list(range(1, min(len(df), 10) + 1))
        results['dept_water']  = df[water_col].head(10).round(2).tolist()
    else:
        results['dept_labels'] = []
        results['dept_water']  = []

    # ── Waste Pie Chart ────────────────────────────────────────────────────
    if waste_col:
        total = df[waste_col].sum()
        recycled  = round(total * 0.40, 2)   # simulated breakdown
        landfill  = round(total * 0.35, 2)
        compost   = round(total * 0.25, 2)
        results['waste_breakdown'] = [recycled, landfill, compost]
    else:
        results['waste_breakdown'] = [0, 0, 0]

    # ── Sustainability Score (0–100) ───────────────────────────────────────
    score = 100

    # Penalise upward energy trend
    if results['energy_trend'] > 10:
        score -= 20
    elif results['energy_trend'] > 5:
        score -= 10

    # Penalise upward water trend
    if results['water_trend'] > 10:
        score -= 15
    elif results['water_trend'] > 5:
        score -= 8

    # Penalise upward waste trend
    if results['waste_trend'] > 10:
        score -= 15
    elif results['waste_trend'] > 5:
        score -= 8

    # Reward dataset completeness
    if energy_col and water_col and waste_col:
        score += 5

    results['sustainability_score'] = max(0, min(100, score))

    # ── Efficiency Score (derived from sustainability score) ───────────────
    results['efficiency_score'] = results['sustainability_score']

    # ── Automated Insights ─────────────────────────────────────────────────
    insights = []

    if results['energy_trend'] > 5:
        insights.append(f"⚠️ Energy usage increased by {results['energy_trend']}% — review high-consumption departments.")
    elif results['energy_trend'] < -5:
        insights.append(f"✅ Energy usage dropped by {abs(results['energy_trend'])}% — efficiency measures are working.")
    else:
        insights.append("📊 Energy consumption is stable across the reporting period.")

    if results['water_trend'] > 5:
        insights.append(f"⚠️ Water usage is trending up by {results['water_trend']}% — check for leaks or over-use.")
    else:
        insights.append("✅ Water usage is within acceptable range.")

    if waste_col:
        avg_waste = df[waste_col].mean()
        insights.append(f"♻️ Average waste generation: {avg_waste:.1f} kg/period — target below-average reduction.")

    if dept_col:
        insights.append(f"🏢 {df[dept_col].nunique()} departments tracked — use department view to isolate inefficiencies.")

    if results['sustainability_score'] >= 80:
        insights.append("🌱 Excellent sustainability posture — maintain current practices.")
    elif results['sustainability_score'] >= 60:
        insights.append("🟡 Moderate sustainability score — targeted improvements recommended.")
    else:
        insights.append("🔴 Low sustainability score — immediate operational review advised.")

    results['insights'] = insights

    # ── Summary row count ──────────────────────────────────────────────────
    results['row_count'] = len(df)
    results['columns']   = df.columns.tolist()

    return results


# ── Routes ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Serve the upload page."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Handle CSV upload.
    Saves to /uploads, triggers processing, stores result in session-like
    query param approach (file key passed to dashboard).
    """
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '' or not allowed_file(file.filename):
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    return redirect(url_for('dashboard', filename=filename))


@app.route('/dashboard')
def dashboard():
    """Serve the dashboard page."""
    filename = request.args.get('filename', '')
    return render_template('dashboard.html', filename=filename)


@app.route('/api/analytics')
def analytics():
    """
    REST endpoint — returns JSON analytics for the uploaded CSV.
    Called by dashboard.js on page load.
    """
    filename = request.args.get('filename', '')
    if not filename:
        return jsonify({'error': 'No filename provided'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    try:
        data = process_dataset(filepath)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai')
def ai_insights():
    """
    REST endpoint — returns full AI analysis for the uploaded CSV.
    Called by dashboard.js after main analytics load.
    """
    filename = request.args.get('filename', '')
    if not filename:
        return jsonify({'error': 'No filename provided'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    # Get sustainability score from analytics first
    try:
        from app import process_dataset
        base = process_dataset(filepath)
        score = base.get('sustainability_score', 70)
    except Exception:
        score = 70

    try:
        data = run_ai_analysis(filepath, score)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Chatbot endpoint.
    Receives user question + filename + chat history.
    Returns AI-generated response.
    """
    data     = request.get_json()
    question = data.get('question', '').strip()
    filename = data.get('filename', '')
    history  = data.get('history', [])

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    if not filename:
        return jsonify({'error': 'No filename provided'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    if not os.path.exists(filepath):
        return jsonify({'error': 'Dataset not found'}), 404

    try:
        # Load both base analytics and AI analysis as context
        base_data = process_dataset(filepath)
        ai_data   = run_ai_analysis(filepath, base_data.get('sustainability_score', 70))
        answer    = ask_chatbot(question, ai_data, base_data, history)
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/simulate', methods=['POST'])
def simulate():
    """
    Simulation Twin endpoint.
    Receives scenario + value, runs simulation engine, returns predicted outcomes.

    Body JSON:
        { "filename": "...", "scenario": "runtime|renewable|recycling", "value": 20 }
    """
    data     = request.get_json()
    filename = data.get('filename', '')
    scenario = data.get('scenario', '')
    value    = data.get('value', 20)

    if not filename:
        return jsonify({'error': 'No filename provided'}), 400
    if not scenario:
        return jsonify({'error': 'No scenario provided'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    try:
        result = run_simulation(filepath, scenario, value)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Entry Point ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True, port=5000)
