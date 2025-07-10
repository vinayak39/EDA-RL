import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import plotly.express as px


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

    # 1. Data Summary
    st.header("1. Data Summary")
    st.write("**Shape of Data (rows, columns):**", df.shape)
    st.write("**Number of Columns:**", len(df.columns))
    st.write("**Number of Unique Rows:**", df.drop_duplicates().shape[0])
    st.write("**Missing Values per Column:**")
    st.dataframe(df.isnull().sum().reset_index().rename(columns={0: "Missing Count", "index": "Column"}))
    st.write("**Data Types of Columns:**")
    st.dataframe(df.dtypes.reset_index().rename(columns={0: "Data Type", "index": "Column"}))

    if 'Date' in df.columns:
        st.write("**Parsed Date Column Preview:**")
        st.dataframe(df[['Time.[Planning Month]', 'Date']].dropna().head())

    # 2. Sample Data
    st.header("2. Sample Data Preview")
    st.dataframe(df.head(), use_container_width=True, height=300)

    # 3. Unique Value Summary
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
    # 4. Evergreen Distribution with Volume Analysis and Accuracy Flag
    st.header("4. Evergreen vs Non-Evergreen Distribution")
    if 'Evergreen.[Evergreen]' in df.columns:
        df['Evergreen.[Evergreen]'] = df['Evergreen.[Evergreen]'].astype(str).str.strip().str.upper()
        is_evergreen = df['Evergreen.[Evergreen]'] == 'EVERGREEN'
        is_nonevergreen = df['Evergreen.[Evergreen]'] == 'NON EVERGREEN'

        df['Calculated::Sales Volume ($)'] = df['Sales (Units)'] * df['AUR Actual ($)']
        df['Calculated::Expected Sales ($)'] = df['Calculated::Sales Volume ($)']
        df['Calculated::AUR Accuracy Flag'] = abs(df['Calculated::Expected Sales ($)'] - df['Sales ($)']) > 20

        evergreen_df = pd.DataFrame({
            'Category': ['EVERGREEN', 'NON EVERGREEN'],
            'Row Count': [is_evergreen.sum(), is_nonevergreen.sum()],
            'Sales Volume (Units)': [df[is_evergreen]['Sales (Units)'].sum(), df[is_nonevergreen]['Sales (Units)'].sum()],
            'Calculated::Sales Volume ($)': [df[is_evergreen]['Calculated::Sales Volume ($)'].sum(), df[is_nonevergreen]['Calculated::Sales Volume ($)'].sum()],
            'Actual Sales ($)': [df[is_evergreen]['Sales ($)'].sum(), df[is_nonevergreen]['Sales ($)'].sum()]
        })

        st.write("**Evergreen Distribution Table with Calculated Measures:**")
        st.dataframe(evergreen_df, use_container_width=True)

        fig = px.bar(
            evergreen_df.melt(id_vars='Category', var_name='Metric', value_name='Value'),
            x='Category', y='Value', color='Metric', barmode='group',
            text='Value', title="Evergreen vs Non-Evergreen Distribution"
        )
        fig.update_layout(
            yaxis_tickformat=',',
            legend_title_text='Metric',
            xaxis_title='Evergreen Category',
            margin=dict(t=50, l=30, r=30, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.caption("""
        **Calculation Logic:**
        - **Sales Volume (Units)** = From column `Sales (Units)`
        - **Calculated::Sales Volume ($)** = `Sales (Units)` × `AUR Actual ($)`
        - **Actual Sales ($)** = From dataset `Sales ($)`
        - **Calculated::AUR Accuracy Flag** = Absolute(`Sales (Units)` × `AUR Actual ($)` − `Sales ($)`) > $20
        """)

        st.subheader("🔎 Rows with AUR Accuracy Flag (Mismatch > $20)")
        aur_flag_df = df[df['Calculated::AUR Accuracy Flag'] == True][[
            'Date', 'Item.[PPL]', 'Sales (Units)', 'AUR Actual ($)', 'Sales ($)', 'Calculated::Expected Sales ($)'
        ]].reset_index(drop=True)
        st.write(f"Total flagged rows: {aur_flag_df.shape[0]}")
        st.dataframe(aur_flag_df, use_container_width=True)

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
        st.dataframe(monthly_counts.reset_index().rename(columns={'index': 'Month', 'Date': 'Record Count'}))
        st.bar_chart(monthly_counts)

    # 8. Zero Sales Check
    st.header("8. Zero Sales Check by Item")
    if 'Sales (Units)' in df.columns and 'Item.[PPL]' in df.columns:
        zero_counts = df[df['Sales (Units)'] == 0].groupby('Item.[PPL]').size().sort_values(ascending=False)
        st.dataframe(zero_counts.reset_index().rename(columns={0: 'Zero Sales Count'}))

    # 9. Sales Units Outlier Detection
    st.header("9. Outlier Check on Sales Units")
    if 'Sales (Units)' in df.columns:
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.boxplot(x=df['Sales (Units)'], ax=ax)
        ax.set_title("Boxplot of Sales (Units)")
        ax.set_xlabel("Sales (Units)")
        st.pyplot(fig)

    # 10. Total Volume Checks
    st.header("10. Volume Trends & Breakdown")
    if 'Date' in df.columns:
        with st.expander("Monthly Total Volume Across Business"):
            total_monthly = df.groupby(df['Date'].dt.to_period('M'))['Sales (Units)'].sum()
            st.dataframe(total_monthly.reset_index().rename(columns={'Date': 'Month', 'Sales (Units)': 'Total Volume'}))
            st.line_chart(total_monthly)

        if 'Global Plan Brand.[Global Plan Brand]' in df.columns:
            with st.expander("Monthly Volume by Brand"):
                brand_vol = df.groupby([df['Date'].dt.to_period('M'), 'Global Plan Brand.[Global Plan Brand]'])['Sales (Units)'].sum().unstack()
                st.dataframe(brand_vol.fillna(0).astype(int))
                st.line_chart(brand_vol)

        if 'Region.[Region]' in df.columns:
            with st.expander("Monthly Volume by Region"):
                region_vol = df.groupby([df['Date'].dt.to_period('M'), 'Region.[Region]'])['Sales (Units)'].sum().unstack()
                st.dataframe(region_vol.fillna(0).astype(int))
                st.line_chart(region_vol)

        if 'Channel.[Channel]' in df.columns:
            with st.expander("Monthly Volume by Channel"):
                channel_filter = ['Retail B&M FP', 'Retail B&M OP', 'Retail B&M SPECIAL', 'Retail DIGITAL FP']
                df_channel = df[df['Channel.[Channel]'].isin(channel_filter)]
                if not df_channel.empty:
                    channel_vol = df_channel.groupby([df_channel['Date'].dt.to_period('M'), 'Channel.[Channel]'])['Sales (Units)'].sum().unstack()
                    st.dataframe(channel_vol.fillna(0).astype(int))
                    st.line_chart(channel_vol)
                else:
                    st.warning("No data for selected Retail channels")

        if 'Country' in df.columns:
            with st.expander("Volume by Country for 2024"):
                df_2024 = df[df['Date'].dt.year == 2024]
                country_vol = df_2024.groupby('Country')['Sales (Units)'].sum().sort_values(ascending=False)
                st.dataframe(country_vol.reset_index())
                st.bar_chart(country_vol)

        with st.expander("Brand-Gender-Line x Region x Channel (2024)"):
            if 'Global Plan Brand.[Global Plan Brand]' in df.columns and 'Region.[Region]' in df.columns and 'Channel.[Channel]' in df.columns:
                df_2024 = df[df['Date'].dt.year == 2024]
                breakdown = df_2024.groupby([
                    'Global Plan Brand.[Global Plan Brand]',
                    'Global Plan L1.[Global Plan L1]',
                    'Region.[Region]',
                    'Channel.[Channel]'])['Sales (Units)'].sum().reset_index()
                st.dataframe(breakdown)

    st.success("\n\n✅ Initial EDA Completed. Review insights and refine further based on modeling needs.")

else:
    st.info("Please upload a CSV file to begin EDA.")
