import streamlit as st
import pandas as pd
import matplotlib
# Force headless backend to prevent server-side display errors
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.font_manager as fm
from datetime import datetime
from dateutil.relativedelta import relativedelta
import io

# --- 1. UI & Style Configuration ---
st.set_page_config(layout="wide", page_title="Gantt Chart")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #000000; }
    .title-container { display: flex; align-items: center; justify-content: center; width: 100%; margin: 20px 0; }
    .title-line { flex-grow: 1; height: 3px; background-color: #000; }
    .creative-title {
        padding: 0 30px; font-size: 3.5rem; font-weight: 900; 
        background: linear-gradient(90deg, #073b4c, #118ab2, #06d6a0);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-transform: uppercase; white-space: nowrap;
    }
    .stDateInput label { font-size: 20px !important; font-weight: 700 !important; }
    .timeline-container { display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .timeline-label { font-size: 20px; font-weight: 700; }
    .timeline-value { font-size: 40px; font-weight: 900; line-height: 1.2; }
    .stSelectbox div[data-baseweb="select"] { font-size: 18px !important; font-weight: 500 !important; }
    [data-testid="stDataEditor"] div, [data-testid="stDataEditor"] input { font-size: 20px !important; font-weight: 600 !important; }
    .section-header { font-size: 28px; font-weight: 800; margin-top: 30px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Title & Timeline Logic ---
st.markdown("<div class='title-container'><div class='title-line'></div><div class='creative-title'>Gantt Chart Creator</div><div class='title-line'></div></div>", unsafe_allow_html=True)

st.markdown("<div class='section-header'>Planning Duration</div>", unsafe_allow_html=True)
with st.container(border=True):
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1: start_date = st.date_input("Project Start Date", datetime(2023, 9, 15))
    with c2: end_date = st.date_input("Project End Date", datetime(2027, 9, 15))
    delta = relativedelta(end_date, start_date)
    total_months = max((delta.years * 12) + delta.months, 1)
    with c3: st.markdown(f"<div class='timeline-container'><div class='timeline-label'>Timeline (months)</div><div class='timeline-value'>{total_months}</div></div>", unsafe_allow_html=True)

# Font Selection
st.markdown("<div class='section-header'>Select Font Family</div>", unsafe_allow_html=True)
@st.cache_data
def get_system_fonts():
    # Caching prevents reloading the entire font library on every table edit
    return sorted(list(set([f.name for f in fm.fontManager.ttflist])))

fonts = get_system_fonts()
selected_font = st.selectbox("Font selector:", fonts, index=0, label_visibility="collapsed")
plt.rcParams['font.family'] = selected_font

# --- 3. Inputs to Gantt Chart Generator ---
st.markdown("<div class='section-header'>Inputs to Gantt Chart Generator</div>", unsafe_allow_html=True)
COLOR_PALETTE = {"Rose": "#ef476f", "Mustard": "#ffd166", "Emerald": "#06d6a0", "Blue": "#118ab2", "Midnight": "#073b4c", "Orange": "#ffa500", "Yellow": "#ffff00", "Grey Header": "#d3d3d3"}

if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame([
        {"Row Type": "Header", "Activity description": "Research Plan Overview", "Person incharge": "", "Label": "", "Start month": 1, "End month": total_months, "Color": "Grey Header", "Alignment": "Center", "Bold": True, "Italics": False, "Font size": 11},
        {"Row Type": "Task", "Activity description": "Pub 1: Review article", "Person incharge": "Sathya", "Label": "PUB1", "Start month": 1, "End month": 5, "Color": "Orange", "Alignment": "Left", "Bold": False, "Italics": True, "Font size": 10},
    ])

df = st.data_editor(st.session_state.data, num_rows="dynamic", width="stretch", column_config={
    "Row Type": st.column_config.SelectboxColumn("Row Type", options=["Task", "Header"]),
    "Color": st.column_config.SelectboxColumn("Color", options=list(COLOR_PALETTE.keys())),
    "Alignment": st.column_config.SelectboxColumn("Alignment", options=["Left", "Center", "Right"]),
})

# --- 4. Drawing Engine ---
def draw_scientific_gantt(data, start_dt, num_months):
    ACT_W, STAFF_W = 7, 2
    ROW_H = 0.85
    Y_H, N_H, M_H = 0.8, 0.7, 1.0 
    H_TOTAL = Y_H + N_H + M_H
    
    # Pre-calculate to avoid NameErrors
    rows_count = len(data)
    
    fig, ax = plt.subplots(figsize=(24, (rows_count + H_TOTAL + 0.5) * ROW_H))
    ax.set_xlim(0, ACT_W + STAFF_W + num_months)
    ax.set_ylim(-0.5, rows_count + H_TOTAL)
    ax.axis('off')

    year_map = [(start_dt + relativedelta(months=m)).year for m in range(num_months)]
    month_names = [(start_dt + relativedelta(months=m)).strftime('%b') for m in range(num_months)]
    
    # Headers
    ax.add_patch(patches.Rectangle((0, rows_count), ACT_W + STAFF_W, H_TOTAL, facecolor='white', edgecolor='black', lw=1.5))
    ax.text((ACT_W + STAFF_W)/2, rows_count + (H_TOTAL/2), "Activities", ha='center', va='center', fontweight='bold', fontsize=18)

    curr_x = ACT_W + STAFF_W
    for yr in sorted(list(set(year_map))):
        span = year_map.count(yr)
        ax.add_patch(patches.Rectangle((curr_x, rows_count + N_H + M_H), span, Y_H, facecolor='#f2f2f2', edgecolor='black', lw=1.5))
        ax.text(curr_x + span/2, rows_count + N_H + M_H + (Y_H/2), str(yr), ha='center', va='center', fontweight='bold', fontsize=13)
        curr_x += span

    for i in range(num_months):
        x = ACT_W + STAFF_W + i
        ax.add_patch(patches.Rectangle((x, rows_count + M_H), 1, N_H, facecolor='white', edgecolor='black', lw=1))
        ax.text(x + 0.5, rows_count + M_H + (N_H/2), str(i + 1), ha='center', va='center', fontsize=10)
        ax.add_patch(patches.Rectangle((x, rows_count), 1, M_H, facecolor='white', edgecolor='black', lw=1))
        ax.text(x + 0.5, rows_count + (M_H/2), month_names[i], ha='center', va='center', fontsize=9, rotation=90)

    # Body
    for idx, row in data.iterrows():
        y = rows_count - 1 - idx
        f_weight, f_style, f_size = ('bold' if row.get('Bold') else 'normal'), ('italic' if row.get('Italics') else 'normal'), (row.get('Font size') or 10)
        h_align = str(row.get('Alignment') or 'Center').lower()
        row_color = COLOR_PALETTE.get(row.get('Color') or 'Orange', '#ffa500')

        if str(row.get('Row Type')) == 'Header':
            ax.add_patch(patches.Rectangle((0, y), ACT_W + STAFF_W + num_months, 1, facecolor=row_color, edgecolor='black', lw=1))
            ax.text((ACT_W + STAFF_W + num_months) * 0.5, y + 0.5, str(row.get('Activity description') or "").upper(), ha='center', va='center', fontweight=f_weight, fontstyle=f_style, fontsize=f_size)
        else:
            ax.add_patch(patches.Rectangle((0, y), ACT_W, 1, facecolor='white', edgecolor='black', lw=1))
            ax.text(ACT_W * 0.05 if h_align == 'left' else ACT_W * 0.5, y + 0.5, str(row.get('Activity description') or ""), ha=h_align, va='center', fontweight=f_weight, fontstyle=f_style, fontsize=f_size)
            ax.add_patch(patches.Rectangle((ACT_W, y), STAFF_W, 1, facecolor='white', edgecolor='black', lw=1))
            ax.text(ACT_W + STAFF_W/2, y + 0.5, str(row.get('Person incharge') or ""), ha='center', va='center', fontsize=f_size)
            for i in range(num_months):
                ax.add_patch(patches.Rectangle((ACT_W + STAFF_W + i, y), 1, 1, facecolor='none', edgecolor='#444444', lw=0.9))
            try:
                s, e = int(row.get('Start month') or 1), int(row.get('End month') or 1)
                bx, bw = (ACT_W + STAFF_W + s - 1), (e - s + 1)
                if bw > 0:
                    ax.add_patch(patches.Rectangle((bx, y + 0.15), bw, 0.7, facecolor=row_color, edgecolor='black', lw=1.2, zorder=5))
                    if row.get('Label'):
                        ax.text(bx + bw/2, y + 0.5, str(row['Label']), ha='center', va='center', fontweight='bold', fontsize=f_size-1, zorder=6)
            except: pass

    ax.add_patch(patches.Rectangle((0, 0), ACT_W + STAFF_W + num_months, rows_count + H_TOTAL, fill=False, edgecolor='black', lw=2.5, zorder=10))
    return fig

# --- 5. Export ---
st.divider()
st.markdown("<div class='section-header'>Gantt Chart Preview</div>", unsafe_allow_html=True)
final_fig = draw_scientific_gantt(df, start_date, total_months)
st.pyplot(final_fig)

st.markdown("<div class='section-header'>Export Options</div>", unsafe_allow_html=True)
with st.container(border=True):
    e1, e2, e3 = st.columns(3)
    # The crash happens here during savefig at 1200 DPI. We must manage memory strictly.
    for i, (fmt, lbl, dpi) in enumerate([("pdf", "PDF (Vector)", 300), ("svg", "SVG (Vector)", 300), ("png", "PNG (1200 DPI)", 1200)]):
        buf = io.BytesIO()
        final_fig.savefig(buf, format=fmt, bbox_inches='tight', dpi=dpi)
        [e1, e2, e3][i].download_button(lbl, buf.getvalue(), f"gantt.{fmt}")
    
    # CRITICAL: Close figure after savefig to free up the 1GB RAM server limit
    plt.close(final_fig)

st.markdown("<br><p style='text-align: center; color: #444; font-weight: 800;'>Developed by Sathya</p>", unsafe_allow_html=True)
