import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.font_manager as fm
from datetime import datetime
from dateutil.relativedelta import relativedelta
import io

# --- 1. System Setup ---
st.set_page_config(layout="wide", page_title="Gantt Chart")

# Custom CSS targeting specific legibility issues
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #000000; }
    
    /* Creative Title with Solid Lines */
    .title-container { display: flex; align-items: center; justify-content: center; width: 100%; margin: 20px 0; }
    .title-line { flex-grow: 1; height: 3px; background-color: #000; opacity: 1; }
    .creative-title {
        padding: 0 30px; font-size: 3.5rem; font-weight: 900; 
        background: linear-gradient(90deg, #073b4c, #118ab2, #06d6a0);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-transform: uppercase; white-space: nowrap;
    }

    /* 1. Planning Duration Labels & Timeline Value */
    .stDateInput label { font-size: 20px !important; font-weight: 700 !important; color: #000 !important; }
    .timeline-container { display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .timeline-label { font-size: 20px; font-weight: 700; color: #000; }
    .timeline-value { font-size: 40px; font-weight: 900; color: #000; margin: 0; padding: 0; line-height: 1.2; }

    /* 2. Select Font Family Dropdown - Reduced Size & Normal Weight */
    .stSelectbox div[data-baseweb="select"] {
        font-size: 18px !important;
        font-weight: 500 !important;
        color: #000000 !important;
        height: 45px !important;
    }

    /* 3. Input Table - Increased Cell Font Size */
    [data-testid="stDataEditor"] div, [data-testid="stDataEditor"] input {
        font-size: 20px !important;
        color: #000000 !important;
        font-weight: 600 !important;
    }
    [data-testid="stDataEditor"] th {
        background-color: #f0f2f6 !important;
        color: #000 !important;
        font-size: 18px !important;
        font-weight: 800 !important;
    }

    .section-header { font-size: 28px; font-weight: 800; color: #000; margin-top: 30px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Title Section ---
st.markdown("""
    <div class='title-container'>
        <div class='title-line'></div>
        <div class='creative-title'>Gantt Chart Creator</div>
        <div class='title-line'></div>
    </div>
    """, unsafe_allow_html=True)

# --- 3. Planning Duration ---
st.markdown("<div class='section-header'>Planning Duration</div>", unsafe_allow_html=True)
with st.container(border=True):
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        start_date = st.date_input("Project Start Date", datetime(2023, 9, 15))
    with c2:
        end_date = st.date_input("Project End Date", datetime(2027, 9, 15))
    
    delta = relativedelta(end_date, start_date)
    total_months = max((delta.years * 12) + delta.months, 1)
    with c3:
        st.markdown(f"<div class='timeline-container'><div class='timeline-label'>Timeline (months)</div><div class='timeline-value'>{total_months}</div></div>", unsafe_allow_html=True)

# Font Selection
st.markdown("<div class='section-header'>Select Font Family</div>", unsafe_allow_html=True)
@st.cache_data
def get_system_fonts():
    return sorted(list(set([f.name for f in fm.fontManager.ttflist])))

system_fonts = get_system_fonts()
default_font = "Arial" if "Arial" in system_fonts else system_fonts[0]
selected_font = st.selectbox("Font selector:", system_fonts, index=system_fonts.index(default_font) if default_font in system_fonts else 0, label_visibility="collapsed")
plt.rcParams['font.family'] = selected_font
plt.rcParams['pdf.fonttype'] = 42

# --- 4. Inputs to Gantt Chart Generator ---
st.markdown("<div class='section-header'>Inputs to Gantt Chart Generator</div>", unsafe_allow_html=True)

COLOR_PALETTE = {"Rose": "#ef476f", "Mustard": "#ffd166", "Emerald": "#06d6a0", "Blue": "#118ab2", "Midnight": "#073b4c", "Orange": "#ffa500", "Yellow": "#ffff00", "Grey Header": "#d3d3d3"}

if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame([
        {"Row Type": "Header", "Activity description": "Research Plan Overview", "Person incharge": "", "Label": "", "Start month": 1, "End month": total_months, "Color": "Grey Header", "Alignment": "Center", "Bold": True, "Italics": False, "Font size": 11},
        {"Row Type": "Task", "Activity description": "Pub 1: Review article", "Person incharge": "Sathya", "Label": "PUB1", "Start month": 1, "End month": 5, "Color": "Orange", "Alignment": "Left", "Bold": False, "Italics": True, "Font size": 10},
    ])

df = st.data_editor(st.session_state.data, num_rows="dynamic", width="stretch", column_config={
    "Row Type": st.column_config.SelectboxColumn("Row Type", options=["Task", "Header"], required=True),
    "Activity description": st.column_config.TextColumn("Activity description", width="large", required=True),
    "Person incharge": st.column_config.TextColumn("Person incharge", width="medium"),
    "Label": st.column_config.TextColumn("Label", width="small"),
    "Start month": st.column_config.NumberColumn("Start month", min_value=1),
    "End month": st.column_config.NumberColumn("End month", min_value=1),
    "Color": st.column_config.SelectboxColumn("Color", options=list(COLOR_PALETTE.keys())),
    "Alignment": st.column_config.SelectboxColumn("Alignment", options=["Left", "Center", "Right"]),
    "Bold": st.column_config.CheckboxColumn("Bold"),
    "Italics": st.column_config.CheckboxColumn("Italics"),
    "Font size": st.column_config.NumberColumn("Font size", min_value=2, max_value=72, step=2, default=10),
})

# --- 5. Drawing Engine ---
def draw_scientific_gantt(data, start_dt, num_months):
    ACT_W, STAFF_W = 7, 2
    ROW_H = 0.85
    total_rows = len(data)
    Y_H, N_H, M_H = 0.8, 0.7, 1.0 
    H_TOTAL = Y_H + N_H + M_H
    
    fig, ax = plt.subplots(figsize=(24, (total_rows + H_TOTAL + 0.5) * ROW_H))
    ax.set_xlim(0, ACT_W + STAFF_W + num_months)
    ax.set_ylim(-0.5, total_rows + H_TOTAL)
    ax.axis('off')

    year_map = [(start_dt + relativedelta(months=m)).year for m in range(num_months)]
    month_names = [(start_dt + relativedelta(months=m)).strftime('%b') for m in range(num_months)]
    
    ax.add_patch(patches.Rectangle((0, total_rows), ACT_W + STAFF_W, H_TOTAL, facecolor='white', edgecolor='black', lw=1.5))
    ax.text((ACT_W + STAFF_W)/2, total_rows + (H_TOTAL/2), "Activities", ha='center', va='center', fontweight='bold', fontsize=18)

    curr_x = ACT_W + STAFF_W
    for yr in sorted(list(set(year_map))):
        span = year_map.count(yr)
        ax.add_patch(patches.Rectangle((curr_x, total_rows + N_H + M_H), span, Y_H, facecolor='#f2f2f2', edgecolor='black', lw=1.5))
        ax.text(curr_x + span/2, total_rows + N_H + M_H + (Y_H/2), str(yr), ha='center', va='center', fontweight='bold', fontsize=13)
        curr_x += span

    for i in range(num_months):
        x = ACT_W + STAFF_W + i
        ax.add_patch(patches.Rectangle((x, total_rows + M_H), 1, N_H, facecolor='white', edgecolor='black', lw=1))
        ax.text(x + 0.5, total_rows + M_H + (N_H/2), str(i + 1), ha='center', va='center', fontsize=10)
        ax.add_patch(patches.Rectangle((x, total_rows), 1, M_H, facecolor='white', edgecolor='black', lw=1))
        ax.text(x + 0.5, total_rows + (M_H/2), month_names[i], ha='center', va='center', fontsize=9, rotation=90)

    for idx, row in data.iterrows():
        y = total_rows - 1 - idx
        f_weight, f_style, f_size = ('bold' if row.get('Bold') else 'normal'), ('italic' if row.get('Italics') else 'normal'), (row.get('Font size') or 10)
        h_align = str(row.get('Alignment') or 'Center').lower()
        align_off = {"left": 0.05, "center": 0.5, "right": 0.95}.get(h_align, 0.5)
        row_color = COLOR_PALETTE.get(row.get('Color') or 'Orange', '#ffa500')

        if str(row.get('Row Type')) == 'Header':
            ax.add_patch(patches.Rectangle((0, y), ACT_W + STAFF_W + num_months, 1, facecolor=row_color, edgecolor='black', lw=1))
            ax.text((ACT_W + STAFF_W + num_months) * align_off, y + 0.5, str(row.get('Activity description') or "").upper(), ha=h_align, va='center', fontweight=f_weight, fontstyle=f_style, fontsize=f_size)
        else:
            ax.add_patch(patches.Rectangle((0, y), ACT_W, 1, facecolor='white', edgecolor='black', lw=1))
            ax.text(ACT_W * align_off, y + 0.5, str(row.get('Activity description') or ""), ha=h_align, va='center', fontweight=f_weight, fontstyle=f_style, fontsize=f_size)
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

    ax.add_patch(patches.Rectangle((0, 0), ACT_W + STAFF_W + num_months, total_rows + H_TOTAL, fill=False, edgecolor='black', lw=2.5, zorder=10))
    return fig

# --- 6. Preview & Export ---
st.divider()
st.markdown("<div class='section-header'>Gantt Chart Preview</div>", unsafe_allow_html=True)
final_fig = draw_scientific_gantt(df, start_date, total_months)
st.pyplot(final_fig)

st.markdown("<div class='section-header'>Export Options</div>", unsafe_allow_html=True)
with st.container(border=True):
    ex_col1, ex_col2, ex_col3 = st.columns(3)
    for i, (fmt, lbl, d_dpi) in enumerate([("pdf", "Download PDF (Vector)", 300), ("svg", "Download SVG (Vector)", 300), ("png", "Download PNG (1200 DPI)", 1200)]):
        buf = io.BytesIO()
        final_fig.savefig(buf, format=fmt, bbox_inches='tight', dpi=d_dpi, transparent=False)
        [ex_col1, ex_col2, ex_col3][i].download_button(lbl, buf.getvalue(), f"gantt_chart.{fmt}")

st.markdown("<br><p style='text-align: center; color: #444; font-weight: 800;'>Developed by Sathya</p>", unsafe_allow_html=True)