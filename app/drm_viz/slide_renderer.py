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
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import html, dcc

from configs.util_configs import get_settings

settings = get_settings()

# --- CONFIGURATION ---
DEFAULT_FY = str(settings.DEFAULT_FY)
DEFAULT_QUARTER = settings.DEFAULT_QUARTER

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

def render_pptx_slide(slide_id, dff, dff_targets, colors, max_period, get_actual_fn, get_target_fn, extract_hts_sdp_metrics_fn,
                      county="All", sub="All", ward="All", fac="All"):
    # -----------------------------------------------------------------------
    # DYNAMIC LEVEL RESOLUTION
    # Determine the parent column and child column to iterate over based on
    # which filter is currently active in the dashboard.
    #
    # Level map:
    #   county == "All"                       -> child = County
    #   county selected, sub == "All"         -> child = Sub County
    #   sub selected, ward == "All"           -> child = Ward
    #   ward selected (any)                   -> child = PRISM Facility Name
    # -----------------------------------------------------------------------
    if county == "All":
        _child_col  = "County"
        _parent_col = "County"
        _child_label = "County"
    elif sub == "All":
        _child_col  = "Sub County"
        _parent_col = "County"
        _child_label = "Sub_County"
    elif ward == "All":
        _child_col  = "Ward"
        _parent_col = "Sub County"
        _child_label = "Ward"
    else:
        _child_col  = "PRISM Facility Name"
        _parent_col = "Ward"
        _child_label = "Facility"


    # --- HELPER FUNCTIONS FOR CHARTS & TABLES ---
    def make_section_slide(title, subtitle=""):
        return html.Div(style={
            "padding": "100px 50px", "textAlign": "center", "backgroundColor": "#002060",
            "color": "white", "borderRadius": "10px", "marginTop": "20px", "boxShadow": "0 4px 6px rgba(0,0,0,0.1)"
        }, children=[
            html.H1(title, style={"fontSize": "48px", "fontWeight": "bold"}),
            html.P(subtitle, style={"fontSize": "24px", "color": "#d0d0d0", "marginTop": "20px"})
        ])

    def make_narrative_slide(title, bullets):
        rows = [html.Li(b, style={"fontSize": "18px", "marginBottom": "12px", "color": "#333"}) for b in bullets]
        return html.Div(style={
            "padding": "30px", "backgroundColor": "#f9f9f9", "borderRadius": "10px",
            "border": "1px solid #ddd", "marginTop": "20px"
        }, children=[
            html.H3(title, style={"color": "#002060", "borderBottom": "2px solid #002060", "paddingBottom": "10px", "marginBottom": "20px"}),
            html.Ul(rows, style={"lineHeight": "1.6", "paddingLeft": "20px"})
        ])

    # --- COLOUR HELPER (for status dots and top/bottom 10 charts) ---
    def _status_color(pct):
        if pct >= 95:   return "#006400"
        elif pct >= 90: return "#00b050"
        elif pct >= 85: return "#92d050"
        elif pct >= 70: return "#ffff00"
        elif pct >= 60: return "#ffc000"
        else:           return "#ff0000"

    def get_cell_style(pct):
        bg = _status_color(pct)
        tc = "white" if bg in ["#006400", "#ff0000", "#00b050"] else "black"
        return {"backgroundColor": bg, "color": tc, "fontWeight": "bold", "textAlign": "center", "border": "1px solid #ddd", "padding": "8px"}

    def get_positivity_cell_style(pct):
        if pct <= 0.5:   bg = "#006400"
        elif pct <= 1.0: bg = "#00b050"
        elif pct <= 2.0: bg = "#92d050"
        elif pct <= 3.5: bg = "#ffff00"
        elif pct <= 5.0: bg = "#ffc000"
        else:            bg = "#ff0000"
        tc = "white" if bg in ["#006400", "#ff0000", "#00b050"] else "black"
        return {"backgroundColor": bg, "color": tc, "fontWeight": "bold", "textAlign": "center", "border": "1px solid #ddd", "padding": "8px"}

    def make_top_bottom_10(indicator_id, indicator_label, is_top):
        """Horizontal bar chart + ranked table of Top or Bottom 10 facilities by % achievement vs target."""
        facilities = dff["PRISM Facility Name"].unique().drop_nulls().to_list() if not dff.is_empty() else []
        fac_data = []
        for f in facilities:
            f_df  = dff.filter(pl.col("PRISM Facility Name") == f)
            f_tdf = dff_targets.filter(pl.col("PRISM Facility Name") == f)
            tgt = get_target_fn(f_tdf, indicator_id)
            ach = get_actual_fn(f_df, indicator_id, max_period)
            pct = round((ach / tgt) * 100, 1) if tgt > 0 else (100.0 if ach > 0 else 0.0)
            fac_data.append({"Facility": f, "Target": tgt, "Achieved": ach, "% Achieved": pct})
        if not fac_data:
            return html.Div(html.H3("No data available for current filters.", style={"textAlign": "center", "marginTop": "50px"}))
        df_f = pl.DataFrame(fac_data)
        df_f = df_f.filter((pl.col("Target") > 0) | (pl.col("Achieved") > 0))
        if df_f.is_empty():
            return html.Div(html.H3("No facility data with targets or achievements.", style={"textAlign": "center", "marginTop": "50px"}))
        df_ranked = df_f.sort("% Achieved", descending=is_top).head(10)
        label = f"{indicator_label} — {'Top' if is_top else 'Bottom'} 10 Facilities by % Achievement vs Target"
        bar_colors_list = [_status_color(p) for p in df_ranked["% Achieved"].to_list()]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_ranked["% Achieved"].to_list(), y=df_ranked["Facility"].to_list(),
            orientation="h", marker_color=bar_colors_list,
            text=[f"{v:.1f}%" for v in df_ranked["% Achieved"].to_list()],
            textposition="auto", textfont=dict(size=13, color="black")
        ))
        fig.update_layout(
            title=dict(text=label, font=dict(size=16, color="#002060")),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            xaxis=dict(title="% Achievement vs Target", tickfont=dict(size=13)),
            yaxis=dict(tickfont=dict(size=12), autorange="reversed"),
            margin=dict(l=230, r=40, t=70, b=60)
        )
        t_rows = [html.Tr([
            html.Th(c, style={"backgroundColor": "#002060", "color": "white", "padding": "8px 10px", "border": "1px solid #002060"})
            for c in ["Rank", "Facility", "Target", "Achieved", "% Achieved", "Status"]
        ])]
        for rank, row in enumerate(df_ranked.iter_rows(named=True), 1):
            sc = _status_color(row["% Achieved"])
            st = html.Div(style={"height": "18px", "width": "18px", "backgroundColor": sc,
                                  "borderRadius": "50%", "margin": "auto", "border": "1px solid #aaa"})
            t_rows.append(html.Tr([
                html.Td(str(rank),                  style={"border": "1px solid #ddd", "padding": "7px 10px", "textAlign": "center"}),
                html.Td(row["Facility"],             style={"border": "1px solid #ddd", "padding": "7px 10px"}),
                html.Td(f"{row['Target']:,.0f}",     style={"border": "1px solid #ddd", "padding": "7px 10px", "textAlign": "center"}),
                html.Td(f"{row['Achieved']:,.0f}",   style={"border": "1px solid #ddd", "padding": "7px 10px", "textAlign": "center"}),
                html.Td(f"{row['% Achieved']:.1f}%", style={"border": "1px solid #ddd", "padding": "7px 10px", "textAlign": "center", "fontWeight": "bold"}),
                html.Td(st,                          style={"border": "1px solid #ddd", "padding": "7px 10px"}),
            ]))
        return html.Div([
            html.Div(dcc.Graph(figure=fig, style={"height": "66vh"}), style={"width": "95%", "margin": "0 auto"}),
            html.Div(html.Table(t_rows, style={"borderCollapse": "collapse", "width": "100%", "fontSize": "13px"}),
                     style={"width": "95%", "margin": "20px auto", "overflowX": "auto"})
        ])

    def make_target_achieved_chart(title, ind_id):
        tgt = get_target_fn(dff_targets, ind_id)
        ach = get_actual_fn(dff, ind_id, max_period)
        pct = round((ach / tgt) * 100, 1) if tgt > 0 else (100.0 if ach > 0 else 0.0)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["Target"], y=[tgt], name="Target", marker_color=colors["target"],
            text=[f"{tgt:,.0f}"], textposition="auto", textfont=dict(size=14, color="black")
        ))
        fig.add_trace(go.Bar(
            x=["Achieved"], y=[ach], name="Achieved", marker_color=colors["achieved"],
            text=[f"{ach:,.0f}"], textposition="auto", textfont=dict(size=14, color="black")
        ))
        fig.update_layout(
            title=dict(text=title, font=dict(size=18, color="#002060")),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", barmode="group",
            margin=dict(l=60, r=40, t=60, b=60),
            xaxis=dict(tickfont=dict(size=14)),
            yaxis=dict(tickfont=dict(size=14), showgrid=True, gridcolor="#e0e0e0", tickformat=",.0f")
        )
        return html.Div([
            html.Div(dcc.Graph(figure=fig, style={"height": "66vh"}), style={"width": "95%", "margin": "0 auto"}),
            html.Table([
                html.Tr([html.Th(c, style={"backgroundColor": "#002060", "color": "white", "padding": "8px 12px"}) for c in ["Target", "Achieved", "% Achievement"]]),
                html.Tr([
                    html.Td(f"{tgt:,.0f}", style={"padding": "8px 12px", "textAlign": "center"}),
                    html.Td(f"{ach:,.0f}", style={"padding": "8px 12px", "textAlign": "center"}),
                    html.Td(f"{pct}%", style={"padding": "8px 12px", "textAlign": "center", "fontWeight": "bold"})
                ])
            ], style={"width": "60%", "margin": "16px auto", "borderCollapse": "collapse",
                      "border": "1px solid #ddd", "textAlign": "center", "fontSize": "14px"})
        ])

    # Slide 1: Cover Page
    if slide_id == "1":
        return make_section_slide(f"{DEFAULT_FY} {DEFAULT_QUARTER} Data Review Meeting", "NYM Performance Review")

    # Slide 2 & 3: County Overall Performance
    elif slide_id in ["2", "3"]:
        indicators = ["HTS_TST", "HTS_TST_POS", "TX_NEW", "PrEP_NEW", "TX_CURR", "CXCA_SCRN"]
        x_vals, tgt_vals, ach_vals = [], [], []
        for ind in indicators:
            x_vals.append(ind)
            tgt_vals.append(get_target_fn(dff_targets, ind))
            ach_vals.append(get_actual_fn(dff, ind, max_period))
            
        fig = go.Figure()
        fig.add_trace(go.Bar(x=x_vals, y=tgt_vals, name="Target", marker_color=colors["target"]))
        fig.add_trace(go.Bar(x=x_vals, y=ach_vals, name="Achieved", marker_color=colors["achieved"]))
        #fig.update_layout(title="County Overall Performance Overview", barmode="group", plot_bgcolor=colors["bg"])
        fig.update_layout(
            title=dict(text="County Overall Performance Overview", font=dict(size=18, color="#002060")),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", barmode="group",
            margin=dict(l=60, r=40, t=60, b=60),
            xaxis=dict(tickfont=dict(size=14)),
            yaxis=dict(tickfont=dict(size=14), showgrid=True, gridcolor="#e0e0e0", tickformat=",.0f")
        )
        return html.Div([dcc.Graph(figure=fig)])

    # Slide 4: Care & Treatment Section Slide
    elif slide_id == "4":
        return make_section_slide("CARE & TREATMENT PERFORMANCE", f"{DEFAULT_FY} {DEFAULT_QUARTER} Review")

    # Slide 5: TX_NEW Performance & Monthly Trends
    elif slide_id == "5":
        return make_target_achieved_chart(f"TX_NEW Target vs Achievement {DEFAULT_FY} {DEFAULT_QUARTER}", "TX_NEW")

    # Slide 6: TX_CURR Monthly Trends
    elif slide_id == "6":
        return make_target_achieved_chart(f"TX_CURR Progress {DEFAULT_FY} {DEFAULT_QUARTER}", "TX_CURR")

    # Slide 7: TX_CURR Performance and Treatment Coverage
    elif slide_id == "7":
        # Dynamic: build (parent_label, child_val) pairs using resolved level columns
        child_vals = dff[_child_col].unique().drop_nulls().to_list() if not dff.is_empty() else []
        child_parent_list = []
        for cv in child_vals:
            cv_df = dff.filter(pl.col(_child_col) == cv)
            cv_tgt_df = dff_targets.filter(pl.col(_child_col) == cv)
            parent_val = cv
            if _parent_col != _child_col:
                if not cv_df.is_empty() and _parent_col in cv_df.columns:
                    p_vals = cv_df[_parent_col].drop_nulls().unique().to_list()
                    if p_vals:
                        parent_val = p_vals[0]
                elif not cv_tgt_df.is_empty() and _parent_col in cv_tgt_df.columns:
                    p_vals = cv_tgt_df[_parent_col].drop_nulls().unique().to_list()
                    if p_vals:
                        parent_val = p_vals[0]
            child_parent_list.append((parent_val, cv))

        child_parent_list = sorted(child_parent_list, key=lambda x: (x[0], x[1]))

        # Dynamic column headers based on level
        _hdr_parent = _parent_col if _child_col == _parent_col else _parent_col
        _hdr_child  = _child_label
        table_rows = [
            html.Tr([
                html.Th(c, style={"backgroundColor": "#002060", "color": "white", "padding": "10px", "border": "1px solid #002060", "textAlign": "center"})
                for c in [_hdr_parent, _hdr_child, "TX_CURR Target", "TX_CURR", "% Achieved", "TX_PVLS (D)", "VLC", "TX_PVLS (N)", "VLS"]
            ])
        ]

        tot_tgt, tot_ach, tot_pvls_d, tot_pvls_n = 0, 0, 0, 0

        for parent_val, cv in child_parent_list:
            cv_df     = dff.filter(pl.col(_child_col) == cv)
            cv_tgt_df = dff_targets.filter(pl.col(_child_col) == cv)

            tgt    = get_target_fn(cv_tgt_df, "TX_CURR")
            ach    = get_actual_fn(cv_df, "TX_CURR", max_period)
            pvls_d = get_actual_fn(cv_df, "TX_PVLS_DEN", max_period)
            pvls_n = get_actual_fn(cv_df, "TX_PVLS_NUM", max_period)

            tot_tgt    += tgt
            tot_ach    += ach
            tot_pvls_d += pvls_d
            tot_pvls_n += pvls_n

            pct_ach = round((ach / tgt) * 100) if tgt > 0 else 0
            vlc     = round((pvls_d / ach) * 100) if ach > 0 else 0
            vls     = round((pvls_n / pvls_d) * 100) if pvls_d > 0 else 0

            table_rows.append(html.Tr([
                html.Td(str(parent_val), style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(str(cv), style={"border": "1px solid #ddd", "padding": "8px", "fontWeight": "bold"}),
                html.Td(f"{tgt:,.0f}",    style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{ach:,.0f}",    style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{pct_ach}%",    style=get_cell_style(pct_ach)),
                html.Td(f"{pvls_d:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{vlc}%",        style=get_cell_style(vlc)),
                html.Td(f"{pvls_n:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{vls}%",        style=get_cell_style(vls))
            ]))

        tot_pct_ach = round((tot_ach / tot_tgt) * 100) if tot_tgt > 0 else 0
        tot_vlc     = round((tot_pvls_d / tot_ach) * 100) if tot_ach > 0 else 0
        tot_vls     = round((tot_pvls_n / tot_pvls_d) * 100) if tot_pvls_d > 0 else 0

        table_rows.append(html.Tr([
            html.Td("",    style={"border": "1px solid #ddd", "padding": "8px"}),
            html.Td("Total", style={"border": "1px solid #ddd", "padding": "8px", "fontWeight": "bold"}),
            html.Td(f"{tot_tgt:,.0f}",    style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_ach:,.0f}",    style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_pct_ach}%",    style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_pvls_d:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_vlc}%",        style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_pvls_n:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_vls}%",        style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"})
        ]))

        return html.Div([
            html.H3("TX_CURR Performance and Treatment Coverage", style={"textAlign": "center", "color": "#002060", "fontSize": "22px", "marginBottom": "20px"}),
            html.Div(html.Table(table_rows, style={"borderCollapse": "collapse", "width": "100%", "fontSize": "14px"}), style={"width": "95%", "margin": "0 auto", "overflowX": "auto"})
        ])

    # Slide 8 & 9: C&T Facility Rankings — ranked by % achievement vs target
    elif slide_id in ["8", "9"]:
        is_top = (slide_id == "8")
        facilities = dff["PRISM Facility Name"].unique().drop_nulls().to_list() if not dff.is_empty() else []
        fac_data = []
        for f in facilities:
            f_df  = dff.filter(pl.col("PRISM Facility Name") == f)
            f_tdf = dff_targets.filter(pl.col("PRISM Facility Name") == f)
            tgt = get_target_fn(f_tdf, "TX_CURR")
            ach = get_actual_fn(f_df, "TX_CURR", max_period)
            pct = round((ach / tgt) * 100, 1) if tgt > 0 else (100.0 if ach > 0 else 0.0)
            fac_data.append({"Facility": f, "Target": tgt, "Achieved": ach, "% Achieved": pct})
        if not fac_data:
            return html.Div(html.H3("No data available.", style={"textAlign": "center", "marginTop": "50px"}))
        df_fac = pl.DataFrame(fac_data)
        df_fac = df_fac.filter((pl.col("Target") > 0) | (pl.col("Achieved") > 0))
        df_ranked = df_fac.sort("% Achieved", descending=is_top).head(10)

        def _sc(pct):
            if pct >= 95: return "#006400"
            elif pct >= 90: return "#00b050"
            elif pct >= 85: return "#92d050"
            elif pct >= 70: return "#ffff00"
            elif pct >= 60: return "#ffc000"
            else: return "#ff0000"

        bar_colors_list = [_sc(p) for p in df_ranked["% Achieved"].to_list()]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_ranked["% Achieved"].to_list(), y=df_ranked["Facility"].to_list(),
            orientation="h", marker_color=bar_colors_list,
            text=[f"{v:.1f}%" for v in df_ranked["% Achieved"].to_list()],
            textposition="auto", textfont=dict(size=13, color="black")
        ))
        fig.update_layout(
            title=dict(text=("TX_CURR Top 10 Facilities by % Achievement" if is_top else "TX_CURR Bottom 10 Facilities by % Achievement"), font=dict(size=18, color="#002060")),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            xaxis=dict(title="% Achievement vs Target", tickfont=dict(size=13)),
            yaxis=dict(tickfont=dict(size=12), autorange="reversed"),
            margin=dict(l=220, r=40, t=60, b=60)
        )
        t_rows = [html.Tr([html.Th(c, style={"backgroundColor": "#002060", "color": "white", "padding": "8px 10px", "border": "1px solid #002060"}) for c in ["Rank", "Facility", "Target", "Achieved", "% Achieved", "Status"]])]
        for rank, row in enumerate(df_ranked.iter_rows(named=True), 1):
            st = html.Div(style={"height": "18px", "width": "18px", "backgroundColor": _sc(row["% Achieved"]), "borderRadius": "50%", "margin": "auto", "border": "1px solid #aaa"})
            t_rows.append(html.Tr([
                html.Td(str(rank), style={"border": "1px solid #ddd", "padding": "7px 10px", "textAlign": "center"}),
                html.Td(row["Facility"], style={"border": "1px solid #ddd", "padding": "7px 10px"}),
                html.Td(f"{row['Target']:,.0f}", style={"border": "1px solid #ddd", "padding": "7px 10px", "textAlign": "center"}),
                html.Td(f"{row['Achieved']:,.0f}", style={"border": "1px solid #ddd", "padding": "7px 10px", "textAlign": "center"}),
                html.Td(f"{row['% Achieved']:.1f}%", style={"border": "1px solid #ddd", "padding": "7px 10px", "textAlign": "center", "fontWeight": "bold"}),
                html.Td(st, style={"border": "1px solid #ddd", "padding": "7px 10px"}),
            ]))
        return html.Div([
            html.Div(dcc.Graph(figure=fig, style={"height": "66vh"}), style={"width": "95%", "margin": "0 auto"}),
            html.Div(html.Table(t_rows, style={"borderCollapse": "collapse", "width": "100%", "fontSize": "13px"}),
                     style={"width": "95%", "margin": "20px auto", "overflowX": "auto"})
        ])

    # Slide 10: Retention Analysis
    elif slide_id == "10":
        return make_narrative_slide("Retention Analysis Notes & Expected Actions (Work In Progress)", [
            "Work In Progress",
        ])

    # Slide 11: VLC & VLS — dynamically grouped by active geographic level
    elif slide_id == "11":
        child_vals = sorted(dff[_child_col].unique().drop_nulls().to_list()) if not dff.is_empty() else []
        vlc_rates, vls_rates = [], []
        for cv in child_vals:
            cv_df   = dff.filter(pl.col(_child_col) == cv)
            tx_curr = get_actual_fn(cv_df, "TX_CURR", max_period)
            vlc_den = get_actual_fn(cv_df, "TX_PVLS_DEN", max_period)
            vls_num = get_actual_fn(cv_df, "TX_PVLS_NUM", max_period)
            vlc_rates.append(round((vlc_den / tx_curr) * 100, 1) if tx_curr > 0 else 0)
            vls_rates.append(round((vls_num / vlc_den) * 100, 1) if vlc_den > 0 else 0)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=child_vals, y=vlc_rates, name="VL Coverage (%)", marker_color=colors["target"],
            text=[f"{v:.1f}%" for v in vlc_rates], textposition="auto", textfont=dict(size=13)
        ))
        fig.add_trace(go.Bar(
            x=child_vals, y=vls_rates, name="VL Suppression (%)", marker_color=colors["achieved"],
            text=[f"{v:.1f}%" for v in vls_rates], textposition="auto", textfont=dict(size=13)
        ))
        fig.update_layout(
            title=dict(text=f"Viral Load Coverage & Suppression by {_child_label}", font=dict(size=18, color="#002060")),
            barmode="group", plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            margin=dict(l=60, r=40, t=60, b=60),
            xaxis=dict(tickfont=dict(size=13)),
            yaxis=dict(tickfont=dict(size=13), showgrid=True, gridcolor="#e0e0e0")
        )
        return html.Div([html.Div(dcc.Graph(figure=fig, style={"height": "66vh"}), style={"width": "95%", "margin": "0 auto"})])

    # Slide 12: VLC & VLS by Age & Gender
    elif slide_id == "12":
        return make_narrative_slide("VLC And VLS By Age & Gender Summary (Work In Progress)", [
            "Work In Progress",
        ])

    # Slide 13 & 14: VL Facility Performance
    elif slide_id in ["13", "14"]:
        return make_narrative_slide("VL Uptake & High Volume Sites Focus (Work In Progress)", [
            "Work In Progress",
        ])

    # Slide 15 & 16: Hypertension Cascade Replications
    elif slide_id in ["15", "16"]:
        htn_labels = ["Eligible Screened", "HTN Diagnosed", "Linked to Care", "Controlled BP"]
        htn_values = [650, 210, 180, 130]
        fig = go.Figure(go.Funnel(y=htn_labels, x=htn_values, marker=dict(color=[colors["target"], colors["achieved"], "#2ca02c", "#ff7f0e"])))
        fig.update_layout(title="Hypertension Cascade Overall Performance (Work in Progress)", paper_bgcolor="#ffffff")
        return html.Div([dcc.Graph(figure=fig)])

    # Slide 17 & 18: Diabetes Mellitus Cascade
    elif slide_id in ["17", "18"]:
        dm_labels = ["Eligible Screened", "DM Diagnosed", "Linked to Care", "Controlled Glucose"]
        dm_values = [580, 150, 120, 90]
        fig = go.Figure(go.Funnel(y=dm_labels, x=dm_values, marker=dict(color=[colors["target"], colors["achieved"], "#2ca02c", "#ff7f0e"])))
        fig.update_layout(title="Diabetes Mellitus Cascade Overall (Work in Progress)", paper_bgcolor="#ffffff")
        return html.Div([dcc.Graph(figure=fig)])

    # Slide 19 & 20: NCD Burden by Age/Disease
    elif slide_id in ["19", "20"]:
        ncd_x = ["HTN Cases", "DM Cases"]
        ncd_y = [210, 150]
        fig = go.Figure(go.Bar(x=ncd_x, y=ncd_y, marker_color=[colors["target"], colors["achieved"]]))
        fig.update_layout(title="NCD Disease Burden Analysis (Work in Progress)", plot_bgcolor=colors["bg"])
        return html.Div([dcc.Graph(figure=fig)])

    # Slide 21: AHD Screening & Treatment
    elif slide_id == "21":
        ahd_labels = ["Eligible for AHD", "Screened", "Identified Positive", "Initiated on Treatment"]
        ahd_values = [120, 105, 30, 28]
        fig = go.Figure(go.Funnel(y=ahd_labels, x=ahd_values, marker=dict(color=[colors["target"], colors["achieved"], "#2ca02c", "#ff7f0e"])))
        fig.update_layout(title="Advanced HIV Disease (AHD) Screening & Treatment (Work in Progress)", paper_bgcolor="#ffffff")
        return html.Div([dcc.Graph(figure=fig)])

    # Slide 22: TAF-LD Transition
    elif slide_id == "22":
        return make_narrative_slide("TAF-LD Transition Progress (Work in Progress)", [
            "Work in Progress",
        ])

    # Slide 23: AYP Viral Load Cascade
    elif slide_id == "23":
        return make_narrative_slide("AYP Viral Load Cascade Summary (Work in Progress)", [
            "Work in Progress",
        ])

    # Slide 24: Operation Triple Zero
    elif slide_id == "24":
        return make_narrative_slide("Operation Triple Zero (OTZ) by Sub-County (Work in Progress)", [
            "Work in Progress",
        ])

    # Slide 25: TPT Performance
    elif slide_id == "25":
        return make_target_achieved_chart("TPT Achievement Performance", "TB_PREV_NUM")

    # Slide 26: HTS and PrEP Cover Slide
    elif slide_id == "26":
        return make_section_slide("HTS & PrEP PERFORMANCE", f"{DEFAULT_FY} {DEFAULT_QUARTER} Review")

    # Slide 27: HTS_TST Target vs Achievement
    elif slide_id == "27":
        return make_target_achieved_chart(f"HTS_TST Performance vs Target {DEFAULT_FY} {DEFAULT_QUARTER}", "HTS_TST")

    # Slide 28: HTS POS Target vs Achievement
    elif slide_id == "28":
        return make_target_achieved_chart(f"HTS POS Performance vs Target {DEFAULT_FY} {DEFAULT_QUARTER}", "HTS_TST_POS")

    # Slide 29: HTS Monthly Progress
    elif slide_id == "29":
        # Monthly trends for HTS_TST, HTS_POS and % Positivity
        months = dff["Period"].unique().drop_nulls().sort().to_list() if not dff.is_empty() else []
        hts_vals, pos_vals, pos_pct = [], [], []
        for m in months:
            m_df = dff.filter(pl.col("Period") == m)
            tst = sum(r["HTS_TST"] for r in extract_hts_sdp_metrics_fn(m_df))
            pos = sum(r["HTS_TST_POSITIVES"] for r in extract_hts_sdp_metrics_fn(m_df))
            hts_vals.append(tst)
            pos_vals.append(pos)
            pos_pct.append((pos/tst)*100 if tst > 0 else 0)
            
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=months, y=hts_vals, name="HTS_TST", marker_color=colors["target"]), secondary_y=False)
        fig.add_trace(go.Bar(x=months, y=pos_vals, name="HTS_POS", marker_color=colors["achieved"]), secondary_y=False)
        fig.add_trace(go.Scattergl(x=months, y=pos_pct, name="Positivity %", mode="lines+markers", line=dict(color="#2ca02c", width=2)), secondary_y=True)
        #fig.update_layout(title=f"HTS_TST Monthly Progress: {DEFAULT_FY} {DEFAULT_QUARTER}")
        fig.update_layout(
            title=dict(text=f"HTS_TST Monthly Progress: {DEFAULT_FY} {DEFAULT_QUARTER}", font=dict(size=18, color="#002060")),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", barmode="group",
            margin=dict(l=60, r=40, t=60, b=60),
            xaxis=dict(tickfont=dict(size=14)),
            yaxis=dict(tickfont=dict(size=14), showgrid=True, gridcolor="#e0e0e0", tickformat=",.0f")
        )
        return html.Div([dcc.Graph(figure=fig)])

    # Slide 30: SDP Positivity Contribution
    elif slide_id == "30":
        results = extract_hts_sdp_metrics_fn(dff)
        sdps = [r["SDP"] for r in results]
        tst_vals = [r["HTS_TST"] for r in results]
        pos_vals = [r["HTS_TST_POSITIVES"] for r in results]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=sdps, y=tst_vals, name="Tests Done", marker_color=colors["target"]))
        fig.add_trace(go.Bar(x=sdps, y=pos_vals, name="Positives", marker_color=colors["achieved"]))
        #fig.update_layout(title="Positivity Contribution by SDP Modality", barmode="group")
        fig.update_layout(
            title=dict(text="Positivity Contribution by SDP Modality", font=dict(size=18, color="#002060")),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", barmode="group",
            margin=dict(l=60, r=40, t=60, b=60),
            xaxis=dict(tickfont=dict(size=14)),
            yaxis=dict(tickfont=dict(size=14), showgrid=True, gridcolor="#e0e0e0", tickformat=",.0f")
        )
        return html.Div([dcc.Graph(figure=fig)])

    # Slide 31: HTS Positivity Contribution by Modality — dynamically grouped
    elif slide_id == "31":
        child_vals = sorted(dff[_child_col].unique().drop_nulls().to_list()) if not dff.is_empty() else []
        modalities = ["ANC1", "Index", "IPD", "Other PITC", "Pediatrics", "Post ANC1", "SNS", "TB", "VCT"]
        
        th_style = {"backgroundColor": "#002060", "color": "white", "padding": "8px", "border": "1px solid #002060", "textAlign": "center", "fontSize": "13px"}
        
        row1 = [html.Th("Modality", style=th_style)]
        for m in modalities:
            row1.append(html.Th(m, colSpan=2, style=th_style))
            
        row2 = [html.Th(_child_label, style=th_style)]
        for m in modalities:
            row2.extend([
                html.Th("Tested", style=th_style),
                html.Th("Positivity", style=th_style)
            ])
            
        table_rows = [html.Tr(row1), html.Tr(row2)]
        
        col_totals = {m: {"tested": 0, "pos": 0} for m in modalities}
        
        for cv in child_vals:
            cv_df = dff.filter(pl.col(_child_col) == cv)
            cv_df_cat = cv_df.filter(pl.col("Category").is_in(["HTS", "PMTCT", "TB_CASCADE", "APNS_Testing_Negative_SDP", "APNS_Testing_Positive_SDP"]))
            
            row_cells = [html.Td(str(cv), style={"border": "1px solid #ddd", "padding": "6px", "fontWeight": "bold", "fontSize": "12px"})]
            
            for m in modalities:
                tested, pos = 0, 0
                if m == "ANC1":
                    pos = cv_df_cat.filter(pl.col("Indicator") == "d. PMTCT_STAT_Numerator_Newly_Tested_Positives")["value"].sum() or 0
                    neg = cv_df_cat.filter(pl.col("Indicator") == "c. PMTCT_STAT_Numerator_Newly_Tested_Negatives")["value"].sum() or 0
                    tested = pos + neg
                elif m == "Index":
                    apns_pos = 0
                    apns_neg = 0
                    for sdp_key, mapping in SDP_MAPPING.items():
                        apns_pos += cv_df_cat.filter(pl.col("DATIM_Indicator").is_in(mapping.get("apns_pos", [])))["value"].sum() or 0
                        apns_neg += cv_df_cat.filter(pl.col("DATIM_Indicator").is_in(mapping.get("apns_neg", [])))["value"].sum() or 0
                    pos = apns_pos
                    tested = apns_pos + apns_neg
                elif m == "TB":
                    pos = cv_df_cat.filter(pl.col("Indicator") == "c. TB_STAT_Numerator Newly Identified Positive")["value"].sum() or 0
                    neg = cv_df_cat.filter(pl.col("Indicator") == "d. TB_STAT_Numerator Newly Tested_Negative")["value"].sum() or 0
                    tested = pos + neg
                else:
                    sdp_key = "Pediatric" if m == "Pediatrics" else m
                    mapping = SDP_MAPPING[sdp_key]
                    base_pos = cv_df_cat.filter((pl.col("DATIM_Indicator").is_in(mapping["base"])) & (pl.col("Testing Results").str.to_uppercase() == "POSITIVE"))["value"].sum() or 0
                    base_neg = cv_df_cat.filter((pl.col("DATIM_Indicator").is_in(mapping["base"])) & (pl.col("Testing Results").str.to_uppercase() == "NEGATIVE"))["value"].sum() or 0
                    apns_pos = cv_df_cat.filter(pl.col("DATIM_Indicator").is_in(mapping["apns_pos"]))["value"].sum() or 0
                    apns_neg = cv_df_cat.filter(pl.col("DATIM_Indicator").is_in(mapping["apns_neg"]))["value"].sum() or 0
                    net_pos, net_neg = max(0, base_pos - apns_pos), max(0, base_neg - apns_neg)
                    tested = net_pos + net_neg
                    pos = net_pos
                
                col_totals[m]["tested"] += tested
                col_totals[m]["pos"] += pos
                
                if tested == 0:
                    row_cells.extend([
                        html.Td("0", style={"border": "1px solid #ddd", "padding": "6px", "textAlign": "center", "backgroundColor": "#f0f0f0", "fontSize": "12px"}),
                        html.Td("", style={"border": "1px solid #ddd", "padding": "6px", "textAlign": "center", "backgroundColor": "#f0f0f0", "fontSize": "12px"})
                    ])
                else:
                    pos_pct = (pos / tested) * 100
                    row_cells.extend([
                        html.Td(f"{tested:,.0f}", style={"border": "1px solid #ddd", "padding": "6px", "textAlign": "center", "fontSize": "12px"}),
                        html.Td(f"{pos_pct:.1f}%", style=get_positivity_cell_style(pos_pct))
                    ])
            table_rows.append(html.Tr(row_cells))
            
        tot_cells = [html.Td("Total", style={"border": "1px solid #ddd", "padding": "6px", "fontWeight": "bold", "fontSize": "12px", "backgroundColor": "#f4f6fb"})]
        for m in modalities:
            tested = col_totals[m]["tested"]
            pos = col_totals[m]["pos"]
            if tested == 0:
                tot_cells.extend([
                    html.Td("0", style={"border": "1px solid #ddd", "padding": "6px", "textAlign": "center", "fontWeight": "bold", "fontSize": "12px", "backgroundColor": "#f4f6fb"}),
                    html.Td("", style={"border": "1px solid #ddd", "padding": "6px", "textAlign": "center", "fontWeight": "bold", "fontSize": "12px", "backgroundColor": "#f4f6fb"})
                ])
            else:
                pos_pct = (pos / tested) * 100
                tot_cells.extend([
                    html.Td(f"{tested:,.0f}", style={"border": "1px solid #ddd", "padding": "6px", "textAlign": "center", "fontWeight": "bold", "fontSize": "12px", "backgroundColor": "#f4f6fb"}),
                    html.Td(f"{pos_pct:.1f}%", style=get_positivity_cell_style(pos_pct))
                ])
        table_rows.append(html.Tr(tot_cells))
        
        return html.Div([
            html.H3("HTS Positivity Contribution by Modality", style={"textAlign": "center", "color": "#002060", "fontSize": "22px", "marginBottom": "20px"}),
            html.Div(html.Table(table_rows, style={"borderCollapse": "collapse", "width": "100%", "fontSize": "12px"}), style={"width": "98%", "margin": "0 auto", "overflowX": "auto"})
        ])

    # Slide 32: HTS_TST Positivity and Achievement
    elif slide_id == "32":
        sc_county_list = []
        unique_scs = dff["Sub County"].unique().drop_nulls().to_list() if not dff.is_empty() else []
        for sc in unique_scs:
            sc_df = dff.filter(pl.col("Sub County") == sc)
            sc_tgt_df = dff_targets.filter(pl.col("Sub County") == sc)
            sc_county = "Unknown"
            if not sc_df.is_empty() and "County" in sc_df.columns:
                c_vals = sc_df["County"].drop_nulls().unique().to_list()
                if c_vals:
                    sc_county = c_vals[0]
            elif not sc_tgt_df.is_empty() and "County" in sc_tgt_df.columns:
                c_vals = sc_tgt_df["County"].drop_nulls().unique().to_list()
                if c_vals:
                    sc_county = c_vals[0]
            sc_county_list.append((sc_county, sc))
        
        # Sort by county first, then by sub-county
        sc_county_list = sorted(sc_county_list, key=lambda x: (x[0], x[1]))
        
        hts_vals, pos_vals, pos_pct = [], [], []
        
        table_rows = [
            html.Tr([
                html.Th(c, style={"backgroundColor": "#002060", "color": "white", "padding": "8px", "border": "1px solid #002060", "textAlign": "center"})
                for c in ["County", "Sub_County", "HTS_TST Target", "HTS_TST", "HTS_TST Achieved", "HTS_TST_POS Target", "HTS_TST_POS", "HTS_TST_POS Achieved", "Positivity"]
            ])
        ]
        
        tot_tst_tgt, tot_tst, tot_pos_tgt, tot_pos = 0, 0, 0, 0
        
        for county_name, sc in sc_county_list:
            sc_df = dff.filter(pl.col("Sub County") == sc)
            sc_tgt_df = dff_targets.filter(pl.col("Sub County") == sc)
            
            tst_tgt = get_target_fn(sc_tgt_df, "HTS_TST")
            tst = sum(r["HTS_TST"] for r in extract_hts_sdp_metrics_fn(sc_df))
            pos_tgt = get_target_fn(sc_tgt_df, "HTS_TST_POS")
            pos = sum(r["HTS_TST_POSITIVES"] for r in extract_hts_sdp_metrics_fn(sc_df))
            
            tot_tst_tgt += tst_tgt
            tot_tst += tst
            tot_pos_tgt += pos_tgt
            tot_pos += pos
            
            hts_vals.append(tst)
            pos_vals.append(pos)
            pos_pct.append((pos/tst)*100 if tst > 0 else 0)
            
            tst_ach = round((tst / tst_tgt) * 100) if tst_tgt > 0 else 0
            pos_ach = round((pos / pos_tgt) * 100) if pos_tgt > 0 else 0
            pos_rate = (pos / tst) * 100 if tst > 0 else 0
            
            table_rows.append(html.Tr([
                html.Td(county_name, style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(sc.replace(" Sub County", ""), style={"border": "1px solid #ddd", "padding": "8px", "fontWeight": "bold"}),
                html.Td(f"{tst_tgt:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{tst:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{tst_ach}%", style=get_cell_style(tst_ach)),
                html.Td(f"{pos_tgt:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{pos:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{pos_ach}%", style=get_cell_style(pos_ach)),
                html.Td(f"{pos_rate:.1f}%", style=get_positivity_cell_style(pos_rate))
            ]))
            
        tot_tst_ach = round((tot_tst / tot_tst_tgt) * 100) if tot_tst_tgt > 0 else 0
        tot_pos_ach = round((tot_pos / tot_pos_tgt) * 100) if tot_pos_tgt > 0 else 0
        tot_pos_rate = (tot_pos / tot_tst) * 100 if tot_tst > 0 else 0
        
        table_rows.append(html.Tr([
            html.Td("", style={"border": "1px solid #ddd", "padding": "8px"}),
            html.Td("Total", style={"border": "1px solid #ddd", "padding": "8px", "fontWeight": "bold"}),
            html.Td(f"{tot_tst_tgt:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_tst:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_tst_ach}%", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_pos_tgt:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_pos:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_pos_ach}%", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_pos_rate:.1f}%", style=get_positivity_cell_style(tot_pos_rate))
        ]))
        
        chart_sc_names = [sc.replace(" Sub County", "") for _, sc in sc_county_list]
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(
            x=chart_sc_names, y=hts_vals, name="HTS_TST", 
            marker_color=colors["target"], text=[f"{v:,.0f}" for v in hts_vals], textposition="auto",
            textfont=dict(size=14, color="black")
        ), secondary_y=False)
        fig.add_trace(go.Bar(
            x=chart_sc_names, y=pos_vals, name="HTS_POS", 
            marker_color=colors["achieved"], text=[f"{v:,.0f}" for v in pos_vals], textposition="auto",
            textfont=dict(size=14, color="black")
        ), secondary_y=False)
        fig.add_trace(go.Scattergl(
            x=chart_sc_names, y=pos_pct, name="Positivity %", 
            mode="lines+markers+text", line=dict(color="#2ca02c", width=3), marker=dict(size=10),
            text=[f"{v:.1f}%" for v in pos_pct], textposition="top center",
            textfont=dict(color="black", size=14, family="Arial Black")
        ), secondary_y=True)
        
        fig.update_layout(
            title=dict(text="HTS_TST Positivity and Achievement", font=dict(size=18, color="#002060")),
            barmode="group", plot_bgcolor=colors["bg"], paper_bgcolor="#ffffff",
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(size=14)),
            margin=dict(l=40, r=40, t=60, b=60),
            font=dict(size=14)
        )
        fig.update_xaxes(tickfont=dict(size=14))
        fig.update_yaxes(tickfont=dict(size=14), showgrid=False)
        
        return html.Div([
            html.Div(dcc.Graph(figure=fig, style={"height": "66vh"}), style={"width": "95%", "margin": "0 auto"}),
            html.Div(html.Table(table_rows, style={"borderCollapse": "collapse", "width": "100%", "fontSize": "14px"}), style={"width": "95%", "margin": "20px auto", "overflowX": "auto"})
        ])

    # Slide 33 & 34: HTS Facility rankings
    elif slide_id in ["33", "34"]:
        return make_narrative_slide("HTS Facility Positivity Rankings (Work In Progress)", [
            "Work In Progress",
        ])
    # Slide 35: TX_NEW Achievement and Proxy Linkage Status — dynamically grouped
    elif slide_id == "35":
        child_vals = dff[_child_col].unique().drop_nulls().to_list() if not dff.is_empty() else []
        child_parent_list = []
        for cv in child_vals:
            cv_df = dff.filter(pl.col(_child_col) == cv)
            cv_tgt_df = dff_targets.filter(pl.col(_child_col) == cv)
            parent_val = cv
            if _parent_col != _child_col:
                if not cv_df.is_empty() and _parent_col in cv_df.columns:
                    p_vals = cv_df[_parent_col].drop_nulls().unique().to_list()
                    if p_vals:
                        parent_val = p_vals[0]
                elif not cv_tgt_df.is_empty() and _parent_col in cv_tgt_df.columns:
                    p_vals = cv_tgt_df[_parent_col].drop_nulls().unique().to_list()
                    if p_vals:
                        parent_val = p_vals[0]
            child_parent_list.append((parent_val, cv))

        child_parent_list = sorted(child_parent_list, key=lambda x: (x[0], x[1]))

        t1_rows = [
            html.Tr([
                html.Th(c, style={"backgroundColor": "#002060", "color": "white", "padding": "8px", "border": "1px solid #002060", "textAlign": "center"})
                for c in [_parent_col, _child_label, "TX_NEW Target", "TX_NEW", "% Achieved"]
            ])
        ]

        t2_rows = [
            html.Tr([
                html.Th(c, style={"backgroundColor": "#002060", "color": "white", "padding": "8px", "border": "1px solid #002060", "textAlign": "center"})
                for c in [_parent_col, _child_label, "HTS_TST_POS", "TX_NEW", "Proxy Linkage", "Not Linked"]
            ])
        ]

        tot_tx_tgt, tot_tx, tot_pos = 0, 0, 0

        for parent_val, cv in child_parent_list:
            cv_df     = dff.filter(pl.col(_child_col) == cv)
            cv_tgt_df = dff_targets.filter(pl.col(_child_col) == cv)

            tx_tgt  = get_target_fn(cv_tgt_df, "TX_NEW")
            tx_ach  = get_actual_fn(cv_df, "TX_NEW", max_period)
            pos_ach = sum(r["HTS_TST_POSITIVES"] for r in extract_hts_sdp_metrics_fn(cv_df))

            tot_tx_tgt += tx_tgt
            tot_tx     += tx_ach
            tot_pos    += pos_ach

            pct_ach    = round((tx_ach / tx_tgt) * 100) if tx_tgt > 0 else 0
            linkage    = round((tx_ach / pos_ach) * 100) if pos_ach > 0 else 0
            not_linked = pos_ach - tx_ach

            t1_rows.append(html.Tr([
                html.Td(str(parent_val), style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(str(cv),         style={"border": "1px solid #ddd", "padding": "8px", "fontWeight": "bold"}),
                html.Td(f"{tx_tgt:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{tx_ach:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{pct_ach}%",   style=get_cell_style(pct_ach))
            ]))

            if not_linked <= 0:
                nl_bg, nl_tc = "#00b050", "white"
            elif not_linked == 1:
                nl_bg, nl_tc = "#ffff00", "black"
            else:
                nl_bg, nl_tc = "#ff0000", "white"
            nl_style = {"backgroundColor": nl_bg, "color": nl_tc, "fontWeight": "bold", "textAlign": "center", "border": "1px solid #ddd", "padding": "8px"}

            t2_rows.append(html.Tr([
                html.Td(str(parent_val), style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(str(cv),         style={"border": "1px solid #ddd", "padding": "8px", "fontWeight": "bold"}),
                html.Td(f"{pos_ach:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{tx_ach:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{linkage}%",   style=get_cell_style(linkage)),
                html.Td(f"{not_linked}", style=nl_style)
            ]))

        tot_pct_ach  = round((tot_tx / tot_tx_tgt) * 100) if tot_tx_tgt > 0 else 0
        tot_linkage  = round((tot_tx / tot_pos) * 100) if tot_pos > 0 else 0
        tot_not_linked = tot_pos - tot_tx

        t1_rows.append(html.Tr([
            html.Td("", style={"border": "1px solid #ddd", "padding": "8px"}),
            html.Td("Total", style={"border": "1px solid #ddd", "padding": "8px", "fontWeight": "bold"}),
            html.Td(f"{tot_tx_tgt:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_tx:,.0f}",     style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_pct_ach}%",    style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"})
        ]))

        t2_rows.append(html.Tr([
            html.Td("", style={"border": "1px solid #ddd", "padding": "8px"}),
            html.Td("Total", style={"border": "1px solid #ddd", "padding": "8px", "fontWeight": "bold"}),
            html.Td(f"{tot_pos:,.0f}",      style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_tx:,.0f}",       style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_linkage}%",      style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_not_linked}",    style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"})
        ]))

        return html.Div([
            html.H3("TX_NEW Achievement and Proxy Linkage Status", style={"textAlign": "center", "color": "#002060", "fontSize": "22px", "marginBottom": "20px"}),
            html.Div([
                html.Table(t1_rows, style={"borderCollapse": "collapse", "width": "100%", "fontSize": "14px", "marginBottom": "30px"}),
                html.Table(t2_rows, style={"borderCollapse": "collapse", "width": "100%", "fontSize": "14px"})
            ], style={"width": "95%", "margin": "0 auto", "overflowX": "auto"})
        ])


    # Slide 36: Accounting for Unlinked
    elif slide_id == "36":
        return make_narrative_slide(f"Accounting for Unlinked {DEFAULT_FY} {DEFAULT_QUARTER} (Work In Progress)", [
            "Work In Progress."
        ])

    # Slide 37: Linkage Monthly Trends
    elif slide_id == "37":
        months = dff["Period"].unique().drop_nulls().sort().to_list() if not dff.is_empty() else []
        pos_vals, tx_vals, link_pct = [], [], []
        for m in months:
            m_df = dff.filter(pl.col("Period") == m)
            pos = sum(r["HTS_TST_POSITIVES"] for r in extract_hts_sdp_metrics_fn(m_df))
            tx_new = get_actual_fn(m_df, "TX_NEW", max_period)
            pos_vals.append(pos)
            tx_vals.append(tx_new)
            link_pct.append((tx_new/pos)*100 if pos > 0 else 0)
            
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=months, y=pos_vals, name="HTS POS", marker_color=colors["achieved"]), secondary_y=False)
        fig.add_trace(go.Bar(x=months, y=tx_vals, name="TX_NEW", marker_color=colors["target"]), secondary_y=False)
        fig.add_trace(go.Scattergl(x=months, y=link_pct, name="Linkage %", mode="lines+markers", line=dict(color="#2ca02c", width=2)), secondary_y=True)
        #fig.update_layout(title="Proxy Linkage - Monthly Progress Trends")
        fig.update_layout(
            title=dict(text="Proxy Linkage - Monthly Progress Trends", font=dict(size=18, color="#002060")),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", barmode="group",
            margin=dict(l=60, r=40, t=60, b=60),
            xaxis=dict(tickfont=dict(size=14)),
            yaxis=dict(tickfont=dict(size=14), showgrid=True, gridcolor="#e0e0e0", tickformat=",.0f")
        )
        return html.Div([dcc.Graph(figure=fig)])

    # Slide 38: SNS Cascade
    elif slide_id == "38":
        sns_labels = ["Eligible for SNS", "Tested via SNS", "SNS Positive", "Linked to ART"]
        sns_values = [150, 142, 18, 17]
        fig = go.Figure(go.Funnel(y=sns_labels, x=sns_values, marker=dict(color=[colors["target"], colors["achieved"], "#2ca02c", "#ff7f0e"])))
        fig.update_layout(title="Social Network Strategy (SNS) Cascade Overall (Work In Progress)")
        return html.Div([dcc.Graph(figure=fig)])

    # Slide 39 & 40: Index Testing Cascade
    elif slide_id in ["39", "40"]:
        index_labels = ["Index Cases Offered", "Contacts Elicited", "Contacts Tested", "Index Positives", "Linked"]
        index_values = [320, 410, 380, 45, 43]
        fig = go.Figure(go.Funnel(y=index_labels, x=index_values, marker=dict(color=[colors["target"], colors["achieved"], "#2ca02c", "#ff7f0e", "#1f77b4"])))
        fig.update_layout(title="Index Testing Cascade (Work In Progress)")
        return html.Div([dcc.Graph(figure=fig)])

    # Slide 41: HTS_SELF Performance
    elif slide_id == "41":
        return make_target_achieved_chart(f"HTS_SELF Target vs Achievement {DEFAULT_FY} {DEFAULT_QUARTER}", "HTS_SELF")

    # Slide 42: Kits Distribution
    elif slide_id == "42":
        return make_narrative_slide("Self-Test Kits Distribution by Sub-County (Work In Progress)", [
            "Work In Progress",
        ])

    # Slide 43: PrEP Cascade
    elif slide_id == "43":
        prep_new = get_actual_fn(dff, "PrEP_NEW", max_period)
        prep_ct = get_actual_fn(dff, "PrEP_CT", max_period)
        fig = go.Figure(go.Bar(x=["PrEP_NEW", "PrEP_CT"], y=[prep_new, prep_ct], marker_color=[colors["target"], colors["achieved"]]))
        #fig.update_layout(title="PrEP_NEW and PrEP_CT Current Status Overview")
        fig.update_layout(
            title=dict(text="PrEP_NEW and PrEP_CT Current Status Overview", font=dict(size=18, color="#002060")),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", barmode="group",
            margin=dict(l=60, r=40, t=60, b=60),
            xaxis=dict(tickfont=dict(size=14)),
            yaxis=dict(tickfont=dict(size=14), showgrid=True, gridcolor="#e0e0e0", tickformat=",.0f")
        )
        return html.Div([dcc.Graph(figure=fig)])

    # Slide 44 & 45: PrEP Females PBFW
    elif slide_id in ["44", "45"]:
        return make_narrative_slide("PrEP Delivery in Pregnant & Breastfeeding Women (Work In Progress)", [
            "Work In Progress",
        ])

    # Slide 46: TB Case Finding Cover
    elif slide_id == "46":
        return make_section_slide("TB CASE FINDING", "HIV/TB Cascades & Outcomes")

    # Slide 47: TB indicators
    elif slide_id == "47":
        tb_indicators = ["TB_STAT_DEN", "TB_STAT_NUM", "TB_ART", "TB_PREV_DEN", "TB_PREV_NUM"]
        x_vals, tgt_vals, ach_vals = [], [], []
        for ind in tb_indicators:
            x_vals.append(ind)
            tgt_vals.append(get_target_fn(dff_targets, ind))
            ach_vals.append(get_actual_fn(dff, ind, max_period))

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=x_vals, y=tgt_vals, name="Target", marker_color=colors["target"],
            text=[f"{v:,.0f}" for v in tgt_vals], textposition="auto", textfont=dict(size=13)
        ))
        fig.add_trace(go.Bar(
            x=x_vals, y=ach_vals, name="Achieved", marker_color=colors["achieved"],
            text=[f"{v:,.0f}" for v in ach_vals], textposition="auto", textfont=dict(size=13)
        ))
        fig.update_layout(
            title=dict(text="Overall TB Indicators Performance Cascade", font=dict(size=18, color="#002060")),
            barmode="group", plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            margin=dict(l=60, r=40, t=60, b=60),
            xaxis=dict(tickfont=dict(size=13)),
            yaxis=dict(tickfont=dict(size=13), showgrid=True, gridcolor="#e0e0e0", tickformat=",.0f")
        )
        return html.Div([html.Div(dcc.Graph(figure=fig, style={"height": "66vh"}), style={"width": "95%", "margin": "0 auto"})])

    # Slide 48: TB Cases Identification and ART Initiation Outcomes — dynamically grouped
    elif slide_id == "48":
        child_vals = dff[_child_col].unique().drop_nulls().to_list() if not dff.is_empty() else []
        child_parent_list = []
        for cv in child_vals:
            cv_df     = dff.filter(pl.col(_child_col) == cv)
            cv_tgt_df = dff_targets.filter(pl.col(_child_col) == cv)
            parent_val = cv
            if _parent_col != _child_col:
                if not cv_df.is_empty() and _parent_col in cv_df.columns:
                    p_vals = cv_df[_parent_col].drop_nulls().unique().to_list()
                    if p_vals:
                        parent_val = p_vals[0]
                elif not cv_tgt_df.is_empty() and _parent_col in cv_tgt_df.columns:
                    p_vals = cv_tgt_df[_parent_col].drop_nulls().unique().to_list()
                    if p_vals:
                        parent_val = p_vals[0]
            child_parent_list.append((parent_val, cv))

        child_parent_list = sorted(child_parent_list, key=lambda x: (x[0], x[1]))

        table_rows = [
            html.Tr([
                html.Th(c, style={"backgroundColor": "#002060", "color": "white", "padding": "8px", "border": "1px solid #002060", "textAlign": "center"})
                for c in [_parent_col, _child_label, "TB_STAT (D)", "TB_STAT (N)", "TB_STAT", "TB_STAT_POS", "% POS", "TB_ART", "TB_ART %", "Missed ART"]
            ])
        ]

        tot_stat_d, tot_stat_n, tot_stat_pos, tot_art = 0, 0, 0, 0

        for parent_val, cv in child_parent_list:
            cv_df     = dff.filter(pl.col(_child_col) == cv)
            cv_tgt_df = dff_targets.filter(pl.col(_child_col) == cv)

            stat_d   = get_actual_fn(cv_df, "TB_STAT_DEN", max_period)
            stat_n   = get_actual_fn(cv_df, "TB_STAT_NUM", max_period)
            stat_pos = get_actual_fn(cv_df, "TB_STAT_POS", max_period)
            art      = get_actual_fn(cv_df, "TB_ART", max_period)

            tot_stat_d   += stat_d
            tot_stat_n   += stat_n
            tot_stat_pos += stat_pos
            tot_art      += art

            tb_stat    = round((stat_n / stat_d) * 100) if stat_d > 0 else 0
            pos_rate   = (stat_pos / stat_n) * 100 if stat_n > 0 else 0
            tb_art_pct = round((art / stat_pos) * 100) if stat_pos > 0 else 0
            missed_art = stat_pos - art

            if pos_rate >= 30:
                pos_bg, pos_tc = "#ff0000", "white"
            elif pos_rate >= 22:
                pos_bg, pos_tc = "#ffc000", "black"
            else:
                pos_bg, pos_tc = "#00b050", "white"
            pos_style = {"backgroundColor": pos_bg, "color": pos_tc, "fontWeight": "bold", "textAlign": "center", "border": "1px solid #ddd", "padding": "8px"}

            if missed_art == 0:
                ma_bg, ma_tc = "#00b050", "white"
            else:
                ma_bg, ma_tc = "#ff0000", "white"
            ma_style = {"backgroundColor": ma_bg, "color": ma_tc, "fontWeight": "bold", "textAlign": "center", "border": "1px solid #ddd", "padding": "8px"}

            table_rows.append(html.Tr([
                html.Td(str(parent_val), style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(str(cv),         style={"border": "1px solid #ddd", "padding": "8px", "fontWeight": "bold"}),
                html.Td(f"{stat_d:,.0f}",   style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{stat_n:,.0f}",   style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{tb_stat}%",      style=get_cell_style(tb_stat)),
                html.Td(f"{stat_pos:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{pos_rate:.1f}%", style=pos_style),
                html.Td(f"{art:,.0f}",       style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{tb_art_pct}%",   style=get_cell_style(tb_art_pct)),
                html.Td(f"{missed_art}",     style=ma_style)
            ]))

        tot_tb_stat     = round((tot_stat_n / tot_stat_d) * 100) if tot_stat_d > 0 else 0
        tot_pos_rate    = (tot_stat_pos / tot_stat_n) * 100 if tot_stat_n > 0 else 0
        tot_tb_art_pct  = round((tot_art / tot_stat_pos) * 100) if tot_stat_pos > 0 else 0
        tot_missed_art  = tot_stat_pos - tot_art

        table_rows.append(html.Tr([
            html.Td("",      style={"border": "1px solid #ddd", "padding": "8px"}),
            html.Td("Total", style={"border": "1px solid #ddd", "padding": "8px", "fontWeight": "bold"}),
            html.Td(f"{tot_stat_d:,.0f}",   style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_stat_n:,.0f}",   style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_tb_stat}%",      style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_stat_pos:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_pos_rate:.1f}%", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_art:,.0f}",      style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_tb_art_pct}%",  style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_missed_art}",    style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"})
        ]))

        return html.Div([
            html.H3("TB Cases Identification and ART Initiation Outcomes", style={"textAlign": "center", "color": "#002060", "fontSize": "22px", "marginBottom": "20px"}),
            html.Div(html.Table(table_rows, style={"borderCollapse": "collapse", "width": "100%", "fontSize": "14px"}), style={"width": "95%", "margin": "0 auto", "overflowX": "auto"})
        ])

    # Slide 49: TB PREV Achievement and TX_TB — dynamically grouped
    elif slide_id == "49":
        child_vals = dff[_child_col].unique().drop_nulls().to_list() if not dff.is_empty() else []
        child_parent_list = []
        for cv in child_vals:
            cv_df     = dff.filter(pl.col(_child_col) == cv)
            cv_tgt_df = dff_targets.filter(pl.col(_child_col) == cv)
            parent_val = cv
            if _parent_col != _child_col:
                if not cv_df.is_empty() and _parent_col in cv_df.columns:
                    p_vals = cv_df[_parent_col].drop_nulls().unique().to_list()
                    if p_vals:
                        parent_val = p_vals[0]
                elif not cv_tgt_df.is_empty() and _parent_col in cv_tgt_df.columns:
                    p_vals = cv_tgt_df[_parent_col].drop_nulls().unique().to_list()
                    if p_vals:
                        parent_val = p_vals[0]
            child_parent_list.append((parent_val, cv))

        child_parent_list = sorted(child_parent_list, key=lambda x: (x[0], x[1]))

        table_rows = [
            html.Tr([
                html.Th(c, style={"backgroundColor": "#002060", "color": "white", "padding": "8px", "border": "1px solid #002060", "textAlign": "center"})
                for c in [
                    _parent_col, _child_label,
                    "TB_PREV (D) Target", "TB_PREV (D)", "TB_PREV (D) Achieved",
                    "TB_PREV (N) Target", "TB_PREV (N)", "TB_PREV (N) Achieved",
                    "TPT Completion Rate", "TX_CURR", "TX_TB (D)", "% Screened"
                ]
            ])
        ]

        tot_prev_d_tgt, tot_prev_d_ach, tot_prev_n_tgt, tot_prev_n_ach = 0, 0, 0, 0
        tot_tx_curr, tot_tx_tb = 0, 0

        for parent_val, cv in child_parent_list:
            cv_df     = dff.filter(pl.col(_child_col) == cv)
            cv_tgt_df = dff_targets.filter(pl.col(_child_col) == cv)

            prev_d_tgt = get_target_fn(cv_tgt_df, "TB_PREV_DEN")
            prev_d_ach = get_actual_fn(cv_df, "TB_PREV_DEN", max_period)
            prev_n_tgt = get_target_fn(cv_tgt_df, "TB_PREV_NUM")
            prev_n_ach = get_actual_fn(cv_df, "TB_PREV_NUM", max_period)
            tx_curr    = get_actual_fn(cv_df, "TX_CURR", max_period)
            tx_tb      = get_actual_fn(cv_df, "TX_TB", max_period)

            tot_prev_d_tgt += prev_d_tgt
            tot_prev_d_ach += prev_d_ach
            tot_prev_n_tgt += prev_n_tgt
            tot_prev_n_ach += prev_n_ach
            tot_tx_curr    += tx_curr
            tot_tx_tb      += tx_tb

            pct_d_ach      = round((prev_d_ach / prev_d_tgt) * 100) if prev_d_tgt > 0 else 0
            pct_n_ach      = round((prev_n_ach / prev_n_tgt) * 100) if prev_n_tgt > 0 else 0
            tpt_completion = round((prev_n_ach / prev_d_ach) * 100) if prev_d_ach > 0 else 0
            pct_screened   = round((tx_tb / tx_curr) * 100) if tx_curr > 0 else 0

            table_rows.append(html.Tr([
                html.Td(str(parent_val),     style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(str(cv),             style={"border": "1px solid #ddd", "padding": "8px", "fontWeight": "bold"}),
                html.Td(f"{prev_d_tgt:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{prev_d_ach:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{pct_d_ach}%",     style=get_cell_style(pct_d_ach)),
                html.Td(f"{prev_n_tgt:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{prev_n_ach:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{pct_n_ach}%",     style=get_cell_style(pct_n_ach)),
                html.Td(f"{tpt_completion}%", style=get_cell_style(tpt_completion)),
                html.Td(f"{tx_curr:,.0f}",   style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{tx_tb:,.0f}",     style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center"}),
                html.Td(f"{pct_screened}%",  style=get_cell_style(pct_screened))
            ]))

        tot_pct_d_ach      = round((tot_prev_d_ach / tot_prev_d_tgt) * 100) if tot_prev_d_tgt > 0 else 0
        tot_pct_n_ach      = round((tot_prev_n_ach / tot_prev_n_tgt) * 100) if tot_prev_n_tgt > 0 else 0
        tot_tpt_completion = round((tot_prev_n_ach / tot_prev_d_ach) * 100) if tot_prev_d_ach > 0 else 0
        tot_pct_screened   = round((tot_tx_tb / tot_tx_curr) * 100) if tot_tx_curr > 0 else 0

        table_rows.append(html.Tr([
            html.Td("",      style={"border": "1px solid #ddd", "padding": "8px"}),
            html.Td("Total", style={"border": "1px solid #ddd", "padding": "8px", "fontWeight": "bold"}),
            html.Td(f"{tot_prev_d_tgt:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_prev_d_ach:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_pct_d_ach}%",      style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_prev_n_tgt:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_prev_n_ach:,.0f}", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_pct_n_ach}%",      style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_tpt_completion}%", style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_tx_curr:,.0f}",    style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_tx_tb:,.0f}",      style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"}),
            html.Td(f"{tot_pct_screened}%",   style={"border": "1px solid #ddd", "padding": "8px", "textAlign": "center", "fontWeight": "bold"})
        ]))

        return html.Div([
            html.H3(f"TB PREV Achievement and TX_TB by {_child_label}", style={"textAlign": "center", "color": "#002060", "fontSize": "22px", "marginBottom": "20px"}),
            html.Div(html.Table(table_rows, style={"borderCollapse": "collapse", "width": "100%", "fontSize": "14px"}), style={"width": "95%", "margin": "0 auto", "overflowX": "auto"})
        ])

    # Slide 50: TX_TB Cascade
    elif slide_id == "50":
        tx_tb_tgt = get_target_fn(dff_targets, "TX_TB")
        tx_tb_ach = get_actual_fn(dff, "TX_TB", max_period)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=["Target", "Achieved"], y=[tx_tb_tgt, tx_tb_ach], marker_color=[colors["target"], colors["achieved"]]))
        #fig.update_layout(title="TX_TB Achievement Cascade (HIV patients screened for TB)")
        fig.update_layout(
            title=dict(text="TX_TB Achievement Cascade (HIV patients screened for TB)", font=dict(size=18, color="#002060")),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", barmode="group",
            margin=dict(l=60, r=40, t=60, b=60),
            xaxis=dict(tickfont=dict(size=14)),
            yaxis=dict(tickfont=dict(size=14), showgrid=True, gridcolor="#e0e0e0", tickformat=",.0f")
        )
        return html.Div([dcc.Graph(figure=fig)])

    # Slide 51 & 52: TB outcomes & TPT
    elif slide_id in ["51", "52"]:
        return make_narrative_slide("TB Treatment Outcomes & TPT Cascade (Work In Progress)", [
            "Work In Progress"
        ])

    # Slide 53: PMTCT Cover
    elif slide_id == "53":
        return make_section_slide("ELIMINATION OF MOTHER-TO-CHILD TRANSMISSION", "PMTCT & EID Cascade Performance")

    # Slide 54 & 55: PMTCT Achievement Overall & Sub-County
    elif slide_id in ["54", "55"]:
        indicators = ["PMTCT_STAT_DEN", "PMTCT_STAT_NUM", "PMTCT_ART", "PMTCT_EID"]
        x_vals, tgt_vals, ach_vals = [], [], []
        for ind in indicators:
            x_vals.append(ind)
            tgt_vals.append(get_target_fn(dff_targets, ind))
            ach_vals.append(get_actual_fn(dff, ind, max_period))

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=x_vals, y=tgt_vals, name="Target", marker_color=colors["target"],
            text=[f"{v:,.0f}" for v in tgt_vals], textposition="auto", textfont=dict(size=13)
        ))
        fig.add_trace(go.Bar(
            x=x_vals, y=ach_vals, name="Achieved", marker_color=colors["achieved"],
            text=[f"{v:,.0f}" for v in ach_vals], textposition="auto", textfont=dict(size=13)
        ))
        fig.update_layout(
            title=dict(text="PMTCT Core Indicators Overview", font=dict(size=18, color="#002060")),
            barmode="group", plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            margin=dict(l=60, r=40, t=60, b=60),
            xaxis=dict(tickfont=dict(size=13)),
            yaxis=dict(tickfont=dict(size=13), showgrid=True, gridcolor="#e0e0e0", tickformat=",.0f")
        )
        return html.Div([html.Div(dcc.Graph(figure=fig, style={"height": "66vh"}), style={"width": "95%", "margin": "0 auto"})])

    # Slide 56 & 57: ANC Coverage Rankings
    elif slide_id in ["56", "57"]:
        return make_narrative_slide("ANC & PMTCT Positive Facility Rankings (Work In Progress)", [
            "Work In Progress",
        ])

    # Slide 58: PMTCT sub-county cascades
    elif slide_id == "58":
        sub_counties = dff["Sub County"].unique().drop_nulls().to_list() if not dff.is_empty() else []
        pmtct_art_rates = []
        for sc in sub_counties:
            sc_df = dff.filter(pl.col("Sub County") == sc)
            num = get_actual_fn(sc_df, "PMTCT_STAT_NUM", max_period)
            art = get_actual_fn(sc_df, "PMTCT_ART", max_period)
            pmtct_art_rates.append((art / num) * 100 if num > 0 else 0)
            
        fig = go.Figure(go.Bar(x=sub_counties, y=pmtct_art_rates, marker_color=colors["achieved"]))
        #fig.update_layout(title="Maternal ART Initiation Rates by Sub-County (%)")
        fig.update_layout(
            title=dict(text="Maternal ART Initiation Rates by Sub-County (%)", font=dict(size=18, color="#002060")),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", barmode="group",
            margin=dict(l=60, r=40, t=60, b=60),
            xaxis=dict(tickfont=dict(size=14)),
            yaxis=dict(tickfont=dict(size=14), showgrid=True, gridcolor="#e0e0e0", tickformat=",.0f")
        )
        return html.Div([dcc.Graph(figure=fig)])

    # Slide 59 & 60: Post ANC 1 Testing
    elif slide_id in ["59", "60"]:
        return make_narrative_slide("Post ANC 1 Testing and Positivity (Work In Progress)", [
            "Work In Progress",
        ])

    # Slide 61 & 62: AYP PMTCT & PrEP in MCH
    elif slide_id in ["61", "62"]:
        return make_narrative_slide("AYP PMTCT & PrEP in MCH Clinic (Work In Progress)", [
            "Work In Progress",
        ])

    # Slide 63: PMTCT VL Cascade
    elif slide_id == "63":
        return make_narrative_slide("PMTCT Maternal VL Cascade (Work In Progress)", [
            "Work In Progress",
        ])

    # Slide 64: EID Performance
    elif slide_id == "64":
        return make_target_achieved_chart("EID overall PCR Samples Collection Performance", "PMTCT_EID")

    # Slide 65: EID Initials vs Overall
    elif slide_id == "65":
        return make_narrative_slide("EID Overall PCR Tests vs Initial PCRs only (Work In Progress)", [
            "Work In Progress",
        ])

    # Slide 66 & 67: EID < 2 Months Performance
    elif slide_id in ["66", "67"]:
        eid_2m = get_actual_fn(dff, "PMTCT_EID_<2MONTHS", max_period)
        eid_12m = get_actual_fn(dff, "PMTCT_EID_2_12_MONTHS", max_period)
        
        fig = go.Figure(go.Pie(labels=["PCR <2 Months", "PCR 2-12 Months"], values=[eid_2m, eid_12m], marker_colors=[colors["target"], colors["achieved"]]))
        #fig.update_layout(title="EID Infant PCR Testing Intervals (Slide 66 & 67)")
        fig.update_layout(
            title=dict(text="EID Infant PCR Testing Intervals", font=dict(size=18, color="#002060")),
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", barmode="group",
            margin=dict(l=60, r=40, t=60, b=60),
            xaxis=dict(tickfont=dict(size=14)),
            yaxis=dict(tickfont=dict(size=14), showgrid=True, gridcolor="#e0e0e0", tickformat=",.0f")
        )
        return html.Div([dcc.Graph(figure=fig)])

    # Slide 68: PMTCT 24m Outcome
    elif slide_id == "68":
        return make_narrative_slide("PMTCT Final Outcome at 24 Months (Work In Progress)", [
            "Work In Progress",
        ])

    # Slide 69: Cervical Cancer Achievement
    elif slide_id == "69":
        return make_target_achieved_chart("Cervical Cancer Screening (CXCA_SCRN) Achievement", "CXCA_SCRN")

    # Slide 70 & 71: Cervical Cancer screening progress
    elif slide_id in ["70", "71"]:
        return make_narrative_slide("Cervical Cancer Screening Positivity & Progress (Work In Progress)", [
            "Work In Progress",
        ])

    # Slide 72: HPV Vaccination
    elif slide_id == "72":
        return make_narrative_slide(f"HPV Vaccination Progress {DEFAULT_FY} {DEFAULT_QUARTER} (Work In Progress)", [
            "Work In Progress",
        ])

    # Slides 73-76: HTS Top/Bottom 10
    elif slide_id == "73": return make_top_bottom_10("HTS_TST",     "HTS_TST",     is_top=True)
    elif slide_id == "74": return make_top_bottom_10("HTS_TST",     "HTS_TST",     is_top=False)
    elif slide_id == "75": return make_top_bottom_10("HTS_TST_POS", "HTS_TST_POS", is_top=True)
    elif slide_id == "76": return make_top_bottom_10("HTS_TST_POS", "HTS_TST_POS", is_top=False)
    # Slides 77-84: TB Top/Bottom 10
    elif slide_id == "77": return make_top_bottom_10("TB_STAT_DEN", "TB_STAT_DEN", is_top=True)
    elif slide_id == "78": return make_top_bottom_10("TB_STAT_DEN", "TB_STAT_DEN", is_top=False)
    elif slide_id == "79": return make_top_bottom_10("TB_STAT_NUM", "TB_STAT_NUM", is_top=True)
    elif slide_id == "80": return make_top_bottom_10("TB_STAT_NUM", "TB_STAT_NUM", is_top=False)
    elif slide_id == "81": return make_top_bottom_10("TB_PREV_DEN", "TB_PREV_DEN", is_top=True)
    elif slide_id == "82": return make_top_bottom_10("TB_PREV_DEN", "TB_PREV_DEN", is_top=False)
    elif slide_id == "83": return make_top_bottom_10("TB_PREV_NUM", "TB_PREV_NUM", is_top=True)
    elif slide_id == "84": return make_top_bottom_10("TB_PREV_NUM", "TB_PREV_NUM", is_top=False)
    # Slides 85-90: PMTCT / CXCA Top/Bottom 10
    elif slide_id == "85": return make_top_bottom_10("PMTCT_STAT_DEN", "PMTCT_STAT_DEN", is_top=True)
    elif slide_id == "86": return make_top_bottom_10("PMTCT_STAT_DEN", "PMTCT_STAT_DEN", is_top=False)
    elif slide_id == "87": return make_top_bottom_10("PMTCT_STAT_NUM", "PMTCT_STAT_NUM", is_top=True)
    elif slide_id == "88": return make_top_bottom_10("PMTCT_STAT_NUM", "PMTCT_STAT_NUM", is_top=False)
    elif slide_id == "89": return make_top_bottom_10("CXCA_SCRN",      "CXCA_SCRN",      is_top=True)
    elif slide_id == "90": return make_top_bottom_10("CXCA_SCRN",      "CXCA_SCRN",      is_top=False)

    # Fallback/Undefined Slide
    return html.Div([
        html.H3(f"Slide Layout for Slide {slide_id} is under construction.")
    ])
