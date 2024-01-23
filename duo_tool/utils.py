import datetime
import streamlit as st
import pandas as pd


def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month


def check_date_format(date: str, date_format: str = '%m-%Y'):
    try:
        datetime.datetime.strptime(date, date_format)
    except ValueError:
        st.error("Verkeerde datum. Type je datum als maand-jaar > '01-2026'")
        raise ValueError('Wrong date format')
    return pd.to_datetime(date)


def check_amount_format(amount: int, lower_limit: int = 0, upper_limit: int = None):
    if amount <= lower_limit:
        st.error(f'Het getal moet groter dan {lower_limit} zijn.')
        raise ValueError('Amount too low')
    if upper_limit and amount > upper_limit:
        st.error(f'Het getal moet kleiner of gelijk zijn aan {upper_limit}')
        raise ValueError('Amount too high')
