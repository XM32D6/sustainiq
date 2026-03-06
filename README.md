# 🌱 SustainIQ — Enterprise Sustainability Dashboard

A web-based sustainability data intelligence platform. Upload any CSV containing
energy, water, and waste usage data and instantly generate a professional analytics dashboard.

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the server
```bash
python app.py
```

### 3. Open browser
```
http://localhost:5000
```

### 4. Upload CSV
Use the sample file in `data/sample_sustainability_data.csv` or your own.

---

## 📂 Project Structure

```
sustainability-dashboard/
├── app.py                        ← Flask backend (upload + analytics API)
├── requirements.txt              ← Python dependencies
├── data/
│   └── sample_sustainability_data.csv
├── uploads/                      ← Uploaded CSVs saved here (auto-created)
├── templates/
│   ├── index.html                ← Upload page
│   └── dashboard.html            ← Analytics dashboard page
└── static/
    └── js/
        └── dashboard.js          ← Chart rendering + API calls
```

---

## 📊 Expected CSV Columns

| Column | Description |
|---|---|
| `date` | Date of measurement |
| `electricity_usage_kwh` | Energy consumed (kWh) |
| `water_usage_liters` | Water consumed (L) |
| `waste_generated_kg` | Waste produced (kg) |
| `department` | Department name |

All columns are optional — the system auto-detects what's available.

---

## 🛠 Tech Stack

- **Backend**: Python 3.10+, Flask 3.x, Pandas
- **Frontend**: HTML5, CSS3, Vanilla JS
- **Charts**: Chart.js 4.x
- **Fonts**: Syne + DM Sans (Google Fonts)

---

## 📄 License
MIT — open source, free for any organization to deploy.
