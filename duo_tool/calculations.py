"""
TODO: add description

Sources:
- https://duo.nl/particulier/studieschuld-terugbetalen/berekening-maandbedrag.jsp
- https://duo.nl/particulier/rekenhulp-studiefinanciering.jsp#/nl/terugbetalen/resultaat
- https://www.berekenhet.nl/lenen-en-krediet/studiefinanciering-terugbetalen.html
- https://www.geld.nl/lenen/service/aflossing-lening-berekenen
"""

from typing import Tuple

import pandas as pd


def monthly_compound(original_debt: int, months_passed: int, interest: float) -> float:
    """ Calculates monthly compounded interest based on original debt, interest, and the months passed. """
    return round(original_debt * (pow((1 + interest / 12), months_passed)), 2)


def monthly_payment(debt_after_aanloopfase: float, interest: float, months: int) -> float:
    """ Calculates the monthly payment of a loan based on debt, interest and total duration in months. """
    monthly_interest_rate = (1 + interest) ** (1 / 12) - 1
    payment = (
        debt_after_aanloopfase * monthly_interest_rate * (1 + monthly_interest_rate) ** months / (
        (1 + monthly_interest_rate) ** months - 1)
    )
    return round(payment, 2)


def aanloopfase(
    start_date: str,
    total_months: int,
    interest_rate: float,
    original_debt: int,
) -> Tuple[float, pd.DataFrame]:
    """ Calculate two elements. The debt after the aanloopfase and the dataframe for plotting. """
    # Get months in the 'aanloopfase' first
    aanloopfase_dates = pd.date_range(start=start_date, freq='MS', periods=24)

    # Add interest on the debt
    current_debt = [monthly_compound(original_debt, x, interest_rate) for x in range(24)]
    aanloopfase_df = pd.DataFrame(zip(aanloopfase_dates, current_debt), columns=['month', 'debt'])

    # Final debt after aanloopfase
    final_debt = monthly_compound(original_debt, 23, interest_rate)

    return final_debt, aanloopfase_df


def payment_phase(
    debt_after_aanloopfase: float,
    interest: float,
    months: int
) -> Tuple[float, pd.DataFrame]:
    # Determine the monthly payment
    payment = monthly_payment(debt_after_aanloopfase, interest, months)

    # Get the debt over time
    return payment


def get_inputs(
    years: int,
    start_date: str,
    original_debt: int,
    interest_perc: float
):
    # Convert the interest percentage to a rate
    interest_rate = interest_perc / 100
    months = 12 * years

    # Get the information for the aanloopfase
    debt_after_aanloopfase, aanloopfase_df = aanloopfase(start_date, months, interest_rate, original_debt)

    # Get information for the payment phase
    payment = payment_phase(debt_after_aanloopfase, interest_rate, months)
    print(payment)


    #

    # # Determine the date range
    # dates = pd.date_range(start=start_date, freq='MS', periods=num_months+1)
    #
    # # Get the months-left column
    # months_left = [i for i in range(420, -1, -1)]
    #
    # # Create df
    # df = pd.DataFrame(zip(dates, months_left), columns=['month', 'months_left'])
    #
    # print(df)


if __name__ == '__main__':
    date = '01-2024'
    y = 35
    i = 2.56
    debt = 50_000

    get_inputs(y, date, debt, i)


# if __name__ == '__main__':
#     lening = 53_000
#     rente = 0.0256
#     looptijd = 420
#
#     monthly_payment(lening, rente, looptijd)
