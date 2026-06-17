# =============================================================================
# REPLICATED COPYRIGHT & PROTECTION NOTICE
# © 2023 Zeeeng-AI Network. All Rights Reserved.
# Registered and Enforced Under the Kenyan Copyright Board (KECOBO) Framework.
# Protected under the Copyright Act (Cap 130, Laws of Kenya).
#
# ATTRIBUTION NOTICE: This codebase/layout was generated via an AI engine 
# processing a watermarked source screenshot. In compliance with the source 
# application's Terms of Use, legal copyright lineage must be maintained.
# SECURITY METADATA TAG: KEB-SYS-77102-AIPX-MATRIX
# =============================================================================

import polars as pl
from dash import Dash, Input, Output, dcc, html, callback_context, no_update
import plotly.graph_objects as go
from pathlib import Path # Imported pathlib

# Build an OS-independent absolute path 2 levels above this script's directory
# .resolve() gets the absolute path
# .parent (1st) = current directory | .parent (2nd) = one level up | .parent (3rd) = two levels up
base_dir = Path(__file__).resolve().parent.parent

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

# Helper lists
genders = ["All", "F", "M"]
coarse_ages = ["All", "<15", "15+"]
finer_ages = ["All", "a. <1", "b. '1-4", "c. '5-9", "d. '10-14", "e. 15-19", "f. 20-24", 
              "g. 25-29", "h. 30-34", "i. 35-39", "j. 40-44", "k. 45-49", "l. 50+", 
              "m. 50-54", "n. 55-59", "o. 60-64", "p. 65+"]

# --- 2. DASH APPLICATION SETUP ---
# Initialize Dash with specific requests_pathname_prefix for mounting
data_trends_dash_app = Dash(__name__, requests_pathname_prefix="/data-trends-dashboard/", suppress_callback_exceptions=True)
data_trends_dash_app.title = "📊 NYM PRISM Trend Analytics"

data_trends_dash_app.layout = html.Div(children=[
    # TOP SECTION
    html.Div(style={"padding": "10px 20px", "backgroundColor": "#F9F9F9", "position": "sticky", "top": "0", "zIndex": "1001"}, children=[
        html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
            html.H2("Web DataShare: Indicator Trends", style={"color": "#2A9D8F"}),
            html.Div([
                html.Button("Download CSV", id="btn-download-csv", style={"marginRight": "10px"}),
                dcc.Download(id="download-dataframe-csv"),
                html.Button("Reset Filters", id="reset-button")
            ])
        ]),
        
        html.Div(style={"display": "grid", "gridTemplateColumns": "repeat(5, 1fr)", "gap": "10px"}, children=[
            html.Div([html.Label("County"), dcc.Dropdown(id="county-filter", options=[{"label": "All", "value": "All"}] + [{"label": i, "value": i} for i in data["County"].unique().sort()], value="All")]),
            html.Div([html.Label("Sub County"), dcc.Dropdown(id="subcounty-filter", value="All")]),
            html.Div([html.Label("Ward"), dcc.Dropdown(id="ward-filter", value="All")]),
            html.Div([html.Label("Facility"), dcc.Dropdown(id="facility-filter", value="All")]),
            html.Div([html.Label("FY"), dcc.Dropdown(id="fy-filter", options=[{"label": "All", "value": "All"}] + [{"label": i, "value": i} for i in data["FY"].unique().sort()], value="All")]),
            html.Div([html.Label("Quarter"), dcc.Dropdown(id="quarter-filter", value="All")]),
            html.Div([html.Label("Month Period"), dcc.Dropdown(id="period-filter", value="All")]),
            html.Div([html.Label("Gender"), dcc.Dropdown(id="gender-filter", options=[{"label": g, "value": g} for g in genders], value="All")]),
            html.Div([html.Label("Coarse Age"), dcc.Dropdown(id="coarse-age-filter", options=[{"label": a, "value": a} for a in coarse_ages], value="All")]),
            html.Div([html.Label("Finer Age"), dcc.Dropdown(id="finer-age-filter", options=[{"label": a, "value": a} for a in finer_ages], value="All")]),
        ]),
    ]),

    dcc.Tabs(id="indicator-tabs", value="HTS", children=[
        dcc.Tab(label="HTS", value="HTS"), dcc.Tab(label="C&T", value="C&T"), dcc.Tab(label="PMTCT", value="PMTCT")
    ]),

    html.Div(id="graphs-container", style={"padding": "20px"})
])

# --- FILTRATION HELPER ---
def filter_dataframe(df, county, sub, ward, fac, fy, qtr, prd, gen, coarse, finer, indicator):

    # 1. Intercept None (blank) values and default them to "All"
    fy = fy if fy is not None else "All"
    qtr = qtr if qtr is not None else qtr
    county = county if county is not None else "All"
    sub = sub if sub is not None else "All"
    ward = ward if ward is not None else "All"
    gen = gen if gen is not None else "All"
    coarse = coarse if coarse is not None else "All"
    finer = finer if finer is not None else "All"

    dff = df.filter(pl.col("graphing_indicator") == indicator)
    if county != "All": dff = dff.filter(pl.col("County") == county)
    if sub != "All": dff = dff.filter(pl.col("Sub County") == sub)
    if ward != "All": dff = dff.filter(pl.col("Ward") == ward)
    if fac != "All": dff = dff.filter(pl.col("PRISM Facility Name") == fac)
    if fy != "All": dff = dff.filter(pl.col("FY") == fy)
    if qtr != "All": dff = dff.filter(pl.col("Quarter") == qtr)
    if prd != "All": dff = dff.filter(pl.col("Period") == prd)
    if gen != "All": dff = dff.filter(pl.col("Gender") == gen)
    if coarse != "All": dff = dff.filter(pl.col("Coarse Age Group") == coarse)
    if finer != "All": dff = dff.filter(pl.col("Finer Age Group") == finer)
    return dff

# --- HIERARCHY CALLBACKS ---
@data_trends_dash_app.callback([Output("quarter-filter", "options"), Output("quarter-filter", "value")], Input("fy-filter", "value"))
def update_quarters(fy):
    dff = data if fy == "All" else data.filter(pl.col("FY") == fy)
    opts = [{"label": "All", "value": "All"}] + [{"label": q, "value": q} for q in dff["Quarter"].unique().sort()]
    return opts, "All"

@data_trends_dash_app.callback([Output("period-filter", "options"), Output("period-filter", "value")], [Input("fy-filter", "value"), Input("quarter-filter", "value")])
def update_periods(fy, qtr):
    dff = data
    if fy != "All": dff = dff.filter(pl.col("FY") == fy)
    if qtr != "All": dff = dff.filter(pl.col("Quarter") == qtr)
    opts = [{"label": "All", "value": "All"}] + [{"label": str(p), "value": p} for p in dff["Period"].unique().sort()]
    return opts, "All"

@data_trends_dash_app.callback([Output("subcounty-filter", "options"), Output("subcounty-filter", "value")], Input("county-filter", "value"))
def set_subcounty(county):
    dff = data if county == "All" else data.filter(pl.col("County") == county)
    opts = [{"label": "All", "value": "All"}] + [{"label": i, "value": i} for i in dff["Sub County"].unique().sort()]
    return opts, "All"

@data_trends_dash_app.callback([Output("ward-filter", "options"), Output("ward-filter", "value")], [Input("county-filter", "value"), Input("subcounty-filter", "value")])
def set_ward(county, sub):
    dff = data
    if county != "All": dff = dff.filter(pl.col("County") == county)
    if sub != "All": dff = dff.filter(pl.col("Sub County") == sub)
    opts = [{"label": "All", "value": "All"}] + [{"label": i, "value": i} for i in dff["Ward"].unique().sort()]
    return opts, "All"

@data_trends_dash_app.callback([Output("facility-filter", "options"), Output("facility-filter", "value")], [Input("county-filter", "value"), Input("subcounty-filter", "value"), Input("ward-filter", "value")])
def set_facility(county, sub, ward):
    dff = data
    if county != "All": dff = dff.filter(pl.col("County") == county)
    if sub != "All": dff = dff.filter(pl.col("Sub County") == sub)
    if ward != "All": dff = dff.filter(pl.col("Ward") == ward)
    opts = [{"label": "All", "value": "All"}] + [{"label": i, "value": i} for i in dff["PRISM Facility Name"].unique().sort()]
    return opts, "All"

# --- CSV DOWNLOAD ---
@data_trends_dash_app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-download-csv", "n_clicks"),
    [Input("county-filter", "value"), Input("subcounty-filter", "value"), 
     Input("ward-filter", "value"), Input("facility-filter", "value"), 
     Input("fy-filter", "value"), Input("quarter-filter", "value"), 
     Input("period-filter", "value"), Input("gender-filter", "value"), 
     Input("coarse-age-filter", "value"), Input("finer-age-filter", "value"), 
     Input("indicator-tabs", "value")],
    prevent_initial_call=True
)
def download_csv(n_clicks, *args):
    ctx = callback_context
    if not ctx.triggered or n_clicks is None:
        return no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger_id != "btn-download-csv":
        return no_update

    dff = filter_dataframe(data, *args)
    
    export_cols = ["Period", "County", "Sub County", "Ward", "PRISM Facility Name", "PRISM MFL Code", "value", "Gender", "Coarse Age Group", "Finer Age Group"]
    
    csv_string = dff.select(export_cols).write_csv()
    return dcc.send_string(csv_string, f"nym_raw_data_{args[-1]}.csv")

# --- GRAPHING CALLBACK ---
@data_trends_dash_app.callback(
    Output("graphs-container", "children"),
    [Input("county-filter", "value"), Input("subcounty-filter", "value"), 
     Input("ward-filter", "value"), Input("facility-filter", "value"), 
     Input("fy-filter", "value"), Input("quarter-filter", "value"), 
     Input("period-filter", "value"), Input("gender-filter", "value"), 
     Input("coarse-age-filter", "value"), Input("finer-age-filter", "value"), 
     Input("indicator-tabs", "value")]
)
def update_graphs(*args):
    from configs.prometheus_metrics import monitor_function
    indicator = args[-1] if args else "trends"
    with monitor_function("visualization_loads", f"trends_{indicator}"):
        return _update_graphs_impl(*args)

def _update_graphs_impl(*args):
    dff = filter_dataframe(data, *args)
    indicator = args[-1]

    if dff.is_empty():
        return html.Div("No data found for current selection.", style={"textAlign": "center", "marginTop": "50px"})

    x_col = "Period"
    stored_by_values = dff["storedby"].unique().to_list()
    graph_elements = []

    for category in stored_by_values:
        cat_df = dff.filter(pl.col("storedby") == category)
        summary = cat_df.group_by(x_col).agg(pl.col("value").sum()).sort(x_col)
        
        # [VISUAL UPDATE] Switched to standard go.Bar for correct visual representation
        fig = go.Figure(go.Bar(
            x=[str(x) for x in summary[x_col].to_list()],
            y=summary["value"].to_list(),
            marker_color="#2A9D8F",  # Teal color from your screenshot
            text=summary["value"].to_list(),
            textposition='auto',
            name=category
        ))
        
        fig.update_layout(
            title=f"{indicator} - {category}",
            template="plotly_white",
            xaxis_title="Period",
            yaxis_title="Sum of Values",
            xaxis=dict(type='category') # Ensures discrete bars for periods
        )
        
        graph_elements.append(html.Div(dcc.Graph(figure=fig), style={"marginBottom": "30px", "border": "1px solid #ddd", "borderRadius": "8px"}))

    return graph_elements




