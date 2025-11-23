import os, json, time
import streamlit as st
import pandas as pd
import requests
from fpdf import FPDF

# ---- CONFIG
NGROK_URL = os.environ.get("PLANNER_URL", "https://8eeb555ef2c9.ngrok-free.app")  
API_KEY   = os.environ.get("PLANNER_API_KEY", "secret123")

st.set_page_config(page_title="AI Travel Planner", page_icon="🌍", layout="wide")
st.title("🌍 AI Travel Planner")

# ---- Inputs
col1, col2 = st.columns(2)
destination = col1.text_input("Destination (city)", "Cairo")
days        = col2.number_input("Days", 1, 14, 3)
budget      = col1.number_input("Total Budget (USD)", 50, 10000, 400, 50)
prefs       = col2.text_input("Preferences", "history, food, markets")

st.markdown("**Filters**")
fc1, fc2, fc3 = st.columns(3)
avoid_walks = fc1.toggle("Avoid long walks", value=False)
family      = fc2.toggle("Family friendly", value=False)
vegetarian  = fc3.toggle("Vegetarian", value=False)

def call_api(city, days, budget, prefs, filters=None):
    payload = {
        "city": city,
        "days": int(days),
        "budget": float(budget),
        "preferences": prefs,
        
    }
    if filters:
        payload["filters"] = filters

    headers = {"Authorization": f"Bearer {API_KEY}", "Cache-Control": "no-cache"}
    try:
        r = requests.post(f"{NGROK_URL}/plan", json=payload, headers=headers, timeout=60)
    except Exception as e:
        st.error(f"Cannot reach backend: {e}")
        return None

    if not r.ok:
        # show the exact backend error so you can diagnose quickly
        st.error(f"Backend error {r.status_code}: {r.text}")
        return None

    try:
        return r.json()
    except Exception as e:
        st.error(f"Invalid JSON from backend: {e}\n\n{r.text[:1000]}")
        return None

if "itinerary" not in st.session_state:
    st.session_state.itinerary = None

colA, colB = st.columns([1,1])
if colA.button("Generate Itinerary", use_container_width=True):
    with st.spinner("Planning…"):
        filters = {
            "avoid_long_walks": avoid_walks,
            "family_friendly": family,
            "vegetarian": vegetarian
        }
        st.session_state.itinerary = call_api(destination, days, budget, prefs, filters=filters)

data = st.session_state.itinerary

if data and isinstance(data, dict) and data.get("days"):
    # ---- Build table
    rows, total_cost = [], 0.0
    for d in data["days"]:
        m = float(d["morning"]["est_cost_usd"])
        a = float(d["afternoon"]["est_cost_usd"])
        e = float(d["evening"]["est_cost_usd"])
        day_total = round(m + a + e, 2)
        total_cost += day_total
        rows.append({
            "Day": d["day_number"],
            "Morning":   f"{d['morning']['place']} — {d['morning']['reason']} (${m:.2f})",
            "Afternoon": f"{d['afternoon']['place']} — {d['afternoon']['reason']} (${a:.2f})",
            "Evening":   f"{d['evening']['place']} — {d['evening']['reason']} (${e:.2f})",
            "Daily Total (USD)": day_total,
        })
    df = pd.DataFrame(rows).sort_values("Day")

    # Budget sanity check
    if total_cost > float(budget):
        st.warning(f"⚠️ Estimated plan cost (${total_cost:.2f}) exceeds your budget (${float(budget):.2f}).")

    st.dataframe(df, use_container_width=True)

    # ---- Save trip JSON
    trips_dir = "trips"; os.makedirs(trips_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{trips_dir}/{destination}_{int(days)}d_{ts}.json"
    if st.button("💾 Save trip (JSON)"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        st.success(f"Saved: {filename}")

    # ---- Download CSV
    st.download_button("⬇️ Download CSV",
                       df.to_csv(index=False).encode("utf-8"),
                       "itinerary.csv", "text/csv")

    # ---- Export PDF
    def to_pdf(df: pd.DataFrame, city: str):
        pdf = FPDF(orientation="L", unit="mm", format="A4")
        pdf.set_margins(12, 12, 12)
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()

        # Title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"Itinerary: {city}", ln=1)
        pdf.ln(2)

        # Column widths
        avail_w = pdf.w - pdf.l_margin - pdf.r_margin
        w_day, w_total = 18, 28
        w_text = (avail_w - w_day - w_total) / 3.0
        col_w = [w_day, w_text, w_text, w_text, w_total]

        # Header
        pdf.set_font("Arial", "B", 11)
        pdf.set_fill_color(240, 240, 240)
        for i, h in enumerate(df.columns):
            pdf.cell(col_w[i], 8, str(h), border=1, align="C", fill=True)
        pdf.ln(8)

        # Body
        pdf.set_font("Arial", "", 11)
        line_h = 7
        for _, row in df.iterrows():
            x0, y0 = pdf.get_x(), pdf.get_y()
            max_h = line_h
            texts = [str(row["Morning"]), str(row["Afternoon"]), str(row["Evening"])]
            for j, txt in enumerate(texts):
                x = x0 + col_w[0] + sum(col_w[1:1 + j])
                pdf.set_xy(x, y0)
                y_before = pdf.get_y()
                pdf.multi_cell(col_w[1 + j], line_h, txt, border=1)
                y_after = pdf.get_y()
                max_h = max(max_h, y_after - y_before)

            pdf.set_xy(x0, y0)
            pdf.multi_cell(col_w[0], line_h, str(row["Day"]), border=1, align="C")

            pdf.set_xy(x0 + sum(col_w[:-1]), y0)
            pdf.multi_cell(col_w[-1], line_h, f"{row['Daily Total (USD)']:.2f}", border=1, align="C")

            pdf.set_xy(x0, y0 + max_h)

        out = f"itinerary_{city.replace(' ', '_')}.pdf"
        pdf.output(out)
        return out

    if st.button("🖨️ Export PDF"):
        path = to_pdf(df, destination)
        with open(path, "rb") as f:
            st.download_button("Download PDF", f,
                               file_name=os.path.basename(path),
                               mime="application/pdf")
else:
    # If a call failed you’ll see the error above; this keeps the page tidy otherwise.
    pass
