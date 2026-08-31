import pandas as pd
import os
import streamlit as st

#reading the file in different formats
def _read(selected_file):
    if not selected_file:
        print("No file was selected.")
        return None, None

    print(f"Opening and reading: {selected_file}...")

    selected_file.seek(0)  # rewind — Streamlit reruns the script on every interaction,
                            # and the uploaded file's read position persists across reruns
    df = None
    try:
        df = pd.read_csv(selected_file, encoding='utf-8', on_bad_lines='skip', sep=',')
        except UnicodeDecodeError:
        try:
            selected_file.seek(0)  # rewind again before retrying with a different encoding
            df = pd.read_csv(selected_file, encoding='latin1', on_bad_lines='skip', sep=',')
        except pd.errors.ParserError as e:
            print(f"ParserError: An error occurred while parsing the CSV after UnicodeDecodeError. {e}")
            print("Try specifying the separator (e.g., sep=';') or inspect the file for malformed lines.")
            return None, None
    except pd.errors.ParserError as e:
        print(f"ParserError: An error occurred while parsing the CSV. {e}")
        print("Try specifying the separator (e.g., sep=';') or inspect the file for malformed lines.")
        return None, None

    st.write("Preview:", df.head())
    all_columns = df.columns.tolist()
    mapped_df = delete_unmatched_columns(all_columns, df)
    return all_columns, mapped_df

to_be_matched_columns = ['full name','email','pin_code','company','city','state','country','phone','linkedin url','linkedin url company','company website']

def delete_unmatched_columns(list_of_columns,selected_file):
    mapping = {}
    st.form_key = "mapping_form"
    with st.form("mapping_form"):
        for required_col in to_be_matched_columns:
            # Create a dropdown for each required column
            options = ["None"] + list_of_columns
            selected = st.selectbox(f"Select column for '{required_col}'", options)
            if selected != "None":
                mapping[selected] = required_col

        submitted = st.form_submit_button("Apply Mapping")

        if submitted:
            if mapping:
                df = selected_file.rename(columns=mapping)
                # Filter to keep only matched columns
                available_targets = [c for c in to_be_matched_columns if c in df.columns]
                st.success("Mapping Applied!")
                st.dataframe(df[available_targets])
                return df
            else:
                st.warning("No columns mapped.")

operations = ['Delete']
operator = ['Equal','Contains']

def delete_rows(df):
    st.subheader("Row Operations")
    if "working_df" not in st.session_state or st.session_state.working_df is None:
        st.session_state.working_df = df.copy()

    # Only offer columns that were actually matched (present in to_be_matched_columns)
    matched_columns = [c for c in st.session_state.working_df.columns.tolist() if c in to_be_matched_columns]

    if not matched_columns:
        st.warning("No matched columns available to filter on.")
        return st.session_state.working_df

    operators = ["Is Empty", "Is Not Empty", "Equals", "Not Equals", "Contains", "Greater Than", "Less Than"]
    actions = ["Delete matching rows", "Keep only matching rows"]
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_column = st.selectbox("Column", matched_columns, key="row_op_column")
    with col2:
        selected_operator = st.selectbox("Operator", operators, key="row_op_operator")
    with col3:
        selected_action = st.selectbox("Action", actions, key="row_op_action")
    needs_value = selected_operator not in ("Is Empty", "Is Not Empty")
    value = st.text_input("Value", key="row_op_value") if needs_value else None
    if st.button("Apply Operation"):
        df_current = st.session_state.working_df
        col_data = df_current[selected_column]
        if selected_operator == "Is Empty":
            mask = col_data.isna() | (col_data.astype(str).str.strip() == "")
        elif selected_operator == "Is Not Empty":
            mask = ~(col_data.isna() | (col_data.astype(str).str.strip() == ""))
        elif selected_operator == "Equals":
            mask = col_data.astype(str) == value
        elif selected_operator == "Not Equals":
            mask = col_data.astype(str) != value
        elif selected_operator == "Contains":
            mask = col_data.astype(str).str.contains(value, case=False, na=False)
        elif selected_operator == "Greater Than":
            mask = pd.to_numeric(col_data, errors='coerce') > pd.to_numeric(value, errors='coerce')
        elif selected_operator == "Less Than":
            mask = pd.to_numeric(col_data, errors='coerce') < pd.to_numeric(value, errors='coerce')
        before = len(df_current)
        if selected_action == "Delete matching rows":
            st.session_state.working_df = df_current[~mask]
        else:
            st.session_state.working_df = df_current[mask]
        after = len(st.session_state.working_df)
        st.success(
            f"{selected_action}: {selected_column} {selected_operator} {value or ''} — {before - after} row(s) removed" if selected_action == "Delete matching rows" else f"Kept {after} of {before} rows")
    st.write(f"Current row count: {len(st.session_state.working_df)}")
    st.dataframe(st.session_state.working_df.head(20))
    if st.button("Reset row operations"):
        st.session_state.working_df = df.copy()
        st.rerun()
    return st.session_state.working_df

def facebook_template(df):
    if st.button("Download Facebook formatted data"):
        df_fb = df.copy()

        df_fb['fn'] = df_fb['full name'].apply(lambda x: x.split(' ')[0] if pd.notna(x) else '')
        df_fb['ln'] = df_fb['full name'].apply(lambda x: ' '.join(x.split(' ')[1:]) if pd.notna(x) and len(x.split(' ')) > 1 else '')
        df_fb['phone'] = df['phone'].astype(str).str.replace(r'[^\d]', '', regex=True)
        # Rename columns as requested
        df_fb = df_fb.rename(columns={
            'phone': 'phone',
            'email':'email',
            'city': 'ct',
            'state': 'st',
            'country': 'country'
        })

        # Keep only the Facebook-required columns, in order
        facebook_columns = ['fn', 'ln', 'email', 'phone', 'ct', 'st', 'country']
        available_columns = [c for c in facebook_columns if c in df_fb.columns]
        missing_columns = [c for c in facebook_columns if c not in df_fb.columns]

        if missing_columns:
            st.warning(f"These columns were missing and will be left out: {', '.join(missing_columns)}")

        df_fb = df_fb[available_columns]

        st.dataframe(df_fb.head(20))

        csv_data = df_fb.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Confirm Facebook CSV Download",
            data=csv_data,
            file_name="facebook_matched.csv",
            mime="text/csv",
            key="fb_download_confirm"
        )

def google_template(df):
    if st.button("Download Google formatted data"):
        df_google = df.copy()

        df_google['First Name'] = df_google['full name'].apply(lambda x: x.split(' ')[0] if pd.notna(x) else '')
        df_google['Last Name'] = df_google['full name'].apply(lambda x: ' '.join(x.split(' ')[1:]) if pd.notna(x) and len(x.split(' ')) > 1 else '')
        df_google['phone'] = '+' + df_google['phone'].astype(str).str.replace(r'[^\d]', '', regex=True)

        # Rename columns as requested
        df_google = df_google.rename(columns={
            'email': 'Email',
            'phone': 'Phone',
            'country': 'Country'
        })

        # Keep only the Facebook-required columns, in order
        google_columns = ['Email', 'Phone', 'First Name', 'Last Name', 'Country']
        available_columns = [c for c in google_columns if c in df_google.columns]
        missing_columns = [c for c in google_columns if c not in df_google.columns]

        if missing_columns:
            st.warning(f"These columns were missing and will be left out: {', '.join(missing_columns)}")

        df_google = df_google[available_columns]

        st.dataframe(df_google.head(20))

        csv_data = df_google.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Confirm Google CSV Download",
            data=csv_data,
            file_name="Google_formatted.csv",
            mime="text/csv",
            key="Google_download_confirm"
        )

def linkedin_contact_template(df):
    if st.button("Download LinkedIn Contact List formatted data"):
        df_li = df.copy()

        df_li['phone'] = '+' + df_li['phone'].astype(str).str.replace(r'[^\d]', '', regex=True)

        # Rename columns as required by LinkedIn (keep 'full name' as is, don't split)
        df_li = df_li.rename(columns={
            'email': 'email',
            'full name': 'full name',
            'company': 'companyName',
            'city': 'city',
            'state': 'state',
            'country': 'country',
            'phone': 'phone',
            'linkedin url': 'linkedinUrl'
        })

        # Keep only the LinkedIn-required/supported columns, in order
        linkedin_columns = ['email', 'full name', 'companyName', 'city', 'state', 'country', 'phone', 'linkedinUrl']
        available_columns = [c for c in linkedin_columns if c in df_li.columns]
        missing_columns = [c for c in linkedin_columns if c not in df_li.columns]

        if 'email' not in available_columns:
            st.error("Email column is required for LinkedIn contact list uploads — cannot proceed.")
            return

        if missing_columns:
            st.warning(f"These optional columns were missing and will be left out: {', '.join(missing_columns)}")

        df_li = df_li[available_columns]

        st.dataframe(df_li.head(20))

        csv_data = df_li.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Confirm LinkedIn Contact CSV Download",
            data=csv_data,
            file_name="LinkedIn_contact_formatted.csv",
            mime="text/csv",
            key="LinkedIn_contact_download_confirm"
        )


def linkedin_company_template(df):
    if st.button("Download LinkedIn Company List formatted data"):
        df_li_co = df.copy()

        # Rename columns as required by LinkedIn
        df_li_co = df_li_co.rename(columns={
            'company': 'companyName',
            'company website': 'companyWebsite',
            'linkedin url company': 'companyLinkedInPageURL',
            'country': 'country'
        })

        # LinkedIn requires AT LEAST ONE of these identifier columns (not all)
        linkedin_company_columns = ['companyName', 'companyWebsite', 'companyLinkedInPageURL', 'country']
        available_columns = [c for c in linkedin_company_columns if c in df_li_co.columns]

        if not available_columns or not any(c in available_columns for c in ['companyName', 'companyWebsite', 'companyLinkedInPageURL']):
            st.error("At least one of companyName, companyWebsite, or companyLinkedInPageURL is required — cannot proceed.")
            return

        missing_columns = [c for c in linkedin_company_columns if c not in df_li_co.columns]
        if missing_columns:
            st.info(f"These optional columns were not found: {', '.join(missing_columns)}")

        df_li_co = df_li_co[available_columns]

        # Drop duplicate companies - keep first occurrence, dedupe by companyName if present, else fall back to whatever identifier is available
        dedupe_key = 'companyName' if 'companyName' in df_li_co.columns else available_columns[0]
        before_count = len(df_li_co)
        df_li_co = df_li_co.drop_duplicates(subset=[dedupe_key], keep='first')
        after_count = len(df_li_co)

        if before_count != after_count:
            st.info(f"Removed {before_count - after_count} duplicate compan{'y' if before_count - after_count == 1 else 'ies'} — {after_count} unique companies remain.")

        st.dataframe(df_li_co.head(20))

        csv_data = df_li_co.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Confirm LinkedIn Company CSV Download",
            data=csv_data,
            file_name="LinkedIn_company_formatted.csv",
            mime="text/csv",
            key="LinkedIn_company_download_confirm"
        )
