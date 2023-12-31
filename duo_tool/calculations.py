"""
TODO: add description

Sources:
- https://duo.nl/particulier/studieschuld-terugbetalen/berekening-maandbedrag.jsp
- https://duo.nl/particulier/rekenhulp-studiefinanciering.jsp#/nl/terugbetalen/resultaat
- https://www.berekenhet.nl/lenen-en-krediet/studiefinanciering-terugbetalen.html
- https://www.geld.nl/lenen/service/aflossing-lening-berekenen
"""
import pandas as pd

from typing import Tuple
from loguru import logger
from pandas import Timestamp

from utils import diff_month


def monthly_compound(original_debt: int, months_passed: int, interest: float) -> float:
    """ Calculates monthly compounded interest based on original debt, interest, and the months passed. """
    return round(original_debt * (pow((1 + interest / 12), months_passed)), 2)


def monthly_payment(remaining_debt: float, interest: float, months: int) -> float:
    """ Calculates the monthly payment of a loan based on debt, interest and total duration in months. """
    # If the interest is 0%, the monthly payment is simply the debt / months
    if interest == 0:
        return round(remaining_debt / months, 2)

    monthly_interest_rate = (1 + interest) ** (1 / 12) - 1
    payment = (
        remaining_debt * monthly_interest_rate * (1 + monthly_interest_rate) ** months / (
        (1 + monthly_interest_rate) ** months - 1)
    )
    return round(payment, 2)


def aanloopfase(
    start_date: Timestamp,
    interest_rate: float,
    original_debt: int,
    payment_offset: int
) -> Tuple[float, pd.DataFrame]:
    """
    Calculate two elements. The debt after the aanloopfase and the dataframe for plotting.

    Args:
        start_date (str): start date of the aanloopfase
        interest_rate (float): the current interest rate
        original_debt (int): the original debt in euros
        payment_offset (int): the payment offset in months
    """
    # Get months in the 'aanloopfase' first
    aanloopfase_dates = pd.date_range(start=start_date, freq='MS', periods=payment_offset)

    # Add interest on the debt
    current_debt = [monthly_compound(original_debt, x, interest_rate) for x in range(payment_offset)]
    aanloopfase_df = pd.DataFrame(zip(aanloopfase_dates, current_debt), columns=['month', 'debt'])
    aanloopfase_df['payment'] = 0.0

    # Final debt after aanloopfase
    final_debt = monthly_compound(original_debt, payment_offset - 1, interest_rate)
    logger.info(f'final debt after aanloopfase: {final_debt}')

    return final_debt, aanloopfase_df


def payment_phase(
    remaining_debt: float,
    interest: float,
    months: int,
    payment_date: Timestamp,
) -> Tuple[float, pd.DataFrame]:
    """

    Args:
        remaining_debt: the debt after the aanloopfase
        interest: the current interest rate
        months: the amount of months to pay off debt
        payment_date: start date of the payment phase

    Returns:
        Tuple: payment amount, payment dataframe
    """
    # Determine the monthly payment
    payment = monthly_payment(remaining_debt, interest, months)

    # Get the debt over time
    payment_dates = pd.date_range(start=payment_date, freq='MS', periods=months)
    linear_payment = round(remaining_debt / months, 2)
    current_debt = [(remaining_debt - (x * linear_payment)) for x in range(months)]
    payment_phase_df = pd.DataFrame(zip(payment_dates, current_debt), columns=['month', 'debt'])
    payment_phase_df['payment'] = payment

    return payment, payment_phase_df


def get_inputs(
    years: int,
    start_date: Timestamp,
    original_debt: int,
    interest_perc: float,
    custom_payment_date: Timestamp = None
) -> dict:
    """
    Gather the debt over time (df), total interest paid and monthly payment based on input.
    Args:
        years: amount of years to pay back loan
        start_date: the start date of the aanloopfase
        original_debt: the original debt amount in euros
        interest_perc: the interest percentage
        custom_payment_date: optional custom payment date in case of paying earlier or later than standard.

    Returns:
        dict: the debt over time, interest paid, and monthly payment.
    """
    # If a custom payment date is set, we calculate the number of months after which the person wants to start paying.
    payment_offset = 24  # The default offset is two years
    if custom_payment_date:
        delta = custom_payment_date.to_period('M') - start_date.to_period('M')
        payment_offset = delta.n
        logger.info(f"Payment offset = {payment_offset} months.")
        assert 0 < payment_offset <= 60, 'Custom payment date must be after start date and no later than 60 months'

    # Convert the interest percentage to a rate
    interest_rate = interest_perc / 100
    months = 12 * years

    # Get the information for the aanloopfase
    debt_after_aanloopfase, aanloopfase_df = aanloopfase(start_date, interest_rate, original_debt, payment_offset)

    # Get information for the payment phase
    first_payment_date = start_date + pd.DateOffset(months=payment_offset)
    payment, payment_phase_df = payment_phase(debt_after_aanloopfase, interest_rate, months, first_payment_date)

    # Combine dataframes
    df = pd.concat([aanloopfase_df, payment_phase_df], axis=0).reset_index(drop=True)

    # Calculate the total interest paid
    interest_paid = round(df['payment'].sum() - original_debt, 2)

    return {
        'debt_over_time': df,
        'total_interest_paid': interest_paid,
        'monthly_payment': payment
    }


def one_time_payment(
    inputs: dict,
    payment_amount: int,
    payment_date: Timestamp,
    interest_perc: float,
    years: int,
    start_date: Timestamp,
    original_debt: int,
    custom_payment_date: Timestamp = None,  # TODO: change order to conform with previous functions
):
    # If a custom payment date is set, we calculate the number of months after which the person wants to start paying.
    payment_offset = 24  # The default offset is two years
    if custom_payment_date:
        delta = custom_payment_date.to_period('M') - start_date.to_period('M')
        payment_offset = delta.n
        assert 0 < payment_offset <= 60, 'Custom payment date must be after start date and no later than 60 months'
    logger.info(f"Payment offset = {payment_offset} months.")

    # Convert the interest percentage to a rate
    interest_rate = interest_perc / 100

    # If the payment date is after the aanloopfase, we can simply slice the df and recalculate it partially.
    if payment_date > start_date + pd.DateOffset(months=payment_offset-1):
        # Trim the dataframe until payment date
        df = inputs['debt_over_time']
        idx = df.loc[df['month'] == payment_date].index[0]
        df = df[:idx + 1].copy()

        # Subtract/add the extra payment
        df.at[idx, 'debt'] -= payment_amount
        df.at[idx, 'payment'] += payment_amount

        # Recalculate the rest of the payment
        months_left = (years * 12) - diff_month(payment_date, start_date + pd.DateOffset(months=payment_offset))
        remaining_debt = df['debt'].iloc[-1]
        updated_payment, rest_df = payment_phase(
            remaining_debt, interest_rate, months_left, payment_date
        )
        rest_df = rest_df.drop(index=df.index[0], axis=0)

        logger.info(f'months left after extra payment: {months_left}')
        logger.info(f'remaining deb after extra payment: {remaining_debt}')
        logger.info(f'new monthly payment after extra payment: {updated_payment}')

        # Combine data again
        df = pd.concat([df, rest_df], axis=0).reset_index(drop=True)

        # Calculate the total interest paid
        interest_paid = round(df['payment'].sum() - original_debt, 2)

        return {
            'debt_over_time': df,
            'total_interest_paid': interest_paid,
            'monthly_payment': updated_payment  # TODO: add the old payment - as tuple or average
        }

    # TODO: continue here. Add the same functionality for when the additional payment is during the aanloopfase
    # Then implement changes in the dashboard.


if __name__ == '__main__':
    date = pd.to_datetime('01-2024')
    y = 35
    i = 2.56
    debt = 30_000
    custom_date = pd.to_datetime('01-2027')

    out = get_inputs(y, date, debt, i)

    out2 = one_time_payment(
        inputs=out,
        payment_amount=10_000,
        payment_date=pd.to_datetime('01-2027'),
        interest_perc=i,
        years=y,
        start_date=date,
        original_debt=debt
    )
