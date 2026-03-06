"""
chatbot.py — Groq LLM Chatbot for SustainIQ
Reads AI analysis results and answers user questions
using LLaMA 3 via Groq's fast inference API.
"""

from groq import Groq

# ── Replace with your real Groq API key ───────────────────────────────────
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)


def build_context(ai_data, base_data):
    """
    Converts AI analysis results into a structured
    text context block that the LLM can read and reason about.
    """
    lines = ["=== SUSTAINABILITY DASHBOARD DATA ===\n"]

    # ── KPI Summary ───────────────────────────────────────────────────────
    if base_data:
        lines.append("--- Resource Summary ---")
        lines.append(f"Total Energy Consumption : {base_data.get('total_energy', 'N/A')} kWh")
        lines.append(f"Total Water Usage        : {base_data.get('total_water', 'N/A')} liters")
        lines.append(f"Total Waste Generated    : {base_data.get('total_waste', 'N/A')} kg")
        lines.append(f"Sustainability Score     : {base_data.get('sustainability_score', 'N/A')} / 100")
        lines.append(f"Energy Trend             : {base_data.get('energy_trend', 0)}% vs previous period")
        lines.append(f"Water Trend              : {base_data.get('water_trend', 0)}% vs previous period")
        lines.append(f"Waste Trend              : {base_data.get('waste_trend', 0)}% vs previous period")
        lines.append("")

    # ── Anomalies ─────────────────────────────────────────────────────────
    if ai_data and ai_data.get('anomalies'):
        lines.append("--- Detected Anomalies ---")
        for a in ai_data['anomalies']:
            lines.append(
                f"• {a['date']} | {a['resource']} | {a['severity'].upper()} | "
                f"{a['deviation']}% {a['direction']} average (value: {a['value']}, avg: {a['avg']})"
            )
        lines.append("")

    # ── Root Cause ────────────────────────────────────────────────────────
    if ai_data and ai_data.get('root_cause'):
        rc = ai_data['root_cause']
        if rc.get('dept_contributions'):
            dc = rc['dept_contributions']
            lines.append("--- Department Energy Contributions ---")
            for label, val in zip(dc['labels'], dc['values']):
                lines.append(f"• {label}: {val}%")
            lines.append(f"Top contributor: {dc['top_dept']} at {dc['top_pct']}%")
            lines.append("")

        if rc.get('dow_consumption'):
            dow = rc['dow_consumption']
            lines.append(f"--- Day-of-Week Peak ---")
            lines.append(f"Highest consumption day: {dow['peak_day']} ({dow['peak_val']} kWh avg)")
            lines.append("")

    # ── Recommendations ───────────────────────────────────────────────────
    if ai_data and ai_data.get('recommendations'):
        lines.append("--- AI Recommendations ---")
        for r in ai_data['recommendations']:
            lines.append(f"• [{r['priority']}] {r['title']}: {r['description']}")
        lines.append("")

    # ── Predictions ───────────────────────────────────────────────────────
    if ai_data and ai_data.get('predictions'):
        pred = ai_data['predictions']
        lines.append("--- Energy Prediction ---")
        lines.append(pred.get('summary', 'No prediction available'))
        lines.append("")

    return "\n".join(lines)


def ask_chatbot(question, ai_data, base_data, chat_history=None):
    """
    Main chatbot function.
    Sends user question + full context to Groq LLM.
    Returns AI-generated response string.

    Parameters:
        question     — user's natural language question
        ai_data      — output from run_ai_analysis()
        base_data    — output from process_dataset()
        chat_history — list of previous messages for multi-turn conversation
    """

    # Build context from current dashboard data
    context = build_context(ai_data, base_data)

    # System prompt — tells the LLM its role and behaviour
    system_prompt = f"""You are SustainIQ, an expert AI sustainability assistant embedded in an enterprise resource analytics dashboard.

You have access to real-time sustainability data from the organization's uploaded dataset.

Your job is to:
- Answer questions about energy, water, and waste consumption
- Explain detected anomalies and their possible causes
- Provide actionable sustainability recommendations
- Interpret predictions and trends
- Be concise, professional, and data-driven

Always refer to the actual data provided. If data is unavailable for a question, say so clearly.
Format responses clearly using bullet points where helpful.
Keep responses under 200 words unless the user asks for detail.

Here is the current dashboard data:

{context}
"""

    # Build messages array for multi-turn conversation
    messages = [{"role": "system", "content": system_prompt}]

    # Add previous conversation history if available
    if chat_history:
        for msg in chat_history[-6:]:  # keep last 6 messages for context window
            messages.append(msg)

    # Add current user question
    messages.append({"role": "user", "content": question})

    # ── Call Groq API ─────────────────────────────────────────────────────
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=400,
        temperature=0.7,
    )

    return response.choices[0].message.content
