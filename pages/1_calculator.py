import streamlit as st

st.set_page_config(page_title="💰 Tip Calculator", layout="centered")

st.title("💰 Tip Calculator")

# Input section
st.header("กรอกข้อมูล")
bill_amount = st.number_input("ยอดบิลทั้งหมด (บาท)", min_value=0.0, step=10.0, value=100.0)
tip_percent = st.slider("เปอร์เซ็นต์ทิป (%)", 0, 30, 10, step=1)
num_people = st.number_input("จำนวนคนหาร", min_value=1, step=1, value=1)

# Calculation
tip_amount = bill_amount * (tip_percent / 100)
total_amount = bill_amount + tip_amount
amount_per_person = total_amount / num_people if num_people > 0 else total_amount

# Output
st.header("ผลลัพธ์")
st.metric("💸 ทิปทั้งหมด", f"{tip_amount:,.2f} บาท")
st.metric("💳 ยอดรวม", f"{total_amount:,.2f} บาท")
st.metric("👥 ต่อคน", f"{amount_per_person:,.2f} บาท")
