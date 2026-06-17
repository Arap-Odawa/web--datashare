import polars as pl

# 1. Define the list of strings to be treated as Null
# Including variants of N/A ensures robust parsing
null_values = ["#N/A", 
               "N/A", 
               "NA", 
               "NULL", 
               "nan",
               "ni",
               "Ni",

               ]

schema_overrides = {
        "Finer Age Group": pl.String,
        "Coarse Age Group": pl.String,
        "Gender": pl.String,
        "County": pl.String,
        "Sub County": pl.String,
        "Ward": pl.String,
        "PRISM Facility Name": pl.String,
        "storedby": pl.String,
        "DATIM_Indicator": pl.String,
        "Indicator": pl.String,
        "Testing Results": pl.String,
        "prism_de": pl.String,
        "prism_categoryOptionCombo": pl.String,
        "metadata_type": pl.String,
        "Finer Age Group_duplicated_0": pl.String,
        "Coarse Age Group_duplicated_0": pl.String,
        "Gender_duplicated_0": pl.String,
        "Age Group Gender": pl.String,
        "Age Group Gender_duplicated_0": pl.String,
        "graphing_indicator": pl.String,
        "Aggregate_Indicators": pl.String,
        "Dataset": pl.String,
        # You can explicitly force the MFL code to String or Int here if needed
        "PRISM MFL Code": pl.String, 
        "AZ Period": pl.String,
        "AMPATH Period": pl.String,
        "DATIM_DataElement": pl.String,
        "DATIM_CategoryOptionCombo": pl.String,
        "DATIM_Aggregation": pl.String,
        "DATIM_Quarter_Type": pl.String,
        "Indicator Category": pl.String,
    }

file_name = "PRISM_KHIS_PROCESSED_Q2_FY26_Dataset_01032026_v1" #PRISM_KHIS_PROCESSED_Q2_FY26_Dataset_01032026_v1
dataset = f"{file_name}.csv"

# 2. Add the null_values parameter to read_csv
df = pl.read_csv(
    dataset,
    schema_overrides=schema_overrides,
    infer_schema_length=10000,
    encoding="latin-1",
    null_values=null_values,  # Handles the #N/A error
    ignore_errors=False       # Set to True only if you want to skip unparseable lines
)

# 3. Write to Parquet
#df.write_parquet(f"processed_dhis2_data.parquet",compression="zstd")

df.write_parquet(f"{file_name}.parquet",compression="zstd")

print(f"Successfully converted {dataset} to {file_name}.parquet")
print(f"Total rows processed: {df.height}")





