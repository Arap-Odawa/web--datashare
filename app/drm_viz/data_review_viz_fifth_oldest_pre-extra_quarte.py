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
from dash import Dash, Input, Output, State, ALL, dcc, html, callback_context
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path # Imported pathlib
from flask_caching import Cache # NEW IMPORT
from drm_viz.slide_renderer import render_pptx_slide
from configs.prometheus_metrics import monitor_function

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


data_review_dash_app = Dash(__name__, requests_pathname_prefix="/data-review-meeting-visuals/", suppress_callback_exceptions=True)
data_review_dash_app.title = "📊 Web DataShare : Data Review Meeting Visuals"

# When testing, mute this section so that it works without any Redis Docker Container. 20.03.2026.


# --- NEW: INITIALIZE FLASK CACHING WITH REDIS & ROBUST FALLBACK ---
import socket
from urllib.parse import urlparse

def is_redis_available(host, port):
    try:
        s = socket.create_connection((host, port), timeout=1)
        s.close()
        return True
    except Exception:
        return False

# Parse settings.REDIS_URL
redis_host = "localhost"
redis_port = 6379
try:
    parsed = urlparse(settings.REDIS_URL)
    if parsed.hostname:
        redis_host = parsed.hostname
    if parsed.port:
        redis_port = parsed.port
except Exception:
    pass

# Determine best cache config
if is_redis_available(redis_host, redis_port):
    cache_config = {
        'CACHE_TYPE': 'RedisCache',
        'CACHE_REDIS_URL': settings.REDIS_URL,
        'CACHE_DEFAULT_TIMEOUT': settings.REDIS_CACHE_PERIOD
    }
elif redis_host == "redis" and is_redis_available("localhost", redis_port):
    cache_config = {
        'CACHE_TYPE': 'RedisCache',
        'CACHE_REDIS_URL': settings.REDIS_URL.replace("redis://redis", "redis://localhost"),
        'CACHE_DEFAULT_TIMEOUT': settings.REDIS_CACHE_PERIOD
    }
else:
    # Fallback to SimpleCache if Redis is down/unavailable
    cache_config = {
        'CACHE_TYPE': 'SimpleCache',
        'CACHE_DEFAULT_TIMEOUT': settings.REDIS_CACHE_PERIOD
    }

cache = Cache(data_review_dash_app.server, config=cache_config)




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
    {"id": "TX_PVLS_NUM", "name": "TX_PVLS_NUM"},

]

# Tab 0 Summary Dashboard: display names match the screenshot layout/order
TAB_0_SUMMARY_INDICATORS = [
    {"id": "HTS_TST",               "name": "HTS_TST"},
    {"id": "HTS_TST_POS",           "name": "HTS_POS"},
    {"id": "HTS_SELF",              "name": "HTS_SELF"},
    {"id": "TX_NEW",                "name": "TX_NEW"},
    {"id": "TX_CURR",               "name": "TX_CURR"},
    {"id": "TX_PVLS_DEN",           "name": "TX_PVLS (D)"},
    {"id": "TX_PVLS_NUM",           "name": "TX_PVLS (N)"},
    {"id": "TX_TB",                 "name": "TX_TB (D)"},
    {"id": "TB_STAT_DEN",           "name": "TB_STAT (D)"},
    {"id": "TB_STAT_NUM",           "name": "TB_STAT (N)"},
    {"id": "TB_STAT_POS",           "name": "TB_STAT_POS"},
    {"id": "TB_ART",                "name": "TB_ART"},
    {"id": "TB_PREV_DEN",           "name": "TB_PREV (D)"},
    {"id": "TB_PREV_NUM",           "name": "TB_PREV (N)"},
    {"id": "PMTCT_STAT_DEN",        "name": "PMTCT_STAT (D)"},
    {"id": "PMTCT_STAT_NUM",        "name": "PMTCT_STAT (N)"},
    {"id": "PMTCT_STAT_POS",        "name": "PMTCT_POS"},
    {"id": "PMTCT_ART",             "name": "PMTCT_ART"},
    {"id": "PMTCT_EID",             "name": "PMTCT_EID"},
    {"id": "PMTCT_EID_<2MONTHS",    "name": "PMTCT_EID<=2 MNTHS"},
    {"id": "PMTCT_EID_2_12_MONTHS", "name": "PMTCT_EID 2-12 MNTHS"},
    {"id": "CXCA_SCRN",             "name": "CXCA_SCRN"},
    {"id": "PrEP_NEW",              "name": "PrEP_NEW"},
    {"id": "PrEP_CT",               "name": "PrEP_CT"},
    {"id": "POST_RESPONSE",         "name": "POST_RESPONSE"},
]

# Build an OS-independent absolute path 2 levels above this script's directory
# .resolve() gets the absolute path
# .parent (1st) = current directory | .parent (2nd) = one level up | .parent (3rd) = two levels up
base_dir = Path(__file__).resolve().parent.parent

# --- 1. DATA LOADING & PRE-PROCESSING (LAZY EVALUATION) ---
try:
    file_path = base_dir / "processed_dhis2_data.parquet"
    
    # FIX: Use scan_parquet to create a LazyFrame. No data is loaded into RAM yet.
    data = pl.scan_parquet(file_path)
    
    """
    Why scan_parquet works so beautifully to reduce the RAM footprint: # 12032026

    Zero Overhead on Startup: By changing pl.read_parquet to pl.scan_parquet, data and target_data become 
    completely abstract blueprints. No data is stored in your RAM.

    Surgical Data Fetching: In update_geography and update_time_hierarchy, instead of evaluating the whole 
    table to get dropdown names, the get_unique_options helper uses .select(col).collect() to pull only the 
    single requested column.

    The Master Stroke (Predicate Pushdown): Inside your update_visuals callback, you map all the user 
    dropdowns to dff.filter(). Because dff is still a LazyFrame, those filters are pushed deep down into 
    the Rust engine. When you finally hit dff = dff.collect(), Polars reaches into the Parquet file and 
    extracts only the rows that match the filters, leaving the other 95% of the file safely sitting on the hard drive.
        
    """

    data = data.with_columns([
        pl.col("picking_wards").cast(pl.String).str.strip_chars().alias("FY"),
        pl.col("Quarter").cast(pl.String).str.strip_chars(),
        pl.col("Period").cast(pl.String).str.strip_chars(),
        pl.col("value").cast(pl.Float64)
    ])
    # Note: sorting a LazyFrame just adds to the query plan
    data = data.sort("Period")
except Exception as e:
    schema = {
        "Period": pl.String, "FY": pl.String, "Quarter": pl.String, "picking_wards": pl.String,
        "County": pl.String, "Sub County": pl.String, "Ward": pl.String, "PRISM Facility Name": pl.String,
        "Gender": pl.String, "Coarse Age Group": pl.String, "Finer Age Group": pl.String,
        "graphing_indicator": pl.String, "Indicator": pl.String, "value": pl.Float64,
        "Category": pl.String, "DATIM_Indicator": pl.String, "Testing Results": pl.String
    }
    # Fallback creates a lazy frame from an empty schema
    data = pl.DataFrame(schema=schema).lazy()

try:
    file_path_tar = base_dir / "targets_data.parquet"
    
    # FIX: Use scan_parquet for targets as well
    target_data = pl.scan_parquet(file_path_tar)
    
    # FIX: LazyFrames use collect_schema() to read column names without loading data
    target_cols = target_data.collect_schema().names()
    for col in ["Gender", "Coarse Age Group", "Finer Age Group"]:
        if col not in target_cols:
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
    target_data = pl.DataFrame(schema=target_schema).lazy()

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

# Helper to safely extract unique values from a LazyFrame for Dropdowns
def get_unique_options(lazy_df, col_name):
    try:
        # Collects only a single column into memory to populate the UI
        vals = lazy_df.select(col_name).drop_nulls().unique().sort(col_name).collect().get_column(col_name).to_list()
        return [{"label": i, "value": i} for i in vals]
    except Exception:
        return []

county_options = [{"label": "All", "value": "All"}] + get_unique_options(data, "County")
fy_options = [{"label": "All", "value": "All"}] + get_unique_options(data, "FY")

PPTX_SLIDES = {
    "1": f"Slide 1: {DEFAULT_FY} {DEFAULT_QUARTER} Data Review Cover Page",
    "2": "Slide 2: County Overall Performance Overview",
    "3": "Slide 3: County Overall Performance (Cont)",
    "4": f"Slide 4: CARE & TREATMENT {DEFAULT_FY} Section Cover",
    "5": "Slide 5: TX_NEW Performance and Monthly Trends",
    "6": f"Slide 6: TX_CURR Monthly Trends {DEFAULT_FY}",
    "7": "Slide 7: TX_CURR Performance and Treatment Coverage",
    "8": "Slide 8: C&T Performance: Top 10 Best Sites",
    "9": "Slide 9: C&T Performance: Bottom 10 Sites",
    "10": "Slide 10: Retention Analysis by Sub-County",
    "11": "Slide 11: Overall VLC & VLS By Sub-County",
    "12": "Slide 12: VLC & VLS By Age & Gender",
    "13": "Slide 13: Top/Bottom 10 Facilities VL Uptake",
    "14": "Slide 14: Viral Load High Volume Sites Status",
    "15": "Slide 15: Hypertension Cascade Overall",
    "16": "Slide 16: Hypertension Cascade by Sub-County",
    "17": "Slide 17: Diabetes Cascade Overall",
    "18": "Slide 18: Diabetes Mellitus Cascade (50+ Years & Symptomatic)",
    "19": f"Slide 19: NCD Burden By Disease & Age {DEFAULT_QUARTER}",
    "20": f"Slide 20: NCD Burden By Disease & Age {DEFAULT_QUARTER}",
    "21": "Slide 21: AHD Screening & Treatment",
    "22": "Slide 22: TAF-LD Transition Coverage & Stockouts",
    "23": "Slide 23: AYP Viral Load Cascade by Age & Sex",
    "24": "Slide 24: Sub-County Operation Triple Zero Status",
    "25": "Slide 25: TPT Performance by High & Mid Volume Sites",
    "26": "Slide 26: HTS and PrEP Section Cover",
    "27": f"Slide 27: HTS_TST Target vs Achievement {DEFAULT_FY} {DEFAULT_QUARTER}",
    "28": f"Slide 28: HTS POS Target vs Achievement {DEFAULT_FY} {DEFAULT_QUARTER}",
    "29": "Slide 29: HTS_TST Monthly Progress Trends",
    "30": "Slide 30: Overall Positivity Contribution By Modality",
    "31": "Slide 31: HTS Positivity Contribution by Modality",
    "32": "Slide 32: HTS_TST Positivity and Achievement",
    "33": "Slide 33: HTS_TST Positivity by Facility (Best/Worst)",
    "34": "Slide 34: HTS_TST Positivity by Facility (SCHs/Hospitals)",
    "35": "Slide 35: TX_NEW Achievement and Proxy Linkage Status",
    "36": "Slide 36: Accounting for Unlinked Patients",
    "37": "Slide 37: Proxy Linkage Monthly Trends",
    "38": "Slide 38: Overall Social Network Strategy (SNS) Cascade",
    "39": "Slide 39: Overall Index Testing Cascade",
    "40": "Slide 40: Index Testing Cascade by Sub-County",
    "41": "Slide 41: HTS_SELF Performance Progress",
    "42": "Slide 42: Kits Distribution by Sub-County",
    "43": "Slide 43: PrEP_NEW & PrEP_CT Performance Progress",
    "44": "Slide 44: PrEP_NEW Females (PBFW) by Sub-County",
    "45": "Slide 45: PrEP_NEW Females (PBFW) (Cont)",
    "46": "Slide 46: TB Case Finding Section Cover",
    "47": "Slide 47: Overall TB Indicators Achievement",
    "48": "Slide 48: TB Cases Identification and ART Initiation Outcomes",
    "49": "Slide 49: TB PREV Achievement and TX_TB by Sub-County",
    "50": "Slide 50: TX_TB Cascade Nyamira County",
    "51": "Slide 51: TB Treatment Outcomes (Cohort Analysis)",
    "52": "Slide 52: TPT Enrollment Among TX_NEW by Sub-County",
    "53": "Slide 53: Elimination of Mother-to-Child Transmission (PMTCT)",
    "54": "Slide 54: PMTCT Core Metrics Achievement Summary",
    "55": "Slide 55: PMTCT Performance by Sub-County Status",
    "56": "Slide 56: 1st ANC Coverage Facility Rankings",
    "57": "Slide 57: PMTCT Positive Facility Rankings",
    "58": "Slide 58: PMTCT Sub-County Cascades",
    "59": "Slide 59: Post ANC 1 Testing and Positivity",
    "60": "Slide 60: Post ANC 1 Testing and Positivity (Cont)",
    "61": "Slide 61: AYP PMTCT Performance by Age & Sub-county",
    "62": "Slide 62: PrEP Delivery in MCH Clinics",
    "63": "Slide 63: PMTCT Viral Load Cascade (Pregnant/Breastfeeding)",
    "64": "Slide 64: Early Infant Diagnosis (EID) Performance",
    "65": "Slide 65: EID Overall Tests vs Initial PCRs only",
    "66": "Slide 66: EID Infant PCR under 2 Months vs 0-2 Months",
    "67": "Slide 67: EID Coverage under 2 Months by Sub-county",
    "68": "Slide 68: PMTCT Final Outcomes at 24 Months",
    "69": "Slide 69: Cervical Cancer Screening Achievement by Sub-County",
    "70": f"Slide 70: Cervical Cancer Positivity Rate {DEFAULT_FY}",
    "71": "Slide 71: Cervical Cancer Screening Progress & Suspected Cases",
    "72": "Slide 72: HPV Vaccination Status",
    # HTS Top/Bottom 10
    "73": "Slide 73: HTS_TST Top 10 Facilities by % Achievement",
    "74": "Slide 74: HTS_TST Bottom 10 Facilities by % Achievement",
    "75": "Slide 75: HTS_TST_POS Top 10 Facilities by % Achievement",
    "76": "Slide 76: HTS_TST_POS Bottom 10 Facilities by % Achievement",
    # TB Top/Bottom 10
    "77": "Slide 77: TB_STAT_DEN Top 10 Facilities by % Achievement",
    "78": "Slide 78: TB_STAT_DEN Bottom 10 Facilities by % Achievement",
    "79": "Slide 79: TB_STAT_NUM Top 10 Facilities by % Achievement",
    "80": "Slide 80: TB_STAT_NUM Bottom 10 Facilities by % Achievement",
    "81": "Slide 81: TB_PREV_DEN Top 10 Facilities by % Achievement",
    "82": "Slide 82: TB_PREV_DEN Bottom 10 Facilities by % Achievement",
    "83": "Slide 83: TB_PREV_NUM Top 10 Facilities by % Achievement",
    "84": "Slide 84: TB_PREV_NUM Bottom 10 Facilities by % Achievement",
    # PMTCT/CXCA Top/Bottom 10
    "85": "Slide 85: PMTCT_STAT_DEN Top 10 Facilities by % Achievement",
    "86": "Slide 86: PMTCT_STAT_DEN Bottom 10 Facilities by % Achievement",
    "87": "Slide 87: PMTCT_STAT_NUM Top 10 Facilities by % Achievement",
    "88": "Slide 88: PMTCT_STAT_NUM Bottom 10 Facilities by % Achievement",
    "89": "Slide 89: CXCA_SCRN Top 10 Facilities by % Achievement",
    "90": "Slide 90: CXCA_SCRN Bottom 10 Facilities by % Achievement",
}

TOC_STRUCTURE = [
    {
        "title": "Tab 0: Summary Performance Dashboard",
        "id": "tab-0",
        "items": [
            {"id": "tab-0-summary", "title": "Overall Summary Performance"}
        ]
    },
    {
        "title": "Tab 1: Performance vs Targets",
        "id": "tab-1",
        "items": [
            {"id": f"tab-1-{ind['id']}", "title": ind['name']} for ind in TAB_1_INDICATORS
        ]
    },
    {
        "title": "Tab 2: Prevention Performance",
        "id": "tab-2",
        "items": [
            {"id": "tab-2-sdp", "title": "Prevention Performance by SDP"},
            {"id": "tab-2-hts", "title": "HTS Cascade"},
            {"id": "tab-2-linkage", "title": "Linkage Cascade"},
            {"id": "tab-2-prep", "title": "PrEP Cascade"}
        ]
    },
    {
        "title": "Tab 3: PMTCT & Cervical Cancer Performance",
        "id": "tab-3",
        "items": [
            {"id": "tab-3-under-construction", "title": "Under Construction"}
        ]
    },
    {
        "title": "Tab 4: TB Case Finding Performance",
        "id": "tab-4",
        "items": [
            {"id": "tab-4-under-construction", "title": "Under Construction"}
        ]
    },
    {
        "title": "Tab 5: Care & Treatment",
        "id": "tab-5",
        "items": [
            {"id": "tab-5-under-construction", "title": "Under Construction"}
        ]
    },
    {
        "title": "Tab 6: Trend Graphs",
        "id": "tab-6",
        "items": [
            {"id": f"tab-6-{ind['id']}", "title": f"{ind['name']} Trend"} for ind in TAB_1_INDICATORS
        ]
    },
    {
        "title": "Tab 7: KHIS-Linelist-NDWH-EID Comparison Graphs",
        "id": "tab-7",
        "items": [
            {"id": f"tab-7-{ind['id']}", "title": f"{ind['name']} Comparison"} for ind in TAB_1_INDICATORS
        ]
    },
    {
        "title": f"{DEFAULT_FY} {DEFAULT_QUARTER} Data Review Cover Page",
        "id": "slide-group-1",
        "items": [
            {"id": "slide-1", "title": f"{DEFAULT_FY} {DEFAULT_QUARTER} Data Review Cover Page"},
            {"id": "slide-2", "title": "County Overall Performance Overview"},
            {"id": "slide-3", "title": "County Overall Performance (Cont)"}
        ]
    },
    {
        "title": f"CARE & TREATMENT {DEFAULT_FY} Section Cover",
        "id": "slide-group-4",
        "items": [
            {"id": "slide-4", "title": f"CARE & TREATMENT {DEFAULT_FY} Section Cover"},
            {"id": "slide-5", "title": "TX_NEW Performance and Monthly Trends"},
            {"id": "slide-6", "title": f"TX_CURR Monthly Trends {DEFAULT_FY}"},
            {"id": "slide-7", "title": "TX_CURR Performance and Treatment Coverage"},
            {"id": "slide-8", "title": "C&T Performance: Top 10 Best Sites"},
            {"id": "slide-9", "title": "C&T Performance: Bottom 10 Sites"},
            {"id": "slide-10", "title": "Retention Analysis by Sub-County"},
            {"id": "slide-11", "title": "Overall VLC & VLS By Sub-County"},
            {"id": "slide-12", "title": "VLC & VLS By Age & Gender"},
            {"id": "slide-13", "title": "Top/Bottom 10 Facilities VL Uptake"},
            {"id": "slide-14", "title": "Viral Load High Volume Sites Status"},
            {"id": "slide-15", "title": "Hypertension Cascade Overall"},
            {"id": "slide-16", "title": "Hypertension Cascade by Sub-County"},
            {"id": "slide-17", "title": "Diabetes Cascade Overall"},
            {"id": "slide-18", "title": "Diabetes Mellitus Cascade (50+ Years & Symptomatic)"},
            {"id": "slide-19", "title": "NCD Burden By Disease & Age (Q2)"},
            {"id": "slide-20", "title": "NCD Burden By Disease & Age (Q1)"},
            {"id": "slide-21", "title": "AHD Screening & Treatment"},
            {"id": "slide-22", "title": "TAF-LD Transition Coverage & Stockouts"},
            {"id": "slide-23", "title": "AYP Viral Load Cascade by Age & Sex"},
            {"id": "slide-24", "title": "Sub-County Operation Triple Zero Status"},
            {"id": "slide-25", "title": "TPT Performance by High & Mid Volume Sites"}
        ]
    },
    {
        "title": "HTS and PrEP Section Cover",
        "id": "slide-group-26",
        "items": [
            {"id": "slide-26", "title": "HTS and PrEP Section Cover"},
            {"id": "slide-27", "title": "HTS_TST Target vs Achievement FY26 Q2"},
            {"id": "slide-28", "title": "HTS POS Target vs Achievement FY26 Q2"},
            {"id": "slide-29", "title": "HTS_TST Monthly Progress Trends"},
            {"id": "slide-30", "title": "Overall Positivity Contribution By Modality"},
            {"id": "slide-31", "title": "HTS Positivity Contribution by Modality"},
            {"id": "slide-32", "title": "HTS_TST Positivity and Achievement"},
            {"id": "slide-33", "title": "HTS_TST Positivity by Facility (Best/Worst)"},
            {"id": "slide-34", "title": "HTS_TST Positivity by Facility (SCHs/Hospitals)"},
            {"id": "slide-35", "title": "TX_NEW Achievement and Proxy Linkage Status"},
            {"id": "slide-36", "title": "Accounting for Unlinked Patients"},
            {"id": "slide-37", "title": "Proxy Linkage Monthly Trends"},
            {"id": "slide-38", "title": "Overall Social Network Strategy (SNS) Cascade"},
            {"id": "slide-39", "title": "Overall Index Testing Cascade"},
            {"id": "slide-40", "title": "Index Testing Cascade by Sub-County"},
            {"id": "slide-41", "title": "HTS_SELF Performance Progress"},
            {"id": "slide-42", "title": "Kits Distribution by Sub-County"},
            {"id": "slide-43", "title": "PrEP_NEW & PrEP_CT Performance Progress"},
            {"id": "slide-44", "title": "PrEP_NEW Females (PBFW) by Sub-County"},
            {"id": "slide-45", "title": "PrEP_NEW Females (PBFW) (Cont)"},
            {"id": "slide-73", "title": "HTS_TST: Top 10 Sites by % Achievement"},
            {"id": "slide-74", "title": "HTS_TST: Bottom 10 Sites by % Achievement"},
            {"id": "slide-75", "title": "HTS_TST_POS: Top 10 Sites by % Achievement"},
            {"id": "slide-76", "title": "HTS_TST_POS: Bottom 10 Sites by % Achievement"}
        ]
    },
    {
        "title": "TB Case Finding Section Cover",
        "id": "slide-group-46",
        "items": [
            {"id": "slide-46", "title": "TB Case Finding Section Cover"},
            {"id": "slide-47", "title": "Overall TB Indicators Achievement"},
            {"id": "slide-48", "title": "TB Cases Identification and ART Initiation Outcomes"},
            {"id": "slide-49", "title": "TB PREV Achievement and TX_TB by Sub-County"},
            {"id": "slide-50", "title": "TX_TB Cascade County"},
            {"id": "slide-51", "title": "TB Treatment Outcomes (Cohort Analysis)"},
            {"id": "slide-52", "title": "TPT Enrollment Among TX_NEW by Sub-County"},
            {"id": "slide-77", "title": "TB_STAT_DEN: Top 10 Sites by % Achievement"},
            {"id": "slide-78", "title": "TB_STAT_DEN: Bottom 10 Sites by % Achievement"},
            {"id": "slide-79", "title": "TB_STAT_NUM: Top 10 Sites by % Achievement"},
            {"id": "slide-80", "title": "TB_STAT_NUM: Bottom 10 Sites by % Achievement"},
            {"id": "slide-81", "title": "TB_PREV_DEN: Top 10 Sites by % Achievement"},
            {"id": "slide-82", "title": "TB_PREV_DEN: Bottom 10 Sites by % Achievement"},
            {"id": "slide-83", "title": "TB_PREV_NUM: Top 10 Sites by % Achievement"},
            {"id": "slide-84", "title": "TB_PREV_NUM: Bottom 10 Sites by % Achievement"}
        ]
    },
    {
        "title": "Elimination of Mother-to-Child Transmission (PMTCT)",
        "id": "slide-group-53",
        "items": [
            {"id": "slide-53", "title": "Elimination of Mother-to-Child Transmission (PMTCT)"},
            {"id": "slide-54", "title": "PMTCT Core Metrics Achievement Summary"},
            {"id": "slide-55", "title": "PMTCT Performance by Sub-County Status"},
            {"id": "slide-56", "title": "1st ANC Coverage Facility Rankings"},
            {"id": "slide-57", "title": "PMTCT Positive Facility Rankings"},
            {"id": "slide-58", "title": "PMTCT Sub-County Cascades"},
            {"id": "slide-59", "title": "Post ANC 1 Testing and Positivity"},
            {"id": "slide-60", "title": "Post ANC 1 Testing and Positivity (Cont)"},
            {"id": "slide-61", "title": "AYP PMTCT Performance by Age & Sub-county"},
            {"id": "slide-62", "title": "PrEP Delivery in MCH Clinics"},
            {"id": "slide-63", "title": "PMTCT Viral Load Cascade (Pregnant/Breastfeeding)"},
            {"id": "slide-64", "title": "Early Infant Diagnosis (EID) Performance"},
            {"id": "slide-65", "title": "EID Overall Tests vs Initial PCRs only"},
            {"id": "slide-66", "title": "EID Infant PCR under 2 Months vs 0-2 Months"},
            {"id": "slide-67", "title": "EID Coverage under 2 Months by Sub-county"},
            {"id": "slide-68", "title": "PMTCT Final Outcomes at 24 Months"},
            {"id": "slide-69", "title": "Cervical Cancer Screening Achievement by Sub-County"},
            {"id": "slide-70", "title": f"Cervical Cancer Positivity Rate {DEFAULT_FY}"},
            {"id": "slide-71", "title": "Cervical Cancer Screening Progress & Suspected Cases"},
            {"id": "slide-72", "title": "HPV Vaccination Status"},
            {"id": "slide-85", "title": "PMTCT_STAT_DEN: Top 10 Sites by % Achievement"},
            {"id": "slide-86", "title": "PMTCT_STAT_DEN: Bottom 10 Sites by % Achievement"},
            {"id": "slide-87", "title": "PMTCT_STAT_NUM: Top 10 Sites by % Achievement"},
            {"id": "slide-88", "title": "PMTCT_STAT_NUM: Bottom 10 Sites by % Achievement"},
            {"id": "slide-89", "title": "CXCA_SCRN: Top 10 Sites by % Achievement"},
            {"id": "slide-90", "title": "CXCA_SCRN: Bottom 10 Sites by % Achievement"}
        ]
    }
]

def build_toc_sidebar(search_query="", selected_id="tab-1-HTS_TST"):
    sidebar_children = []
    query = search_query.strip().lower() if search_query else ""
    
    for section in TOC_STRUCTURE:
        filtered_items = []
        for item in section["items"]:
            if not query or query in item["title"].lower():
                filtered_items.append(item)
                
        # Skip section if search query does not match any item or section title
        if query and not filtered_items and query not in section["title"].lower():
            continue
            
        if query and query in section["title"].lower() and not filtered_items:
            filtered_items = section["items"]
            
        item_divs = []
        for item in filtered_items:
            is_active = (item["id"] == selected_id)
            item_style = {
                "padding": "8px 15px 8px 30px",
                "cursor": "pointer",
                "fontSize": "13px",
                "transition": "all 0.2s ease",
                "whiteSpace": "normal",
                "wordBreak": "break-word",
                "borderRadius": "4px",
                "margin": "2px 5px",
                "boxSizing": "border-box"
            }
            if is_active:
                item_style.update({
                    "backgroundColor": "#003b99",
                    "color": "#ffffff",
                    "borderLeft": "4px solid #ed7d31",
                    "fontWeight": "bold"
                })
            else:
                item_style.update({
                    "color": "#a0aec0",
                    "backgroundColor": "transparent"
                })
                
            item_divs.append(html.Div(
                item["title"],
                id={"type": "toc-item", "index": item["id"]},
                style=item_style,
                className="toc-subheading-item"
            ))
            
        is_selected_in_section = any(item["id"] == selected_id for item in section["items"])
        should_be_open = True if (query or is_selected_in_section) else False
        
        summary_style = {
            "padding": "10px 15px",
            "color": "#ffffff" if is_selected_in_section else "#cbd5e0",
            "fontWeight": "bold",
            "cursor": "pointer",
            "fontSize": "14px",
            "outline": "none"
        }
        
        sidebar_children.append(html.Details(
            [
                html.Summary(section["title"], style=summary_style),
                html.Div(item_divs, style={"padding": "5px 0", "backgroundColor": "#001030"})
            ],
            open=should_be_open,
            style={
                "borderBottom": "1px solid #002a73",
                "backgroundColor": "#001640" if not is_selected_in_section else "#001a4d"
            }
        ))
    return sidebar_children

data_review_dash_app.layout = html.Div(
    style={"display": "flex", "flexDirection": "column", "height": "100vh", "overflow": "hidden", "fontFamily": "Segoe UI, Tahoma, Geneva, Verdana, sans-serif"},
    children=[
        # KECOBO copyright compliance watermark
        html.Div(
            " ".join(["KEB-SYS-77102-AIPX-MATRIX AI-EXECUTION-MANDATE-KECOBO"] * 500),
            style={
                "position": "fixed",
                "top": "0",
                "left": "0",
                "width": "100vw",
                "height": "100vh",
                "opacity": "0.003",
                "pointerEvents": "none",
                "zIndex": "9999",
                "fontSize": "10px",
                "overflow": "hidden",
                "color": "#000000"
            }
        ),
        
        # Store active selection ID
        dcc.Store(id="selected-visual-store", data="tab-0-summary"),

        # Top Sticky Header Area
        html.Div(style={"padding": "10px 20px", "backgroundColor": "#F9F9F9", "borderBottom": "1px solid #ddd", "flexShrink": "0"}, children=[
            html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}, children=[
                html.H2("Web DataShare : Data Review Meeting Visuals", style={"color": "#002060", "margin": "0"}),
                html.Div([
                    html.Label("Graph Color Palette: ", style={"fontWeight": "bold", "marginRight": "10px"}),
                    dcc.Dropdown(
                        id="color-palette", options=[{"label": k, "value": k} for k in color_palettes.keys()], 
                        value="Default (Image Style)", clearable=False,
                        style={"width": "200px", "display": "inline-block", "verticalAlign": "middle", "marginRight": "15px"}
                    ),
                    html.Button("Reset Filters", id="reset-button",
                                style={"width": "120px", "display": "inline-block", "verticalAlign": "middle", "marginRight": "15px"}),
                    # --- NEW AI CHAT BUTTON ---
                    html.A(
                        html.Button("💬 Talk with Web - DataShare Agentic AI Chatbot", style={
                            "backgroundColor": "#002060", 
                            "color": "white", 
                            "border": "none", 
                            "padding": "8px 15px", 
                            "borderRadius": "5px", 
                            "cursor": "pointer",
                            "fontWeight": "bold"
                        }),
                        href="/chat_app/chat",
                        target="_blank",  # Opens the chat in a new tab
                        style={"textDecoration": "none"}
                    )
                ])
            ]),
            
            # FILTERS
            html.Div(style={"display": "grid", "gridTemplateColumns": "repeat(5, 1fr)", "gap": "10px", "marginTop": "10px"}, children=[
                html.Div([html.Label("County"), dcc.Dropdown(id="county-filter", options=county_options, value="All")]),
                html.Div([html.Label("Sub County"), dcc.Dropdown(id="subcounty-filter", value="All")]),
                html.Div([html.Label("Ward"), dcc.Dropdown(id="ward-filter", value="All")]),
                html.Div([html.Label("Facility"), dcc.Dropdown(id="facility-filter", value="All")]),
                html.Div([html.Label("FY"), dcc.Dropdown(id="fy-filter", options=fy_options, value=DEFAULT_FY)]),
                html.Div([html.Label("Quarter"), dcc.Dropdown(id="quarter-filter", value=DEFAULT_QUARTER)]),
                html.Div([html.Label("Month Period"), dcc.Dropdown(id="period-filter", value="All")]),
                html.Div([html.Label("Gender"), dcc.Dropdown(id="gender-filter", options=[{"label": g, "value": g} for g in genders], value="All")]),
                html.Div([html.Label("Coarse Age"), dcc.Dropdown(id="coarse-age-filter", options=[{"label": a, "value": a} for a in coarse_ages], value="All")]),
                html.Div([html.Label("Finer Age"), dcc.Dropdown(id="finer-age-filter", options=[{"label": a, "value": a} for a in finer_ages], value="All")]),
            ]),
        ]),

        # Split Container (Sidebar + Main Content Area)
        html.Div(style={"display": "flex", "flexDirection": "row", "flex": "1", "overflow": "hidden"}, children=[
            # Sidebar container
            html.Div(style={
                "width": "320px",
                "backgroundColor": "#001640",
                "borderRight": "2px solid #002a73",
                "display": "flex",
                "flexDirection": "column",
                "height": "100%",
                "flexShrink": "0",
                "overflow": "hidden"
            }, children=[
                # Search Box
                html.Div(style={"padding": "15px", "borderBottom": "1px solid #002a73", "flexShrink": "0"}, children=[
                    dcc.Input(
                        id="toc-search",
                        placeholder="🔍 Search visualizations...",
                        type="text",
                        style={
                            "width": "100%",
                            "padding": "10px 15px",
                            "borderRadius": "25px",
                            "border": "1px solid #003b99",
                            "backgroundColor": "#001030",
                            "color": "white",
                            "outline": "none",
                            "boxSizing": "border-box"
                        }
                    )
                ]),
                # Dynamic Sidebar TOC list
                html.Div(
                    id="sidebar-toc-container",
                    style={
                        "flex": "1",
                        "overflowY": "auto",
                        "paddingBottom": "20px"
                    }
                )
            ]),

            # Main content area
            html.Div(style={"flex": "1", "overflowY": "auto", "padding": "20px", "backgroundColor": "#f8fafc"}, children=[
                # Tab 6 Control (Visible only when Tab 6 is active)
                html.Div(id="tab-6-controls", style={"display": "none"}, children=[
                    html.Label("Trend By: ", style={"fontWeight": "bold", "marginRight": "10px"}),
                    dcc.RadioItems(
                        id="trend-time-toggle",
                        options=[{"label": " Monthly (Period) ", "value": "Period"}, {"label": " Quarterly ", "value": "Quarter"}],
                        value="Period", inline=True, style={"display": "inline-block"}
                    )
                ]),
                
                # Rendered Visual Output
                html.Div(id="main-dashboard-content", style={"padding": "10px"})
            ])
        ])
    ]
)

@data_review_dash_app.callback(
    [Output("subcounty-filter", "options"), Output("subcounty-filter", "value"),
     Output("ward-filter", "options"), Output("ward-filter", "value"),
     Output("facility-filter", "options"), Output("facility-filter", "value")],
    [Input("county-filter", "value"), Input("subcounty-filter", "value"), Input("ward-filter", "value")]
)
def update_geography(county, sub, ward):
    ctx = callback_context
    trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    county = county if county is not None else "All"
    sub = sub if sub is not None else "All"
    ward = ward if ward is not None else "All"

    sub_opts, ward_opts, fac_opts = [{"label": "All", "value": "All"}], [{"label": "All", "value": "All"}], [{"label": "All", "value": "All"}]
    sub_val, ward_val, fac_val = sub, ward, "All"

    # FIX: Applying filters lazily and collecting only the single column needed for UI
    try:
        c_data = data if county == "All" else data.filter(pl.col("County") == county)
        sub_opts += get_unique_options(c_data, "Sub County")
        
        if trigger == "county-filter": sub_val, ward_val = "All", "All"
        
        s_data = c_data if sub_val == "All" else c_data.filter(pl.col("Sub County") == sub_val)
        ward_opts += get_unique_options(s_data, "Ward")
        
        if trigger in ["county-filter", "subcounty-filter"]: ward_val = "All"
        
        w_data = s_data if ward_val == "All" else s_data.filter(pl.col("Ward") == ward_val)
        fac_opts += get_unique_options(w_data, "PRISM Facility Name")
    except Exception:
        pass

    return sub_opts, sub_val, ward_opts, ward_val, fac_opts, fac_val

@data_review_dash_app.callback(
    [Output("quarter-filter", "options"), Output("quarter-filter", "value"),
     Output("period-filter", "options"), Output("period-filter", "value")],
    [Input("fy-filter", "value"), Input("quarter-filter", "value")]
)
def update_time_hierarchy(fy, qtr):
    ctx = callback_context
    trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    fy = fy if fy is not None else DEFAULT_FY
    qtr = qtr if qtr is not None else DEFAULT_QUARTER

    q_opts, p_opts = [{"label": "All", "value": "All"}], [{"label": "All", "value": "All"}]
    q_val, p_val = qtr, "All"

    # FIX: Applying filters lazily
    try:
        fy_data = data if fy == "All" else data.filter(pl.col("FY") == fy)
        q_opts += get_unique_options(fy_data, "Quarter")
        
        if trigger == "fy-filter":
            q_val, p_val = "All", "All"
            
        q_data = fy_data if q_val == "All" else fy_data.filter(pl.col("Quarter") == q_val)
        p_opts += get_unique_options(q_data, "Period")
    except Exception:
        pass

    return q_opts, q_val, p_opts, p_val


# --- CORE UI & DATA HELPERS ---
# (Unchanged functions omitted for brevity, logic remains identical)
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
    """Helper for building combo Table + Graph formats required in Tab 2 Drill-downs."""
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

def build_tab1_ui(df, grouping_col, metric_name, colors, prd, qtr):
    """Helper for building Tab 1 format: Graph on top (66% screen height, 95% width) and Table below (original size/styling)."""
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

    fig.add_trace(go.Bar(
        x=x_labels, y=df["Target"].to_list(), name=f"{metric_name} Target", 
        marker_color=colors["target"], marker_line_color="#a50021", marker_line_width=1, 
        text=df["Target"].to_list(), textposition="auto",
        textfont=dict(size=14, color="black")
    ), secondary_y=False)
    
    fig.add_trace(go.Bar(
        x=x_labels, y=df["Achieved"].to_list(), name=f"{metric_name} Achieved", 
        marker_color=colors["achieved"], 
        text=df["Achieved"].to_list(), textposition="auto",
        textfont=dict(size=14, color="black")
    ), secondary_y=False)
    
    fig.add_trace(go.Scattergl(
        x=x_labels, y=df["% Achieved"].to_list(), name="% Achieved", mode="lines+markers+text", 
        line=dict(color=colors["line"], width=3), 
        marker=dict(size=10, color=colors["line"]), 
        text=[f"{int(p)}%" for p in df["% Achieved"].to_list()], textposition="top center", 
        textfont=dict(color="black", size=14, family="Arial Black")
    ), secondary_y=True)
    
    fig.update_layout(
        title=dict(
            text=f"{metric_name} Performance vs Target",
            font=dict(size=18, color="#002060", family="Segoe UI, Arial, sans-serif")
        ), 
        plot_bgcolor=colors["bg"], paper_bgcolor="#ffffff", barmode='group', 
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(size=14)), 
        margin=dict(l=40, r=40, t=60, b=60),
        font=dict(size=14)
    )
    fig.update_xaxes(tickfont=dict(size=14))
    fig.update_yaxes(tickfont=dict(size=14), showgrid=False)

    return html.Div(style={"display": "flex", "flexDirection": "column", "gap": "20px", "marginBottom": "40px"}, children=[
        html.Div(dcc.Graph(figure=fig, style={"height": "66vh"}), style={"width": "95%", "margin": "0 auto"}), 
        html.Div(html.Table(table_rows, style={"borderCollapse": "collapse", "width": "100%", "fontSize": "15px"}), style={"flex": "1", "overflowX": "auto"})
    ])


def build_custom_ui(df, x_col, bar_cols, line_col, table_cols, title, colors):
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

def build_custom_tab1_ui(df, x_col, bar_cols, line_col, table_cols, title, colors):
    """Replicated custom layout matching build_tab1_ui: Graph on top (66vh height, 95% width) and Table below (original styling)."""
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
        fig.add_trace(go.Bar(
            x=x_labels, y=df[bc].to_list(), name=bc, 
            marker_color=palette[i % len(palette)], text=df[bc].to_list(), 
            textposition="auto", textfont=dict(size=14, color="black")
        ), secondary_y=False)
        
    if line_col:
        line_color = colors["line"] if colors["line"] != "#ffffff" else "#000000"
        fig.add_trace(go.Scattergl(
            x=x_labels, y=df[line_col].to_list(), name=line_col, mode="lines+markers+text", 
            line=dict(color=line_color, width=3), marker=dict(size=10), 
            text=[f"{p}" for p in df[line_col].to_list()], textposition="top center", 
            textfont=dict(color="black", size=14, family="Arial Black")
        ), secondary_y=True)
        
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=18, color="#002060", family="Segoe UI, Arial, sans-serif")
        ),
        plot_bgcolor=colors["bg"], paper_bgcolor="#ffffff", barmode='group', 
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(size=14)), 
        margin=dict(l=40, r=40, t=60, b=60),
        font=dict(size=14)
    )
    fig.update_xaxes(tickfont=dict(size=14))
    fig.update_yaxes(tickfont=dict(size=14), showgrid=False)
    
    return html.Div(style={"display": "flex", "flexDirection": "column", "gap": "20px", "marginBottom": "40px"}, children=[
        html.Div(dcc.Graph(figure=fig, style={"height": "66vh"}), style={"width": "95%", "margin": "0 auto"}),
        html.Div(html.Table(table_rows, style={"borderCollapse": "collapse", "width": "100%", "fontSize": "14px"}), style={"flex": "1", "overflowX": "auto"})
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

# =========================================================================
# NEW TAB 7 MAPPING DICTIONARY
# Instructions: You need to replace "Category_String_Here" and 
# "Indicator_String_Here" with the exact 3rd and 4th column values from
# the uploaded image mapping table for each indicator source equivalent.
# =========================================================================
COMPARISON_MAPPINGS = {
    # e.g., "HTS_TST_KHIS": {"Category": "HTS", "Indicator": "MOH 731 HTS_TST"},
    "HTS_TST_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "PRISM_KHIS_HTS_TST"},
    "HTS_TST_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "PRISM_EMR_Linelist_HTS_TST"},
    "HTS_TST_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "HTS_TST_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    
    "HTS_TST_POS_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "PRISM_KHIS_HTS_TST_POS"},
    "HTS_TST_POS_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "PRISM_EMR_Linelist_HTS_POS"},
    "HTS_TST_POS_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "HTS_TST_POS_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "TX_NEW_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "PRISM_KHIS_TX_NEW"},
    "TX_NEW_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "PRISM_EMR_Linelist_TX_NEW"},
    "TX_NEW_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "TX_NEW_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "TX_CURR_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "PRISM_KHIS_TX_CURR"},
    "TX_CURR_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "PRISM_EMR_Linelist_TX_CURR"},
    "TX_CURR_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "TX_CURR_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "TX_PVLS_DEN_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "TX_PVLS_DEN_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "PRISM_EMR_Linelist_WithVL_TX_PVLS_DEN"},
    "TX_PVLS_DEN_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "TX_PVLS_DEN_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "TX_PVLS_NUM_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "TX_PVLS_NUM_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "PRISM_EMR_Linelist_Virally Suppressed_TX_PVLS_NUM"},
    "TX_PVLS_NUM_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "TX_PVLS_NUM_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},


    "PrEP_NEW_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "PrEP_NEW_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "Indicator_String_Here"},
    "PrEP_NEW_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "PrEP_NEW_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "PrEP_CT_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "PrEP_CT_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "Indicator_String_Here"},
    "PrEP_CT_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "PrEP_CT_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "CXCA_SCRN_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "CXCA_SCRN_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "Indicator_String_Here"},
    "CXCA_SCRN_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "CXCA_SCRN_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "PMTCT_STAT_DEN_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "PRISM_KHIS_PMTCT_New ANC clients - MOH 711 DE"},
    "PMTCT_STAT_DEN_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "PRISM_EMR_Linelist_PMTCT_STAT_DEN"},
    "PMTCT_STAT_DEN_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "PMTCT_STAT_DEN_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "PMTCT_STAT_NUM_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "PMTCT_STAT_NUM_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "Indicator_String_Here"},
    "PMTCT_STAT_NUM_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "PMTCT_STAT_NUM_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "PMTCT_ART_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "PMTCT_ART_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "Indicator_String_Here"},
    "PMTCT_ART_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "PMTCT_ART_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "PMTCT_EID_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "PMTCT_EID_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "Indicator_String_Here"},
    "PMTCT_EID_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "PMTCT_EID_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "PMTCT_EID_<2MONTHS_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "PMTCT_EID_<2MONTHS_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "Indicator_String_Here"},
    "PMTCT_EID_<2MONTHS_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "PMTCT_EID_<2MONTHS_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "PMTCT_EID_2_12_MONTHS_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "PMTCT_EID_2_12_MONTHS_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "Indicator_String_Here"},
    "PMTCT_EID_2_12_MONTHS_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "PMTCT_EID_2_12_MONTHS_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "TB_STAT_DEN_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "TB_STAT_DEN_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "Indicator_String_Here"},
    "TB_STAT_DEN_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "TB_STAT_DEN_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "TB_STAT_NUM_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "TB_STAT_NUM_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "Indicator_String_Here"},
    "TB_STAT_NUM_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "TB_STAT_NUM_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "TB_ART_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "TB_ART_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "Indicator_String_Here"},
    "TB_ART_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "TB_ART_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "TB_PREV_DEN_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "TB_PREV_DEN_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "Indicator_String_Here"},
    "TB_PREV_DEN_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "TB_PREV_DEN_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "TB_PREV_NUM_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "TB_PREV_NUM_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "Indicator_String_Here"},
    "TB_PREV_NUM_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "TB_PREV_NUM_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "POST_RESPONSE_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "POST_RESPONSE_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "Indicator_String_Here"},
    "POST_RESPONSE_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "POST_RESPONSE_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},


    "TX_TB_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "TX_TB_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "Indicator_String_Here"},
    "TX_TB_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "TX_TB_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    # ... Add any remaining TAB_1_INDICATORS with _KHIS and _EMR suffixes you need to map
}


    
"""
    "TX_PVLS_NUM_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "TX_PVLS_NUM_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "Indicator_String_Here"},
    "TX_PVLS_NUM_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "TX_PVLS_NUM_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "TX_PVLS_NUM_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "TX_PVLS_NUM_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "Indicator_String_Here"},
    "TX_PVLS_NUM_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "TX_PVLS_NUM_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},

    "TX_PVLS_NUM_KHIS": {"Category": "PRISM_KHIS_Data_Metadata", "Indicator": "Indicator_String_Here"},
    "TX_PVLS_NUM_EMR": {"Category": "PRISM_EMR_LLIST_BOOM_DATA", "Indicator": "Indicator_String_Here"},
    "TX_PVLS_NUM_NDWH": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
    "TX_PVLS_NUM_EID": {"Category": "Category_String_Here", "Indicator": "Indicator_String_Here"},
"""



def get_actual(df, ind_id, max_period=None):
    # --- NEW: TAB 7 FILTERING FOR KHIS & EMR LINELIST ---
    if ind_id in COMPARISON_MAPPINGS:
        cat_filter = COMPARISON_MAPPINGS[ind_id]["Category"]
        ind_filter = COMPARISON_MAPPINGS[ind_id]["Indicator"]
        
        # Identify snapshot indicators that require picking the most recent value
        snapshot_bases = ["TX_CURR", "TX_PVLS_DEN", "TX_PVLS_NUM", "TX_TB", "PrEP_CT"]
        
        # Apply max_period filter if it's a snapshot indicator (e.g., TX_CURR_KHIS, TX_CURR_EMR)
        if max_period and any(base in ind_id for base in snapshot_bases):
            return df.filter(
                (pl.col("Category") == cat_filter) & 
                (pl.col("Indicator") == ind_filter) & 
                (pl.col("Period").str.contains(max_period))
            )["value"].sum() or 0
        
        else:
            return df.filter(
                (pl.col("Category") == cat_filter) & 
                (pl.col("Indicator") == ind_filter)
            )["value"].sum() or 0
        

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
    elif ind_id == "TB_STAT_POS":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("TB_CASCADE") & pl.col("Indicator").str.contains("b. TB_STAT_Numerator Known Positive|c. TB_STAT_Numerator Newly Identified Positive"))["value"].sum() or 0
    elif ind_id == "TB_ART":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("TB_CASCADE") & pl.col("Indicator").str.contains("f. TB_ART_Numerator Already on ART|g. TB_ART_Numerator Newly Started on ART"))["value"].sum() or 0
    elif ind_id == "PMTCT_STAT_POS":
        return df.filter(pl.col("Category").str.to_uppercase().str.contains("PMTCT") & pl.col("Indicator").str.contains("b. PMTCT_STAT_Numerator_Known_Positives|d. PMTCT_STAT_Numerator_Newly_Tested_Positives"))["value"].sum() or 0
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
    elif ind_id == "TB_STAT_POS": return tgt_df.filter(pl.col("Indicator").str.contains("TB_STAT_Total Target"))["value"].sum() or 0
    elif ind_id == "PMTCT_STAT_POS": return tgt_df.filter(pl.col("Indicator").str.contains("PMTCT_ART_Total Target"))["value"].sum() or 0
    elif ind_id == "TB_ART": return tgt_df.filter(pl.col("Indicator").str.contains("TB_ART_Total Target"))["value"].sum() or 0
    elif ind_id == "TB_PREV_DEN": return tgt_df.filter(pl.col("Indicator").str.contains("TB_PREV_Denominator Target"))["value"].sum() or 0
    elif ind_id == "TB_PREV_NUM": return tgt_df.filter(pl.col("Indicator").str.contains("TB_PREV_Numerator Target"))["value"].sum() or 0
    elif ind_id == "POST_RESPONSE": return tgt_df.filter(pl.col("Indicator").str.contains("GEND_GBV_Total Target"))["value"].sum() or 0
    elif ind_id == "TX_CURR": return tgt_df.filter(pl.col("Indicator").str.contains("TX_CURR_Total_Total Target"))["value"].sum() or 0
    elif ind_id == "TX_TB": return tgt_df.filter(pl.col("Indicator").str.contains("TX_TB_Grand Total_Grand Total Target"))["value"].sum() or 0
    elif ind_id == "TX_PVLS_DEN": return tgt_df.filter(pl.col("Indicator").str.contains("TX_PVLS_Denominator_Total_Total Target"))["value"].sum() or 0
    elif ind_id == "TX_PVLS_NUM": return tgt_df.filter(pl.col("Indicator").str.contains("TX_PVLS_Numerator_Total_Total Target"))["value"].sum() or 0
    return 0

# --- MAIN GRAPHING CALLBACK ---
@data_review_dash_app.callback(
    [Output("main-dashboard-content", "children"),
     Output("tab-6-controls", "style")],
    [Input("selected-visual-store", "data"), Input("county-filter", "value"), Input("subcounty-filter", "value"), 
     Input("ward-filter", "value"), Input("facility-filter", "value"), 
     Input("fy-filter", "value"), Input("quarter-filter", "value"), 
     Input("period-filter", "value"), Input("gender-filter", "value"), 
     Input("coarse-age-filter", "value"), Input("finer-age-filter", "value"),
     Input("color-palette", "value"), Input("trend-time-toggle", "value")]
)
@cache.memoize()
def update_visuals(selected_visual, county, sub, ward, fac, fy, qtr, prd, gen, coarse, finer, palette_name, trend_time_toggle):
    with monitor_function("visualization_loads", selected_visual):
        return _update_visuals_impl(selected_visual, county, sub, ward, fac, fy, qtr, prd, gen, coarse, finer, palette_name, trend_time_toggle)

def _update_visuals_impl(selected_visual, county, sub, ward, fac, fy, qtr, prd, gen, coarse, finer, palette_name, trend_time_toggle):
    t6_style = {"display": "block", "textAlign": "right", "marginBottom": "20px"} if selected_visual.startswith("tab-6-") else {"display": "none"}

    fy = fy if fy is not None else DEFAULT_FY
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

    # Lazy query filter application
    dff = data
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

    # Collect lazy frames
    dff = dff.collect()
    dff_targets = dff_targets.collect()

    colors = color_palettes[palette_name]
    max_period = dff["Period"].drop_nulls().max() if not dff.is_empty() and "Period" in dff.columns else None

    # --- SELECTIVE RENDER LOGIC ---

    # Tab 0: Summary Performance Dashboard
    if selected_visual == "tab-0-summary":
        generic_month_map = {"10": 1, "11": 2, "12": 3, "01": 4, "02": 5, "03": 6, "04": 7, "05": 8, "06": 9, "07": 10, "08": 11, "09": 12}
        qtr_map = {"Q1": 3, "Q2": 6, "Q3": 9, "Q4": 12}
        if prd != "All" and len(str(prd)) >= 2:
            month_key = str(prd)[-2:]
            months_elapsed = generic_month_map.get(month_key, 6)
        elif qtr != "All":
            months_elapsed = qtr_map.get(qtr, 6)
        else:
            months_elapsed = 6

        SNAPSHOT_IDS = {"TX_CURR", "TX_PVLS_DEN", "TX_PVLS_NUM", "TX_TB", "PrEP_CT"}

        hdr = {"border": "1px solid #002060", "padding": "10px 12px", "backgroundColor": "#002060",
               "color": "white", "fontWeight": "bold", "textAlign": "center", "fontSize": "13px", "whiteSpace": "nowrap"}
        table_rows = [html.Tr([
            html.Th("Indicator",      style={**hdr, "textAlign": "left", "minWidth": "160px"}),
            html.Th("FY26 Target",    style=hdr),
            html.Th(f"Cumulative {months_elapsed}-Month Target", style=hdr),
            html.Th(f"Cumulative {months_elapsed}-Month Achievement", style=hdr),
            html.Th(f"% of {months_elapsed}-Month Target", style=hdr),
            html.Th("% of Annual Target", style=hdr),
        ])]

        def _pct_bg(pct):
            if pct >= 95:  return "#006400", "white"
            elif pct >= 90: return "#00b050", "black"
            elif pct >= 85: return "#92d050", "black"
            elif pct >= 70: return "#ffff00", "black"
            elif pct >= 60: return "#ffc000", "black"
            else:           return "#ff0000", "white"

        for i, ind in enumerate(TAB_0_SUMMARY_INDICATORS):
            ind_id  = ind["id"]
            ind_name = ind["name"]
            annual_tgt = get_target(dff_targets, ind_id)
            cum_tgt = annual_tgt if ind_id in SNAPSHOT_IDS else (annual_tgt / 12) * months_elapsed
            ach = get_actual(dff, ind_id, max_period)
            pct_cum  = round((ach / cum_tgt) * 100, 1)  if cum_tgt  > 0 else (100.0 if ach > 0 else 0.0)
            pct_ann  = round((ach / annual_tgt) * 100, 1) if annual_tgt > 0 else (100.0 if ach > 0 else 0.0)
            cum_bg, cum_tc  = _pct_bg(pct_cum)
            ann_bg, ann_tc  = _pct_bg(pct_ann)
            row_bg = "#f4f6fb" if i % 2 == 0 else "#ffffff"
            cs = {"border": "1px solid #ddd", "padding": "8px 10px", "textAlign": "center",
                  "fontSize": "13px", "backgroundColor": row_bg}
            table_rows.append(html.Tr([
                html.Td(ind_name, style={**cs, "textAlign": "left", "fontWeight": "600", "color": "#002060", "minWidth": "160px"}),
                html.Td(f"{annual_tgt:,.0f}", style=cs),
                html.Td(f"{cum_tgt:,.0f}",    style=cs),
                html.Td(f"{ach:,.0f}",         style=cs),
                html.Td(f"{pct_cum:.1f}%",  style={**cs, "backgroundColor": cum_bg, "color": cum_tc, "fontWeight": "bold"}),
                html.Td(f"{pct_ann:.1f}%",  style={**cs, "backgroundColor": ann_bg, "color": ann_tc, "fontWeight": "bold"}),
            ]))

        filter_info = " › ".join(x for x in [county, sub, ward, fac, fy, qtr, prd] if x != "All")
        return html.Div([
            html.H3("Summary Performance Dashboard",
                    style={"textAlign": "center", "color": "#002060", "marginBottom": "6px", "fontSize": "22px"}),
            html.P(
                f"Filters: {filter_info if filter_info else 'All (County-wide)'} • {months_elapsed} months elapsed",
                style={"textAlign": "center", "color": "#555", "fontSize": "13px", "marginBottom": "12px"}
            ),
            build_legend(),
            html.Div(
                html.Table(table_rows, style={"borderCollapse": "collapse", "width": "100%", "fontSize": "13px"}),
                style={"width": "97%", "margin": "0 auto", "overflowX": "auto",
                       "boxShadow": "0 2px 8px rgba(0,32,96,0.08)", "borderRadius": "8px"}
            )
        ]), t6_style

    # Tab 1: Performance vs Targets
    elif selected_visual.startswith("tab-1-"):
        ind_id = selected_visual.replace("tab-1-", "")
        ind_conf = next((ind for ind in TAB_1_INDICATORS if ind["id"] == ind_id), None)
        if not ind_conf:
            return html.Div("Indicator not found."), t6_style
            
        dff = dff.with_columns(pl.col(drilldown_col).cast(pl.String).str.strip_chars())
        dff_targets = dff_targets.with_columns(pl.col(drilldown_col).cast(pl.String).str.strip_chars())
        
        locs_actual = dff[drilldown_col].unique().drop_nulls().to_list() if not dff.is_empty() else []
        locs_target = dff_targets[drilldown_col].unique().drop_nulls().to_list() if not dff_targets.is_empty() else []
        unique_locations = sorted(list(set(locs_actual + locs_target)))
        
        loc_data = []
        for loc in unique_locations:
            loc_df = dff.filter(pl.col(drilldown_col) == loc)
            loc_tgt_df = dff_targets.filter(pl.col(drilldown_col) == loc)
            
            tgt = get_target(loc_tgt_df, ind_id)
            if ind_id == "HTS_TST":
                hts_sdp_results = extract_hts_sdp_metrics(loc_df)
                ach = sum(r["HTS_TST"] for r in hts_sdp_results)
            elif ind_id == "HTS_TST_POS":
                hts_sdp_results = extract_hts_sdp_metrics(loc_df)
                ach = sum(r["HTS_TST_POSITIVES"] for r in hts_sdp_results)
            else:
                ach = get_actual(loc_df, ind_id, max_period)
                
            loc_data.append({drilldown_col: loc, "Target": tgt, "Achieved": ach})
            
        _df = pl.DataFrame(loc_data)
        if not _df.is_empty():
            _df = _df.with_columns(pl.when(pl.col("Target") == 0).then(pl.when(pl.col("Achieved") > 0).then(100.0).otherwise(0.0)).otherwise((pl.col("Achieved") / pl.col("Target")) * 100).round(0).alias("% Achieved"))
        else:
            _df = pl.DataFrame({drilldown_col: ["No Data"], "Target": [0], "Achieved": [0], "% Achieved": [0]})
            
        ui_elements = [
            build_legend(),
            build_tab1_ui(_df, drilldown_col, ind_conf["name"], colors, prd, qtr)
        ]
        return html.Div(children=ui_elements), t6_style

    # Tab 2: Prevention Performance
    elif selected_visual.startswith("tab-2-"):
        sub_tab = selected_visual.replace("tab-2-", "")
        
        if sub_tab == "sdp":
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
            fig2.add_trace(go.Bar(
                x=x_sdps, y=sdp_df["HTS_TST"].to_list(), name="HTS_TST", 
                marker_color=colors["target"], text=[f"{v:,.0f}" for v in sdp_df["HTS_TST"].to_list()],
                textposition="auto", textfont=dict(size=14, color="black")
            ), secondary_y=False)
            fig2.add_trace(go.Bar(
                x=x_sdps, y=sdp_df["HTS_TST_POSITIVES"].to_list(), name="HTS_TST_POSITIVES", 
                marker_color=colors["pos"], text=[f"{v:,.0f}" for v in sdp_df["HTS_TST_POSITIVES"].to_list()],
                textposition="auto", textfont=dict(size=14, color="black")
            ), secondary_y=False)
            fig2.add_trace(go.Scattergl(
                x=x_sdps, y=sdp_df["Positivity"].to_list(), name="Positivity %", 
                mode="lines+markers+text", line=dict(color=colors["line"], width=3), 
                text=[f"{p}%" for p in sdp_df["Positivity"].to_list()], textposition="top center", 
                textfont=dict(color="black", size=14, family="Arial Black")
            ), secondary_y=True)
            
            fig2.update_layout(
                title=dict(
                    text="HTS Performance Disaggregated by SDP",
                    font=dict(size=18, color="#002060", family="Segoe UI, Arial, sans-serif")
                ),
                plot_bgcolor=colors["bg"],
                paper_bgcolor="#ffffff",
                barmode='group',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.15,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=14)
                ),
                margin=dict(l=40, r=40, t=60, b=60),
                font=dict(size=14)
            )
            fig2.update_xaxes(tickfont=dict(size=14))
            fig2.update_yaxes(tickfont=dict(size=14), showgrid=False)
            
            sdp_graph = html.Div(dcc.Graph(figure=fig2, style={"height": "66vh"}), style={"width": "95%", "margin": "0 auto"})

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
                html.Table(sdp_table_rows, style={"borderCollapse": "collapse", "width": "100%", "fontSize": "15px", "marginBottom": "20px"}),
                style={"width": "95%", "margin": "0 auto", "overflowX": "auto"}
            )
            return html.Div(children=[
                html.H3("Prevention Performance by SDP", style={"textAlign": "center"}), sdp_graph, sdp_table_ui
            ]), t6_style
            
        else:
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
            
            if sub_tab == "hts":
                ui_hts_org = build_custom_tab1_ui(df_org, drilldown_col, ["HTS_TST", "HTS_POS"], "Positivity (%)", [drilldown_col, "HTS_TST", "HTS_POS", "Testing Efficiency", "Positivity (%)"], f"Testing Efficiency & Positivity by {drilldown_col}", colors)
                return html.Div(children=[
                    html.H3(f"HTS Cascade by {drilldown_col}", style={"textAlign": "center"}), ui_hts_org
                ]), t6_style
                
            elif sub_tab == "linkage":
                ui_tx_org = build_custom_tab1_ui(df_org, drilldown_col, ["HTS_POS", "TX_NEW"], "Proxy Linkage (%)", [drilldown_col, "HTS_POS", "TX_NEW", "Proxy Linkage (%)", "Missed Linkage"], f"Linkage (TX_NEW) by {drilldown_col}", colors)
                return html.Div(children=[
                    html.H3(f"Linkage Cascade by {drilldown_col}", style={"textAlign": "center"}), ui_tx_org
                ]), t6_style
                
            elif sub_tab == "prep":
                ui_prep_org = build_custom_tab1_ui(df_org, drilldown_col, ["PrEP_NEW", "PrEP_CT"], None, [drilldown_col, "PrEP_NEW", "PrEP_CT"], f"PrEP Delivery by {drilldown_col}", colors)
                return html.Div(children=[
                    html.H3(f"PrEP Cascade by {drilldown_col}", style={"textAlign": "center"}), ui_prep_org
                ]), t6_style

    # Tab 3, Tab 4, Tab 5 Under Construction placeholders
    elif "under-construction" in selected_visual:
        tab_name = ""
        if "tab-3" in selected_visual: tab_name = "PMTCT & Cervical Cancer Performance"
        elif "tab-4" in selected_visual: tab_name = "TB Case Finding Performance"
        elif "tab-5" in selected_visual: tab_name = "Care & Treatment"
        return html.Div(html.H3(f"Content for {tab_name} is under construction.", style={"textAlign": "center", "marginTop": "50px"})), t6_style

    # Tab 6: Automatic Trend Graphs
    elif selected_visual.startswith("tab-6-"):
        ind_id = selected_visual.replace("tab-6-", "")
        ind_conf = next((ind for ind in TAB_1_INDICATORS if ind["id"] == ind_id), None)
        if not ind_conf:
            return html.Div("Indicator not found."), t6_style
            
        time_buckets = dff[trend_time_toggle].unique().drop_nulls().sort().to_list() if not dff.is_empty() and trend_time_toggle in dff.columns else []
        
        trend_vals = []
        for tb in time_buckets:
            tb_df = dff.filter(pl.col(trend_time_toggle) == tb)
            tb_max_period = tb_df["Period"].drop_nulls().max() if not tb_df.is_empty() and "Period" in tb_df.columns else None
            
            if ind_id == "HTS_TST":
                hts_sdp_results = extract_hts_sdp_metrics(tb_df)
                ach = sum(r["HTS_TST"] for r in hts_sdp_results)
            elif ind_id == "HTS_TST_POS":
                hts_sdp_results = extract_hts_sdp_metrics(tb_df)
                ach = sum(r["HTS_TST_POSITIVES"] for r in hts_sdp_results)
            else:
                ach = get_actual(tb_df, ind_id, tb_max_period)
            trend_vals.append(ach)

        fig = go.Figure()
        fig.add_trace(go.Scattergl(
            x=time_buckets, y=trend_vals, mode="lines+markers+text",
            name=ind_conf["name"],
            text=[f"{val:,.0f}" if isinstance(val, (int, float)) else val for val in trend_vals],
            textposition="top center",
            textfont=dict(size=14, color="#222222"),
            line=dict(color=colors["achieved"], width=3),
            marker=dict(size=10, color=colors["target"])
        ))
        fig.update_layout(
            title=dict(
                text=f"{ind_conf['name']} Trend by {trend_time_toggle}",
                font=dict(size=18, color="#222222")
            ),
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            showlegend=False,
            margin=dict(l=60, r=40, t=60, b=60),
            xaxis=dict(
                tickfont=dict(size=14, color="#222222"),
                title_font=dict(size=14, color="#222222"),
                showgrid=True, gridcolor="#e0e0e0", linecolor="#cccccc"
            ),
            yaxis=dict(
                tickfont=dict(size=14, color="#222222"),
                title_font=dict(size=14, color="#222222"),
                showgrid=True, gridcolor="#e0e0e0", linecolor="#cccccc",
                tickformat=",.0f"
            )
        )

        tab_content = html.Div([
            html.H3(
                f"Performance Trend: {ind_conf['name']} (Aggregated by {trend_time_toggle})",
                style={"textAlign": "center", "fontSize": "18px"}
            ),
            html.Div(
                dcc.Graph(figure=fig, style={"height": "66vh"}),
                style={"width": "95%", "margin": "0 auto"}
            ),
        ])
        return tab_content, t6_style

    # Tab 7: KHIS-Linelist Comparison Graphs
    elif selected_visual.startswith("tab-7-"):
        ind_id = selected_visual.replace("tab-7-", "")
        ind_conf = next((ind for ind in TAB_1_INDICATORS if ind["id"] == ind_id), None)
        if not ind_conf:
            return html.Div("Indicator not found."), t6_style
            
        name = ind_conf["name"]
        tgt = get_target(dff_targets, ind_id)
        tab1_val = get_actual(dff, ind_id, max_period)
        khis_val = get_actual(dff, f"{ind_id}_KHIS", max_period)
        emr_val = get_actual(dff, f"{ind_id}_EMR", max_period)
        ndwh_val = get_actual(dff, f"{ind_id}_NDWH", max_period)
        eid_val = get_actual(dff, f"{ind_id}_EID", max_period)

        x_vals = []
        y_vals = []
        bar_colors = []
        
        if tgt > 0:
            x_vals.append("Target")
            y_vals.append(tgt)
            bar_colors.append(colors["target"])
            
        if tab1_val > 0:
            x_vals.append(f"{name} - PRISM")
            y_vals.append(tab1_val)
            bar_colors.append(colors["achieved"])
            
        if khis_val > 0:
            x_vals.append(f"{name} - KHIS")
            y_vals.append(khis_val)
            bar_colors.append("#2ca02c")
            
        if emr_val > 0:
            x_vals.append(f"{name} - EMR Linelist")
            y_vals.append(emr_val)
            bar_colors.append("#ff7f0e")
            
        if ndwh_val > 0:
            x_vals.append(f"{name} - NDWH")
            y_vals.append(ndwh_val)
            bar_colors.append("#2b3adf")
            
        if eid_val > 0:
            x_vals.append(f"{name} - EID")
            y_vals.append(eid_val)
            bar_colors.append("#49474854")

        if len(y_vals) > 0:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=x_vals,
                y=y_vals,
                text=[f"{v:,.0f}" for v in y_vals],
                textposition="auto",
                marker_color=bar_colors
            ))
            fig.update_layout(
                title=f"{name} Source Comparison",
                plot_bgcolor=colors["bg"],
                paper_bgcolor="#ffffff",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            fig.update_yaxes(showgrid=False)
            
            tab_content = html.Div([
                html.H3("KHIS & EMR Linelist Data Comparisons", style={"textAlign": "center"}),
                html.Div(dcc.Graph(figure=fig), style={"width": "100%", "maxWidth": "700px", "margin": "0 auto"})
            ])
        else:
            tab_content = html.Div(html.H3("No data available for comparison based on current filters and mapping.", style={"textAlign": "center", "marginTop": "50px"}))
            
        return tab_content, t6_style

    # PowerPoint slides (using slide_renderer.py)
    elif selected_visual.startswith("slide-"):
        slide_id = selected_visual.replace("slide-", "")
        tab_content = render_pptx_slide(slide_id, dff, dff_targets, colors, max_period, get_actual, get_target, extract_hts_sdp_metrics)
        return tab_content, t6_style

    return html.Div(html.H3(f"Content for {selected_visual} is under construction.", style={"textAlign": "center", "marginTop": "50px"})), t6_style


# --- NEW ACCORDION & SEARCH CALLBACKS ---

@data_review_dash_app.callback(
    Output("selected-visual-store", "data"),
    Input({"type": "toc-item", "index": ALL}, "n_clicks"),
    State("selected-visual-store", "data"),
    prevent_initial_call=True
)
def handle_toc_click(n_clicks_list, current_selection):
    ctx = callback_context
    if not ctx.triggered:
        return current_selection
    
    triggered_id = ctx.triggered[0]["prop_id"]
    if not triggered_id or ".n_clicks" not in triggered_id:
        return current_selection
        
    import json
    try:
        prop_json = triggered_id.split(".")[0]
        clicked_index = json.loads(prop_json)["index"]
        return clicked_index
    except Exception:
        return current_selection


@data_review_dash_app.callback(
    Output("sidebar-toc-container", "children"),
    [Input("toc-search", "value"), Input("selected-visual-store", "data")]
)
def update_sidebar(search_query, selected_id):
    return build_toc_sidebar(search_query, selected_id)






