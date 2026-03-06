"""
ai_analysis.py — Explainable AI Engine for SustainIQ
Handles:
  - Anomaly detection (Isolation Forest)
  - Root cause analysis
  - Sustainability recommendations
  - Future resource prediction (Linear Regression)
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression


# ═══════════════════════════════════════════════════════════════════════════
#  HELPER — Auto-detect columns
# ═══════════════════════════════════════════════════════════════════════════

def detect_columns(df):
    cols = df.columns.tolist()
    return {
        'energy': next((c for c in cols if 'electricity' in c or 'energy' in c), None),
        'water':  next((c for c in cols if 'water' in c), None),
        'waste':  next((c for c in cols if 'waste' in c), None),
        'dept':   next((c for c in cols if 'dept' in c or 'department' in c), None),
        'date':   next((c for c in cols if 'date' in c or 'time' in c), None),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  FEATURE 1 — Anomaly Detection (Isolation Forest)
# ═══════════════════════════════════════════════════════════════════════════

def detect_anomalies(df, cols):
    """
    Uses Isolation Forest to flag abnormal rows.
    Returns a list of anomaly dicts with date, column, value, severity.
    """
    numeric_cols = [c for c in [cols['energy'], cols['water'], cols['waste']] if c]

    if not numeric_cols:
        return []

    # Train Isolation Forest on numeric columns
    model = IsolationForest(contamination=0.1, random_state=42)
    features = df[numeric_cols].fillna(df[numeric_cols].mean())
    predictions = model.fit_predict(features)

    # -1 = anomaly, 1 = normal
    anomaly_indices = [i for i, p in enumerate(predictions) if p == -1]

    anomalies = []
    for idx in anomaly_indices:
        row = df.iloc[idx]

        # Find which column is most deviated
        worst_col  = None
        worst_pct  = 0

        for col in numeric_cols:
            col_mean = df[col].mean()
            col_val  = row[col]
            if col_mean > 0:
                pct = abs((col_val - col_mean) / col_mean) * 100
                if pct > worst_pct:
                    worst_pct = pct
                    worst_col = col

        if worst_col is None:
            continue

        # Determine severity
        if worst_pct >= 25:
            severity = 'critical'
        elif worst_pct >= 15:
            severity = 'warning'
        else:
            severity = 'info'

        # Human readable label
        label_map = {
            cols['energy']: 'Energy',
            cols['water']:  'Water',
            cols['waste']:  'Waste',
        }

        direction = 'above' if row[worst_col] > df[worst_col].mean() else 'below'

        date_str = str(row[cols['date']]) if cols['date'] else f"Row {idx + 1}"

        anomalies.append({
            'date':     date_str[:10],
            'resource': label_map.get(worst_col, worst_col),
            'value':    round(float(row[worst_col]), 1),
            'avg':      round(float(df[worst_col].mean()), 1),
            'deviation': round(worst_pct, 1),
            'direction': direction,
            'severity': severity,
            'message':  f"{label_map.get(worst_col, worst_col)} usage is {round(worst_pct, 1)}% {direction} average on {date_str[:10]}",
        })

    # Sort by deviation descending, return top 6
    anomalies.sort(key=lambda x: x['deviation'], reverse=True)
    return anomalies[:6]


# ═══════════════════════════════════════════════════════════════════════════
#  FEATURE 2 — Root Cause Analysis
# ═══════════════════════════════════════════════════════════════════════════

def root_cause_analysis(df, cols):
    """
    Analyses which department and which day-of-week
    contributes most to high resource consumption.
    Returns structured explanation data.
    """
    results = {}

    # Department contribution breakdown
    if cols['dept'] and cols['energy']:
        dept_energy = df.groupby(cols['dept'])[cols['energy']].sum()
        total = dept_energy.sum()
        dept_pct = (dept_energy / total * 100).round(1)
        top_dept = dept_pct.idxmax()

        results['dept_contributions'] = {
            'labels': dept_pct.index.tolist(),
            'values': dept_pct.values.tolist(),
            'top_dept': top_dept,
            'top_pct':  float(dept_pct.max()),
        }

    # Day-of-week analysis
    if cols['date'] and cols['energy']:
        df['_dow'] = pd.to_datetime(df[cols['date']], errors='coerce').dt.day_name()
        dow_energy  = df.groupby('_dow')[cols['energy']].mean().round(1)
        day_order   = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dow_energy  = dow_energy.reindex([d for d in day_order if d in dow_energy.index])

        results['dow_consumption'] = {
            'labels': dow_energy.index.tolist(),
            'values': dow_energy.values.tolist(),
            'peak_day': dow_energy.idxmax(),
            'peak_val': float(dow_energy.max()),
        }
        df.drop(columns=['_dow'], inplace=True, errors='ignore')

    # Simulated root cause factors for explanation panel
    results['factors'] = [
        {'label': 'Department Load',   'value': 42},
        {'label': 'Operational Hours', 'value': 28},
        {'label': 'Equipment Age',     'value': 18},
        {'label': 'External Temp',     'value': 12},
    ]

    return results


# ═══════════════════════════════════════════════════════════════════════════
#  FEATURE 3 — Recommendation Engine
# ═══════════════════════════════════════════════════════════════════════════

def generate_recommendations(df, cols, anomalies, score):
    """
    Rule-based recommendation engine.
    Generates actionable sustainability recommendations.
    """
    recs = []

    energy_col = cols['energy']
    water_col  = cols['water']
    waste_col  = cols['waste']
    dept_col   = cols['dept']

    # Energy recommendations
    if energy_col:
        energy_mean = df[energy_col].mean()
        energy_max  = df[energy_col].max()

        if energy_max > energy_mean * 1.3:
            recs.append({
                'category': 'Energy',
                'icon': '⚡',
                'priority': 'High',
                'title': 'Shift Peak Operations to Off-Peak Hours',
                'description': f'Peak energy usage ({round(energy_max, 0)} kWh) is significantly above average ({round(energy_mean, 0)} kWh). Shifting heavy operations to off-peak hours could reduce costs by 15–20%.',
                'impact': 'High',
                'saving': '15–20% energy cost reduction',
            })

        if dept_col:
            dept_energy = df.groupby(dept_col)[energy_col].mean()
            top = dept_energy.idxmax()
            recs.append({
                'category': 'Energy',
                'icon': '🏭',
                'priority': 'Medium',
                'title': f'Audit {top} Department Energy Use',
                'description': f'{top} has the highest average energy consumption. A detailed audit may reveal inefficient equipment or processes.',
                'impact': 'Medium',
                'saving': '8–12% department energy saving',
            })

    # Water recommendations
    if water_col:
        water_trend = _calc_trend(df, water_col)
        if water_trend > 5:
            recs.append({
                'category': 'Water',
                'icon': '💧',
                'priority': 'High',
                'title': 'Inspect for Water Leaks & Over-Use',
                'description': f'Water usage is trending up by {water_trend}%. Check pipelines, cooling systems, and sanitation processes for leaks or inefficiencies.',
                'impact': 'High',
                'saving': '10–15% water usage reduction',
            })

    # Waste recommendations
    if waste_col:
        waste_mean = df[waste_col].mean()
        recs.append({
            'category': 'Waste',
            'icon': '♻️',
            'priority': 'Medium',
            'title': 'Implement Waste Segregation Programme',
            'description': f'Average waste of {round(waste_mean, 1)} kg/period can be reduced through better segregation. Target 40% recycling rate.',
            'impact': 'Medium',
            'saving': 'Up to 40% landfill diversion',
        })

    # Score-based recommendation
    if score < 60:
        recs.append({
            'category': 'Strategy',
            'icon': '🎯',
            'priority': 'Critical',
            'title': 'Sustainability Score Requires Immediate Action',
            'description': 'Your sustainability score is below 60. An immediate operational review across all departments is recommended.',
            'impact': 'Critical',
            'saving': 'Up to 25% overall resource savings',
        })
    elif score < 80:
        recs.append({
            'category': 'Strategy',
            'icon': '📈',
            'priority': 'Low',
            'title': 'Set Monthly Reduction Targets',
            'description': 'Your score is moderate. Setting 5% monthly reduction targets per department can push your score above 80 within 3 months.',
            'impact': 'Medium',
            'saving': '5–10% monthly improvements',
        })

    return recs[:5]


def _calc_trend(df, col):
    mid   = len(df) // 2
    first = df[col].iloc[:mid].mean()
    second = df[col].iloc[mid:].mean()
    if first == 0:
        return 0
    return round(((second - first) / first) * 100, 1)


# ═══════════════════════════════════════════════════════════════════════════
#  FEATURE 4 — Future Prediction (Linear Regression)
# ═══════════════════════════════════════════════════════════════════════════

def predict_future(df, cols, periods=14):
    """
    Uses Linear Regression to predict next N periods of energy usage.
    Returns historical + predicted values for chart rendering.
    """
    energy_col = cols['energy']
    if not energy_col:
        return {}

    series = df[energy_col].dropna().values
    n = len(series)

    # X = time index, y = consumption values
    X = np.arange(n).reshape(-1, 1)
    y = series

    model = LinearRegression()
    model.fit(X, y)

    # Predict future periods
    future_X = np.arange(n, n + periods).reshape(-1, 1)
    future_y = model.predict(future_X)

    # Build date labels
    date_col = cols['date']
    if date_col:
        dates = pd.to_datetime(df[date_col], errors='coerce').dropna()
        if len(dates) >= 2:
            freq  = dates.diff().median()
            last  = dates.iloc[-1]
            future_dates = [
                (last + freq * (i + 1)).strftime('%b %d')
                for i in range(periods)
            ]
        else:
            future_dates = [f"T+{i+1}" for i in range(periods)]
        hist_labels = dates.dt.strftime('%b %d').tolist()
    else:
        hist_labels  = list(range(1, n + 1))
        future_dates = [f"T+{i+1}" for i in range(periods)]

    # Trend summary
    slope = model.coef_[0]
    trend_pct = round((slope * periods / series.mean()) * 100, 1)
    direction = 'increase' if slope > 0 else 'decrease'

    return {
        'hist_labels':   hist_labels[-30:],       # last 30 for readability
        'hist_values':   [round(float(v), 1) for v in series[-30:]],
        'future_labels': future_dates,
        'future_values': [round(float(v), 1) for v in future_y],
        'trend_pct':     abs(trend_pct),
        'direction':     direction,
        'summary':       f"Energy usage is projected to {direction} by {abs(trend_pct)}% over the next {periods} days based on current trend.",
    }


# ═══════════════════════════════════════════════════════════════════════════
#  MASTER FUNCTION — Run all AI analysis
# ═══════════════════════════════════════════════════════════════════════════

def run_ai_analysis(filepath, sustainability_score):
    """
    Entry point called from app.py.
    Reads CSV and runs all 4 AI modules.
    Returns combined JSON-ready dict.
    """
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

    cols = detect_columns(df)

    anomalies    = detect_anomalies(df.copy(), cols)
    root_cause   = root_cause_analysis(df.copy(), cols)
    predictions  = predict_future(df.copy(), cols)
    recs         = generate_recommendations(df.copy(), cols, anomalies, sustainability_score)

    return {
        'anomalies':       anomalies,
        'root_cause':      root_cause,
        'predictions':     predictions,
        'recommendations': recs,
        'anomaly_count':   len(anomalies),
    }
