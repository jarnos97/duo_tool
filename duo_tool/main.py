import streamlit as st
import pandas as pd
import numpy as np


def app():
    st.title('DUO Calculator - How fucked are you?')

    start_date = st.text_input(
        "Wanneer begint je aanloopfase? Dus 1 januari na het jaar van afstuderen. "
        "Type datum als maand-jaar, bijvoorbeeld 01-2024 "
    )
    # TODO: add type check

    years = st.selectbox(
        "Select je terugbetalingsregels, in aantal jaren",
        options=[15, 35]
    )

    initial_interest = st.number_input("Wat is het huidige rente percentage? Bijvoorbeeld 2,56")
    original_st = st.number_input('Vul je originele schuldbedrag in. Bijvoorbeeld 30000')

    # IFF someone fills in the 'delay payments by n months' > just override the start date


# TODO: idee: gebruik een streamlit form om alles in 1 keer in te vullen. Dan kunnen mensen ook meerdere
# Forms invullen om situaties te vergelijken. Plot dan de situaties in elkaar.
# Zorg dat er meer vrijheid is dan bij de andere tool
# Laat mensen dus zelf een extra aflosbedrag eenmalig zowel als maandelijks invullen
# Doe uitgestelde betaling en inkomen als extra.
# VRAAG: hoe wordt maandbedrag uitgerekend? Per jaar. Simpelweg door schuld/tijd over? > 'precies binnen looptijd af te lossen'
# Voeg toe in hoeveel tijd je de studieschuld hebt afbetaald. Als button.
# Houdt rekening met inkomen als extra
# Wettelijk maandbedrag = startschuld + rentebedrag / rest tijd
# Idee: voeg een chatbot toe
# TODO: voeg optie toe om zonder aanloopfase te betalen.

# Calculate some variables
date_range = 1
months_left = 1
interest_range = 1
current_debt = 1
legal_monthly_amount = 1  # TODO: add a definition here > from Duo



if __name__ == '__main__':
    app()
