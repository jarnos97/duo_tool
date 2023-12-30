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


def monthly_compound(original_debt: int, months_passed: int, interest: float) -> float:
    """ Calculates monthly compounded interest based on original debt, interest, and the months passed. """
    return round(original_debt * (pow((1 + interest / 12), months_passed)), 2)


def monthly_payment(debt_after_aanloopfase: float, interest: float, months: int) -> float:
    """ Calculates the monthly payment of a loan based on debt, interest and total duration in months. """
    # If the interest is 0%, the monthly payment is simply the debt / months
    if interest == 0:
        return round(debt_after_aanloopfase/months, 2)

    monthly_interest_rate = (1 + interest) ** (1 / 12) - 1
    payment = (
        debt_after_aanloopfase * monthly_interest_rate * (1 + monthly_interest_rate) ** months / (
        (1 + monthly_interest_rate) ** months - 1)
    )
    return round(payment, 2)


def aanloopfase(
    start_date: str,
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

    # Final debt after aanloopfase
    final_debt = monthly_compound(original_debt, payment_offset - 1, interest_rate)
    logger.info(f'final debt after aanloopfase: {final_debt}')

    return final_debt, aanloopfase_df


def payment_phase(
    original_debt: int,
    debt_after_aanloopfase: float,
    interest: float,
    months: int,
    start_date: str,
    payment_offset: int
) -> Tuple[float, float, pd.DataFrame]:
    """

    Args:
        original_debt: the original debt in euros
        debt_after_aanloopfase: the debt after the aanloopfase
        interest: the current interest rate
        months: the amount of months to pay off debt
        start_date: start date of the aanloopfase
        payment_offset: the payment offset in months

    Returns:

    """
    # Determine the monthly payment > this would get overwritten if someone does an extra monthly payment
    payment = monthly_payment(debt_after_aanloopfase, interest, months)

    # Total interest paid
    interest_paid = (payment * months) - original_debt

    # Get the debt over time
    payment_date = pd.to_datetime(start_date) + pd.DateOffset(months=payment_offset)
    payment_dates = pd.date_range(start=payment_date, freq='MS', periods=months + 1)
    linear_payment = round(debt_after_aanloopfase / months, 2)
    current_debt = [(debt_after_aanloopfase - (x * linear_payment)) for x in range(months + 1)]
    payment_phase_df = pd.DataFrame(zip(payment_dates, current_debt), columns=['month', 'debt'])

    return payment, interest_paid, payment_phase_df


def get_inputs(
    years: int,
    start_date: str,
    original_debt: int,
    interest_perc: float,
    custom_payment_date: str = None
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
        delta = pd.to_datetime(custom_payment_date).to_period('M') - pd.to_datetime(start_date).to_period('M')
        payment_offset = delta.n
        logger.info(f"Payment offset = {payment_offset} months.")
        assert 0 < payment_offset <= 60, 'Custom payment date must be after start date and no later than 60 months'

    # Convert the interest percentage to a rate
    interest_rate = interest_perc / 100
    months = 12 * years

    # Get the information for the aanloopfase
    debt_after_aanloopfase, aanloopfase_df = aanloopfase(start_date, interest_rate, original_debt, payment_offset)

    # Get information for the payment phase
    payment, interest_paid, payment_phase_df = payment_phase(
        original_debt, debt_after_aanloopfase, interest_rate, months, start_date, payment_offset
    )

    # Combine dataframes
    df = pd.concat([aanloopfase_df, payment_phase_df], axis=0)

    return {
        'debt_over_time': df,
        'total_interest_paid': interest_paid,
        'monthly_payment': payment
    }


if __name__ == '__main__':
    date = '01-2024'
    y = 35
    i = 0.0  # 2.56
    debt = 50_000
    custom_date = '01-2027'

    out = get_inputs(y, date, debt, i, custom_date)
    print(out['debt_over_time'].tail(3))
