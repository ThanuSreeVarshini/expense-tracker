import streamlit as st
import pandas as pd
import re
from datetime import datetime
import dateparser
import matplotlib.pyplot as plt

# ---------------- LOGIN SYSTEM ----------------
def login(username, password):
    return username == "admin" and password == "1234"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login Page")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login(username, password):
            st.session_state.logged_in = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

# ---------------- NLP PARSER ----------------
def parse_expense(text):
    amount = re.findall(r'\d+', text)
    amount = int(amount[0]) if amount else 0

    parsed_date = dateparser.parse(text)
    if not parsed_date:
        parsed_date = datetime.now()

    text = text.lower()

    categories = {
        "food": ["food", "pizza", "burger", "restaurant"],
        "travel": ["uber", "bus", "fuel", "petrol"],
        "shopping": ["amazon", "clothes"],
        "entertainment": ["movie", "netflix"]
    }

    category_found = "others"

    for category, keywords in categories.items():
        if any(word in text for word in keywords):
            category_found = category

    return amount, category_found, parsed_date

# ---------------- SAVE EXPENSE ----------------
def save_expense(amount, category, date):
    data = {
        "Amount": amount,
        "Category": category,
        "Date": date
    }

    df = pd.DataFrame([data])

    try:
        old_df = pd.read_csv("expenses.csv")
        df = pd.concat([old_df, df])
    except:
        pass

    df.to_csv("expenses.csv", index=False)

# ---------------- BUDGET FUNCTIONS ----------------
def save_budget(budget):
    df = pd.DataFrame({"Budget": [budget]})
    df.to_csv("budget.csv", index=False)

def load_budget():
    try:
        df = pd.read_csv("budget.csv")
        return df["Budget"][0]
    except:
        return 0

# ---------------- AI ANALYSIS ----------------
def analyze_expenses(df, budget):
    total = df["Amount"].sum()
    category_spending = df.groupby("Category")["Amount"].sum()

    insights = []

    # Budget analysis
    if budget > 0:
        if total > budget:
            insights.append("🚨 Budget exceeded!")
        elif total > 0.8 * budget:
            insights.append("⚠️ You are close to your budget limit")

    # Category analysis
    for category, amount in category_spending.items():
        percent = (amount / total) * 100 if total > 0 else 0

        if percent > 40:
            insights.append(f"⚠️ {category.capitalize()} takes {percent:.1f}% of your spending")

    return total, category_spending, insights

# ---------------- STREAMLIT UI ----------------
st.set_page_config(page_title="AI Expense Tracker", layout="wide")
st.title("💰 AI Smart Expense Tracker")

# -------- SIDEBAR --------
st.sidebar.header("💰 Budget Settings")

budget_input = st.sidebar.number_input("Set Monthly Budget", min_value=0)

if st.sidebar.button("Save Budget"):
    save_budget(budget_input)
    st.sidebar.success("Budget Saved!")

budget = load_budget()
st.sidebar.write(f"Current Budget: ₹{budget}")

if st.sidebar.button("🗑 Clear All Data"):
    pd.DataFrame(columns=["Amount", "Category", "Date"]).to_csv("expenses.csv", index=False)
    st.sidebar.success("Data cleared!")

if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# -------- CHAT INPUT --------
st.subheader("💬 AI Expense Assistant")

user_input = st.chat_input("Enter your expense (e.g., spent 200 on food)")

if user_input:
    amount, category, parsed_date = parse_expense(user_input)
    save_expense(amount, category, parsed_date)

    st.chat_message("user").write(user_input)
    st.chat_message("assistant").write(f"Added ₹{amount} under {category}")

st.divider()

# -------- DISPLAY DATA --------
try:
    df = pd.read_csv("expenses.csv")

    if not df.empty:
        st.subheader("📋 Expense History")
        st.dataframe(df, use_container_width=True)

        total, category_spending, insights = analyze_expenses(df, budget)

        # 🔮 Prediction
        today = datetime.now()
        days_passed = today.day
        total_days = 30

        predicted = (total / days_passed) * total_days if days_passed > 0 else total

        st.subheader("🔮 Monthly Prediction")
        st.info(f"At this rate, you may spend ₹{int(predicted)} this month")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("💵 Total Spending")
            st.metric(label="Total", value=f"₹{total}")

        with col2:
            st.subheader("📊 Category Spending")
            st.bar_chart(category_spending)

        # 📈 Trend
        st.subheader("📈 Spending Over Time")
        df["Date"] = pd.to_datetime(df["Date"])
        daily_spending = df.groupby(df["Date"].dt.date)["Amount"].sum()
        st.line_chart(daily_spending)

        # 🥧 Pie chart
        st.subheader("🥧 Category Distribution")
        fig, ax = plt.subplots()
        ax.pie(category_spending, labels=category_spending.index, autopct='%1.1f%%')
        st.pyplot(fig)

        # 🤖 Insights
        st.subheader("🤖 AI Insights")
        if insights:
            for insight in insights:
                st.warning(insight)
        else:
            st.success("All spending is under control 👍")

    else:
        st.info("No expenses recorded yet.")

except:
    st.info("Start by adding your first expense 🚀")

# -------- FILTER --------
st.subheader("📅 Filter Expenses")

try:
    df = pd.read_csv("expenses.csv")
    df["Date"] = pd.to_datetime(df["Date"])

    selected_date = st.date_input("Select Date")
    filtered_df = df[df["Date"].dt.date == selected_date]

    st.dataframe(filtered_df)

except:
    st.info("No data available")

# -------- DOWNLOAD --------
csv = df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="📥 Download Expense Report",
    data=csv,
    file_name='expenses_report.csv',
    mime='text/csv'
)

# -------- RESET --------
if st.sidebar.button("♻️ Reset All Data"):
    pd.DataFrame(columns=["Amount", "Category", "Date"]).to_csv("expenses.csv", index=False)
    pd.DataFrame({"Budget": [0]}).to_csv("budget.csv", index=False)
    st.sidebar.success("All data & budget reset!")