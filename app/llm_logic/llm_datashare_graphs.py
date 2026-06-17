import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from drm_viz.data_review_viz import data, target_data, color_palettes, get_actual, get_target



# Helper to generate Graph JSON using your existing logic
def generate_chat_graph_json(indicator_id: str, county: str = "All"):
    """
    Re-uses your LazyFrame logic to fetch data and build a Plotly fig.
    Returns the JSON string of the graph.
    """
    colors = color_palettes["Default (Image Style)"]
    
    # 1. Filter Data
    dff_chat = data
    dff_chat_tgt = target_data
    
    if county != "All":
        dff_chat = dff_chat.filter(pl.col("County") == county)
        dff_chat_tgt = dff_chat_tgt.filter(pl.col("County") == county)
        
    dff_chat = dff_chat.collect()
    dff_chat_tgt = dff_chat_tgt.collect()
    
    # 2. Extract specific indicator data
    drilldown_col = "County" if county == "All" else "Sub County"
    locs = dff_chat[drilldown_col].unique().drop_nulls().to_list() if not dff_chat.is_empty() else []
    
    chart_data = []
    for loc in locs:
        loc_df = dff_chat.filter(pl.col(drilldown_col) == loc)
        loc_tgt_df = dff_chat_tgt.filter(pl.col(drilldown_col) == loc)
        
        ach = get_actual(loc_df, indicator_id, max_period=None)
        tgt = get_target(loc_tgt_df, indicator_id)
        chart_data.append({drilldown_col: loc, "Target": tgt, "Achieved": ach})
    
    _df = pl.DataFrame(chart_data)
    if _df.is_empty():
        return None
        
    _df = _df.with_columns(
        pl.when(pl.col("Target") == 0)
        .then(pl.when(pl.col("Achieved") > 0).then(100.0).otherwise(0.0))
        .otherwise((pl.col("Achieved") / pl.col("Target")) * 100).round(0).alias("% Achieved")
    )
    
    # 3. Build Figure (Mimicking build_performance_ui layout)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    x_labels = _df[drilldown_col].to_list()

    fig.add_trace(go.Bar(x=x_labels, y=_df["Target"].to_list(), name=f"{indicator_id} Target", marker_color=colors["target"]), secondary_y=False)
    fig.add_trace(go.Bar(x=x_labels, y=_df["Achieved"].to_list(), name=f"{indicator_id} Achieved", marker_color=colors["achieved"]), secondary_y=False)
    
    fig.update_layout(title=f"{indicator_id} Performance for {county}", plot_bgcolor=colors["bg"], paper_bgcolor="#ffffff", barmode='group')
    
    # Convert figure to JSON string for the frontend to render natively
    return pio.to_json(fig)



# --- PLOTLY JSON WRAPPERS ---

def build_performance_fig_json(df: pl.DataFrame, grouping_col: str, metric_name: str, colors: dict) -> str:
    """Extracts the Plotly figure logic from build_performance_ui and returns JSON."""
    if df.is_empty():
        return None
        
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    x_labels = df[grouping_col].to_list()

    fig.add_trace(go.Bar(x=x_labels, y=df["Target"].to_list(), name=f"{metric_name} Target", 
                         marker_color=colors["target"], marker_line_color="#a50021", 
                         marker_line_width=1, text=df["Target"].to_list(), textposition="auto"), secondary_y=False)
    
    fig.add_trace(go.Bar(x=x_labels, y=df["Achieved"].to_list(), name=f"{metric_name} Achieved", 
                         marker_color=colors["achieved"], text=df["Achieved"].to_list(), textposition="auto"), secondary_y=False)
    
    fig.add_trace(go.Scattergl(
        x=x_labels, y=df["% Achieved"].to_list(), name="% Achieved", mode="lines+markers+text", 
        line=dict(color=colors["line"], width=3), marker=dict(size=8, color=colors["line"]), 
        text=[f"{int(p)}%" for p in df["% Achieved"].to_list()], textposition="top center", 
        textfont=dict(color="black", size=14, family="Arial Black")), secondary_y=True)
        
    fig.update_layout(title=f"{metric_name} Performance by {grouping_col}", 
                      plot_bgcolor=colors["bg"], paper_bgcolor="#ffffff", barmode='group', 
                      legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5), 
                      margin=dict(l=20, r=20, t=40, b=20))
    fig.update_yaxes(showgrid=False)
    
    return pio.to_json(fig)



def build_custom_fig_json(df: pl.DataFrame, x_col: str, bar_cols: list, line_col: str, title: str, colors: dict) -> str:
    """Extracts the Plotly figure logic from build_custom_ui and returns JSON."""
    if df.is_empty():
        return None

    fig = make_subplots(specs=[[{"secondary_y": True if line_col else False}]])
    x_labels = df[x_col].to_list()
    palette = [colors["target"], colors["achieved"], "#1f77b4", "#ff7f0e", "#2ca02c"] 
    
    for i, bc in enumerate(bar_cols):
        fig.add_trace(go.Bar(x=x_labels, y=df[bc].to_list(), name=bc, 
                             marker_color=palette[i % len(palette)], text=df[bc].to_list(), textposition="auto"), secondary_y=False)
        
    if line_col:
        line_color = colors["line"] if colors["line"] != "#ffffff" else "#000000"
        fig.add_trace(go.Scattergl(
            x=x_labels, y=df[line_col].to_list(), name=line_col, mode="lines+markers+text", 
            line=dict(color=line_color, width=3), marker=dict(size=8), 
            text=[f"{p}" for p in df[line_col].to_list()], textposition="top center", 
            textfont=dict(color="black", size=12, family="Arial Black")
        ), secondary_y=True)
        
    fig.update_layout(title=title, plot_bgcolor=colors["bg"], paper_bgcolor="#ffffff", barmode='group', 
                      legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5), 
                      margin=dict(l=20, r=20, t=40, b=20))
    fig.update_yaxes(showgrid=False)
    
    return pio.to_json(fig)
























