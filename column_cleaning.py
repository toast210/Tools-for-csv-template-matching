import io
import re
import pandas as pd

TO_BE_MATCHED_COLUMNS = [
    'full name',
    'email',
    'pin_code',
    'company',
    'city',
    'state',
    'country',
    'phone',
    'linkedin url',
    'linkedin url company',
    'company website'
]

def read_file(uploaded_file) -> pd.DataFrame:
    """Reads CSV or Excel file safely into a string-typed DataFrame."""
    if not uploaded_file:
        return None

    uploaded_file.seek(0)
    filename = getattr(uploaded_file, "name", "").lower()

    if filename.endswith(".xlsx"):
        return pd.read_excel(uploaded_file, dtype=str, engine="openpyxl")
    elif filename.endswith(".xls"):
        return pd.read_excel(uploaded_file, dtype=str)
    else:
        try:
            return pd.read_csv(uploaded_file, encoding="utf-8", on_bad_lines="skip", dtype=str)
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding="latin1", on_bad_lines="skip", dtype=str)


def clean_phone_series(series: pd.Series) -> pd.Series:
    """Extracts numeric digits and prepends '+' only if valid digits exist."""
    def _format(val):
        if pd.isna(val):
            return ""
        digits = re.sub(r"[^\d]", "", str(val))
        return f"+{digits}" if digits else ""
    return series.apply(_format)


def split_full_name(series: pd.Series):
    """Safely extracts First Name and Last Name from a full name series."""
    def _split(val):
        if pd.isna(val) or not str(val).strip():
            return "", ""
        parts = str(val).strip().split()
        first_name = parts[0]
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        return first_name, last_name

    names = series.apply(_split)
    first_names = names.apply(lambda x: x[0])
    last_names = names.apply(lambda x: x[1])
    return first_names, last_names


def apply_column_mapping(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Renames mapped columns and retains only matched target columns."""
    df_renamed = df.rename(columns=mapping)
    available_targets = [c for c in TO_BE_MATCHED_COLUMNS if c in df_renamed.columns]
    return df_renamed[available_targets].copy()


def filter_rows(df: pd.DataFrame, column: str, operator: str, action: str, value: str = None) -> pd.DataFrame:
    """Applies filter conditions and either keeps or deletes matching rows."""
    if column not in df.columns:
        return df

    col_data = df[column]

    if operator == "Is Empty":
        mask = col_data.isna() | (col_data.astype(str).str.strip() == "")
    elif operator == "Is Not Empty":
        mask = ~(col_data.isna() | (col_data.astype(str).str.strip() == ""))
    elif operator == "Equals":
        mask = col_data.astype(str) == str(value)
    elif operator == "Not Equals":
        mask = col_data.astype(str) != str(value)
    elif operator == "Contains":
        mask = col_data.astype(str).str.contains(str(value or ""), case=False, na=False)
    elif operator == "Greater Than":
        mask = pd.to_numeric(col_data, errors="coerce") > pd.to_numeric(value, errors="coerce")
    elif operator == "Less Than":
        mask = pd.to_numeric(col_data, errors="coerce") < pd.to_numeric(value, errors="coerce")
    else:
        mask = pd.Series(True, index=df.index)

    return df[~mask].copy() if action == "Delete matching rows" else df[mask].copy()


def generate_facebook_template(df: pd.DataFrame) -> pd.DataFrame:
    """Builds the Facebook audience upload schema."""
    df_out = pd.DataFrame(index=df.index)

    if 'full name' in df.columns:
        df_out['fn'], df_out['ln'] = split_full_name(df['full name'])
    else:
        df_out['fn'], df_out['ln'] = "", ""

    df_out['email'] = df.get('email', '')
    df_out['phone'] = clean_phone_series(df['phone']) if 'phone' in df.columns else ""
    df_out['ct'] = df.get('city', '')
    df_out['st'] = df.get('state', '')
    df_out['country'] = df.get('country', '')

    target_cols = ['fn', 'ln', 'email', 'phone', 'ct', 'st', 'country']
    return df_out[[c for c in target_cols if c in df_out.columns]]


def generate_google_template(df: pd.DataFrame) -> pd.DataFrame:
    """Builds the Google Customer Match schema."""
    df_out = pd.DataFrame(index=df.index)

    df_out['Email'] = df.get('email', '')
    df_out['Phone'] = clean_phone_series(df['phone']) if 'phone' in df.columns else ""

    if 'full name' in df.columns:
        df_out['First Name'], df_out['Last Name'] = split_full_name(df['full name'])
    else:
        df_out['First Name'], df_out['Last Name'] = "", ""

    df_out['Country'] = df.get('country', '')

    target_cols = ['Email', 'Phone', 'First Name', 'Last Name', 'Country']
    return df_out[[c for c in target_cols if c in df_out.columns]]


def generate_linkedin_contact_template(df: pd.DataFrame) -> pd.DataFrame:
    """Builds the LinkedIn Contact List upload schema."""
    df_out = pd.DataFrame(index=df.index)

    df_out['email'] = df.get('email', '')
    df_out['full name'] = df.get('full name', '')
    df_out['companyName'] = df.get('company', '')
    df_out['city'] = df.get('city', '')
    df_out['state'] = df.get('state', '')
    df_out['country'] = df.get('country', '')
    df_out['phone'] = clean_phone_series(df['phone']) if 'phone' in df.columns else ""
    df_out['linkedinUrl'] = df.get('linkedin url', '')

    target_cols = ['email', 'full name', 'companyName', 'city', 'state', 'country', 'phone', 'linkedinUrl']
    return df_out[[c for c in target_cols if c in df_out.columns]]


def generate_linkedin_company_template(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the LinkedIn Company List upload schema including
    geographic disambiguation attributes (city, state, postalcode, country).
    """
    df_out = pd.DataFrame(index=df.index)

    # Identifiers
    df_out['companyname'] = df.get('company', '')
    df_out['companywebsite'] = df.get('company website', '')
    df_out['linkedincompanypageurl'] = df.get('linkedin url company', '')
    
    # Geographic disambiguation
    df_out['city'] = df.get('city', '')
    df_out['state'] = df.get('state', '')
    df_out['postalcode'] = df.get('pin_code', '')
    df_out['country'] = df.get('country', '')

    target_cols = [
        'companyname',
        'companywebsite',
        'linkedincompanypageurl',
        'city',
        'state',
        'postalcode',
        'country'
    ]
    df_out = df_out[[c for c in target_cols if c in df_out.columns]]

    # Deduplicate against the first valid available identifier
    dedupe_col = next(
        (c for c in ['companywebsite', 'linkedincompanypageurl', 'companyname'] if c in df_out.columns),
        None
    )
    if dedupe_col:
        df_out = df_out.drop_duplicates(subset=[dedupe_col], keep='first')

    return df_out

    return df_out
