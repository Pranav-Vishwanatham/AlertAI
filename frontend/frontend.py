import gradio as gr
import pandas as pd
import folium
import threading
import time
import requests

API_BASE_URL = "http://localhost:8000"
ASSIGN_API_URL = f"{API_BASE_URL}/assign_unit"

data_lock = threading.Lock()
emergencies = pd.DataFrame()
resources = {'Police Units': 0, 'Ambulances': 0, 'Fire Trucks': 0}

UNIT_TYPE_MAP = {
    "Police": "police",
    "Ambulance": "ambulance",
    "Fire Dept": "fire_truck"
}

assignment_status_map = {}
assigned_unit_map = {}

def assigned_unit_display(assigned):
    if isinstance(assigned, list) and assigned and isinstance(assigned[0], dict):
        return ", ".join(f"{u.get('unit_id', '')} ({u.get('unit_type', '')})" for u in assigned)
    elif isinstance(assigned, list):
        return ", ".join(assigned)
    elif isinstance(assigned, str):
        return assigned
    return ""

def assign_units(call_id, unit_types):
    if not call_id or not unit_types:
        return "Please select at least one unit type and a valid emergency.", None
    results = []
    assigned_units = []
    for ut in unit_types:
        payload = {"call_id": call_id, "unit_type": UNIT_TYPE_MAP[ut]}
        try:
            resp = requests.post(ASSIGN_API_URL, json=payload)
            if resp.ok:
                try:
                    rjson = resp.json()
                    assigned_unit = rjson.get("assigned_unit", "")
                    unit_type = rjson.get("unit_type", ut)
                    if assigned_unit:
                        assigned_units.append({"unit_id": assigned_unit, "unit_type": unit_type})
                except Exception:
                    assigned_units.append({"unit_id": "", "unit_type": ut})
                results.append(f"{ut} assigned.")
            else:
                results.append(f"{ut}: {resp.text}")
        except Exception as e:
            results.append(f"{ut}: error {str(e)}")
    msg = "Unit(s) assigned successfully" if all("assigned." in r for r in results) else "; ".join(results)
    assignment_status_map[call_id] = msg
    if assigned_units:
        if call_id in assigned_unit_map:
            prev_units = assigned_unit_map[call_id]
            new_units = prev_units + [u for u in assigned_units if u not in prev_units]
            assigned_unit_map[call_id] = new_units
        else:
            assigned_unit_map[call_id] = assigned_units
    return msg, assigned_units

def get_priority_indicator(priority):
    if priority == 'HIGH':
        return '🔴 HIGH'
    elif priority == 'MEDIUM':
        return '🟠 MEDIUM'
    else:
        return '🟢 LOW'

def fetch_from_api():
    try:
        resp = requests.get(f"{API_BASE_URL}/emergencies")
        api_json = resp.json() if resp.ok else {}
        if isinstance(api_json, dict):
            emergencies_list = api_json.get("emergencies", [])
        elif isinstance(api_json, list):
            emergencies_list = api_json
        else:
            emergencies_list = []
    except Exception:
        emergencies_list = []

    df = pd.DataFrame(emergencies_list)

    resources['Police Units'] = get_unit_count("police")
    resources['Ambulances'] = get_unit_count("ambulance")
    resources['Fire Trucks'] = get_unit_count("fire_truck")

    ui_columns = [
        'ID', 'PRIORITY', 'CALLER', 'EMERGENCY', 'TIME', 'LOCATION',
        'LAT', 'LON', 'STATUS', 'ASSIGNED_UNIT', 'TRANSCRIPT', 'AI_RECOMMENDATION'
    ]
    if not df.empty:
        df['ID'] = df.get('call_id', df.index)
        df['PRIORITY'] = df.get('priority', 'LOW').fillna('LOW')
        df['PRIORITY_DISPLAY'] = df['PRIORITY'].apply(get_priority_indicator)
        df['CALLER'] = df.get('caller_name', '')
        df['EMERGENCY'] = df.get('emergency_type', '')
        df['TIME'] = df.get('time', '')
        df['LOCATION'] = df.get('location', '')
        df['STATUS'] = df.get('status', 'UNASSIGNED').fillna('UNASSIGNED').str.upper()
        df['LAT'] = df.get('latitude', '')
        df['LON'] = df.get('longitude', '')
        df['ASSIGNED_UNIT'] = df.get('assigned_unit', '')
        df['ASSIGNED_UNIT_DISPLAY'] = df['ASSIGNED_UNIT'].apply(assigned_unit_display)
        df['TRANSCRIPT'] = df.get('transcript', '')
        df['AI_RECOMMENDATION'] = df.get('ai_recommendation', df.get('recommended_actions', ''))
        for col in ui_columns + ['ASSIGNED_UNIT_DISPLAY', 'PRIORITY_DISPLAY']:
            if col not in df:
                df[col] = ""
    else:
        df = pd.DataFrame(columns=ui_columns + ['ASSIGNED_UNIT_DISPLAY', 'PRIORITY_DISPLAY'])
    return df

def get_unit_count(unit_type):
    try:
        resp = requests.get(f"{API_BASE_URL}/units/count", params={"type": unit_type})
        if resp.status_code == 200:
            count = resp.json().get("count", 0)
            return count
        return 0
    except Exception:
        return 0

def updater():
    global emergencies
    while True:
        time.sleep(5)
        with data_lock:
            emergencies = fetch_from_api()

threading.Thread(target=updater, daemon=True).start()

def create_map(highlight_id=None):
    m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)  # Center USA, zoomed out
    with data_lock:
        for _, row in emergencies.iterrows():
            lat, lon = row['LAT'], row['LON']
            try:
                lat = float(lat)
                lon = float(lon)
            except:
                continue
            icon_color = 'blue' if highlight_id is not None and row['ID'] == highlight_id else (
                'red' if 'HIGH' in row['PRIORITY'] else
                'orange' if 'MEDIUM' in row['PRIORITY'] else 'green')
            popup = f"ID: {row['ID']}, {row['EMERGENCY']}, Priority: {row['PRIORITY']}"
            folium.Marker([lat, lon], popup=popup, icon=folium.Icon(color=icon_color)).add_to(m)
    return m._repr_html_()

# -------------- NEW: Always use the same sorting for both display and selection --------------
def get_sorted_emergencies_df():
    df = emergencies.copy()
    if df.empty:
        return df
    def prio_num(priority_str):
        if isinstance(priority_str, str):
            if 'HIGH' in priority_str:
                return 3
            elif 'MEDIUM' in priority_str:
                return 2
            elif 'LOW' in priority_str:
                return 1
        return 0
    df['PRIORITY_NUM'] = df['PRIORITY'].apply(prio_num)
    df['IS_UNASSIGNED'] = (df['STATUS'] == 'UNASSIGNED').astype(int)
    df = df.sort_values(by=['IS_UNASSIGNED', 'PRIORITY_NUM'], ascending=[False, False])
    df = df.drop(columns=['PRIORITY_NUM', 'IS_UNASSIGNED'])
    return df

def update_dashboard():
    with data_lock:
        df = get_sorted_emergencies_df()
        if df.empty:
            table_data = pd.DataFrame(columns=['ID', 'PRIORITY_DISPLAY', 'CALLER',
                                               'EMERGENCY', 'TIME', 'LOCATION', 'STATUS', 'ASSIGNED_UNIT_DISPLAY'])
            return ["0", "0", table_data, "", "0", "0", "0"]

        unassigned = len(df[df['STATUS'] == 'UNASSIGNED'])
        assigned = len(df[df['STATUS'] == 'ASSIGNED'])
        table_data = df[['ID', 'PRIORITY_DISPLAY', 'CALLER',
                         'EMERGENCY', 'TIME', 'LOCATION', 'STATUS', 'ASSIGNED_UNIT_DISPLAY']].reset_index(drop=True)
    return [f"{unassigned}", f"{assigned}", table_data,
            create_map(), f"Police Units: {resources['Police Units']}",
            f"Ambulances: {resources['Ambulances']}", f"Fire Trucks: {resources['Fire Trucks']}"]

def get_emergency_details(evt: gr.SelectData):
    index = evt.index[0] if isinstance(evt.index, list) else evt.index
    df = get_sorted_emergencies_df()
    table_data = df[['ID', 'PRIORITY_DISPLAY', 'CALLER',
                     'EMERGENCY', 'TIME', 'LOCATION', 'STATUS', 'ASSIGNED_UNIT', 'ASSIGNED_UNIT_DISPLAY']].reset_index(drop=True)
    if index >= len(table_data):
        return [gr.update()] * 10 + [gr.update(value=[]), gr.update(value="")]

    selected_id = table_data.loc[index, 'ID']
    row = df[df['ID'] == selected_id].iloc[0]
    assign_status = assignment_status_map.get(selected_id, "")
    assigned_unit_display_str = assigned_unit_display(row['ASSIGNED_UNIT'])
    status_message = ""
    if assigned_unit_display_str:
        status_message = f"Assigned Unit(s): {assigned_unit_display_str}"
    elif assign_status:
        status_message = assign_status

    return [
        row['ID'], row['PRIORITY_DISPLAY'], row['CALLER'],
        row['EMERGENCY'], row['TIME'], row['LOCATION'], row['STATUS'],
        row['TRANSCRIPT'], row['AI_RECOMMENDATION'],
        gr.update(value=[]),
        gr.update(value=status_message)
    ]

def load_initial_details():
    with data_lock:
        df = get_sorted_emergencies_df()
        if df.empty:
            return [gr.update()] * 11

        def score(p):
            if 'HIGH' in p:
                return 3
            elif 'MEDIUM' in p:
                return 2
            return 1

        df['PRIORITY_SCORE'] = df['PRIORITY'].map(score)
        df = df.sort_values(by=['PRIORITY_SCORE'], ascending=[False])
        row = df.iloc[0]
        assign_status = assignment_status_map.get(row.get('ID'), "")
        assigned_unit_display_str = assigned_unit_display(row.get('ASSIGNED_UNIT'))
        status_message = ""
        if assigned_unit_display_str:
            status_message = f"Assigned Unit(s): {assigned_unit_display_str}"
        elif assign_status:
            status_message = assign_status

        return [
            row.get('ID'), row.get('PRIORITY_DISPLAY'), row.get('CALLER'),
            row.get('EMERGENCY'), row.get('TIME'), row.get('LOCATION'), row.get('STATUS'),
            row.get('TRANSCRIPT', ''), row.get('AI_RECOMMENDATION', ''),
            gr.update(value=[]),
            gr.update(value=status_message)
        ]

css = """
/* Highlight the full row in the gradio dataframe when any cell is selected */
.gr-dataframe tbody tr:has(td.svelte-13yo3y5-selected) {
    background-color: #363da0 !important;
    color: #fff !important;
}
/* Make the map component height similar to the table */
#map_html {
    min-height: 500px !important;
    height: 500px !important;
    max-height: 100vh !important;
}
"""

with gr.Blocks(theme="soft", css=css) as demo:
    gr.Markdown("# 🚨 **AlertAI - Real-Time Emergency Dashboard**")
    gr.Markdown(
        "Easily monitor, review, and manage incoming emergency calls and incidents. "
        "Status and details update in real-time."
    )

    with gr.Row():
        with gr.Column():
            police_units = gr.Textbox(label="Available Police Units", interactive=False)
        with gr.Column():
            ambulances = gr.Textbox(label="Available Ambulances", interactive=False)
        with gr.Column():
            fire_trucks = gr.Textbox(label="Available Fire Trucks", interactive=False)

    gr.Markdown(" ")

    with gr.Row():
        unassigned = gr.Textbox(label="Unassigned", interactive=False)
        assigned = gr.Textbox(label="Assigned", interactive=False)

    gr.Markdown("---")

    gr.Markdown("## 🚨 Live Emergencies")
    with gr.Row():
        with gr.Column(scale=2):
            emergency_table = gr.Dataframe(
                headers=['ID', 'PRIORITY_DISPLAY', 'CALLER', 'EMERGENCY', 'TIME', 'LOCATION', 'STATUS', 'ASSIGNED_UNIT_DISPLAY'],
                datatype=['str', 'str', 'str', 'str', 'str', 'str', 'str', 'str'],
                col_count=(8, 'fixed'),
                interactive=False,
                height=500,
            )
        with gr.Column(scale=1):
            map_component = gr.HTML(label="Emergency Locations", elem_id="map_html")

    gr.Markdown("---")

    gr.Markdown("## 📋 Emergency Details")
    with gr.Row():
        with gr.Column(scale=1):
            selected_id = gr.Textbox(label="Emergency ID", interactive=False)
            selected_priority = gr.Textbox(label="Priority", interactive=False)
            selected_caller = gr.Textbox(label="Caller", interactive=False)
            selected_emergency = gr.Textbox(label="Emergency", interactive=False)
            selected_time = gr.Textbox(label="Time", interactive=False)
            selected_location = gr.Textbox(label="Location", interactive=False)
            selected_status = gr.Textbox(label="Status", interactive=False)
        with gr.Column(scale=2):
            transcript = gr.Textbox(label="Transcript", lines=5, interactive=False)
            ai_recommendation = gr.Textbox(label="AI Recommendation", lines=3, interactive=False)
            unit_types_dropdown = gr.CheckboxGroup(
                ["Police", "Ambulance", "Fire Dept"],
                label="Assign Units",
                info="Select which units to dispatch"
            )
            assign_btn = gr.Button("Assign Units")
            assignment_status = gr.Textbox(label="Assignment Status", interactive=False)

    emergency_table.select(get_emergency_details, outputs=[
        selected_id, selected_priority, selected_caller,
        selected_emergency, selected_time, selected_location, selected_status,
        transcript, ai_recommendation,
        unit_types_dropdown, assignment_status
    ])

    demo.load(update_dashboard, outputs=[
        unassigned, assigned,
        emergency_table, map_component,
        police_units, ambulances, fire_trucks
    ], every=5)
    demo.load(load_initial_details, outputs=[
        selected_id, selected_priority, selected_caller,
        selected_emergency, selected_time, selected_location, selected_status,
        transcript, ai_recommendation,
        unit_types_dropdown, assignment_status
    ])

    def assign_and_refresh(unit_types, call_id):
        msg, assigned_units = assign_units(call_id, unit_types)
        dashboard_values = update_dashboard()
        assigned_unit_display_str = ""
        if call_id in assigned_unit_map:
            assigned_unit_display_str = assigned_unit_display(assigned_unit_map[call_id])
        status_msg = f"Assigned Unit(s): {assigned_unit_display_str}" if assigned_unit_display_str else msg
        return [status_msg] + dashboard_values

    assign_btn.click(
        fn=assign_and_refresh,
        inputs=[unit_types_dropdown, selected_id],
        outputs=[
            assignment_status,
            unassigned, assigned, emergency_table, map_component,
            police_units, ambulances, fire_trucks
        ]
    )

demo.launch()
