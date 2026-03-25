import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.font_manager as fm
from datetime import datetime
from dateutil.relativedelta import relativedelta
import textwrap
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
    [data-testid="stDataEditor"] div, [data-testid="stDataEditor"] input { font-size: 20px !important; font-weight: 600 !important; }
    .section-header { font-size: 28px; font-weight: 800; margin-top: 30px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='title-container'><div class='title-line'></div><div class='creative-title'>Gantt Chart Creator</div><div class='title-line'></div></div>", unsafe_allow_html=True)

# --- 2. Timeline Logic ---
st.markdown("<div class='section-header'>Planning Duration</div>", unsafe_allow_html=True)
with st.container(border=True):
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1: start_date = st.date_input("Project Start Date", datetime(2023, 9, 15))
    with c2: end_date = st.date_input("Project End Date", datetime(2027, 9, 15))
    delta = relativedelta(end_date, start_date)
    total_months = max((delta.years * 12) + delta.months, 1)
    with c3: st.markdown(f"<div class='timeline-container'><div class='timeline-label'>Timeline (months)</div><div class='timeline-value'>{total_months}</div></div>", unsafe_allow_html=True)

@st.cache_data
def get_system_fonts():
    return sorted(list(set([f.name for f in fm.fontManager.ttflist])))

selected_font = st.selectbox("Font selector:", get_system_fonts(), index=0)
plt.rcParams['font.family'] = selected_font

# --- 3. Inputs ---
st.markdown("<div class='section-header'>Inputs to Gantt Chart Generator</div>", unsafe_allow_html=True)
COLOR_PALETTE = {"Rose": "#ef476f", "Mustard": "#ffd166", "Emerald": "#06d6a0", "Blue": "#118ab2", "Midnight": "#073b4c", "Orange": "#ffa500", "Yellow": "#ffff00", "Grey Header": "#d3d3d3", "None": "none"}

if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame([
        {"Row Type": "Header", "Group": "", "Activity description": "RESEARCH PLAN", "Person incharge": "", "Label": "", "Start month": 1, "End month": total_months, "Color": "Grey Header", "Bold": True, "Italics": False, "Font size": 12},
        {"Row Type": "Task", "Group": "Pub 4 - Thermal model", "Activity description": "", "Person incharge": "Sathya", "Label": "PUB4", "Start month": 37, "End month": 41, "Color": "Orange", "Bold": False, "Italics": False, "Font size": 10},
        {"Row Type": "Task", "Group": "Pub 4 - Thermal model", "Activity description": "", "Person incharge": "MSc 1 Aryeshah", "Label": "", "Start month": 6, "End month": 16, "Color": "Yellow", "Bold": False, "Italics": False, "Font size": 10},
    ])

df = st.data_editor(st.session_state.data, num_rows="dynamic", width="stretch")

# --- 4. Drawing Engine ---
def draw_scientific_gantt(data, start_dt, num_months):
    ACT_W, STAFF_W, BASE_ROW_H = 7, 2.5, 0.8
    Y_H, N_H, M_H = 0.8, 0.7, 1.0 
    H_TOTAL = Y_H + N_H + M_H
    
    # Calculate Adaptive Row Heights
    row_heights = []
    for _, row in data.iterrows():
        # Estimate lines based on text length and manual newlines
        lines = max(len(str(row.get('Group') or "").split('\n')), 
                    len(str(row.get('Person incharge') or "").split('\n')), 1)
        row_heights.append(lines * BASE_ROW_H)
    
    total_body_height = sum(row_heights)
    fig, ax = plt.subplots(figsize=(24, (total_body_height + H_TOTAL + 1)))
    ax.set_xlim(0, ACT_W + STAFF_W + num_months)
    ax.set_ylim(-0.5, total_body_height + H_TOTAL)
    ax.axis('off')

    # Header Logic (Years/Months)
    ax.add_patch(patches.Rectangle((0, total_body_height), ACT_W + STAFF_W, H_TOTAL, facecolor='white', edgecolor='black', lw=1.5))
    ax.text((ACT_W + STAFF_W)/2, total_body_height + (H_TOTAL/2), "Activities", ha='center', va='center', fontweight='bold', fontsize=18)

    year_map = [(start_dt + relativedelta(months=m)).year for m in range(num_months)]
    month_names = [(start_dt + relativedelta(months=m)).strftime('%b') for m in range(num_months)]
    
    curr_x = ACT_W + STAFF_W
    for yr in sorted(list(set(year_map))):
        span = year_map.count(yr)
        ax.add_patch(patches.Rectangle((curr_x, total_body_height + N_H + M_H), span, Y_H, facecolor='#f2f2f2', edgecolor='black', lw=1.5))
        ax.text(curr_x + span/2, total_body_height + N_H + M_H + (Y_H/2), str(yr), ha='center', va='center', fontweight='bold', fontsize=13)
        curr_x += span

    for i in range(num_months):
        x = ACT_W + STAFF_W + i
        ax.add_patch(patches.Rectangle((x, total_body_height + M_H), 1, N_H, facecolor='white', edgecolor='black', lw=1))
        ax.text(x + 0.5, total_body_height + M_H + (N_H/2), str(i + 1), ha='center', va='center', fontsize=9)
        ax.add_patch(patches.Rectangle((x, total_body_height), 1, M_H, facecolor='white', edgecolor='black', lw=1))
        ax.text(x + 0.5, total_body_height + (M_H/2), month_names[i], ha='center', va='center', fontsize=8, rotation=90)

    # Body Drawing
    curr_y = total_body_height
    for idx, row in data.iterrows():
        h = row_heights[idx]
        curr_y -= h
        r_type = str(row.get('Row Type'))
        f_weight = 'bold' if row.get('Bold') else 'normal'
        f_style = 'italic' if row.get('Italics') else 'normal'
        f_size = row.get('Font size') or 10
        r_color = COLOR_PALETTE.get(row.get('Color'), 'none')

        if r_type in ['Header', 'Subheader']:
            # Single Text Entry for Headers spanning full width
            alpha = 1.0 if r_type == 'Header' else 0.4
            ax.add_patch(patches.Rectangle((0, curr_y), ACT_W + STAFF_W + num_months, h, facecolor=r_color, edgecolor='black', alpha=alpha))
            ax.text((ACT_W + STAFF_W + num_months)/2, curr_y + h/2, str(row.get('Activity description') or "").upper(), 
                    ha='center', va='center', fontweight=f_weight, fontstyle=f_style, fontsize=f_size)
        else:
            # Task Row Logic
            # Staff Column
            ax.add_patch(patches.Rectangle((ACT_W, curr_y), STAFF_W, h, facecolor='white', edgecolor='black'))
            ax.text(ACT_W + STAFF_W/2, curr_y + h/2, str(row.get('Person incharge') or ""), ha='center', va='center', fontsize=f_size)
            
            # Grid and Bar
            for i in range(num_months):
                ax.add_patch(patches.Rectangle((ACT_W + STAFF_W + i, curr_y), 1, h, facecolor='none', edgecolor='#ddd', lw=0.5))
            
            if r_color != 'none':
                try:
                    s, e = int(row.get('Start month')), int(row.get('End month'))
                    ax.add_patch(patches.Rectangle((ACT_W + STAFF_W + s - 1, curr_y + h*0.2), (e - s + 1), h*0.6, facecolor=r_color, edgecolor='black', zorder=5))
                    if row.get('Label'):
                        ax.text(ACT_W + STAFF_W + s - 1 + (e - s + 1)/2, curr_y + h/2, str(row['Label']), ha='center', va='center', fontweight='bold', fontsize=f_size-1, zorder=6)
                except: pass

    # Merged Group Column (Post-processing to draw over rows)
    curr_y = total_body_height
    i = 0
    while i < len(data):
        group_name = str(data.iloc[i].get('Group') or "")
        row_type = str(data.iloc[i].get('Row Type'))
        
        if group_name != "" and row_type == 'Task':
            start_idx = i
            while i < len(data) and str(data.iloc[i].get('Group')) == group_name:
                i += 1
            merge_h = sum(row_heights[start_idx:i])
            y_pos = total_body_height - sum(row_heights[:i])
            ax.add_patch(patches.Rectangle((0, y_pos), ACT_W, merge_h, facecolor='white', edgecolor='black'))
            ax.text(ACT_W/2, y_pos + merge_h/2, "\n".join(textwrap.wrap(group_name, width=20)), ha='center', va='center', fontstyle='italic', fontsize=11)
        else:
            if row_type == 'Task':
                y_pos = total_body_height - sum(row_heights[:i+1])
                ax.add_patch(patches.Rectangle((0, y_pos), ACT_W, row_heights[i], facecolor='white', edgecolor='black'))
                ax.text(ACT_W/2, y_pos + row_heights[i]/2, str(data.iloc[i].get('Activity description') or ""), ha='center', va='center', fontsize=10)
            i += 1

    return fig

st.divider()
final_fig = draw_scientific_gantt(df, start_date, total_months)
st.pyplot(final_fig, dpi=100)

buf = io.BytesIO()
final_fig.savefig(buf, format="pdf", bbox_inches='tight')
st.download_button("Download PDF", buf.getvalue(), "gantt.pdf")
