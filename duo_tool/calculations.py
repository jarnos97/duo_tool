"""
TODO: add description

Sources:
- https://duo.nl/particulier/studieschuld-terugbetalen/berekening-maandbedrag.jsp
- https://duo.nl/particulier/rekenhulp-studiefinanciering.jsp#/nl/terugbetalen/resultaat
- https://www.berekenhet.nl/lenen-en-krediet/studiefinanciering-terugbetalen.html
- https://www.geld.nl/lenen/service/aflossing-lening-berekenen
- https://www.calculator.net/loan-calculator.html
"""
import abc

import numpy as np
import pandas as pd
from loguru import logger
from pandas import Timestamp

from duo_tool.utils import diff_month


class LoanPhase(abc.ABC):
    """Each phase should have a calculate method that returns a dataframe"""

    def __init__(self, start_date: Timestamp, interest_rate: float, debt: float):
        self.start_date = start_date
        self.interest_rate = interest_rate
        self.debt = debt

    def calculate(self) -> pd.DataFrame:
        ...


class AanloopPhase(LoanPhase):
    """Class to calculate the aanloopfase"""

    def __init__(self, start_date: Timestamp, interest_rate: float, debt: float, payment_offset: int):
        """
        Args:
            start_date (str): start date of the aanloopfase
            interest_rate: The annual interest rate (as a decimal).
            debt (int): the original debt in euros
            payment_offset (int): the payment offset in months
        """
        super().__init__(start_date, interest_rate, debt)
        self.payment_offset = payment_offset
        self.final_debt = None
        # self.final_debt_plus_one = None

    @staticmethod
    def _monthly_compound(original_debt: float, months_passed: int, interest: float) -> float:
        """Calculates monthly compounded interest based on original debt, yearly interest, and the months passed."""
        return round(original_debt * (pow((1 + interest / 12), months_passed)), 2)

    def calculate(self) -> pd.DataFrame:
        """
        Calculate two elements. The debt after the aanloopfase and the dataframe for plotting.
        """
        # Get months in the 'aanloopfase' first
        aanloopfase_dates = pd.date_range(start=self.start_date, freq="MS", periods=self.payment_offset)

        # Add interest on the debt
        current_debt = [self._monthly_compound(self.debt, x, self.interest_rate) for x in range(self.payment_offset)]

        # Create output dataframe
        aanloopfase_df = pd.DataFrame(zip(aanloopfase_dates, current_debt), columns=["month", "debt"])
        aanloopfase_df[["payment", "principal", "interest"]] = 0.0

        # Save the final debt after aanloopfase
        self.final_debt = aanloopfase_df["debt"].iloc[-1]
        logger.info(f"final debt after aanloopfase: {self.final_debt}")

        # # For the first month of the payment phase there is one additional compound after the aanloopfase
        # self.final_debt_plus_one = self._monthly_compound(self.final_debt, 1, self.interest_rate)

        return aanloopfase_df


class PaymentPhase(LoanPhase):
    """Class to calculate the payment phase"""

    def __init__(self, start_date: Timestamp, interest_rate: float, debt: float, months: int):
        """
        Args:
            start_date (str): start date of the aanloopfase
            interest_rate: The annual interest rate (as a decimal).
            debt (int): the current debt in euros, after the aanloopfase
            months: the amount of months to pay off debt
        """
        super().__init__(start_date, interest_rate, debt)
        self.months = months
        self.payment = None

    @staticmethod
    def _monthly_payment(remaining_debt: float, interest: float, months: int) -> float:
        """Calculates the monthly payment of an amortized loan based on debt, interest and total duration in months."""
        # If the interest is 0%, the monthly payment is simply the debt / months
        if interest == 0:
            return round(remaining_debt / months, 2)

        # Define i as the monthly interest rate
        i = interest / 12
        n = months
        payment = ((1 + i) ** n * i) / ((1 + i) ** n - 1) * remaining_debt
        return round(payment, 2)

    def _calculate_amortization(self) -> pd.DataFrame:
        """
        Calculate amortization schedule for loan.

        Returns:
            amortization_schedule: pandas dataframe containing amortization information for each month.
        """
        # Convert annual interest rate to monthly rate
        monthly_interest_r = self.interest_rate / 12

        # Get the date range
        payment_dates = pd.date_range(start=self.start_date, freq="MS", periods=self.months)

        # Initialize variables
        remaining_balance = self.debt
        amortization_schedule = []

        for month in payment_dates:
            # Calculate interest for the current month
            interest_payment = round(remaining_balance * monthly_interest_r, 2)

            # Calculate principal for the current month
            principal_payment = round(self.payment - interest_payment, 2)

            # Update the remaining balance
            remaining_balance -= principal_payment

            # Ensure the remaining balance doesn't go below zero
            remaining_balance = max(0, remaining_balance)

            # Create a dictionary for the current month's information
            month_info = {
                "month": month,
                "debt": remaining_balance,
                "payment": self.payment,
                "principal": principal_payment,
                "interest": interest_payment,
            }

            # Append the dictionary to the amortization schedule
            amortization_schedule.append(month_info)

        return pd.DataFrame(amortization_schedule)

    def calculate(self) -> pd.DataFrame:
        """
        Calculate the monthly payment and the amortization schedule
        """
        # Determine the monthly payment
        logger.info(self.debt)
        self.payment = self._monthly_payment(self.debt, self.interest_rate, self.months)
        logger.info(f"Monthly payment will be: {self.payment}")

        # # Get the debt over time
        # payment_dates = pd.date_range(start=self.start_date, freq="MS", periods=self.months)
        # linear_payment = round(self.debt / self.months, 2)
        # current_debt = [(self.debt - (x * linear_payment)) for x in range(self.months)]
        # payment_phase_df = pd.DataFrame(zip(payment_dates, current_debt), columns=["month", "debt"])
        # payment_phase_df["payment"] = self.payment

        payment_phase_df = self._calculate_amortization()

        return payment_phase_df


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

    # If the payment date is after the aanloopfase, we can simply slice the df and recalculate it partially.
    if payment_date > start_date + pd.DateOffset(months=payment_offset - 1):
        # Recalculate the rest of the payment
        months_left = (years * 12) - diff_month(payment_date, start_date + pd.DateOffset(months=payment_offset))
        remaining_debt = df["debt"].iloc[-1]

        payment_phase = PaymentPhase(payment_date, interest_rate, remaining_debt, months_left)
        rest_df = payment_phase.calculate()
        updated_payment = payment_phase.payment()
        rest_df = rest_df.drop(index=df.index[0], axis=0)

        logger.info(f"months left after extra payment: {months_left}")
        logger.info(f"remaining deb after extra payment: {remaining_debt}")
        logger.info(f"new monthly payment after extra payment: {updated_payment}")

        # Combine data again
        df = pd.concat([df, rest_df], axis=0).reset_index(drop=True)

        # Calculate the total interest paid
        interest_paid = round(df["payment"].sum() - original_debt, 2)
        # TODO: this is not correct!! Need to calculate using the monthly amounts * months

        return {
            "debt_over_time": df,
            "total_interest_paid": interest_paid,
            "monthly_payment": round(np.mean([updated_payment, current_monthly_payment]), 2),
        }

    # If the payment is during the aanloopfase adapt the aanloopfase and then calculate the payment phase
    else:
        # Calculate rest of aanloopfase and combine
        aanloopfase = AanloopPhase(
            start_date=payment_date + pd.DateOffset(months=1),  # The month after the additional payment
            interest_rate=interest_rate,
            debt=df["debt"].iloc[idx],  # The updated debt after payment
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
        # TODO: this is not correct!! Need to calculate using the monthly amounts * months

        return {"debt_over_time": df, "total_interest_paid": interest_paid, "monthly_payment": payment_phase.payment}

    # TODO: continue here. Add the same functionality for when the additional payment is during the aanloopfase
    # TODO: look into the total interest paid > is this correct. Why does it increase if you make an extra payment later


if __name__ == "__main__":
    date = pd.to_datetime("01-2024")
    y = 35
    i_p = 2.56
    d = 30_000
    offset = 24  # in months

    out = get_inputs(y, date, d, i_p, 24)
    out_df = out["debt_over_time"]

    # out2 = one_time_payment(
    #     inputs=out,
    #     payment_amount=10_000,
    #     payment_date=pd.to_datetime("01-2025"),
    #     interest_perc=i,
    #     years=y,
    #     start_date=date,
    #     original_debt=debt,
    #     payment_offset=24,
    #     current_monthly_payment=out["monthly_payment"],
    # )
    # print(out)
