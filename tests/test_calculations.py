# import pandas as pd
#
# from duo_tool.calculations import PaymentPhase
# from duo_tool.inputs import get_inputs

#
#
# def test_monthly_interest_rate():
#     assert round(monthly_interest_rate(0.05), 5) == 0.00407
#
#
# class TestMonthlyCompound:
#     def test_no_months(self):
#         assert round(monthly_compound(5000, 0, 0.05), 2) == 5000.00
#
#     def test_one_month(self):
#         assert round(monthly_compound(5000, 1, 0.05), 2) == 5020.83
#
#
# class TestMonthlyPayment:
#     """
#     All of these calculations are checked using DUO's own calculator tool.
#     Link: https://duo.nl/particulier/rekenhulp-studiefinanciering.jsp#/nl/terugbetalen/start
#     We round the number to whole euro's to allow for a few cents' deviation.
#     """
# def __init__(self):
#     self.
#     )

# def test_15_years(self):
#     payment_phase = PaymentPhase(
#             start_date=pd.to_datetime('01-2024'),
#             interest_rate=0.0256,
#             debt=10_00,
#             months=420
#     )
#     assert (
#         round(payment_phase._monthly_payment(10_000, 0.0295, 24), 0)
#         == 73
#     )

#     def test_35_years(self):
#         assert (
#             round(
#                 get_inputs(35, pd.to_datetime("01-2024"), 10_000, 2.56, 24)["monthly_payment"],
#                 0,
#             )
#             == 38
#         )
# # TODO: update tests with new set-up!
