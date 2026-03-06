"""
simulation.py — Sustainability Twin Simulation Engine for SustainIQ
Predicts the outcome of sustainability scenarios BEFORE they happen.

3 Scenarios:
  1. Reduce Machine Runtime    — cut energy by X%
  2. Switch to Renewable       — adopt X% green energy
  3. Improve Recycling Rate    — increase recycling to X%
"""

import pandas as pd

# ── Emission / conversion constants ───────────────────────────────────────
CO2_PER_KWH     = 0.233   # kg CO2 per kWh (UK grid average)
TREES_PER_TONNE = 21      # trees equivalent per tonne CO2 absorbed/year


def _detect_columns(df):
    cols = df.columns.tolist()
    return {
        'energy': next((c for c in cols if 'electricity' in c or 'energy' in c), None),
        'water':  next((c for c in cols if 'water' in c), None),
        'waste':  next((c for c in cols if 'waste' in c), None),
    }


def _trees(co2_kg):
    return max(1, round((co2_kg / 1000) * TREES_PER_TONNE))


def _boost(pct, multiplier=0.4, cap=25):
    return min(round(pct * multiplier), cap)


# ═══════════════════════════════════════════════════════════════════════════
#  SCENARIO 1 — Reduce Machine Runtime
# ═══════════════════════════════════════════════════════════════════════════

def simulate_reduce_runtime(df, cols, reduction_pct):
    energy_col = cols['energy']
    water_col  = cols['water']

    if not energy_col:
        return {'error': 'No energy column found in dataset'}

    factor          = reduction_pct / 100.0
    baseline_energy = float(df[energy_col].sum())
    baseline_water  = float(df[water_col].sum()) if water_col else 0

    new_energy   = round(baseline_energy * (1 - factor), 1)
    new_water    = round(baseline_water  * (1 - factor * 0.6), 1) if water_col else 0
    energy_saved = round(baseline_energy - new_energy, 1)
    water_saved  = round(baseline_water  - new_water,  1)
    co2_saved    = round(energy_saved * CO2_PER_KWH, 1)
    trees        = _trees(co2_saved)

    return {
        'scenario':    'Reduce Machine Runtime',
        'icon':        'zap',
        'input_label': f'{reduction_pct}% runtime reduction',
        'before': {'energy': round(baseline_energy, 1), 'water': round(baseline_water, 1), 'waste': 0},
        'after':  {'energy': new_energy, 'water': new_water, 'waste': 0},
        'savings': {
            'energy_kwh':   energy_saved,
            'water_liters': water_saved,
            'waste_kg':     0,
            'co2_kg':       co2_saved,
            'trees_equiv':  trees,
        },
        'score_boost': _boost(reduction_pct, 0.4, 20),
        'summary': (
            f"Reducing runtime by {reduction_pct}% saves {energy_saved:,.0f} kWh "
            f"and {co2_saved:,.0f} kg CO\u2082 — like planting {trees} trees."
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  SCENARIO 2 — Switch to Renewable Energy
# ═══════════════════════════════════════════════════════════════════════════

def simulate_renewable_switch(df, cols, renewable_pct):
    energy_col = cols['energy']
    if not energy_col:
        return {'error': 'No energy column found in dataset'}

    factor          = renewable_pct / 100.0
    baseline_energy = float(df[energy_col].sum())
    co2_baseline    = round(baseline_energy * CO2_PER_KWH, 1)
    co2_after       = round(baseline_energy * (1 - factor) * CO2_PER_KWH, 1)
    co2_saved       = round(co2_baseline - co2_after, 1)
    trees           = _trees(co2_saved)

    return {
        'scenario':    'Switch to Renewable Energy',
        'icon':        'sun',
        'input_label': f'{renewable_pct}% renewable adoption',
        'before': {'energy': round(baseline_energy, 1), 'water': 0, 'waste': 0, 'co2': co2_baseline},
        'after':  {'energy': round(baseline_energy, 1), 'water': 0, 'waste': 0, 'co2': co2_after},
        'savings': {
            'energy_kwh':   0,
            'water_liters': 0,
            'waste_kg':     0,
            'co2_kg':       co2_saved,
            'trees_equiv':  trees,
        },
        'score_boost': _boost(renewable_pct, 0.35, 25),
        'summary': (
            f"Switching {renewable_pct}% to renewables eliminates {co2_saved:,.0f} kg CO\u2082 "
            f"— equivalent to {trees} trees planted annually."
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  SCENARIO 3 — Improve Recycling Rate
# ═══════════════════════════════════════════════════════════════════════════

def simulate_recycling_improvement(df, cols, target_pct):
    waste_col = cols['waste']
    if not waste_col:
        return {'error': 'No waste column found in dataset'}

    current_pct    = 40.0
    baseline_waste = float(df[waste_col].sum())

    current_recycled = round(baseline_waste * (current_pct / 100), 1)
    current_landfill = round(baseline_waste - current_recycled, 1)
    new_recycled     = round(baseline_waste * (target_pct / 100), 1)
    new_landfill     = round(baseline_waste - new_recycled, 1)
    waste_diverted   = round(max(new_recycled - current_recycled, 0), 1)
    co2_saved        = round(waste_diverted * 2.5, 1)
    trees            = _trees(co2_saved)

    return {
        'scenario':    'Improve Recycling Rate',
        'icon':        'recycle',
        'input_label': f'Recycling target: {target_pct}%',
        'before': {
            'energy': 0, 'water': 0,
            'waste': round(baseline_waste, 1),
            'recycled': current_recycled,
            'landfill': current_landfill,
        },
        'after': {
            'energy': 0, 'water': 0,
            'waste': round(baseline_waste, 1),
            'recycled': new_recycled,
            'landfill': new_landfill,
        },
        'savings': {
            'energy_kwh':   0,
            'water_liters': 0,
            'waste_kg':     waste_diverted,
            'co2_kg':       co2_saved,
            'trees_equiv':  trees,
        },
        'score_boost': _boost(max(target_pct - current_pct, 0), 0.3, 20),
        'summary': (
            f"Raising recycling to {target_pct}% diverts {waste_diverted:,.0f} kg from landfill "
            f"and saves {co2_saved:,.0f} kg CO\u2082."
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  MASTER ENTRY — called from app.py /api/simulate
# ═══════════════════════════════════════════════════════════════════════════

def run_simulation(filepath, scenario, value):
    """
    Parameters:
        filepath : str   — path to uploaded CSV
        scenario : str   — 'runtime' | 'renewable' | 'recycling'
        value    : float — slider % (1–100)
    Returns:
        dict — JSON-serialisable simulation result
    """
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    cols  = _detect_columns(df)
    value = max(1.0, min(100.0, float(value)))

    if scenario == 'runtime':
        return simulate_reduce_runtime(df, cols, value)
    elif scenario == 'renewable':
        return simulate_renewable_switch(df, cols, value)
    elif scenario == 'recycling':
        return simulate_recycling_improvement(df, cols, value)
    else:
        return {'error': f'Unknown scenario: {scenario}'}
