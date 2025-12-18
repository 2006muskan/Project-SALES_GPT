import pandas as pd
import numpy as np
import IntentIdentifier
import google.generativeai as genai

#  SET YOUR DESIRED OUTPUT FILENAME HERE
input_file =  r"sales_data.csv"
output_csv_file = 'cleaned_data.csv'

#  SET THE DUMMY VALUE FOR MISSING IDs
dummy_transaction_id = 'DUMMY_ID_999'

# --- Main Script Logic ---
def clean_transaction_data(df, output_file):
    """
    Reads an Excel file, applies cleaning rules, and saves the result.
        """
    # --- Main Logic ---
    df = CleanTransactionID(df)
    df = CleanTransactionDate(df)
    df = CleanTransactionCategory(df, category_col='Category', product_name_col='ProductName')
    df = CleanTransactionProductNameAndUnitPrice(df)
    #df = CleanTranscationQuantity(df)
    df.to_csv(output_file, index=False)
    return df

def CleanTransactionID(df):
    try:
        # Check if the 'TransactionID' column exists
        if 'TransactionID' in df.columns:
            missing_count = df['TransactionID'].isnull().sum()
            
            if missing_count > 0:
                print(f"Found {missing_count} missing value(s) in the 'TransactionID' column.")
                df['TransactionID'].fillna(dummy_transaction_id, inplace=True)
                print(f"Replaced missing values with '{dummy_transaction_id}'.")
            else:
                print("No missing values found in the 'TransactionID' column.")
                
        else:
            print("⚠️ Warning: A column named 'TransactionID' was not found in your file.")
        return df


    except FileNotFoundError:
        print(f"❌ ERROR: The file '{input_file}' could not be found.")
        print("Please make sure the script is in the same folder as your Excel file and the filename is correct.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def CleanTransactionDate(df):
    # Rule 2: Delete any ROW where 'TransactionDate' is missing.
        if 'TransactionDate' in df.columns:
            initial_rows = len(df)
            
            # First, ensure the date column is properly formatted as datetime objects.
            # 'coerce' will turn any unreadable dates into NaT (Not a Time), which is a missing value.
            df['TransactionDate'] = pd.to_datetime(df['TransactionDate'], errors='coerce')
            
            # Drop rows where the 'TransactionDate' is missing.
            df.dropna(subset=['TransactionDate'], inplace=True)
            
            rows_dropped = initial_rows - len(df)
            print(f"Rule 2: Dropped {rows_dropped} row(s) due to missing 'TransactionDate'.")
        else:
            print("Rule 2: 'TransactionDate' column not present, so no rows were dropped based on it.")
        return df

def CleanTransactionCategory(df, category_col='Category', product_name_col='ProductName'):
    df_filled = df.copy()

    # Only fill missing categories
    for idx, row in df_filled.iterrows():
        if pd.isnull(row[category_col]):
            product = str(row[product_name_col]).strip().lower()
            if 'Laptop' in product or 'Smartphone' in product:
                df_filled.at[idx, category_col] = 'Electronics'
            
            elif 'Bed Sheet' in product or 'Coffee Maker' in product:
                df_filled.at[idx, category_col] = 'Home Goods'
            
            elif 'Jeans' in product or 'T-shirt' in product:
                df_filled.at[idx, category_col] = 'Apparel'
            
            else:
                df_filled.at[idx, category_col] = 'Unknown Category'
    return df_filled

def CleanTransactionProductNameAndUnitPrice(df):
    
    print("--- Starting Data:Product_Name Cleaning Process ---")
    
    df_cleaned = df.copy()
    
    # --- Rule 1: Delete rows with missing Quantity ---
    rows_before = len(df_cleaned)
    df_cleaned.dropna(subset=['Quantity'], inplace=True)
    rows_after = len(df_cleaned)
    print(f"[Rule 1] Dropped {rows_before - rows_after} row(s) with missing 'Quantity'.")
    
    # --- Rule 2: Fill missing Unit Price with the category's mean ---
    missing_prices_before = df_cleaned['UnitPrice'].isnull().sum()
    if missing_prices_before > 0:
        print(f"[Rule 2] Found {missing_prices_before} row(s) with missing 'UnitPrice'.")
        category_mean_prices = df_cleaned.groupby('ProductName')['UnitPrice'].transform('mean')
        df_cleaned['UnitPrice'].fillna(category_mean_prices, inplace=True)
        print("          -> Filled missing prices with their category's average.")
    else:
        print("[Rule 2] No missing 'UnitPrice' values found.")

    # Edge Case: If a category's mean couldn't be calculated (e.g., all prices were missing),
    # fill any remaining NaNs with the global average price.
    if df_cleaned['UnitPrice'].isnull().any():
        print("[Edge Case] Filling remaining missing prices with the global average.")
        global_mean_price = df_cleaned['UnitPrice'].mean()
        df_cleaned['UnitPrice'].fillna(global_mean_price, inplace=True)

    # --- Rule 3: Fill missing ProductName based on closest mean UnitPrice in the category ---
    missing_productname_idx = df_cleaned[df_cleaned['ProductName'].isnull()].index
    for idx in missing_productname_idx:
        row = df_cleaned.loc[idx]
        category = row['Category']
        unit_price = row['UnitPrice']
        # Get all products in this category (excluding missing names)
        products = df_cleaned[(df_cleaned['Category'] == category) & (df_cleaned['ProductName'].notnull())]
        product_means = products.groupby('ProductName')['UnitPrice'].mean()
        if len(product_means) == 2:
            # Find the product whose mean price is closest to this row's unit price
            closest_product = (product_means - unit_price).abs().idxmin()
            df_cleaned.at[idx, 'ProductName'] = closest_product
            print(f"[Rule 3] Filled missing ProductName at index {idx} with '{closest_product}' (closest mean price).")
        else:
            print(f"[Rule 3] Could not fill ProductName at index {idx} (category '{category}' does not have exactly 2 products).")

    print("--- Data Cleaning Process Complete ---\n")
    return df_cleaned
def CleanTranscationQuantity(df):
    if 'Quantity' in df.columns:
            initial_rows = len(df)
            
            # Drop rows where the 'Quantity' is missing.
            df.dropna(subset=['Quantity'], inplace=True)
            
            rows_dropped = initial_rows - len(df)
            print(f"Rule 2: Dropped {rows_dropped} row(s) due to missing 'Quantity'.")
    else:
            print("Rule 2: 'Quantity' column not present, so no rows were dropped based on it.")
    return df

def DataProcessing(extractedData, df,user_prompt):
    extracted_type = extractedData.split(",")[0]

    match extracted_type:
        case "Trend Analysis":
            # Trend: Show total revenue per Month
            monthRevenue= ""
            if {'TransactionDate', 'Quantity', 'UnitPrice'}.issubset(df.columns):
                df['TransactionDate'] = pd.to_datetime(df['TransactionDate'], errors='coerce')
                df['Revenue'] = df['Quantity'] * df['UnitPrice']
                df['Month'] = df['TransactionDate'].dt.to_period('M')
                trend = df.groupby('Month')['Revenue'].sum()
                print("Monthly Revenue Trend:")
                # Print trend in "MonthName:Value" format
                for period, value in trend.items():
                    month_name = period.strftime('%B')
                    monthRevenue += f"{month_name}:{int(value)},"+"\n"
                    # print(f"{month_name}:{int(value)}")
            else:
                print("Required columns for trend analysis are missing.")

            refinedPrompt = ("Prompt:" + user_prompt + "\n" "Context: Monthly Revenue: "+ monthRevenue)
            print(refinedPrompt)
        case "Outlier Analysis":
            # Outlier: Show transactions with revenue much higher than average
            df['Revenue'] = df['Quantity'] * df['UnitPrice']
            if {'Quantity', 'UnitPrice'}.issubset(df.columns):
                category_col = 'Category'
                target_category = extractedData.split(",")[1]
                value_col = 'UnitPrice'
                category_df = df[df[category_col] == target_category]

                # If the category doesn't exist or has no data, return an empty DataFrame
                if category_df.empty:
                    return pd.DataFrame()

                # Step 2: Calculate Q1 and Q3 on the filtered data
                Q1 = category_df[value_col].quantile(0.25)
                Q3 = category_df[value_col].quantile(0.75)

                # Step 3: Calculate the IQR
                IQR = Q3 - Q1
                

                # Step 4: Define the outlier boundaries
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                # Step 5: Identify and return the outliers
                outliers = category_df[(category_df[value_col] < lower_bound) | (category_df[value_col] > upper_bound)]
                if not outliers.empty:
                    refinedPrompt = f"Outliers in '{target_category}' category:"+"\n"
                    for idx, row in outliers.iterrows():
                        refinedPrompt += (
                            f"TransactionID: {row['TransactionID']}, "
                            f"UnitPrice: {row[value_col]:.2f}, "
                            f"Date: {row['TransactionDate']}, "
                            f"Product: {row.get('ProductName', 'N/A')}\n"
                        )
                    refinedPrompt +=(f"Mean Unit Price in '{target_category}': {category_df[value_col].mean():.2f}")
                else:
                    print(f"No outliers found in '{target_category}' category.")
            else:
                print("Required columns for outlier analysis are missing.")
        case "Comparative Analysis":
            # Comparative: Compare total revenue by ProductName
            if {'ProductName', 'Quantity', 'UnitPrice'}.issubset(df.columns):
                df['Revenue'] = df['Quantity'] * df['UnitPrice']
                productRevenue1 = df[df['ProductName'] == extractedData.split(',')[1]]['Revenue'].sum()
                productRevenue2 = df[df['ProductName'] == extractedData.split(',')[2]]['Revenue'].sum()
                # Format revenues to 2 decimal places
                productRevenue1 = round(productRevenue1, 2)
                productRevenue2 = round(productRevenue2, 2)
                refinedPrompt = ("Prompt:" + user_prompt + "\n" "Context: Revenue of products are: "
                                 + extractedData.split(',')[1] + ':' + str(productRevenue1) + ',' + extractedData.split(',')[2] + ':' + str(productRevenue2))
                print(refinedPrompt)
            else:
                print("Required columns for comparative analysis are missing.")
        case _:
           refinedPrompt = "Unknown intent"
        
    return refinedPrompt

# --- Run the cleaning function ---
# if __name__ == "__main__":
#     user_prompt = "Analyze the sales data for trends, outliers, and comparisons."
#     df = pd.read_csv(input_file)
#     df = clean_transaction_data(df, output_file=output_csv_file)
#     extractedData = IntentIdentifier.classify_and_extract(user_prompt)
#     refinedPrompt = DataProcessing(extractedData,df,user_prompt)
#     if(refinedPrompt == "Unknown intent"):
#         output = refinedPrompt
#     else:
#         model = genai.GenerativeModel(model_name="gemini-2.5-flash")
#         output = model.generate_content(refinedPrompt).text.strip() 

