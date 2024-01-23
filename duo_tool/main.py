from typing import Tuple

import pandas as pd
import streamlit as st
from loguru import logger
from utils import check_amount_format, check_date_format

from duo_tool.inputs import get_inputs, one_time_payment


def option_custom_payment_date() -> pd.Timestamp:
    with st.expander("Later of eerder aflossen", expanded=False):
        st.write("**5. Later/eerder aflossen**")
        start_paying_date = st.text_input(
            "Standaard begin je twee jaar na begin van de aanloopfase met aflossen. Echter, kan je ook al eerder of "
            "juist later beginnen met aflossen. Uitstellen kan maximaal 5 jaar. \n\n"
            "Vul niks in als je niet eerder of later wilt gaan aflossen. Vul anders wederom een maand en jaar in.",
            value=None,
        )
        if start_paying_date:  # Check format if date is specified
            start_paying_date = check_date_format(start_paying_date)

    return start_paying_date


def option_one_time_payment(start_date: pd.Timestamp, original_debt: int) -> Tuple[pd.Timestamp, int]:
    with st.expander("Eenmalige extra aflossing", expanded=False):
        st.write("**6. Eenmalige extra aflossing**")
        st.write(
            """
            Je kan een eenmalige extra aflossing doen om versneld af te lossen. Dit betekent dat je uiteindelijk
            minder rente betaald en je maandelijkse aflossingsbedrag omlaag gaat. Dit kan ook helpen met het verkrijgen
            van een hypotheek.

            Vul hieronder het bedrag in dat je extra wilt aflossen en de datum (maand-jaar) waarop je dat wil doen.
            De maand nadat je een extra aflossing hebt gedaan wordt je maandbedrag opnieuw uitgerekend. Dit is niet per
            se wat er in werkelijkheid gebeurd.

            **let op:** Het nieuwe maandbedrag dat je ziet is het gemiddelde van het originele
            maandbedrag en het nieuwe lagere bedrag.
            """
        )
        # Get and check payment date
        payment_date = st.text_input("Wanneer wil je een extra betaling doen? Vul maand-jaar in: 01-2026", value=None)
        if payment_date:
            payment_date = check_date_format(payment_date)
            if payment_date < start_date:
                st.error(f"De extra betaling moet op of na de start datum van de aanloopfase gaan ({start_date})")
                raise ValueError("Wrong payment date")
            # TODO: ideally, we should also check this date to be before the end of the payment term!

        # Get and check payment amount
        payment_amount = st.number_input(
            "Wat is het bedrag dat je extra wil aflossen, in hele euro's. Bijv. €5.000", value=None, step=1000
        )
        if payment_amount:
            check_amount_format(payment_amount, upper_limit=original_debt)

    return payment_date, payment_amount


def advanced_options():
    with st.expander("Klik hier voor de uitgebreide opties", expanded=False):
        st.write("**6. Veranderende rente**")
        st.write("under development")

        st.write("**8. Maandelijks extra aflossen**")
        st.write("under development")

        st.write("**9. Inkomen meenemen**")
        st.write("under development")


def app() -> None:
    st.set_page_config(layout="wide")
    st.title("DUO Studielening Calculator")

    st.write(
        """
    Introductie ...

    Disclaimer: deze tool geeft alleen schattingen en verleent geen financieel advies.
    Er kunnen geen rechten ontleend worden aan de gepresenteerde informatie.
    Let op: Er is geen inflatie meegenomen in de berekeningen.
    """
    )

    # with st.expander('Klik hier om de basis tool te verbergen',expanded=True):
    with st.form("basic form"):
        st.write(
            """
            Vul hieronder je gegevens in en druk op 'klik om te berekenen' om de uitslag te zien.
            """
        )

        # Aanloopfase
        st.write("**1. Aanloopfase**")
        start_date = st.text_input(
            "Wanneer begint je aanloopfase? Dit is meestal januari na het jaar van afstuderen. "
            "Type datum als maand-jaar, bijvoorbeeld 01-2024 ",
            value="01-2024",
        )
        logger.info(f"{start_date}")
        start_date = check_date_format(start_date)

        # Terugbetalingsregels
        st.write("**2. Terugbetalingsregeling**")
        years = st.selectbox(
            "Selecteer je terugbetalingsregeling, in aantal jaren",
            options=[15, 35],
            index=1,
            help="Verander deze waarde omhoog of omlaag om het effect van de afbetalingstermijn te zien.",
        )

        # Rente
        st.write("**3. Rente**")
        initial_interest = st.number_input(
            "Wat is het huidige rente percentage? Bijvoorbeeld 2,56",
            help="Verander deze waarde omhoog of omlaag om het effect op je betaalde rente te zien.",
        )
        if initial_interest < 0:
            st.error("De rente kan niet negatief zijn.")
            raise ValueError("Negative interest")

        # Schuld
        st.write("**4. Schuld**")
        original_debt = st.number_input(
            "Vul je originele schuldbedrag in hele euros in. Bijvoorbeeld €80.000", value=10_000, step=5000
        )
        if original_debt <= 0:
            st.error("De schuld moet groter dan 0 zijn.")
            raise ValueError("Debt too low")

        # Add advanced options here
        st.write(
            """
            Met de optionele uitgebreide opties beneden heb je meer vrijheid om dingen aan te passen.
            Je kan bijvoorbeeld ervoor kiezen om al eerder of juist later te beginnen met afbetalen, een
            maandelijkse of eenmalige extra betaling te doen, of te experimenteren met veranderende rentes
            door de tijd.
            """
        )
        custom_payment_date = option_custom_payment_date()

        # Check the custom_payment_date value to determine offset
        payment_offset = 24  # This is the standard 2 years from the aanloopfase
        if custom_payment_date:
            delta = custom_payment_date.to_period("M") - start_date.to_period("M")

            # Check the value for correctness
            if delta.n <= 0 or delta.n > 84:
                st.error(
                    """
                    De datum moet minstens 1 maand na het begin van de afloopfase zijn, en niet later dan 60 maanden na
                    het einde van de afloopfase.
                    """
                )
                raise ValueError("Wrong customer date")

            else:  # override the payment offset
                payment_offset = delta.n
        logger.info(f"Payment offset = {payment_offset} months.")

        # One time payment
        one_time_payment_date, one_time_payment_amount = option_one_time_payment(start_date, original_debt)

        # Upon submit
        submitted = st.form_submit_button("Klik om te berekenen..")
        if submitted:
            inputs = get_inputs(years, start_date, original_debt, initial_interest, payment_offset)

            # IF there is a one time payment we have to split up and override the inputs
            if one_time_payment_date and one_time_payment_amount:
                logger.info("One time payment > recalculating inputs")
                inputs = one_time_payment(
                    inputs=inputs,
                    payment_amount=one_time_payment_amount,
                    payment_date=one_time_payment_date,
                    interest_perc=initial_interest,
                    years=years,
                    start_date=start_date,
                    original_debt=original_debt,
                    payment_offset=payment_offset,
                    current_monthly_payment=inputs["monthly_payment"],
                )

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric(
                    label="**Geschat maandbedrag:**",
                    value=f"€ {inputs['monthly_payment']:,.2f}",
                    help="Dit is het bedrag dat je elke maand aan DUO betaald.",
                )

            with c2:
                st.metric(
                    label="**Betaalde rente:**",
                    value=f"€ {inputs['total_interest_paid']:,.2f}",
                    help="Dit is de totale rente die je over je lening betaald. Berekent als het totaal betaalde "
                    "bedrag min het originele schuldbedrag. Kleine verschillen met de werkelijkheid kunnen "
                    "ontstaan door het afronden van getallen.",
                )

            with c3:
                st.metric(
                    label="**Schuld afgelost op:**", value=inputs["debt_over_time"]["month"].iloc[-1].strftime("%m-%Y")
                )

            st.write("**Schuld door de tijd:**")
            st.line_chart(
                inputs["debt_over_time"].rename(columns={"debt": "Schuld", "month": "Jaar"}), x="Jaar", y="Schuld"
            )

    # Add call for contributions
    github_url = "https://github.com/jarnos97/duo_tool"
    st.write("#")
    st.write("Bijdragen aan dit project? Zie [Github](%s)" % github_url)


# Desired features:
# [check] Determine monthly payment
# [check] Calculate total paid interest
# [check] Compare 15yrs and 35yrs
# [check] Compare different debt amounts
# [check] start paying directly after study (no aanloopfase)
# [check] postpone paying
# [check] one time payment
# - Fill in different interest rates over time
# - Extra monthly payment (difficult: compare with other tool to check calculations. Takes a whole other approach.)
# - Account for income > must calculate the draagkracht
# - Add a chatbot for questions > would be very interesting for myself.


if __name__ == "__main__":
    app()
