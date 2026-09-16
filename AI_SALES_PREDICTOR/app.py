import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import hashlib
from datetime import datetime

# --- DATABASE SETUP ---
DB_FILE = "canteen_pro_v2.db" # Version update for new schema

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS shops (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, shop_name TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, shop_id INTEGER, item_name TEXT)')
    # Added review_score and month to improve accuracy
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            date TEXT,
            day_of_week TEXT,
            month INTEGER,
            is_exam_day INTEGER,
            weather TEXT,
            review_score INTEGER,
            quantity_sold INTEGER
        )
    ''')
    conn.commit()
    conn.close()

create_tables()

try:
    from sklearn.ensemble import RandomForestRegressor
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

st.set_page_config(page_title="TN Smart Canteen AI", page_icon="🍱", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user_id': None, 'username': "", 'role': ""})

# --- AUTH ---
if not st.session_state['logged_in']:
    st.title("🍱 TN Smart Canteen AI System")
    auth_mode = st.tabs(["Login", "Sign Up"])
    with auth_mode[0]:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            conn = get_db_connection()
            user = conn.execute("SELECT * FROM users WHERE username = ?", (u,)).fetchone()
            if user and check_hashes(p, user['password']):
                st.session_state.update({'logged_in': True, 'user_id': user['id'], 'username': user['username'], 'role': user['role']})
                st.rerun()
            else: st.error("Invalid credentials")
    with auth_mode[1]:
        nu = st.text_input("New Username")
        np_ = st.text_input("New Password", type="password")
        nr = st.selectbox("Role", ["Shop Owner", "Admin"])
        if st.button("Register"):
            conn = get_db_connection()
            try:
                conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (nu, make_hashes(np_), nr))
                conn.commit()
                st.success("Success!")
            except: st.error("Exists!")

# --- MAIN APP ---
else:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    st.sidebar.title(f"Vanakkam, {st.session_state['username']}")
    if st.sidebar.button("Logout"):
        st.session_state.update({'logged_in': False})
        st.rerun()

    # Shop Selection
    my_shops = cursor.execute("SELECT id, shop_name FROM shops WHERE user_id = ?", (st.session_state['user_id'],)).fetchall()
    if not my_shops:
        st.warning("No shops registered.")
        with st.expander("Register Shop"):
            sn = st.text_input("Shop Name")
            if st.button("Save Shop"):
                cursor.execute("INSERT INTO shops (user_id, shop_name) VALUES (?, ?)", (st.session_state['user_id'], sn))
                conn.commit()
                st.rerun()
    else:
        shop_dict = {s['shop_name']: s['id'] for s in my_shops}
        sel_shop = st.sidebar.selectbox("Select Shop", list(shop_dict.keys()))
        sel_id = shop_dict[sel_shop]

        tabs = st.tabs(["Menu", "Daily Log", "History", "AI Forecast 🚀"])

        # TAB 1: MENU
        with tabs[0]:
            it_name = st.text_input("New Item Name")
            if st.button("Add Item"):
                cursor.execute("INSERT INTO items (shop_id, item_name) VALUES (?, ?)", (sel_id, it_name))
                conn.commit()
            items = cursor.execute("SELECT * FROM items WHERE shop_id = ?", (sel_id,)).fetchall()
            for i in items: st.text(f"• {i['item_name']}")

        # TAB 2: LOGGING
        with tabs[1]:
            with st.form("log_form"):
                d = st.date_input("Date", datetime.now())
                ex = st.checkbox("Exam Day / Special Event?")
                w = st.selectbox("Weather", ["Sunny", "Rainy", "Cloudy"])
                rev = st.slider("Customer Review Score (1-5)", 1, 5, 3)
                st.divider()
                inputs = {i['id']: st.number_input(f"Qty Sold: {i['item_name']}", min_value=0) for i in items}
                if st.form_submit_button("Save"):
                    for item_id, q in inputs.items():
                        cursor.execute("INSERT INTO sales_data (item_id, date, day_of_week, month, is_exam_day, weather, review_score, quantity_sold) VALUES (?,?,?,?,?,?,?,?)",
                                       (item_id, d.strftime('%Y-%m-%d'), d.strftime('%A'), d.month, 1 if ex else 0, w, rev, q))
                    conn.commit()
                    st.success("Logged!")

        # TAB 3: HISTORY
        with tabs[2]:
            data = cursor.execute("SELECT sd.date, it.item_name, sd.quantity_sold, sd.review_score FROM sales_data sd JOIN items it ON sd.item_id = it.id WHERE it.shop_id = ?", (sel_id,)).fetchall()
            if data: st.dataframe(pd.DataFrame(data, columns=['Date', 'Item', 'Qty', 'Review']))

        # TAB 4: AI FORECAST (HIGH ACCURACY)
        with tabs[3]:
            st.subheader("Smart AI Prediction (Tamil Nadu Context)")
            p_date = st.date_input("Forecast Date", datetime.now(), key="f_date")
            p_ex = st.selectbox("Is Exam Day?", [0, 1])
            p_w = st.selectbox("Weather Forecast", ["Sunny", "Rainy", "Cloudy"])
            # Inga review-a munnadi average review vechu predict pannuvom
            
            if st.button("Run AI Forecast"):
                day_map = {"Monday":0, "Tuesday":1, "Wednesday":2, "Thursday":3, "Friday":4, "Saturday":5, "Sunday":6}
                weather_map = {"Sunny":0, "Rainy":1, "Cloudy":2}
                
                results = []
                for it in items:
                    rows = cursor.execute("SELECT day_of_week, month, is_exam_day, weather, review_score, quantity_sold FROM sales_data WHERE item_id = ?", (it['id'],)).fetchall()
                    
                    if HAS_SKLEARN and len(rows) >= 7: # 1 week data kooda accuracy improve aagum
                        df = pd.DataFrame(rows, columns=['day', 'month', 'exam', 'weather', 'review', 'qty'])
                        df['day_n'] = df['day'].map(day_map)
                        df['weather_n'] = df['weather'].map(weather_map)
                        
                        # AI Model training with review score and month features
                        X = df[['day_n', 'month', 'exam', 'weather_n', 'review']]
                        y = df['qty']
                        
                        model = RandomForestRegressor(n_estimators=100, random_state=42).fit(X.values, y)
                        
                        # Predicting with Avg Review of that item
                        avg_rev = df['review'].mean()
                        p_input = [[p_date.weekday(), p_date.month, p_ex, weather_map[p_w], avg_rev]]
                        prediction = model.predict(p_input)[0]
                        
                        results.append({"Item": it['item_name'], "AI Prediction": int(round(prediction)), "Method": "RandomForest (High Accuracy)"})
                    else:
                        # Simple calculation for new shops
                        avg = [r['quantity_sold'] for r in rows]
                        pred = (sum(avg)/len(avg)) if avg else 0
                        if p_ex: pred *= 1.3 # TN colleges-la exam appo canteen rush 30% koodum
                        results.append({"Item": it['item_name'], "AI Prediction": int(round(pred)), "Method": "Basic Avg (Need more data)"})
                
                st.table(pd.DataFrame(results))
                st.info("💡 Accuracy improves as you log more daily reviews and sales.")

    conn.close()