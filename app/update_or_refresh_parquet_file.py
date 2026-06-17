import polars as pl
import os


# Replace the name of the parquet file here without the extension

file_name = "PRISM_KHIS_PROCESSED_Q2_FY26_Dataset_01032026_v1"

dataset_to_convert = f"{file_name}.parquet"


def update_source_parquet(new_file_path, source_file="processed_dhis2_data.parquet"):
    """
    Updates the master parquet file by replacing data for specific periods.
    """
    try:
        # 1. Read the new data
        print(f"Reading new data from: {new_file_path}")
        new_data = pl.read_parquet(new_file_path)
        
        # 2. Identify the unique periods in the new file
        # This ensures we only delete what we are actually replacing
        new_periods = new_data["Period"].unique().to_list()
        print(f"Periods to be updated: {new_periods}")

        # 3. Check if source file exists; if not, the new file becomes the source
        if not os.path.exists(source_file):
            print("Source file not found. Creating new source file.")
            new_data.write_parquet(source_file)
            return

        # 4. Read the master source file
        source_df = pl.read_parquet(source_file)

        # 5. Filter out the periods that exist in the new data
        # 'is_in' combined with '~' (not) removes the overlapping periods
        filtered_source = source_df.filter(~pl.col("Period").is_in(new_periods))

        # 6. Concatenate the cleaned source with the new data
        updated_df = pl.concat([filtered_source, new_data])

        # 7. Write back to parquet (using snappy compression for performance)
        updated_df.write_parquet(source_file, compression="zstd")
        
        print(f"Successfully updated {source_file}.")
        print(f"Rows before: {source_df.height} | Rows after: {updated_df.height}")

    except Exception as e:
        print(f"An error occurred during update: {e}")

# Example usage:
#update_source_parquet("january_2026_updates.parquet")
update_source_parquet(dataset_to_convert)