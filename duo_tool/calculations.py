"""
This module contains the code for all basic calculations related to the loan.

Sources:
- https://duo.nl/particulier/studieschuld-terugbetalen/berekening-maandbedrag.jsp
- https://duo.nl/particulier/rekenhulp-studiefinanciering.jsp#/nl/terugbetalen/resultaat
- https://www.berekenhet.nl/lenen-en-krediet/studiefinanciering-terugbetalen.html
- https://www.geld.nl/lenen/service/aflossing-lening-berekenen
- https://www.calculator.net/loan-calculator.html
"""
import abc

import pandas as pd
from loguru import logger
from pandas import Timestamp


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
        self.payment = self._monthly_payment(self.debt, self.interest_rate, self.months)
        logger.info(f"Monthly payment will be: {self.payment}")

        # Get the payment phase information
        payment_phase_df = self._calculate_amortization()

        return payment_phase_df
