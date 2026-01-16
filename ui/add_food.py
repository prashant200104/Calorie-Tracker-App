import streamlit as st
from services.foods import add_food

def render_add_food():
    st.header("Add Food (One-time)")

    name = st.text_input("Food name")

    calories = st.number_input("Calories per 100g", min_value=0.0)
    protein = st.number_input("Protein per 100g (g)", min_value=0.0)
    fiber = st.number_input("Fiber per 100g (g)", min_value=0.0)
    carbs = st.number_input("Carbohydrates per 100g (g)", min_value=0.0)
    fat = st.number_input("Fat per 100g (g)", min_value=0.0)
    bad_fat = st.number_input("Bad fat per 100g (g)", min_value=0.0)
    sugar = st.number_input("Sugar per 100g (g)", min_value=0.0)

    if st.button("Add food"):
        if not name:
            st.error("Food name is required")
            return

        food = {
            "name": name.strip().lower(),
            "calories_per_100g": calories,
            "protein_per_100g": protein,
            "fiber_per_100g": fiber,
            "carbohydrates_per_100g": carbs,
            "fat_per_100g": fat,
            "bad_fat_per_100g": bad_fat,
            "sugar_per_100g": sugar,
        }

        add_food(food)
        st.success("Food added")
