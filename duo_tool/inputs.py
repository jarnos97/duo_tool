import numpy as np
import pandas as pd
from loguru import logger
from pandas import Timestamp

from duo_tool.calculations import AanloopPhase, PaymentPhase
from duo_tool.utils import diff_month


def get_inputs(
    years: int, start_date: Timestamp, original_debt: int, interest_perc: float, payment_offset: int
) -> dict:
    """
    Gather the debt over time (df), total interest paid and monthly payment based on input.
    Args:
        years: amount of years to pay back loan
        start_date: the start date of the aanloopfase
        original_debt: the original debt amount in euros
        interest_perc: the interest percentage
        payment_offset: the number of months after the start date to start paying back the loan.

    Returns:
        dict: the debt over time, interest paid, and monthly payment.
    """
    # Convert the interest percentage to a rate
    interest_rate = interest_perc / 100
    months = 12 * years

    # Get the information for the aanloopfase
    aanloopfase = AanloopPhase(start_date, interest_rate, original_debt, payment_offset)
    aanloopfase_df = aanloopfase.calculate()
    debt_after_aanloopfase = aanloopfase.final_debt

    # Get information for the payment phase
    first_payment_date = start_date + pd.DateOffset(months=payment_offset)
    payment_phase = PaymentPhase(first_payment_date, interest_rate, debt_after_aanloopfase, months)
    payment_phase_df = payment_phase.calculate()
    payment = payment_phase.payment

    # Combine dataframes
    df = pd.concat([aanloopfase_df, payment_phase_df], axis=0).reset_index(drop=True)

    # Calculate the total interest paid
    interest_paid = round(df["payment"].sum() - original_debt, 2)

    return {"debt_over_time": df, "total_interest_paid": interest_paid, "monthly_payment": payment}


def one_time_payment(
    inputs: dict,
    payment_amount: int,
    payment_date: Timestamp,
    interest_perc: float,
    years: int,
    start_date: Timestamp,
    original_debt: int,
    payment_offset: int,  # TODO: change order to conform with previous functions
    current_monthly_payment: float,
):
    # Convert the interest percentage to a rate
    interest_rate = interest_perc / 100

    # Trim the dataframe until payment date
    df = inputs["debt_over_time"]
    idx = df.loc[df["month"] == payment_date].index[0]
    df = df[: idx + 1].copy()

    # If the remaining debt is lower than the payment amount, throw error
    if df["debt"].iloc[idx] < payment_amount:
        raise ValueError(
            f"De schuld op de datum van extra aflossing ({df['debt'].iloc[idx]:.2f}) moet hoger dan of gelijk "
            f"zijn aan het af te lossen bedrag ({payment_amount})"
        )

    # If the remaining debt equals the payment amount, there is no need to recalculate.
    if df["debt"].iloc[idx] == payment_amount:
        # TODO: in this case we should not recalculate > and the payment finishes earlier than the 35/15 years
        raise NotImplementedError("to be implemented")

    # Subtract/add the extra payment
    df.at[idx, "debt"] -= payment_amount
    df.at[idx, "payment"] += payment_amount
    df.at[idx, "principal"] += payment_amount

    # If the payment date is after the aanloopfase, we can simply slice the df and recalculate it partially.
    if payment_date > start_date + pd.DateOffset(months=payment_offset - 1):
        # Recalculate the rest of the payment
        months_left = (years * 12) - diff_month(payment_date, start_date + pd.DateOffset(months=payment_offset))
        remaining_debt = df["debt"].iloc[-1]

        payment_phase = PaymentPhase(payment_date, interest_rate, remaining_debt, months_left)
        rest_df = payment_phase.calculate()
        updated_payment = payment_phase.payment
        rest_df = rest_df.drop(index=df.index[0], axis=0)

        logger.info(f"months left after extra payment: {months_left}")
        logger.info(f"remaining deb after extra payment: {remaining_debt}")
        logger.info(f"new monthly payment after extra payment: {updated_payment}")

        # Combine data again
        df = pd.concat([df, rest_df], axis=0).reset_index(drop=True)

        # Calculate the total interest paid > old amount * time past + new amount * time left
        interest_paid = round(df["payment"].sum() - original_debt, 2)

        return {
            "debt_over_time": df,
            "total_interest_paid": interest_paid,
            "monthly_payment": round(np.mean([updated_payment, current_monthly_payment]), 2),
        }

    # If the payment is during the aanloopfase adapt the aanloopfase and then calculate the payment phase
    else:
        # The debt needs to be increased with interest of 1 month
        debt_plus_interest = round(df["debt"].iloc[idx] * (pow((1 + interest_rate / 12), 1)), 2)

        # Calculate rest of aanloopfase and combine
        aanloopfase = AanloopPhase(
            start_date=payment_date + pd.DateOffset(months=1),  # The month after the additional payment
            interest_rate=interest_rate,
            debt=debt_plus_interest,
            payment_offset=payment_offset - idx - 1,  # The original offset minus the amount of months that have passed
        )
        aanloopfase_df = aanloopfase.calculate()
        debt_after_aanloopfase = aanloopfase.final_debt
        aanloopfase_df = pd.concat([df, aanloopfase_df], axis=0).reset_index(drop=True)

        # Calculate the payment phase
        first_payment_date = start_date + pd.DateOffset(months=payment_offset)
        payment_phase = PaymentPhase(first_payment_date, interest_rate, debt_after_aanloopfase, 12 * years)
        payment_phase_df = payment_phase.calculate()

        # Combine dataframes
        df = pd.concat([aanloopfase_df, payment_phase_df], axis=0).reset_index(drop=True)

        # Calculate the total interest paid
        interest_paid = round(df["payment"].sum() - original_debt, 2)

        return {"debt_over_time": df, "total_interest_paid": interest_paid, "monthly_payment": payment_phase.payment}


if __name__ == "__main__":
    date = pd.to_datetime("01-2024")
    y = 35
    i_p = 2.56
    d = 30_000
    offset = 24  # in months

    out = get_inputs(y, date, d, i_p, 24)
    out_df = out["debt_over_time"]

    out2 = one_time_payment(
        inputs=out,
        payment_amount=10_000,
        payment_date=pd.to_datetime("03-2025"),
        interest_perc=i_p,
        years=y,
        start_date=date,
        original_debt=d,
        payment_offset=24,
        current_monthly_payment=out["monthly_payment"],
    )
    print(out2)
