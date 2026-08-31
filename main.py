import base64

import streamlit as st
import column_cleaning as sdc

st.title("Column Matcher for data cleaning")


uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    if "matched_df" not in st.session_state:
        st.session_state.matched_df = None

    all_columns, df = sdc._read(uploaded_file)

    if df is not None:
        st.session_state.matched_df = df

    if st.session_state.matched_df is not None:
        filtered_df = sdc.delete_rows(st.session_state.matched_df)
        facebook_df = sdc.facebook_template(filtered_df)
        google_df = sdc.google_template(filtered_df)
        linked_df = sdc.linkedin_company_template(filtered_df)
        linked_df1 = sdc.linkedin_contact_template(filtered_df)
        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download matched_output.csv",
            data=csv_data,
            file_name="matched_output.csv",
            mime="text/csv",
        )

else:
    st.info("Please upload a CSV file to begin.")
