import streamlit as st
from services.foods import list_foods
from services.logs import add_log
from datetime import date


def render_log_food():
    st.header("Log Food")

    # ------------------ Date ------------------
    selected_date = st.date_input(
        "Select date",
        value=date.today()
    )

    # ------------------ Foods ------------------
    foods = list_foods()
    if not foods:
        st.warning("No foods found. Seed foods first.")
        return

    food_map = {food["name"]: food for food in foods}

    selected_food_name = st.selectbox(
        "Select food",
        options=list(food_map.keys())
    )
    food = food_map[selected_food_name]

    # ------------------ Mode ------------------
    input_mode = st.radio(
        "Log food by",
        ["Grams", "Units"],
        horizontal=True
    )

    grams = 0

    # ------------------ Units ------------------
    if input_mode == "Units":
        if food.get("grams_per_unit") is None:
            st.warning("This food cannot be logged by units. Use grams.")
        else:
            units_str = st.text_input(
                f"Quantity (1 unit = {food['grams_per_unit']} g)",
                placeholder="Enter units (e.g. 1, 0.5)"
            )

            if units_str.strip():
                try:
                    units = float(units_str)
                    if units > 0:
                        grams = units * food["grams_per_unit"]
                except ValueError:
                    st.error("Enter a valid number")

    # ------------------ Grams ------------------
    else:
        grams_str = st.text_input(
            "Weight (grams)",
            placeholder="Enter grams (e.g. 60)"
        )

        if grams_str.strip():
            try:
                grams = int(float(grams_str))
            except ValueError:
                st.error("Enter a valid number")

    # ------------------ Submit ------------------
    if st.button("Add Food"):
        if grams <= 0:
            st.error("Amount must be greater than 0")
            return

        try:
            add_log(
                date=selected_date,
                food=food,
                grams=int(grams)
            )
            st.success("Food logged successfully")
        except Exception as e:
            st.error(str(e))
