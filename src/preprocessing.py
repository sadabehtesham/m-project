"""
Shared data cleaning & feature preparation helpers, used across the
per-disease preprocessing notebooks. Extracting these here avoids
copy-pasting the same imputation/encoding logic 5 times.

These are intentionally generic (work on any DataFrame/column), since
each disease's specific cleaning steps (e.g. CKD's messy '?' values,
liver's Gender encoding) are still disease-specific and live inline
in that disease's 02_preprocessing.ipynb.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def replace_invalid_with_nan(df, columns, invalid_value=0):
    """Replaces a placeholder 'invalid' value (e.g. 0 where 0 is not
    medically possible, like Glucose or BMI) with NaN so it can be
    properly imputed instead of silently treated as a real reading."""
    df = df.copy()
    df[columns] = df[columns].replace(invalid_value, np.nan)
    return df


def impute_median(df, columns):
    """Fills missing values in the given columns with each column's
    own median. Median is preferred over mean for medical data since
    it's less skewed by outliers (e.g. one extreme lab value)."""
    df = df.copy()
    for col in columns:
        df[col] = df[col].fillna(df[col].median())
    return df


def encode_binary(df, column, mapping):
    """Maps a categorical column (e.g. 'yes'/'no') to 0/1 using the
    given mapping dict. Any value not in the mapping becomes NaN,
    then gets filled with the column's most common value."""
    df = df.copy()
    df[column] = df[column].map(mapping)
    if df[column].isnull().any():
        df[column] = df[column].fillna(df[column].mode()[0])
    return df


def strip_whitespace(df, columns=None):
    """Strips leading/trailing whitespace from string columns -- a
    common issue in messier datasets like CKD (' yes' vs 'yes')."""
    df = df.copy()
    cols = columns if columns is not None else df.select_dtypes(include="object").columns
    for col in cols:
        df[col] = df[col].astype(str).str.strip()
    return df


def split_and_scale(X, y, test_size=0.2, random_state=42, stratify=True):
    """Standard train/test split + StandardScaler, fit ONLY on the
    training set to avoid leaking test-set information. Returns
    scaled DataFrames (not raw arrays) so column names are preserved."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y if stratify else None,
    )

    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train), columns=X.columns, index=X_train.index
    )
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test), columns=X.columns, index=X_test.index
    )

    return X_train_scaled, X_test_scaled, y_train, y_test, scaler
