import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import hashlib
from datetime import datetime

# --- DATABASE SETUP ---
DB_FILE = "canteen_pro_v2.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'CREATE TABLE IF NOT EXISTS users '
        '(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT)'
    )

    cursor.execute(
        'CREATE TABLE IF NOT EXISTS shops '
        '(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, shop_name TEXT)'
    )

    cursor.execute(
        'CREATE TABLE IF NOT EXISTS items '
        '(id INTEGER PRIMARY KEY AUTOINCREMENT, shop_id INTEGER, item_name TEXT)'
    )

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


# --- MACHINE LEARNING ---
try:
    from sklearn.ensemble import RandomForestRegressor
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


# --- PASSWORD HASHING ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()


def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text


# --- PAGE CONFIG ---
st.set_page_config(
    page_title="TN Smart Canteen AI",
    page_icon="🍱",
    layout="wide"
)


# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False,
        'user_id': None,
        'username': "",
        'role': ""
    })


# =========================================================
# AUTHENTICATION
# =========================================================

if not st.session_state['logged_in']:

    st.title("🍱 TN Smart Canteen AI System")

    auth_mode = st.tabs(["Login", "Sign Up"])

    # --- LOGIN ---
    with auth_mode[0]:

        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):

            conn = get_db_connection()

            user = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (u,)
            ).fetchone()

            conn.close()

            if user and check_hashes(p, user['password']):

                st.session_state.update({
                    'logged_in': True,
                    'user_id': user['id'],
                    'username': user['username'],
                    'role': user['role']
                })

                st.rerun()

            else:
                st.error("Invalid credentials")


    # --- SIGN UP ---
    with auth_mode[1]:

        nu = st.text_input("New Username")
        np_ = st.text_input("New Password", type="password")
        nr = st.selectbox("Role", ["Shop Owner", "Admin"])

        if st.button("Register"):

            conn = get_db_connection()

            try:

                conn.execute(
                    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    (nu, make_hashes(np_), nr)
                )

                conn.commit()

                st.success("Success!")

            except sqlite3.IntegrityError:

                st.error("Username already exists!")

            finally:

                conn.close()


# =========================================================
# MAIN APPLICATION
# =========================================================

else:

    conn = get_db_connection()
    cursor = conn.cursor()

    # --- SIDEBAR ---
    st.sidebar.title(
        f"Vanakkam, {st.session_state['username']}"
    )

    if st.sidebar.button("Logout"):

        st.session_state.update({
            'logged_in': False,
            'user_id': None,
            'username': "",
            'role': ""
        })

        st.rerun()


    # =====================================================
    # SHOP SELECTION
    # =====================================================

    my_shops = cursor.execute(
        "SELECT id, shop_name FROM shops WHERE user_id = ?",
        (st.session_state['user_id'],)
    ).fetchall()


    if not my_shops:

        st.warning("No shops registered.")

        with st.expander("Register Shop"):

            sn = st.text_input("Shop Name")

            if st.button("Save Shop"):

                if sn.strip():

                    cursor.execute(
                        "INSERT INTO shops (user_id, shop_name) VALUES (?, ?)",
                        (st.session_state['user_id'], sn.strip())
                    )

                    conn.commit()

                    st.success(
                        "Shop registered successfully!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Please enter a shop name."
                    )


    else:

        shop_dict = {
            s['shop_name']: s['id']
            for s in my_shops
        }

        sel_shop = st.sidebar.selectbox(
            "Select Shop",
            list(shop_dict.keys())
        )

        sel_id = shop_dict[sel_shop]


        # Get items for selected shop
        items = cursor.execute(
            "SELECT * FROM items WHERE shop_id = ?",
            (sel_id,)
        ).fetchall()


        tabs = st.tabs([
            "Menu",
            "Daily Log",
            "History",
            "AI Forecast 🚀"
        ])


        # =================================================
        # TAB 1: MENU
        # =================================================

        with tabs[0]:

            st.subheader("🍽️ Menu Management")

            it_name = st.text_input(
                "New Item Name"
            )

            if st.button("Add Item"):

                if it_name.strip():

                    cursor.execute(
                        "INSERT INTO items (shop_id, item_name) VALUES (?, ?)",
                        (sel_id, it_name.strip())
                    )

                    conn.commit()

                    st.success(
                        f"{it_name.strip()} added successfully!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Please enter an item name."
                    )


            items = cursor.execute(
                "SELECT * FROM items WHERE shop_id = ?",
                (sel_id,)
            ).fetchall()


            if items:

                st.subheader("Current Menu")

                for i in items:
                    st.text(
                        f"• {i['item_name']}"
                    )

            else:

                st.info(
                    "No menu items added yet."
                )


        # =================================================
        # TAB 2: DAILY LOG
        # =================================================

        with tabs[1]:

            st.subheader("📅 Daily Sales Log")

            if not items:

                st.warning(
                    "Please add at least one menu item before logging sales."
                )

            else:

                with st.form("log_form"):

                    d = st.date_input(
                        "Date",
                        datetime.now()
                    )

                    ex = st.checkbox(
                        "Exam Day / Special Event?"
                    )

                    w = st.selectbox(
                        "Weather",
                        ["Sunny", "Rainy", "Cloudy"]
                    )

                    rev = st.slider(
                        "Customer Review Score (1-5)",
                        1,
                        5,
                        3
                    )

                    st.divider()


                    inputs = {
                        i['id']: st.number_input(
                            f"Qty Sold: {i['item_name']}",
                            min_value=0,
                            step=1
                        )
                        for i in items
                    }


                    if st.form_submit_button("Save"):

                        for item_id, q in inputs.items():

                            cursor.execute(
                                """
                                INSERT INTO sales_data
                                (
                                    item_id,
                                    date,
                                    day_of_week,
                                    month,
                                    is_exam_day,
                                    weather,
                                    review_score,
                                    quantity_sold
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    item_id,
                                    d.strftime('%Y-%m-%d'),
                                    d.strftime('%A'),
                                    d.month,
                                    1 if ex else 0,
                                    w,
                                    rev,
                                    int(q)
                                )
                            )

                        conn.commit()

                        st.success(
                            "Daily sales logged successfully! ✅"
                        )


        # =================================================
        # TAB 3: HISTORY
        # =================================================

        with tabs[2]:

            st.subheader("📊 Sales History")


            data = cursor.execute(
                """
                SELECT
                    sd.id,
                    sd.date,
                    it.item_name,
                    sd.quantity_sold,
                    sd.review_score
                FROM sales_data sd
                JOIN items it
                    ON sd.item_id = it.id
                WHERE it.shop_id = ?
                ORDER BY sd.date DESC, sd.id DESC
                """,
                (sel_id,)
            ).fetchall()


            if data:

                df = pd.DataFrame(
                    data,
                    columns=[
                        'ID',
                        'Date',
                        'Item',
                        'Qty',
                        'Review'
                    ]
                )


                # =================================================
                # SEARCH AND FILTER
                # =================================================

                st.subheader("🔎 Search and Filter")


                col_search, col_date = st.columns(2)


                # --- SEARCH BY ITEM ---
                with col_search:

                    search_item = st.text_input(
                        "Search Item Name",
                        placeholder="Example: briyani"
                    )


                # --- FILTER BY DATE ---
                with col_date:

                    unique_dates = sorted(
                        df["Date"].unique(),
                        reverse=True
                    )

                    date_options = [
                        "All Dates"
                    ] + unique_dates

                    filter_date = st.selectbox(
                        "Filter by Date",
                        date_options
                    )


                # Copy original dataframe
                filtered_df = df.copy()


                # Search item name
                if search_item.strip():

                    filtered_df = filtered_df[
                        filtered_df["Item"].str.contains(
                            search_item.strip(),
                            case=False,
                            na=False
                        )
                    ]


                # Filter date
                if filter_date != "All Dates":

                    filtered_df = filtered_df[
                        filtered_df["Date"] == filter_date
                    ]


                st.caption(
                    f"Showing {len(filtered_df)} record(s)"
                )


                # Display filtered data
                st.dataframe(
                    filtered_df[
                        ['Date', 'Item', 'Qty', 'Review']
                    ],
                    use_container_width=True
                )


                st.divider()


                # =================================================
                # RECORD OPTIONS
                # =================================================

                record_options = {
                    f"#{row['id']} | {row['date']} - {row['item_name']}":
                    row['id']
                    for row in data
                }


                col1, col2 = st.columns(2)


                # =================================================
                # UPDATE
                # =================================================

                with col1:

                    st.subheader(
                        "✏️ Update Sales Record"
                    )


                    selected_record = st.selectbox(
                        "Select Record to Update",
                        list(record_options.keys()),
                        key="update_record_select"
                    )


                    selected_id = record_options[
                        selected_record
                    ]


                    selected_data = cursor.execute(
                        """
                        SELECT
                            quantity_sold,
                            review_score
                        FROM sales_data
                        WHERE id = ?
                        """,
                        (selected_id,)
                    ).fetchone()


                    new_qty = st.number_input(
                        "New Quantity Sold",
                        min_value=0,
                        value=int(
                            selected_data['quantity_sold']
                        ),
                        step=1,
                        key="update_qty_input"
                    )


                    new_review = st.slider(
                        "New Review Score",
                        1,
                        5,
                        int(
                            selected_data['review_score']
                        ),
                        key="update_review_slider"
                    )


                    if st.button(
                        "Update Record",
                        key="update_record_button"
                    ):

                        cursor.execute(
                            """
                            UPDATE sales_data
                            SET
                                quantity_sold = ?,
                                review_score = ?
                            WHERE id = ?
                            """,
                            (
                                int(new_qty),
                                int(new_review),
                                selected_id
                            )
                        )


                        conn.commit()


                        st.success(
                            "Sales record updated successfully! ✅"
                        )


                        st.rerun()


                # =================================================
                # DELETE
                # =================================================

                with col2:

                    st.subheader(
                        "🗑️ Delete Sales Record"
                    )


                    delete_record = st.selectbox(
                        "Select Record to Delete",
                        list(record_options.keys()),
                        key="delete_record_select"
                    )


                    delete_id = record_options[
                        delete_record
                    ]


                    if st.button(
                        "Delete Record",
                        key="delete_record_button"
                    ):

                        cursor.execute(
                            "DELETE FROM sales_data WHERE id = ?",
                            (delete_id,)
                        )


                        conn.commit()


                        st.success(
                            "Sales record deleted successfully! 🗑️"
                        )


                        st.rerun()


            else:

                st.info(
                    "No sales records available."
                )


        # =================================================
        # TAB 4: AI FORECAST
        # =================================================

        with tabs[3]:

            st.subheader(
                "🤖 Smart AI Prediction (Tamil Nadu Context)"
            )


            if not items:

                st.warning(
                    "Please add menu items before running a forecast."
                )

            else:

                p_date = st.date_input(
                    "Forecast Date",
                    datetime.now(),
                    key="f_date"
                )


                p_ex = st.selectbox(
                    "Is Exam Day?",
                    [0, 1]
                )


                p_w = st.selectbox(
                    "Weather Forecast",
                    ["Sunny", "Rainy", "Cloudy"]
                )


                if st.button(
                    "Run AI Forecast",
                    key="run_forecast"
                ):

                    day_map = {
                        "Monday": 0,
                        "Tuesday": 1,
                        "Wednesday": 2,
                        "Thursday": 3,
                        "Friday": 4,
                        "Saturday": 5,
                        "Sunday": 6
                    }


                    weather_map = {
                        "Sunny": 0,
                        "Rainy": 1,
                        "Cloudy": 2
                    }


                    results = []


                    for it in items:

                        rows = cursor.execute(
                            """
                            SELECT
                                day_of_week,
                                month,
                                is_exam_day,
                                weather,
                                review_score,
                                quantity_sold
                            FROM sales_data
                            WHERE item_id = ?
                            """,
                            (it['id'],)
                        ).fetchall()


                        # =================================================
                        # RANDOM FOREST
                        # =================================================

                        if HAS_SKLEARN and len(rows) >= 7:

                            train_df = pd.DataFrame(
                                rows,
                                columns=[
                                    'day',
                                    'month',
                                    'exam',
                                    'weather',
                                    'review',
                                    'qty'
                                ]
                            )


                            train_df['day_n'] = (
                                train_df['day'].map(day_map)
                            )


                            train_df['weather_n'] = (
                                train_df['weather'].map(weather_map)
                            )


                            X = train_df[
                                [
                                    'day_n',
                                    'month',
                                    'exam',
                                    'weather_n',
                                    'review'
                                ]
                            ]


                            y = train_df['qty']


                            model = RandomForestRegressor(
                                n_estimators=100,
                                random_state=42
                            ).fit(
                                X.values,
                                y
                            )


                            avg_rev = train_df[
                                'review'
                            ].mean()


                            p_input = [[
                                p_date.weekday(),
                                p_date.month,
                                p_ex,
                                weather_map[p_w],
                                avg_rev
                            ]]


                            prediction = model.predict(
                                p_input
                            )[0]


                            results.append({
                                "Item": it['item_name'],
                                "AI Prediction": int(
                                    round(prediction)
                                ),
                                "Method": "RandomForest"
                            })


                        # =================================================
                        # BASIC AVERAGE FALLBACK
                        # =================================================

                        else:

                            avg = [
                                r['quantity_sold']
                                for r in rows
                            ]


                            pred = (
                                sum(avg) / len(avg)
                                if avg
                                else 0
                            )


                            if p_ex:
                                pred *= 1.3


                            results.append({
                                "Item": it['item_name'],
                                "AI Prediction": int(
                                    round(pred)
                                ),
                                "Method": "Basic Avg (Need more data)"
                            })


                    # =================================================
                    # DISPLAY FORECAST
                    # =================================================

                    if results:

                        st.subheader(
                            "📈 Forecast Result"
                        )


                        st.table(
                            pd.DataFrame(results)
                        )


                        st.info(
                            "💡 Accuracy can improve as more daily "
                            "sales data is logged."
                        )


    conn.close()