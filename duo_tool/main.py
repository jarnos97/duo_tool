import streamlit as st

from calculations import get_inputs
from loguru import logger


def advanced_options():
    with st.expander("Klik hier voor de uitgebreide opties", expanded=False):
        st.write(
            """
            Met deze uitgebreidere opties heb je meer vrijheid om dingen aan te passen.
            Je kan bijvoorbeeld ervoor kiezen om al eerder of juist later te beginnen met afbetalen, een
            maandelijkse of eenmalige extra betaling te doen, of te experimenteren met verschillende rentes
            door de tijd.
            """
        )

        st.write('**5. Later/eerder aflossen**')
        start_paying_date = st.text_input(
            'Standaard begin je twee jaar na begin van de aanloopfase met aflossen. Echter, kan je ook al eerder of '
            'juist later beginnen met aflossen. Uitstellen kan maximaal 5 jaar. \n\n'
            'Vul niks in als je niet eerder of later wilt gaan aflossen. Vul anders wederom een maand en jaar in.',
            value=None
        )

        st.write('**6. Veranderende rente**')
        st.write('under development')

        st.write('**7. Eenmalige extra aflossing**')
        st.write('under development')

        st.write('**8. Maandelijks extra aflossen**')
        st.write('under development')

        st.write('**9. Inkomen meenemen**')
        st.write('under development')
    return start_paying_date


def app():
    st.set_page_config(layout="wide")
    st.title('DUO Studielening Tool')

    st.write('introductie ... ')

    # with st.expander('Klik hier om de basis tool te verbergen',expanded=True):
    with st.form("basic form"):
        st.write(
            """
            Vul hieronder je gegevens in en druk op 'klik om te berekenen' om de uitslag te zien.
            """
        )
        st.write("**1. Aanloopfase**")
        start_date = st.text_input(
            "Wanneer begint je aanloopfase? Dit is meestal januari na het jaar van afstuderen. "
            "Type datum als maand-jaar, bijvoorbeeld 01-2024 ",
            value='01-2024'
        )
        logger.info(f'{start_date}')

        st.write("**2. Terugbetalingsregeling**")
        years = st.selectbox(
            "Selecteer je terugbetalingsregeling, in aantal jaren",
            options=[15, 35],
            index=1,
            help="Verander deze waarde omhoog of omlaag om het effect van de afbetalingstermijn te zien."
        )

        st.write("**3. Rente**")
        initial_interest = st.number_input(
            "Wat is het huidige rente percentage? Bijvoorbeeld 2,56",
            help="Verander deze waarde omhoog of omlaag om het effect op je betaalde rente te zien."
        )

        st.write("**4. Schuld**")
        original_debt = st.number_input('Vul je originele schuldbedrag in hele euros in. Bijvoorbeeld 30000', step=5000)

        # we add the advanced options here
        custom_payment_date = advanced_options()

        submitted = st.form_submit_button('Klik om te berekenen..')
        if submitted:
            inputs = get_inputs(years, start_date, original_debt, initial_interest, custom_payment_date)

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric(
                    label='**Geschat maandbedrag:**',
                    value=f"€ {inputs['monthly_payment']:,.2f}",
                    help='Dit is het bedrag dat je elke maand aan DUO betaald.'
                )

            with c2:
                st.metric(
                    label='**Betaalde rente:**',
                    value=f"€ {inputs['total_interest_paid']:,.2f}",
                    help='Dit is de totale rente die je over je lening betaald. Berekent als het totaal betaalde '
                         'bedrag min het originele schuldbedrag.'
                )

            with c3:
                st.metric(
                    label='**Schuld afgelost op:**',
                    value=inputs['debt_over_time']['month'].iloc[-1].strftime('%m-%Y')
                )

            st.write('**Schuld door de tijd:**')
            st.line_chart(
                inputs['debt_over_time'].rename(columns={'debt': 'schuld', 'month': 'jaar'}),
                x='jaar', y='schuld', width=800, use_container_width=False
            )


# Desired features:
# [check] Determine monthly payment
# [check] Calculate total paid interest
# [check] Compare 15yrs and 35yrs
# [check] Compare different debt amounts
# [check] start paying directly after study (no aanloopfase)
# [check] postpone paying
# - Fill in different interest rates over time
# - one time payment
# - Extra monthly payment (difficult: compare with other tool to check calculations. Takes a whole other approach.)
# - Account for income > must calculate the draagkracht
# - Add a chatbot for questions > would be very interesting for myself.


# Calculate some variables
date_range = 1
months_left = 1
interest_range = 1
current_debt = 1
legal_monthly_amount = 1  # TODO: add a definition here > from Duo

if __name__ == '__main__':
    app()
