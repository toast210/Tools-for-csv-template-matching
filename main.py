import io
import zipfile
import streamlit as st
import column_cleaning as sdc

st.set_page_config(page_title="Data Matcher & Cleaner", layout="wide")
st.title("Data Column Matcher & Template Generator")

# Initialize persistent session states
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None
if "mapped_df" not in st.session_state:
    st.session_state.mapped_df = None
if "filtered_df" not in st.session_state:
    st.session_state.filtered_df = None

uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    # 1. Ingest File
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.get("file_id") != file_id:
        st.session_state.raw_df = sdc.read_file(uploaded_file)
        st.session_state.mapped_df = None
        st.session_state.filtered_df = None
        st.session_state.file_id = file_id

    raw_df = st.session_state.raw_df

    if raw_df is not None:
        st.subheader("1. Column Mapping")
        with st.expander("Raw Data Preview (First 5 Rows)", expanded=False):
            st.dataframe(raw_df.head(5), use_container_width=True)

        raw_columns = raw_df.columns.tolist()

        # Step 1: Mapping Form with automatic best-guess matching
        with st.form("mapping_form"):
            st.write("Match raw columns to platform target columns:")
            cols = st.columns(2)
            temp_mapping = {}

            for idx, target in enumerate(sdc.TO_BE_MATCHED_COLUMNS):
                col_box = cols[idx % 2]
                
                # Auto-select if column names match case-insensitively
                default_idx = 0
                for c_idx, c in enumerate(raw_columns, start=1):
                    if c.strip().lower() == target.lower():
                        default_idx = c_idx
                        break

                selected = col_box.selectbox(
                    f"Target: '{target}'",
                    options=["None"] + raw_columns,
                    index=default_idx,
                    key=f"map_{target}"
                )
                if selected != "None":
                    temp_mapping[selected] = target

            submit_mapping = st.form_submit_button("Confirm & Apply Mapping")
            if submit_mapping:
                if temp_mapping:
                    st.session_state.mapped_df = sdc.apply_column_mapping(raw_df, temp_mapping)
                    st.session_state.filtered_df = st.session_state.mapped_df.copy()
                    st.success("Column mapping applied successfully.")
                else:
                    st.warning("Please map at least one column.")

        # Step 2: Row Filtering
        if st.session_state.filtered_df is not None:
            st.divider()
            st.subheader("2. Row Operations")

            f_cols = st.columns([2, 2, 2, 2])
            with f_cols[0]:
                filter_col = st.selectbox("Column", st.session_state.filtered_df.columns.tolist())
            with f_cols[1]:
                operator = st.selectbox("Operator", ["Is Empty", "Is Not Empty", "Equals", "Not Equals", "Contains", "Greater Than", "Less Than"])
            with f_cols[2]:
                action = st.selectbox("Action", ["Delete matching rows", "Keep only matching rows"])
            with f_cols[3]:
                needs_val = operator not in ("Is Empty", "Is Not Empty")
                val = st.text_input("Filter Value") if needs_val else None

            btn_col1, btn_col2 = st.columns([1, 4])
            with btn_col1:
                if st.button("Apply Filter", type="primary"):
                    before = len(st.session_state.filtered_df)
                    st.session_state.filtered_df = sdc.filter_rows(
                        st.session_state.filtered_df, filter_col, operator, action, val
                    )
                    after = len(st.session_state.filtered_df)
                    st.toast(f"Updated: {before - after} rows removed.", icon="✂️")

            with btn_col2:
                if st.button("Reset to Mapped Data"):
                    st.session_state.filtered_df = st.session_state.mapped_df.copy()
                    st.rerun()

            st.caption(f"Active rows: {len(st.session_state.filtered_df):,}")

            # Step 3: Template Generation & Downloads
            st.divider()
            st.subheader("3. Export Platform Templates")

            active_df = st.session_state.filtered_df

            # Pre-calculate dataframes
            exports = {
                "base_matched.csv": active_df,
                "facebook_audience.csv": sdc.generate_facebook_template(active_df),
                "google_customer_match.csv": sdc.generate_google_template(active_df),
                "linkedin_contacts.csv": sdc.generate_linkedin_contact_template(active_df),
                "linkedin_companies.csv": sdc.generate_linkedin_company_template(active_df)
            }

            # Batch ZIP download
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for filename, frame in exports.items():
                    zip_file.writestr(filename, frame.to_csv(index=False))

            st.download_button(
                label="📦 Download All Templates (ZIP)",
                data=zip_buffer.getvalue(),
                file_name="marketing_templates.zip",
                mime="application/zip"
            )

            # Tabbed Previews & Individual CSV downloads
            tab_names = ["Filtered Base", "Facebook", "Google", "LinkedIn Contacts", "LinkedIn Companies"]
            tabs = st.tabs(tab_names)

            for tab, (filename, frame) in zip(tabs, exports.items()):
                with tab:
                    st.caption(f"Dimensions: {frame.shape[0]} rows × {frame.shape[1]} columns")
                    st.dataframe(frame.head(20), use_container_width=True)
                    st.download_button(
                        label=f"Download {filename}",
                        data=frame.to_csv(index=False).encode("utf-8"),
                        file_name=filename,
                        mime="text/csv",
                        key=f"dl_{filename}"
                    )
else:
    st.info("Upload a CSV or Excel file to get started.")
