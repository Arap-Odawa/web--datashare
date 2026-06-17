import polars as pl
from dash import Dash, Input, Output, dcc, html, callback_context
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path # Imported pathlib

from configs.util_configs import get_settings

settings = get_settings()


reload1=settings.ENV_PROD_DEV

if reload1=="PROD":
    CHAT_APP_URL=f"http://{settings.DOMAIN_PORTLESS_PROD}:{settings.DEFAULT_PORT}"

elif reload1=="DEV":        
    CHAT_APP_URL=f"http://{settings.DOMAIN_CHAT_PORTLESS_DEV}:{settings.DEFAULT_PORT}"


else:
    # Fallback option so the variable ALWAYS exists
    print(f"Warning: Unknown environment '{reload1}'. Defaulting CHAT_APP_URL to localhost.")
    CHAT_APP_URL = f"http://127.0.0.1:{settings.DEFAULT_PORT}"

# --- CONFIGURATION ---
DEFAULT_FY = str(settings.DEFAULT_FY)
DEFAULT_QUARTER = settings.DEFAULT_QUARTER

# Centralized Indicator Configuration for automatic generic rendering across Tabs 1 & 6
TAB_1_INDICATORS = [
    {"id": "HTS_TST", "name": "HTS_TST"},
    {"id": "HTS_TST_POS", "name": "HTS_TST_POS"},
    {"id": "TX_NEW", "name": "TX_NEW"},
    {"id": "PrEP_NEW", "name": "PrEP_NEW"},
    {"id": "PrEP_CT", "name": "PrEP_CT"}, # Snapshot indicator
    {"id": "HTS_SELF", "name": "HTS_SELF"},
    {"id": "CXCA_SCRN", "name": "CXCA_SCRN"},
    {"id": "PMTCT_STAT_DEN", "name": "PMTCT_STAT_DEN"},
    {"id": "PMTCT_STAT_NUM", "name": "PMTCT_STAT_NUM"},
    {"id": "PMTCT_ART", "name": "PMTCT_ART"},
    {"id": "PMTCT_EID", "name": "PMTCT_EID"},
    {"id": "PMTCT_EID_<2MONTHS", "name": "PMTCT_EID_<2MONTHS"},
    {"id": "PMTCT_EID_2_12_MONTHS", "name": "PMTCT_EID 2_12_MONTHS"},


    {"id": "TB_STAT_DEN", "name": "TB_STAT_DEN"},
    {"id": "TB_STAT_NUM", "name": "TB_STAT_NUM"},
    {"id": "TB_ART", "name": "TB_ART"},
    {"id": "TB_PREV_DEN", "name": "TB_PREV_DEN"},
    {"id": "TB_PREV_NUM", "name": "TB_PREV_NUM"},
    {"id": "POST_RESPONSE", "name": "POST_RESPONSE"},
    {"id": "TX_CURR", "name": "TX_CURR"}, # Snapshot indicator
    {"id": "TX_TB", "name": "TX_TB"}, # Snapshot indicator
    {"id": "TX_PVLS_DEN", "name": "TX_PVLS_DEN"}, # Snapshot indicator
    {"id": "TX_PVLS_NUM", "name": "TX_PVLS_NUM"}, # Snapshot indicator

]

# Build an OS-independent absolute path 2 levels above this script's directory
# .resolve() gets the absolute path
# .parent (1st) = current directory | .parent (2nd) = one level up | .parent (3rd) = two levels up
base_dir = Path(__file__).resolve().parent.parent

# --- 1. DATA LOADING & PRE-PROCESSING ---
try:

    file_path = base_dir / "processed_dhis2_data.parquet"
    
    # (Optional Note: If you specifically wanted it 2 levels above the *execution* directory rather than the *script* directory, you would use: file_path = Path.cwd().parent.parent / "processed_dhis2_data.parquet")

    data = pl.read_parquet(file_path)
    data = data.with_columns([
        pl.col("picking_wards").cast(pl.String).str.strip_chars().alias("FY"),
        pl.col("Quarter").cast(pl.String).str.strip_chars(),
        pl.col("Period").cast(pl.String).str.strip_chars(),
        pl.col("value").cast(pl.Float64)
    ])
    if "Period" in data.columns:
        data = data.sort("Period")
except Exception as e:
    schema = {
        "Period": pl.String, "FY": pl.String, "Quarter": pl.String, "picking_wards": pl.String,
        "County": pl.String, "Sub County": pl.String, "Ward": pl.String, "PRISM Facility Name": pl.String,
        "Gender": pl.String, "Coarse Age Group": pl.String, "Finer Age Group": pl.String,
        "graphing_indicator": pl.String, "Indicator": pl.String, "value": pl.Float64,
        "Category": pl.String, "DATIM_Indicator": pl.String, "Testing Results": pl.String
    }
    data = pl.DataFrame(schema=schema)

try:
    file_path_tar = base_dir / "targets_data.parquet"
    target_data = pl.read_parquet(file_path_tar)
    
    for col in ["Gender", "Coarse Age Group", "Finer Age Group"]:
        if col not in target_data.columns:
            target_data = target_data.with_columns(pl.lit("All").alias(col))
            
    target_data = target_data.with_columns([
        pl.col("FY").cast(pl.String).str.strip_chars(),
        pl.col("Indicator").cast(pl.String).str.strip_chars(),
        pl.col("value").cast(pl.Float64).fill_null(0.0)
    ])
except Exception as e:
    target_schema = {
        "County": pl.String, "Sub County": pl.String, "Ward": pl.String, 
        "PRISM Facility Name": pl.String, "FY": pl.String, 
        "Gender": pl.String, "Coarse Age Group": pl.String, "Finer Age Group": pl.String,
        "Indicator": pl.String, "value": pl.Float64
    }
    target_data = pl.DataFrame(schema=target_schema)

genders = ["All", "F", "M"]
coarse_ages = ["All", "<15", "15+"]
finer_ages = ["All", "a. <1", "b. '1-4", "c. '5-9", "d. '10-14", "e. 15-19", "f. 20-24", 
              "g. 25-29", "h. 30-34", "i. 35-39", "j. 40-44", "k. 45-49", "l. 50+", 
              "m. 50-54", "n. 55-59", "o. 60-64", "p. 65+"]

color_palettes = {
    "Default (Image Style)": {"target": "#5b9bd5", "achieved": "#a50021", "line": "#ffffff", "bg": "#bcbcbc", "pos": "#ed7d31"},
    "Ocean": {"target": "#0077b6", "achieved": "#03045e", "line": "#00b4d8", "bg": "#f0f8ff", "pos": "#0096c7"},
    "Forest": {"target": "#52b788", "achieved": "#1b4332", "line": "#d8f3dc", "bg": "#e9f5e9", "pos": "#2d6a4f"}
}

SDP_MAPPING = {
    "IPD": {"base": ["1. PITC Modality: HTS_Inpatient_Services"], "apns_pos": ["IPD_APNS_Testing_Positive"], "apns_neg": ["IPD_APNS_Testing_Negative"]},
    "Malnutrition": {"base": ["3. PITC Modality: HTS_Malnutrition_Clinic"], "apns_pos": ["Malnutrition_APNS_Testing_Positive"], "apns_neg": ["Malnutrition_APNS_Testing_Negative"]},
    "Pediatric": {"base": ["2. PITC Modality: HTS_Pediatric_Clinic"], "apns_pos": ["MCH_<5yrs_APNS_Testing_Positive"], "apns_neg": ["MCH_<5yrs_APNS_Testing_Negative"]},
    "Other PITC": {"base": ["7. PITC Modality: Other PITC"], "apns_pos": ["Other_PITC_APNS_Testing_Positive"], "apns_neg": ["Other_PITC_APNS_Testing_Negative"]},
    "SNS": {"base": ["9. PITC Modality: HTS_SNS_Services"], "apns_pos": ["SNS_APNS_Testing_Positive"], "apns_neg": ["SNS_APNS_Testing_Negative"]},
    "VCT": {"base": ["8. PITC Modality: HTS_VCT_Services"], "apns_pos": ["VCT_APNS_Testing_Positive"], "apns_neg": ["VCT_APNS_Testing_Negative"]},
    "Emergency": {"base": ["6. HTS_Emergency", "1.b. PITC Modality: HTS_TST_Emergency_Services"], "apns_pos": ["Emergency_APNS_Testing_Positive"], "apns_neg": ["Emergency_APNS_Testing_Negative"]},
    "STI": {"base": ["5. PITC Modality: HTS_STI_Clinic", "9.b. PITC Modality: HTS_TST_STI_Services"], "apns_pos": ["HTS_TST_STI_APNS_Testing_Positive"], "apns_neg": ["HTS_TST_STI_APNS_Testing_Negative"]},
    "Post ANC1": {"base": ["4. PITC Modality: Post ANC1"], "apns_pos": [], "apns_neg": []},
    "VMMC": {"base": ["8.b. PITC Modality: HTS_VMMC_Services"], "apns_pos": [], "apns_neg": []}
}

data_review_dash_app = Dash(__name__, requests_pathname_prefix="/data-review-meeting-visuals/", suppress_callback_exceptions=True)
data_review_dash_app.title = "📊 Web DataShare : Data Review Meeting Visuals"

data_review_dash_app.layout = html.Div(children=[
    html.Div(style={"padding": "10px 20px", "backgroundColor": "#F9F9F9", "position": "sticky", "top": "0", "zIndex": "1001"}, children=[
        html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
            html.H2("Web DataShare : Data Review Meeting Visuals", style={"color": "#002060"}),
            html.Div([
                html.Label("Graph Color Palette: ", style={"fontWeight": "bold", "marginRight": "10px"}),
                dcc.Dropdown(
                    id="color-palette", options=[{"label": k, "value": k} for k in color_palettes.keys()], 
                    value="Default (Image Style)", clearable=False,
                    style={"width": "200px", "display": "inline-block", "verticalAlign": "middle", "marginRight": "15px"}
                ),
                html.Button("Reset Filters", id="reset-button",
                            style={"width": "200px", "display": "inline-block", "verticalAlign": "middle", "marginRight": "15px"}),
                # --- NEW AI CHAT BUTTON ---
                html.A(
                    html.Button("💬 Talk with DataShare Agentic AI", style={
                        "backgroundColor": "#002060", 
                        "color": "white", 
                        "border": "none", 
                        "padding": "8px 15px", 
                        "borderRadius": "5px", 
                        "cursor": "pointer",
                        "fontWeight": "bold"
                    }),
                    href=f"{CHAT_APP_URL}/chat_app/chat",
                    target="_blank",  # Opens the chat in a new tab
                    style={"textDecoration": "none"}
                )
                # --------------------------

            ])
        ]),
        
        # FILTERS
        html.Div(style={"display": "grid", "gridTemplateColumns": "repeat(5, 1fr)", "gap": "10px", "marginTop": "10px"}, children=[
            html.Div([html.Label("County"), dcc.Dropdown(id="county-filter", options=[{"label": "All", "value": "All"}] + [{"label": i, "value": i} for i in data["County"].unique().drop_nulls().sort()] if not data.is_empty() else [], value="All")]),
            html.Div([html.Label("Sub County"), dcc.Dropdown(id="subcounty-filter", value="All")]),
            html.Div([html.Label("Ward"), dcc.Dropdown(id="ward-filter", value="All")]),
            html.Div([html.Label("Facility"), dcc.Dropdown(id="facility-filter", value="All")]),
            html.Div([html.Label("FY"), dcc.Dropdown(id="fy-filter", options=[{"label": "All", "value": "All"}] + [{"label": i, "value": i} for i in data["FY"].unique().drop_nulls().sort()] if not data.is_empty() else [], value=DEFAULT_FY)]),
            html.Div([html.Label("Quarter"), dcc.Dropdown(id="quarter-filter", value=DEFAULT_QUARTER)]),
            html.Div([html.Label("Month Period"), dcc.Dropdown(id="period-filter", value="All")]),
            html.Div([html.Label("Gender"), dcc.Dropdown(id="gender-filter", options=[{"label": g, "value": g} for g in genders], value="All")]),
            html.Div([html.Label("Coarse Age"), dcc.Dropdown(id="coarse-age-filter", options=[{"label": a, "value": a} for a in coarse_ages], value="All")]),
            html.Div([html.Label("Finer Age"), dcc.Dropdown(id="finer-age-filter", options=[{"label": a, "value": a} for a in finer_ages], value="All")]),
        ]),
    ]),

    html.Div(style={"padding": "20px"}, children=[
        dcc.Tabs(id="tabs-menu", value="tab-1", children=[
            dcc.Tab(label="Performance vs Targets", value="tab-1"),
            dcc.Tab(label="Prevention Performance", value="tab-2"),
            dcc.Tab(label="PMTCT & Cervical Cancer Performance", value="tab-3"),
            dcc.Tab(label="TB Case Finding Performance", value="tab-4"),
            dcc.Tab(label="Care & Treatment", value="tab-5"),
            dcc.Tab(label="Ad hoc Graphs", value="tab-6"),
        ]),
        
        # Tab 6 Control (Visible only when Tab 6 is active)
        html.Div(id="tab-6-controls", style={"display": "none"}, children=[
            html.Label("Trend By: ", style={"fontWeight": "bold", "marginRight": "10px"}),
            dcc.RadioItems(
                id="trend-time-toggle",
                options=[{"label": " Monthly (Period) ", "value": "Period"}, {"label": " Quarterly ", "value": "Quarter"}],
                value="Period", inline=True, style={"display": "inline-block"}
            )
        ]),
        #html.Div(id="main-dashboard-content", style={"marginTop": "20px"})
        # THE MAIN CONTENT AREA (Where the error was occurring)
        html.Div(id="main-dashboard-content", style={"padding": "20px"})
    ])
])

@data_review_dash_app.callback(
    [Output("subcounty-filter", "options"), Output("subcounty-filter", "value"),
     Output("ward-filter", "options"), Output("ward-filter", "value"),
     Output("facility-filter", "options"), Output("facility-filter", "value")],
    [Input("county-filter", "value"), Input("subcounty-filter", "value"), Input("ward-filter", "value")]
)
def update_geography(county, sub, ward):

    ctx = callback_context
    trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # 1. Intercept None (blank) values and default them to "All"
    county = county if county is not None else "All"
    sub = sub if sub is not None else "All"
    ward = ward if ward is not None else "All"

    sub_opts, ward_opts, fac_opts = [{"label": "All", "value": "All"}], [{"label": "All", "value": "All"}], [{"label": "All", "value": "All"}]
    sub_val, ward_val, fac_val = sub, ward, "All"

    if not data.is_empty():
        c_data = data if county == "All" else data.filter(pl.col("County") == county)
        sub_opts += [{"label": i, "value": i} for i in c_data["Sub County"].unique().drop_nulls().sort()]
        if trigger == "county-filter": sub_val, ward_val = "All", "All"
        s_data = c_data if sub_val == "All" else c_data.filter(pl.col("Sub County") == sub_val)
        ward_opts += [{"label": i, "value": i} for i in s_data["Ward"].unique().drop_nulls().sort()]
        if trigger in ["county-filter", "subcounty-filter"]: ward_val = "All"
        w_data = s_data if ward_val == "All" else s_data.filter(pl.col("Ward") == ward_val)
        fac_opts += [{"label": i, "value": i} for i in w_data["PRISM Facility Name"].unique().drop_nulls().sort()]

    return sub_opts, sub_val, ward_opts, ward_val, fac_opts, fac_val

@data_review_dash_app.callback(
    [Output("quarter-filter", "options"), Output("quarter-filter", "value"),
     Output("period-filter", "options"), Output("period-filter", "value")],
    [Input("fy-filter", "value"), Input("quarter-filter", "value")]
)
def update_time_hierarchy(fy, qtr):
    ctx = callback_context
    trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None


    # 1. Intercept None (blank) values and default them to "All"
    fy = fy if fy is not None else "All"
    qtr = qtr if qtr is not None else DEFAULT_QUARTER

    q_opts, p_opts = [{"label": "All", "value": "All"}], [{"label": "All", "value": "All"}]
    q_val, p_val = qtr, "All"

    if not data.is_empty():
        fy_data = data if fy == "All" else data.filter(pl.col("FY") == fy)
        q_opts += [{"label": i, "value": i} for i in fy_data["Quarter"].unique().drop_nulls().sort()]
        if trigger == "fy-filter":
            q_val, p_val = "All", "All"
        q_data = fy_data if q_val == "All" else fy_data.filter(pl.col("Quarter") == q_val)
        p_opts += [{"label": i, "value": i} for i in q_data["Period"].unique().drop_nulls().sort()]

    return q_opts, q_val, p_opts, p_val


# --- CORE UI & DATA HELPERS ---

def get_status_color(achieved_val, annual_target, indicator_name, period_selected, quarter_selected):
    if annual_target <= 0: return "#bcbcbc" 
    current_indicators = ["TX_CURR", "TX_TB", "TX_PVLS", "PrEP_CT"]
    is_cumulative = not any(ind in indicator_name for ind in current_indicators)

    generic_month_map = {"10": 1, "11": 2, "12": 3, "01": 4, "02": 5, "03": 6, "04": 7, "05": 8, "06": 9, "07": 10, "08": 11, "09": 12}
    qtr_map = {"Q1": 3, "Q2": 6, "Q3": 9, "Q4": 12}
    months_elapsed = 12 

    if is_cumulative:
        if period_selected != "All" and len(str(period_selected)) >= 2:
            month_key = str(period_selected)[-2:]
            months_elapsed = generic_month_map.get(month_key, 12)
        elif quarter_selected != "All":
            months_elapsed = qtr_map.get(quarter_selected, 12)
        moving_target = (annual_target / 12) * months_elapsed
    else:
        moving_target = annual_target

    perc = (achieved_val / moving_target) * 100 if moving_target > 0 else 0

    if perc >= 95: return "#006400"
    elif perc >= 90: return "#00b050"
    elif perc >= 85: return "#92d050"
    elif perc >= 70: return "#ffff00"
    elif perc >= 60: return "#ffc000"
    else: return "#ff0000"
    
def build_legend():
    legend_items = [("Dark Green", ">95%", "#006400"), ("Green", "90-95%", "#00b050"), ("Light Green", "85-90%", "#92d050"), ("Yellow", "70-85%", "#ffff00"), ("Orange", "60-70%", "#ffc000"), ("Red", "<60%", "#ff0000")]
    return html.Div(style={"display": "flex", "gap": "15px", "justifyContent": "center", "marginBottom": "20px", "padding": "10px", "border": "1px solid #ddd", "borderRadius": "5px"}, children=[
        html.Div([html.Div(style={"width": "15px", "height": "15px", "backgroundColor": color, "display": "inline-block", "marginRight": "5px", "borderRadius": "3px"}), html.Span(f"{label} ({range_})", style={"fontSize": "12px", "fontWeight": "bold"})]) for label, range_, color in legend_items
    ])

def build_performance_ui(df, grouping_col, metric_name, colors, prd, qtr):
    tot_target, tot_ach = df["Target"].sum(), df["Achieved"].sum()
    tot_perc = round((tot_ach / tot_target) * 100) if tot_target > 0 else (100 if tot_ach > 0 else 0)

    table_rows = [html.Tr([html.Th(c, style={"border": "1px solid black", "padding": "10px"}) for c in [grouping_col, f"{metric_name} Target", f"{metric_name} Achieved", "% Achieved", "Status"]])]
    for row in df.iter_rows(named=True):
        status_color = get_status_color(row["Achieved"], row["Target"], metric_name, prd, qtr)
        status_div = html.Div(style={"height": "20px", "width": "20px", "backgroundColor": status_color, "borderRadius": "50%", "margin": "auto", "border": "1px solid black"})
        table_rows.append(html.Tr([
            html.Td(row[grouping_col], style={"border": "1px solid black", "padding": "8px"}),
            html.Td(f"{row['Target']:,.0f}", style={"border": "1px solid black", "padding": "8px", "textAlign": "center"}),
            html.Td(f"{row['Achieved']:,.0f}", style={"border": "1px solid black", "padding": "8px", "textAlign": "center"}),
            html.Td(f"{int(row['% Achieved'])}%", style={"border": "1px solid black", "padding": "8px", "textAlign": "center"}),
            html.Td(status_div, style={"border": "1px solid black", "padding": "8px"})
        ]))
    
    tot_status_color = get_status_color(tot_ach, tot_target, metric_name, prd, qtr)
    table_rows.append(html.Tr([
        html.Td(html.B("Total"), style={"border": "1px solid black", "padding": "8px"}),
        html.Td(html.B(f"{tot_target:,.0f}"), style={"border": "1px solid black", "padding": "8px", "textAlign": "center"}),
        html.Td(html.B(f"{tot_ach:,.0f}"), style={"border": "1px solid black", "padding": "8px", "textAlign": "center"}),
        html.Td(html.B(f"{int(tot_perc)}%"), style={"border": "1px solid black", "padding": "8px", "textAlign": "center"}),
        html.Td(html.Div(style={"height": "20px", "width": "20px", "backgroundColor": tot_status_color, "borderRadius": "50%", "margin": "auto", "border": "1px solid black"}), style={"border": "1px solid black", "padding": "8px"})
    ]))

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    x_labels = df[grouping_col].to_list()

    # ADDED: Formatting tags inside text= to ensure thousands are comma-separated and positioned nicely.
    fig.add_trace(go.Bar(x=x_labels, y=df["Target"].to_list(), name=f"{metric_name} Target", marker_color=colors["target"], marker_line_color="#a50021", marker_line_width=1, text=df["Target"].to_list(), textposition="auto"), secondary_y=False)
    fig.add_trace(go.Bar(x=x_labels, y=df["Achieved"].to_list(), name=f"{metric_name} Achieved", marker_color=colors["achieved"], text=df["Achieved"].to_list(), textposition="auto"), secondary_y=False)
    fig.add_trace(go.Scattergl(
        x=x_labels, y=df["% Achieved"].to_list(), name="% Achieved", mode="lines+markers+text", line=dict(color=colors["line"], width=3), 
        marker=dict(size=8, color=colors["line"]), text=[f"{int(p)}%" for p in df["% Achieved"].to_list()], textposition="top center", textfont=dict(color="black", size=14, family="Arial Black")), secondary_y=True)
    fig.update_layout(title=f"{metric_name} Performance vs Target", plot_bgcolor=colors["bg"], paper_bgcolor="#ffffff", barmode='group', legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5), margin=dict(l=20, r=20, t=40, b=20))
    fig.update_yaxes(showgrid=False)

    return html.Div(style={"display": "flex", "flexDirection": "row", "gap": "20px", "marginBottom": "40px"}, children=[
        html.Div(html.Table(table_rows, style={"borderCollapse": "collapse", "width": "100%", "fontSize": "15px"}), style={"flex": "1", "overflowX": "auto"}), 
        html.Div(dcc.Graph(figure=fig, style={"height": "400px"}), style={"flex": "1.5"})
    ])

def build_custom_ui(df, x_col, bar_cols, line_col, table_cols, title, colors):
    """Helper for building combo Table + Graph formats required in Tab 2 Drill-downs."""
    table_rows = [html.Tr([html.Th(c, style={"border": "1px solid black", "padding": "10px"}) for c in table_cols])]
    
    totals = {x_col: "Total"}
    for c in bar_cols: totals[c] = df[c].sum() if not df.is_empty() else 0
    if "Missed Linkage" in table_cols: totals["Missed Linkage"] = df["Missed Linkage"].sum() if not df.is_empty() else 0

    if "Testing Efficiency" in table_cols:
        totals["Testing Efficiency"] = round(totals.get("HTS_TST", 0) / totals.get("HTS_POS", 1), 1) if totals.get("HTS_POS", 0) > 0 else 0.0
    if "Positivity (%)" in table_cols:
        totals["Positivity (%)"] = round((totals.get("HTS_POS", 0) / totals.get("HTS_TST", 1)) * 100, 1) if totals.get("HTS_TST", 0) > 0 else 0.0
    if "Proxy Linkage (%)" in table_cols:
        totals["Proxy Linkage (%)"] = round((totals.get("TX_NEW", 0) / totals.get("HTS_POS", 1)) * 100, 1) if totals.get("HTS_POS", 0) > 0 else 0.0

    for row in df.iter_rows(named=True):
        tr = []
        for c in table_cols:
            val = row[c]
            if isinstance(val, float): val = f"{val:,.1f}"
            elif isinstance(val, (int, pl.Series)):
                try: val = f"{int(val):,}"
                except: val = str(val)
            tr.append(html.Td(val, style={"border": "1px solid black", "padding": "8px", "textAlign": "center" if c != x_col else "left"}))
        table_rows.append(html.Tr(tr))
        
    tr_tot = []
    for c in table_cols:
        val = totals.get(c, "")
        if isinstance(val, float): val = f"{val:,.1f}"
        elif isinstance(val, int) and c != x_col: val = f"{val:,}"
        tr_tot.append(html.Td(html.B(val), style={"border": "1px solid black", "padding": "8px", "textAlign": "center" if c != x_col else "left", "backgroundColor": "#f0f0f0"}))
    table_rows.append(html.Tr(tr_tot))
    
    fig = make_subplots(specs=[[{"secondary_y": True if line_col else False}]])
    x_labels = df[x_col].to_list()
    palette = [colors["target"], colors["achieved"], "#1f77b4", "#ff7f0e", "#2ca02c"] 
    
    for i, bc in enumerate(bar_cols):
        fig.add_trace(go.Bar(x=x_labels, y=df[bc].to_list(), name=bc, marker_color=palette[i % len(palette)], text=df[bc].to_list(), textposition="auto"), secondary_y=False)
        
    if line_col:
        line_color = colors["line"] if colors["line"] != "#ffffff" else "#000000"
        fig.add_trace(go.Scattergl(
            x=x_labels, y=df[line_col].to_list(), name=line_col, mode="lines+markers+text", 
            line=dict(color=line_color, width=3), marker=dict(size=8), 
            text=[f"{p}" for p in df[line_col].to_list()], textposition="top center", 
            textfont=dict(color="black", size=12, family="Arial Black")
        ), secondary_y=True)
        
    fig.update_layout(title=title, plot_bgcolor=colors["bg"], paper_bgcolor="#ffffff", barmode='group', legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5), margin=dict(l=20, r=20, t=40, b=20))
    fig.update_yaxes(showgrid=False)
    
    return html.Div(style={"display": "flex", "flexDirection": "row", "gap": "20px", "marginBottom": "40px", "alignItems": "flex-start"}, children=[
        html.Div(html.Table(table_rows, style={"borderCollapse": "collapse", "width": "100%", "fontSize": "14px"}), style={"flex": "1", "overflowX": "auto"}),
        html.Div(dcc.Graph(figure=fig, style={"height": "400px"}), style={"flex": "2"})
    ])

def extract_hts_sdp_metrics(df_sub):
    cat_filters = ["HTS", "PMTCT", "TB_CASCADE", "APNS_Testing_Negative_SDP", "APNS_Testing_Positive_SDP"]
    df_cat = df_sub.filter(pl.col("Category").is_in(cat_filters))
    results, total_apns_pos, total_apns_neg = [], 0, 0
    for sdp, mapping in SDP_MAPPING.items():
        base_pos = df_cat.filter((pl.col("DATIM_Indicator").is_in(mapping["base"])) & (pl.col("Testing Results").str.to_uppercase() == "POSITIVE"))["value"].sum() or 0
        base_neg = df_cat.filter((pl.col("DATIM_Indicator").is_in(mapping["base"])) & (pl.col("Testing Results").str.to_uppercase() == "NEGATIVE"))["value"].sum() or 0
        apns_pos = df_cat.filter(pl.col("DATIM_Indicator").is_in(mapping["apns_pos"]))["value"].sum() or 0
        apns_neg = df_cat.filter(pl.col("DATIM_Indicator").is_in(mapping["apns_neg"]))["value"].sum() or 0
        net_pos, net_neg = max(0, base_pos - apns_pos), max(0, base_neg - apns_neg)
        total_apns_pos += apns_pos
        total_apns_neg += apns_neg
        results.append({"SDP": sdp, "HTS_TST": net_pos + net_neg, "HTS_TST_POSITIVES": net_pos})
    
    pmtct_pos = df_cat.filter(pl.col("Indicator") == "d. PMTCT_STAT_Numerator_Newly_Tested_Positives")["value"].sum() or 0
    pmtct_neg = df_cat.filter(pl.col("Indicator") == "c. PMTCT_STAT_Numerator_Newly_Tested_Negatives")["value"].sum() or 0
    results.append({"SDP": "PMTCT", "HTS_TST": pmtct_pos + pmtct_neg, "HTS_TST_POSITIVES": pmtct_pos})

    tb_pos = df_cat.filter(pl.col("Indicator") == "c. TB_STAT_Numerator Newly Identified Positive")["value"].sum() or 0
    tb_neg = df_cat.filter(pl.col("Indicator") == "d. TB_STAT_Numerator Newly Tested_Negative")["value"].sum() or 0
    results.append({"SDP": "TB_CASCADE", "HTS_TST": tb_pos + tb_neg, "HTS_TST_POSITIVES": tb_pos})
    results.append({"SDP": "APNS Testing", "HTS_TST": total_apns_pos + total_apns_neg, "HTS_TST_POSITIVES": total_apns_pos})

    return results

# Generic fetchers to support automation across Tabs 1 & 6
def get_actual(df, ind_id, max_period=None):
    if ind_id == "HTS_TST":
        return sum(r["HTS_TST"] for r in extract_hts_sdp_metrics(df))
    elif ind_id == "HTS_TST_POS":
        return sum(r["HTS_TST_POSITIVES"] for r in extract_hts_sdp_metrics(df))
    elif ind_id == "PrEP_NEW":
        return df.filter(pl.col("Category").str.contains("PrEP") & pl.col("Indicator Category").str.contains("PREP_NEW|PrEP_NEW"))["value"].sum() or 0
    elif ind_id == "TX_NEW":
        return df.filter(pl.col("Indicator").str.to_uppercase().str.contains("TX_NEW") & pl.col("storedby").str.to_uppercase().str.contains("TX_NEW"))["value"].sum() or 0
    elif ind_id == "PrEP_CT":
        return df.filter(pl.col("Category").str.contains("PrEP") & pl.col("Indicator Category").str.contains("PrEP_CT") & pl.col("Period").str.contains(max_period))["value"].sum() or 0
    elif ind_id == "HTS_SELF":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("HTS_SELF") & pl.col("Indicator").str.contains("HTS_SELF_Directly_Assisted|HTS_SELF_Unassisted"))["value"].sum() or 0
    elif ind_id == "CXCA_SCRN":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("CXCA") & pl.col("DATIM_Indicator").str.contains("a. CXCA_SCRN_1st_Time_Screened_Negative|b. CXCA_SCRN_1st_Time_Screened_Positive|c. CXCA_SCRN_1st_Time_Screened_Suspected_Cancer|d. CXCA_SCRN_Rescreened_after_previous _negative_Negative|e. CXCA_SCRN_Rescreened_after_previous _negative_Positive|f. CXCA_SCRN_Rescreened_after_previous _negative_Suspected_Cancer|g. CXCA_SCRN_Post_treatment_follow_up_Negative|h. CXCA_SCRN_Post_treatment_follow_up_Positive|i. CXCA_SCRN_Post_treatment_follow_up_Suspected_Cancer"))["value"].sum() or 0
    elif ind_id == "PMTCT_STAT_DEN":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("PMTCT") & pl.col("Indicator").str.contains("a. PMTCT_STAT_Denominator"))["value"].sum() or 0
    elif ind_id == "PMTCT_STAT_NUM":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("PMTCT") & pl.col("Indicator").str.contains("b. PMTCT_STAT_Numerator_Known_Positives|c. PMTCT_STAT_Numerator_Newly_Tested_Negatives|d. PMTCT_STAT_Numerator_Newly_Tested_Positives"))["value"].sum() or 0
    elif ind_id == "PMTCT_ART":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("PMTCT") & pl.col("Indicator").str.contains("e. PMTCT_ART_New_On_ART|f. PMTCT_ART_Already_On_ART"))["value"].sum() or 0
    elif ind_id == "PMTCT_EID":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("PMTCT_HEI") & pl.col("Indicator").str.to_uppercase().str.contains("PMTCT_HEI") & pl.col("Dataelement Name").str.contains("Initial PCR samples collected only_PMTCT_HEI_xxxx|Second & Other PCR samples collected only_PMTCT_HEI_xxxx") & pl.col("Category Option Name").str.contains("0<=2Months|2-12Months"))["value"].sum() or 0
    elif ind_id == "PMTCT_EID_<2MONTHS":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("PMTCT_HEI") & pl.col("Indicator").str.to_uppercase().str.contains("PMTCT_HEI") & pl.col("Dataelement Name").str.contains("Initial PCR samples collected only_PMTCT_HEI_xxxx|Second & Other PCR samples collected only_PMTCT_HEI_xxxx") & pl.col("Category Option Name").str.contains("0<=2Months"))["value"].sum() or 0
    elif ind_id == "PMTCT_EID_2_12_MONTHS":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("PMTCT_HEI") & pl.col("Indicator").str.to_uppercase().str.contains("PMTCT_HEI") & pl.col("Dataelement Name").str.contains("Initial PCR samples collected only_PMTCT_HEI_xxxx|Second & Other PCR samples collected only_PMTCT_HEI_xxxx") & pl.col("Category Option Name").str.contains("2-12Months"))["value"].sum() or 0


    elif ind_id == "TB_STAT_DEN":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("TB_CASCADE") & pl.col("Indicator").str.contains("a. TB_STAT_Denominator Number of TB Cases"))["value"].sum() or 0
    elif ind_id == "TB_STAT_NUM":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("TB_CASCADE") & pl.col("Indicator").str.contains("b. TB_STAT_Numerator Known Positive|c. TB_STAT_Numerator Newly Identified Positive|d. TB_STAT_Numerator Newly Tested_Negative|i. TB_STAT_Numerator Recently Tested Negatives"))["value"].sum() or 0
    elif ind_id == "TB_ART":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("TB_CASCADE") & pl.col("Indicator").str.contains("f. TB_ART_Numerator Already on ART|g. TB_ART_Numerator Newly Started on ART"))["value"].sum() or 0
    elif ind_id == "TB_PREV_DEN":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("TB_PREV") & pl.col("Indicator").str.contains("TB_PREV") & pl.col("DATIM_Indicator").str.contains("TB_PREV_Denominator Previously Enrolled on ART|TB_PREV_Denominator Newly enrolled on ART"))["value"].sum() or 0
    elif ind_id == "TB_PREV_NUM":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("TB_PREV") & pl.col("Indicator").str.contains("TB_PREV") & pl.col("DATIM_Indicator").str.contains("TB_PREV_Numerator Newly enrolled on ART|TB_PREV_Numerator Previously Enrolled on ART"))["value"].sum() or 0
    elif ind_id == "POST_RESPONSE":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("GEND_GBV") & pl.col("Indicator").str.contains("GEND_GBV_Eligible_for_PEP|GEND_GBV_Physical_&_Emotional_Violence"))["value"].sum() or 0
    elif ind_id == "TX_CURR":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("TX_CURR") & pl.col("storedby").str.to_uppercase().str.contains("TX_CURR") & pl.col("Period").str.contains(max_period))["value"].sum() or 0
    elif ind_id == "TX_TB":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("TX_TB") & pl.col("Indicator").str.contains("TX_TB") & pl.col("DATIM_Indicator").str.contains("a. Screen Positive Newly Enrolled on ART|c. Total Screened Newly Enrolled on ART|b. Screen Positive Previously Enrolled on ART|d. Total Screened Previously Enrolled on ART") & pl.col("Period").str.contains(max_period))["value"].sum() or 0
    elif ind_id == "TX_PVLS_DEN":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("TX_PVLS") & pl.col("DATIM_Indicator").str.contains("g. TX_PVLS_Denominator: Routine_With_VL") & pl.col("Period").str.contains(max_period))["value"].sum() or 0
    elif ind_id == "TX_PVLS_NUM":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("TX_PVLS") & pl.col("DATIM_Indicator").str.contains("a. TX_PVLS_Numerator: Routine_Suppressed") & pl.col("Period").str.contains(max_period))["value"].sum() or 0


    return 0



def get_target(tgt_df, ind_id):
    tst_tgt_col = pl.col("Indicator").str.to_lowercase()
    if ind_id == "HTS_TST": return tgt_df.filter(tst_tgt_col.str.contains("hts_tst target|hts_tst_total target") & ~tst_tgt_col.str.contains("pos"))["value"].sum() or 0
    elif ind_id == "HTS_TST_POS": return tgt_df.filter(tst_tgt_col.str.contains("hts_tst_pos|hts_tstpositive"))["value"].sum() or 0
    elif ind_id == "TX_NEW": return tgt_df.filter(tst_tgt_col.str.contains("tx_new") & tst_tgt_col.str.contains("target"))["value"].sum() or 0
    elif ind_id == "PrEP_NEW": return tgt_df.filter(tst_tgt_col.str.contains("prep_new") & tst_tgt_col.str.contains("target"))["value"].sum() or 0
    elif ind_id == "PrEP_CT": return tgt_df.filter(pl.col("Indicator").str.contains("PrEP_CT_PrEP_CT Target"))["value"].sum() or 0
    elif ind_id == "HTS_SELF": return tgt_df.filter(pl.col("Indicator").str.contains("HTS_SELF_HTS_SELF Target"))["value"].sum() or 0
    elif ind_id == "CXCA_SCRN": return tgt_df.filter(pl.col("Indicator").str.contains("CXCA_SCRN_Number screened Target"))["value"].sum() or 0
    elif ind_id == "PMTCT_STAT_DEN": return tgt_df.filter(pl.col("Indicator").str.contains("PMTCT_STAT_Total Target"))["value"].sum() or 0
    elif ind_id == "PMTCT_STAT_NUM": return tgt_df.filter(pl.col("Indicator").str.contains("PMTCT_STAT_Total Target.1"))["value"].sum() or 0
    elif ind_id == "PMTCT_ART": return tgt_df.filter(pl.col("Indicator").str.contains("PMTCT_ART_Total Target"))["value"].sum() or 0
    elif ind_id == "PMTCT_EID": return tgt_df.filter(pl.col("Indicator").str.contains("PMTCT_EID_Total Target"))["value"].sum() or 0
    elif ind_id == "PMTCT_EID_<2MONTHS": return tgt_df.filter(pl.col("Indicator").str.contains("PMTCT_EID_Less than 2 months Target"))["value"].sum() or 0
    elif ind_id == "PMTCT_EID_2_12_MONTHS": return tgt_df.filter(pl.col("Indicator").str.contains("PMTCT_EID_2-12 months Target"))["value"].sum() or 0


    elif ind_id == "TB_STAT_DEN": return tgt_df.filter(pl.col("Indicator").str.contains("TB_STAT_Total Target"))["value"].sum() or 0
    elif ind_id == "TB_STAT_NUM": return tgt_df.filter(pl.col("Indicator").str.contains("TB_STAT_Total Target"))["value"].sum() or 0
    elif ind_id == "TB_ART": return tgt_df.filter(pl.col("Indicator").str.contains("TB_ART_Total Target"))["value"].sum() or 0
    elif ind_id == "TB_PREV_DEN": return tgt_df.filter(pl.col("Indicator").str.contains("TB_PREV_Denominator Target"))["value"].sum() or 0
    elif ind_id == "TB_PREV_NUM": return tgt_df.filter(pl.col("Indicator").str.contains("TB_PREV_Numerator Target"))["value"].sum() or 0
    elif ind_id == "POST_RESPONSE": return tgt_df.filter(pl.col("Indicator").str.contains("GEND_GBV_Total Target"))["value"].sum() or 0
    elif ind_id == "TX_CURR": return tgt_df.filter(pl.col("Indicator").str.contains("TX_CURR_Total_Total Target"))["value"].sum() or 0
    elif ind_id == "TX_TB": return tgt_df.filter(pl.col("Indicator").str.contains("TX_TB_Grand Total_Grand Total Target"))["value"].sum() or 0
    elif ind_id == "TX_PVLS_DEN": return tgt_df.filter(pl.col("Indicator").str.contains("TX_PVLS_Denominator_Total_Total Target"))["value"].sum() or 0
    elif ind_id == "TX_PVLS_NUM": return tgt_df.filter(pl.col("Indicator").str.contains("TX_PVLS_Numerator_Total_Total Target"))["value"].sum() or 0


    #elif ind_id == "CXCA_SCRN": return tgt_df.filter(tst_tgt_col.str.to_lowercase().str.contains("CXCA_SCRN_Number screened Target"))["value"].sum() or 0

    return 0

# --- MAIN GRAPHING CALLBACK ---
@data_review_dash_app.callback(
    [Output("main-dashboard-content", "children"),
     Output("tab-6-controls", "style")],
    [Input("tabs-menu", "value"), Input("county-filter", "value"), Input("subcounty-filter", "value"), 
     Input("ward-filter", "value"), Input("facility-filter", "value"), 
     Input("fy-filter", "value"), Input("quarter-filter", "value"), 
     Input("period-filter", "value"), Input("gender-filter", "value"), 
     Input("coarse-age-filter", "value"), Input("finer-age-filter", "value"),
     Input("color-palette", "value"), Input("trend-time-toggle", "value")]
)
def update_visuals(active_tab, county, sub, ward, fac, fy, qtr, prd, gen, coarse, finer, palette_name, trend_time_toggle):
    
    # Toggle Visibility logic for Tab 6
    t6_style = {"display": "block", "textAlign": "right", "marginBottom": "20px"} if active_tab == "tab-6" else {"display": "none"}


    # 1. Intercept None (blank) values and default them to "All"
    fy = fy if fy is not None else "All"
    qtr = qtr if qtr is not None else DEFAULT_QUARTER
    county = county if county is not None else "All"
    sub = sub if sub is not None else "All"
    ward = ward if ward is not None else "All"
    gen = gen if gen is not None else "All"
    coarse = coarse if coarse is not None else "All"
    finer = finer if finer is not None else "All"

    drilldown_col = "County"
    if county != "All": drilldown_col = "Sub County"
    if sub != "All": drilldown_col = "Ward"
    if ward != "All": drilldown_col = "PRISM Facility Name"

    # Filter Actuals -old that breaks with empty subcounty and quarter. This is fixed below. 05032026.
    dff = data
    if county != "All": dff = dff.filter(pl.col("County") == county)
    if sub != "All": dff = dff.filter(pl.col("Sub County") == sub)
    if ward != "All": dff = dff.filter(pl.col("Ward") == ward)
    if fac != "All": dff = dff.filter(pl.col("PRISM Facility Name") == fac)
    if fy != "All": dff = dff.filter(pl.col("FY") == fy)
    if qtr != "All": dff = dff.filter(pl.col("Quarter") == qtr)
    if prd != "All": dff = dff.filter(pl.col("Period") == prd)
    if gen != "All": dff = dff.filter(pl.col("Gender") == gen)

    # Target Filters
    dff_targets = target_data
    if county != "All": dff_targets = dff_targets.filter(pl.col("County") == county)
    if sub != "All": dff_targets = dff_targets.filter(pl.col("Sub County") == sub)
    if ward != "All": dff_targets = dff_targets.filter(pl.col("Ward") == ward)
    if fac != "All": dff_targets = dff_targets.filter(pl.col("PRISM Facility Name") == fac)
    if fy != "All": dff_targets = dff_targets.filter(pl.col("FY") == fy)
    
    if gen != "All": dff_targets = dff_targets.filter(pl.col("Gender") == gen)
    else: dff_targets = dff_targets.filter(pl.col("Gender") == "All")
    if coarse != "All": dff_targets = dff_targets.filter(pl.col("Coarse Age Group") == coarse)
    else: dff_targets = dff_targets.filter(pl.col("Coarse Age Group") == "All")
    if finer != "All": dff_targets = dff_targets.filter(pl.col("Finer Age Group") == finer)
    else: dff_targets = dff_targets.filter(pl.col("Finer Age Group") == "All")

    colors = color_palettes[palette_name]
    max_period = dff["Period"].drop_nulls().max() if not dff.is_empty() and "Period" in dff.columns else None

    # --- TAB 1: Performance vs Targets ---
    if active_tab == "tab-1":
        dff = dff.with_columns(pl.col(drilldown_col).cast(pl.String).str.strip_chars())
        dff_targets = dff_targets.with_columns(pl.col(drilldown_col).cast(pl.String).str.strip_chars())
        
        locs_actual = dff[drilldown_col].unique().drop_nulls().to_list() if not dff.is_empty() else []
        locs_target = dff_targets[drilldown_col].unique().drop_nulls().to_list() if not dff_targets.is_empty() else []
        unique_locations = sorted(list(set(locs_actual + locs_target)))
        
        # Initialize generic data storage for Tab 1
        tab1_data = {ind["id"]: [] for ind in TAB_1_INDICATORS}

        for loc in unique_locations:
            loc_df = dff.filter(pl.col(drilldown_col) == loc)
            loc_tgt_df = dff_targets.filter(pl.col(drilldown_col) == loc)
            
            # Cache HTS for the loop iteration to prevent double-calculating
            hts_sdp_results = extract_hts_sdp_metrics(loc_df)
            tst_ach = sum(r["HTS_TST"] for r in hts_sdp_results)
            pos_ach = sum(r["HTS_TST_POSITIVES"] for r in hts_sdp_results)
            
            for ind in TAB_1_INDICATORS:
                iid = ind["id"]
                tgt = get_target(loc_tgt_df, iid)
                if iid == "HTS_TST": ach = tst_ach
                elif iid == "HTS_TST_POS": ach = pos_ach
                else: ach = get_actual(loc_df, iid, max_period)
                tab1_data[iid].append({drilldown_col: loc, "Target": tgt, "Achieved": ach})
        
        def build_perc_df(data_list):
            _df = pl.DataFrame(data_list)
            if not _df.is_empty():
                return _df.with_columns(pl.when(pl.col("Target") == 0).then(pl.when(pl.col("Achieved") > 0).then(100.0).otherwise(0.0)).otherwise((pl.col("Achieved") / pl.col("Target")) * 100).round(0).alias("% Achieved"))
            return pl.DataFrame({drilldown_col: ["No Data"], "Target": [0], "Achieved": [0], "% Achieved": [0]})

        ui_elements = [build_legend()]
        for ind in TAB_1_INDICATORS:
            _df = build_perc_df(tab1_data[ind["id"]])
            ui_elements.append(build_performance_ui(_df, drilldown_col, ind["name"], colors, prd, qtr))
            ui_elements.append(html.Hr())

        return html.Div(children=ui_elements), t6_style

    # --- TAB 2: Prevention Performance ---
    elif active_tab == "tab-2":
        # 1. Existing Prevention Performance by SDP (HTS)
        try:
            results = extract_hts_sdp_metrics(dff)
            sdp_df = pl.DataFrame(results)
            sdp_df = sdp_df.filter(pl.col("HTS_TST") > 0).sort("HTS_TST", descending=True)
        except Exception as e:
            sdp_names = list(SDP_MAPPING.keys()) + ["PMTCT", "TB_CASCADE", "APNS Testing"]
            sdp_df = pl.DataFrame({"SDP": sdp_names, "HTS_TST": [0]*len(sdp_names), "HTS_TST_POSITIVES": [0]*len(sdp_names)})

        sdp_df = sdp_df.with_columns(pl.when(pl.col("HTS_TST") > 0).then((pl.col("HTS_TST_POSITIVES") / pl.col("HTS_TST")) * 100).otherwise(0.0).round(1).alias("Positivity"))

        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        x_sdps = sdp_df["SDP"].to_list()
        fig2.add_trace(go.Bar(x=x_sdps, y=sdp_df["HTS_TST"].to_list(), name="HTS_TST", marker_color=colors["target"], textposition="auto"), secondary_y=False)
        fig2.add_trace(go.Bar(x=x_sdps, y=sdp_df["HTS_TST_POSITIVES"].to_list(), name="HTS_TST_POSITIVES", marker_color=colors["pos"], textposition="auto"), secondary_y=False)
        fig2.add_trace(go.Scattergl(x=x_sdps, y=sdp_df["Positivity"].to_list(), name="Positivity %", mode="lines+markers+text", line=dict(color=colors["line"], width=3), text=[f"{p}%" for p in sdp_df["Positivity"].to_list()], textposition="top center", textfont=dict(color="black", size=12)), secondary_y=True)
        fig2.update_layout(title="HTS Performance Disaggregated by SDP", plot_bgcolor=colors["bg"], paper_bgcolor="#ffffff", barmode='group', legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
        fig2.update_yaxes(showgrid=False)
        sdp_graph = html.Div(dcc.Graph(figure=fig2, style={"height": "600px"}), style={"width": "100%"})

        # --- NEW: Build the Table for SDPs --- Added 08032026
        sdp_table_cols = ["SDP", "HTS_TST", "HTS_TST_POSITIVES", "Positivity (%)"]
        sdp_table_rows = [html.Tr([html.Th(c, style={"border": "1px solid black", "padding": "10px"}) for c in sdp_table_cols])]
        
        tot_hts = sdp_df["HTS_TST"].sum() if not sdp_df.is_empty() else 0
        tot_pos = sdp_df["HTS_TST_POSITIVES"].sum() if not sdp_df.is_empty() else 0
        tot_perc = round((tot_pos / tot_hts) * 100, 1) if tot_hts > 0 else 0.0

        for row in sdp_df.iter_rows(named=True):
            sdp_table_rows.append(html.Tr([
                html.Td(row["SDP"], style={"border": "1px solid black", "padding": "8px", "textAlign": "left"}),
                html.Td(f"{int(row['HTS_TST']):,}", style={"border": "1px solid black", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{int(row['HTS_TST_POSITIVES']):,}", style={"border": "1px solid black", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{row['Positivity']:.1f}", style={"border": "1px solid black", "padding": "8px", "textAlign": "center"})
            ]))

        sdp_table_rows.append(html.Tr([
            html.Td(html.B("Total"), style={"border": "1px solid black", "padding": "8px", "textAlign": "left", "backgroundColor": "#f0f0f0"}),
            html.Td(html.B(f"{int(tot_hts):,}"), style={"border": "1px solid black", "padding": "8px", "textAlign": "center", "backgroundColor": "#f0f0f0"}),
            html.Td(html.B(f"{int(tot_pos):,}"), style={"border": "1px solid black", "padding": "8px", "textAlign": "center", "backgroundColor": "#f0f0f0"}),
            html.Td(html.B(f"{tot_perc:.1f}"), style={"border": "1px solid black", "padding": "8px", "textAlign": "center", "backgroundColor": "#f0f0f0"})
        ]))

        sdp_table_ui = html.Div(
            html.Table(sdp_table_rows, style={"borderCollapse": "collapse", "width": "100%", "fontSize": "14px", "marginBottom": "20px"}),
            style={"width": "100%", "overflowX": "auto"}
        )
        # --- END NEW TABLE ---


        # 2. Lower Org Unit Breakdowns
        org_hts_data = []
        unique_orgs = dff[drilldown_col].unique().drop_nulls().to_list() if not dff.is_empty() else []
        for org in unique_orgs:
            org_df = dff.filter(pl.col(drilldown_col) == org)
            
            sdp_res = extract_hts_sdp_metrics(org_df)
            tst = sum(r["HTS_TST"] for r in sdp_res)
            pos = sum(r["HTS_TST_POSITIVES"] for r in sdp_res)
            tx_new = get_actual(org_df, "TX_NEW")
            prep_new = get_actual(org_df, "PrEP_NEW")
            prep_ct = get_actual(org_df, "PrEP_CT", max_period)
            
            org_hts_data.append({drilldown_col: org, "HTS_TST": float(tst), "HTS_POS": float(pos), "TX_NEW": float(tx_new), "PrEP_NEW": float(prep_new), "PrEP_CT": float(prep_ct)})
            
        schema_map = {drilldown_col: pl.String, "HTS_TST": pl.Float64, "HTS_POS": pl.Float64, "TX_NEW": pl.Float64, "PrEP_NEW": pl.Float64, "PrEP_CT": pl.Float64}
        df_org = pl.DataFrame(org_hts_data, schema=schema_map) if org_hts_data else pl.DataFrame({drilldown_col: [], "HTS_TST": [], "HTS_POS": [], "TX_NEW": [], "PrEP_NEW": [], "PrEP_CT": []}, schema=schema_map)
            
        df_org = df_org.with_columns([
            pl.when(pl.col("HTS_POS") > 0).then(pl.col("HTS_TST") / pl.col("HTS_POS")).otherwise(0.0).round(1).alias("Testing Efficiency"),
            pl.when(pl.col("HTS_TST") > 0).then((pl.col("HTS_POS") / pl.col("HTS_TST")) * 100).otherwise(0.0).round(1).alias("Positivity (%)"),
            pl.when(pl.col("HTS_POS") > 0).then((pl.col("TX_NEW") / pl.col("HTS_POS")) * 100).otherwise(0.0).round(1).alias("Proxy Linkage (%)"),
            (pl.col("HTS_POS") - pl.col("TX_NEW")).alias("Missed Linkage")
        ])
        
        ui_hts_org = build_custom_ui(df_org, drilldown_col, ["HTS_TST", "HTS_POS"], "Positivity (%)", [drilldown_col, "HTS_TST", "HTS_POS", "Testing Efficiency", "Positivity (%)"], f"Testing Efficiency & Positivity by {drilldown_col}", colors)
        ui_tx_org = build_custom_ui(df_org, drilldown_col, ["HTS_POS", "TX_NEW"], "Proxy Linkage (%)", [drilldown_col, "HTS_POS", "TX_NEW", "Proxy Linkage (%)", "Missed Linkage"], f"Linkage (TX_NEW) by {drilldown_col}", colors)
        ui_prep_org = build_custom_ui(df_org, drilldown_col, ["PrEP_NEW", "PrEP_CT"], None, [drilldown_col, "PrEP_NEW", "PrEP_CT"], f"PrEP Delivery by {drilldown_col}", colors)

        return html.Div(children=[
            html.H3("Prevention Performance by SDP", style={"textAlign": "center"}), sdp_graph, sdp_table_ui, html.Hr(),
            html.H3(f"HTS Cascade by {drilldown_col}", style={"textAlign": "center"}), ui_hts_org, html.Hr(),
            html.H3(f"Linkage Cascade by {drilldown_col}", style={"textAlign": "center"}), ui_tx_org, html.Hr(),
            html.H3(f"PrEP Cascade by {drilldown_col}", style={"textAlign": "center"}), ui_prep_org
        ]), t6_style

    # --- TAB 6: Automatic Trend Graphs ---
    elif active_tab == "tab-6":
        time_buckets = dff[trend_time_toggle].unique().drop_nulls().sort().to_list() if not dff.is_empty() and trend_time_toggle in dff.columns else []
        
        trend_data = {ind["id"]: [] for ind in TAB_1_INDICATORS}
        trend_data["Time"] = time_buckets
        
        for tb in time_buckets:
            tb_df = dff.filter(pl.col(trend_time_toggle) == tb)
            tb_max_period = tb_df["Period"].drop_nulls().max() if not tb_df.is_empty() and "Period" in tb_df.columns else None
            
            # Cache HTS
            hts_sdp_results = extract_hts_sdp_metrics(tb_df)
            tst_ach = sum(r["HTS_TST"] for r in hts_sdp_results)
            pos_ach = sum(r["HTS_TST_POSITIVES"] for r in hts_sdp_results)
            
            for ind in TAB_1_INDICATORS:
                iid = ind["id"]
                if iid == "HTS_TST": ach = tst_ach
                elif iid == "HTS_TST_POS": ach = pos_ach
                else: ach = get_actual(tb_df, iid, tb_max_period)
                trend_data[iid].append(ach)

        trend_graphs = []
        for ind in TAB_1_INDICATORS:
            iid = ind["id"]
            fig = go.Figure()
            fig.add_trace(go.Scattergl(
                x=trend_data["Time"], y=trend_data[iid], mode="lines+markers+text", 
                name=ind["name"], text=[f"{val:,.0f}" if isinstance(val, (int, float)) else val for val in trend_data[iid]],
                textposition="top center", line=dict(color=colors["achieved"], width=3), marker=dict(size=8, color=colors["target"])
            ))
            fig.update_layout(title=f"{ind['name']} Trend by {trend_time_toggle}", plot_bgcolor=colors["bg"], paper_bgcolor="#ffffff", showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
            trend_graphs.append(html.Div(dcc.Graph(figure=fig), style={"width": "48%", "display": "inline-block", "margin": "1%"}))

        tab_content = html.Div([
            html.H3(f"Performance Trends (Aggregated by {trend_time_toggle})", style={"textAlign": "center"}),
            html.Div(trend_graphs, id="trend-graphs-container", style={"display": "flex", "flexWrap": "wrap", "justifyContent": "center"}),
            html.Hr(),
            html.Div(id="other-visuals-container", children=[
                html.H4("Additional Custom Visuals Container", style={"textAlign": "center", "color": "#888", "padding": "50px", "border": "2px dashed #ccc", "marginTop": "20px"})
            ])
        ])
        return tab_content, t6_style

    else:
        return html.Div(html.H3(f"Content for {active_tab} is under construction.", style={"textAlign": "center", "marginTop": "50px"})), t6_style









