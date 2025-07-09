import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# Streamlit UI
st.set_page_config(layout="wide")
st.title("Ralph Lauren Size Curve Forecast EDA")

# Load Data
uploaded_file = st.file_uploader("Upload Forecast CSV File", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Parse Planning Month to Date
    month_col = 'Time.[Planning Month]'
    if month_col in df.columns:
        try:
            month_map = {
                'JANUARY': 1, 'FEBRUARY': 2, 'MARCH': 3, 'APRIL': 4, 'MAY': 5, 'JUNE': 6,
                'JULY': 7, 'AUGUST': 8, 'SEPTEMBER': 9, 'OCTOBER': 10, 'NOVEMBER': 11, 'DECEMBER': 12
            }
            df['Date'] = pd.to_datetime(df[month_col].str.extract(r'(FY\d{4})\s-\s(\w+)')
                                          .apply(lambda x: f"{x[0][-4:]}-{month_map.get(x[1].upper(), 1)}-01", axis=1))
        except Exception as e:
            st.warning(f"Could not parse Planning Month properly: {e}")

    # 1. Overview and Data Completeness
    st.header("1. Data Summary")
    st.write("**Shape of Data (rows, columns):**", df.shape)
    st.write("**Number of Columns:**", len(df.columns))
    st.write("**Number of Unique Rows:**", df.drop_duplicates().shape[0])
    st.write("**Missing Values per Column:**")
    st.dataframe(df.isnull().sum().reset_index().rename(columns={0: "Missing Count", "index": "Column"}))
    st.write("**Data Types of Columns:**")
    st.dataframe(df.dtypes.reset_index().rename(columns={0: "Data Type", "index": "Column"}))

    # Show Date column if created
    if 'Date' in df.columns:
        st.write("**Parsed Date Column Preview:**")
        st.dataframe(df[['Time.[Planning Month]', 'Date']].dropna().head())

    # 2. Sample Data
    st.header("2. Sample Data Preview")
    st.dataframe(df.head())

    # 3. Unique Value Counts
    st.header("3. Unique Value Summary by Key Dimensions")
    check_cols = [
        'Global Plan Brand.[Global Plan Brand]', 'Region.[Region]', 'Channel.[Channel]',
        'Global Plan L1.[Global Plan L1]', 'Global Plan L2.[Global Plan L2]',
        'Global Plan L3.[Global Plan L3]', 'Global Plan L4.[Global Plan L4]',
        'Item.[PPL]', 'Evergreen.[Evergreen]'
    ]
    for col in check_cols:
        if col in df.columns:
            st.write(f"**{col}**: {df[col].nunique()} unique values")

    # 4. Evergreen vs Non-Evergreen Distribution
    st.header("4. Evergreen vs Non-Evergreen Distribution")
    if 'Evergreen.[Evergreen]' in df.columns:
        df['Evergreen.[Evergreen]'] = df['Evergreen.[Evergreen]'].astype(str).str.strip().str.upper()
        count_evergreen = (df['Evergreen.[Evergreen]'] == 'EVERGREEN').sum()
        count_nonevergreen = (df['Evergreen.[Evergreen]'] == 'NON EVERGREEN').sum()
        evergreen_df = pd.DataFrame({
            'Category': ['EVERGREEN', 'NON EVERGREEN'],
            'Count': [count_evergreen, count_nonevergreen]
        })
        st.write(f"**EVERGREEN Rows:** {count_evergreen}")
        st.write(f"**NON EVERGREEN Rows:** {count_nonevergreen}")
        st.bar_chart(evergreen_df.set_index('Category'))
    else:
        st.warning("Column 'Evergreen.[Evergreen]' not found in dataset.")


    # 5. Data Horizon Check
    st.header("5. Data Horizon Check")
    if 'Date' in df.columns:
        min_date = df['Date'].min()
        max_date = df['Date'].max()
        st.write("Min Month (Start):", min_date)
        st.write("Max Month (End):", max_date)
        st.write("Total Unique Months Available:", df['Date'].dt.to_period('M').nunique())
        if pd.notna(min_date) and pd.notna(max_date):
            duration_months = (max_date.to_period('M') - min_date.to_period('M')).n
            st.write("Duration in Months:", duration_months)

    # 6. Duplicate Check
    st.header("6. Duplicate Row Check")
    st.write("Number of Duplicate Rows:", df.duplicated().sum())

    # 7. Monthly Record Distribution
    st.header("7. Monthly Record Distribution")
    if 'Date' in df.columns:
        monthly_counts = df['Date'].value_counts().sort_index()
        if not monthly_counts.empty:
            st.bar_chart(monthly_counts)
        else:
            st.write("No data available to plot monthly distribution.")

    # 8. Zero Sales Analysis
    st.header("8. Zero Sales Check by Item")
    if 'Sales (Units)' in df.columns and 'Item.[PPL]' in df.columns:
        zero_counts = df[df['Sales (Units)'] == 0].groupby('Item.[PPL]').size()
        st.write("Top Items with Most Zero Sales:")
        st.dataframe(zero_counts.sort_values(ascending=False).head())

    # 9. Sales Units Outlier Detection
    st.header("9. Outlier Check on Sales Units")
    if 'Sales (Units)' in df.columns:
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.boxplot(x=df['Sales (Units)'], ax=ax)
        st.pyplot(fig)

    st.success("\n\n✅ Initial EDA Completed. Review insights and refine further based on modeling needs.")

else:
    st.info("Please upload a CSV file to begin EDA.")