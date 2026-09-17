import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import qrcode
from io import BytesIO
from PIL import Image
import datetime
import hashlib
import time
import os
import plotly.express as px
import csv

# --- Page Configuration ---
st.set_page_config(
    page_title="SchoolEats - Школьная столовая",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- Custom CSS ---
def load_css():
    st.markdown("""
    <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        body { background-color: #f8fafc; }
        .card {
            background: white;
            border-radius: 2rem;
            padding: 1.5rem;
            box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.05), 0 8px 10px -6px rgb(0 0 0 / 0.01);
            transition: all 0.3s ease;
            border: 1px solid #f1f5f9;
        }
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 25px 30px -12px rgb(0 0 0 / 0.15);
        }
        .stButton > button {
            border-radius: 1rem !important;
            font-weight: 700 !important;
            transition: all 0.2s ease !important;
            background-color: #f97316 !important;
            color: white !important;
            border: none !important;
        }
        .stButton > button:hover {
            background-color: #ea580c !important;
            transform: scale(0.98);
        }
        [data-testid="stSidebar"] {
            background-color: white;
            border-right: 1px solid #f1f5f9;
        }
        .order-number {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 1rem;
            text-align: center;
            font-size: 1.5rem;
            font-weight: bold;
            margin: 1rem 0;
        }
        .week-badge {
            background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 1rem;
            display: inline-block;
            font-weight: 700;
            margin-bottom: 1rem;
        }
        footer { visibility: hidden; }
        .stAlert { border-radius: 1rem; }
    </style>
    """, unsafe_allow_html=True)

load_css()

# --- Ensure directories exist ---
def ensure_directories():
    if not os.path.exists('reports'):
        os.makedirs('reports')
    if not os.path.exists('data'):
        os.makedirs('data')

# --- Google Sheets Setup (Optional) ---
def init_google_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if 'gcp_service_account' in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            weekly_sheet = client.open_by_key("1PIpuFT2UNT00HDJsV-U74hod5KGNckqlmGADknlQaW8").sheet1
            orders_sheet = client.open_by_key("1Zo1APRjQ3hvyR1nYcYNeFn7j3WOnaUfFStVpICtTGYQ").sheet1
            return weekly_sheet, orders_sheet
    except Exception:
        pass
    return None, None

# --- CSV File Setup ---
REPORT_DIR = "reports"
DATA_DIR = "data"
WEEKLY_REPORT_FILE = "Stolovaia ZHD1.csv"
MONTHLY_REPORT_FILE = "Stol_Zhd month1.csv"
ORDERS_FILE = "orders.csv"
MENU_FILE = "menu.csv"

def ensure_report_dir():
    ensure_directories()

def save_weekly_report(data):
    ensure_report_dir()
    df = pd.DataFrame(data)
    filepath = os.path.join(REPORT_DIR, WEEKLY_REPORT_FILE)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')

def save_monthly_report(data):
    ensure_report_dir()
    df = pd.DataFrame(data)
    filepath = os.path.join(REPORT_DIR, MONTHLY_REPORT_FILE)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')

def load_weekly_report():
    ensure_report_dir()
    filepath = os.path.join(REPORT_DIR, WEEKLY_REPORT_FILE)
    cols = ['order_number', 'date', 'day', 'student_name', 'student_class', 'item', 'category', 'quantity', 'price', 'total_item_price', 'order_total', 'payment_method', 'status']
    try:
        if os.path.exists(filepath):
            return pd.read_csv(filepath, encoding='utf-8-sig')
        return pd.DataFrame(columns=cols)
    except Exception:
        return pd.DataFrame(columns=cols)

def load_monthly_report():
    ensure_report_dir()
    filepath = os.path.join(REPORT_DIR, MONTHLY_REPORT_FILE)
    cols = ['order_number', 'date', 'day', 'student_name', 'student_class', 'item', 'category', 'quantity', 'price', 'total_item_price', 'order_total', 'payment_method', 'status']
    try:
        if os.path.exists(filepath):
            return pd.read_csv(filepath, encoding='utf-8-sig')
        return pd.DataFrame(columns=cols)
    except Exception:
        return pd.DataFrame(columns=cols)

def load_orders():
    ensure_report_dir()
    filepath = os.path.join(REPORT_DIR, ORDERS_FILE)
    cols = ['order_number', 'date', 'day', 'student_name', 'student_class', 'items', 'total_price', 'payment_method', 'status']
    try:
        if os.path.exists(filepath):
            df = pd.read_csv(filepath, encoding='utf-8-sig')
            for col in cols:
                if col not in df.columns:
                    df[col] = ''
            return df
        return pd.DataFrame(columns=cols)
    except Exception:
        return pd.DataFrame(columns=cols)

def save_orders(orders_df):
    ensure_report_dir()
    filepath = os.path.join(REPORT_DIR, ORDERS_FILE)
    orders_df.to_csv(filepath, index=False, encoding='utf-8-sig')

# --- Menu Management ---
def create_default_menu():
    ensure_directories()
    menu_file = os.path.join(DATA_DIR, MENU_FILE)
    rows = []
    days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
    for week in [1, 2, 3, 4]:
        for day in days:
            if day == 'Понедельник':
                items = [('Борщ', 'Обед', 450), ('Котлета с пюре', 'Обед', 550), ('Компот', 'Напитки', 150)]
            elif day == 'Вторник':
                items = [('Суп куриный', 'Обед', 400), ('Плов', 'Обед', 600), ('Чай', 'Напитки', 100)]
            elif day == 'Среда':
                items = [('Солянка', 'Обед', 480), ('Рыба с рисом', 'Обед', 650), ('Кисель', 'Напитки', 120)]
            elif day == 'Четверг':
                items = [('Рассольник', 'Обед', 470), ('Гречка с мясом', 'Обед', 550), ('Сок', 'Напитки', 200)]
            else:
                items = [('Лагман', 'Обед', 700), ('Макароны', 'Обед', 500), ('Кофе', 'Напитки', 250)]
            for item_name, category, price in items:
                rows.append({
                    'week': week, 'day': day, 'item_name': item_name,
                    'category': category, 'price': price, 'available': True
                })
    default_menu = pd.DataFrame(rows)
    default_menu.to_csv(menu_file, index=False, encoding='utf-8-sig')
    return default_menu

def load_menu_from_sheet():
    ensure_directories()
    menu_file = os.path.join(DATA_DIR, MENU_FILE)
    try:
        if os.path.exists(menu_file):
            for encoding in ['utf-8-sig', 'utf-8', 'cp1251', 'latin1']:
                try:
                    df = pd.read_csv(menu_file, encoding=encoding)
                    if not df.empty and 'day' in df.columns:
                        if 'week' not in df.columns:
                            df['week'] = 1
                            save_menu_to_sheet(df)
                        return df
                except Exception:
                    continue
            return create_default_menu()
        return create_default_menu()
    except Exception:
        return create_default_menu()

def save_menu_to_sheet(menu_df):
    ensure_directories()
    menu_file = os.path.join(DATA_DIR, MENU_FILE)
    menu_df.to_csv(menu_file, index=False, encoding='utf-8-sig')

def add_new_item(week, day, item_name, category, price, available=True):
    menu_df = load_menu_from_sheet()
    new_item = pd.DataFrame({
        'week': [week], 'day': [day], 'item_name': [item_name],
        'category': [category], 'price': [price], 'available': [available]
    })
    menu_df = pd.concat([menu_df, new_item], ignore_index=True)
    save_menu_to_sheet(menu_df)
    return True

def get_menu_by_week_and_day(week, day):
    menu_df = load_menu_from_sheet()
    if menu_df.empty:
        return pd.DataFrame()
    filtered = menu_df[(menu_df['week'] == week) & (menu_df['day'] == day)]
    return filtered

# --- Order Management ---
def generate_order_number():
    return f"ORD-{datetime.datetime.now().strftime('%Y%m%d')}-{str(int(time.time()))[-4:]}"

def place_order(student_name, student_class, items, total_price, payment_method):
    ensure_directories()
    order_number = generate_order_number()
    current_date = datetime.datetime.now()
    day_name = current_date.strftime("%A")
    day_translation = {
        'Monday': 'Понедельник', 'Tuesday': 'Вторник', 'Wednesday': 'Среда',
        'Thursday': 'Четверг', 'Friday': 'Пятница', 'Saturday': 'Суббота', 'Sunday': 'Воскресенье'
    }
    day_name_ru = day_translation.get(day_name, day_name)
    items_str = ", ".join([f"{item['name']} x{item['quantity']}" for item in items])
    order_data = {
        'order_number': order_number,
        'date': current_date.strftime("%Y-%m-%d %H:%M:%S"),
        'day': day_name_ru,
        'student_name': student_name,
        'student_class': student_class,
        'items': items_str,
        'total_price': total_price,
        'payment_method': payment_method,
        'status': 'pending'
    }
    orders_df = load_orders()
    orders_df = pd.concat([orders_df, pd.DataFrame([order_data])], ignore_index=True)
    save_orders(orders_df)
    update_reports(order_number, current_date.date(), day_name_ru, student_name, student_class, items, total_price, payment_method)
    return order_number

def update_reports(order_number, date, day_name, student_name, student_class, items, total_price, payment_method):
    ensure_directories()
    weekly_df = load_weekly_report()
    monthly_df = load_monthly_report()
    date_str = date.strftime("%Y-%m-%d")
    for item in items:
        new_entry = pd.DataFrame([{
            'order_number': order_number, 'date': date_str, 'day': day_name,
            'student_name': student_name, 'student_class': student_class,
            'item': item['name'], 'category': item['category'],
            'quantity': item['quantity'], 'price': item['price'],
            'total_item_price': item['price'] * item['quantity'],
            'order_total': total_price, 'payment_method': payment_method, 'status': 'pending'
        }])
        weekly_df = pd.concat([weekly_df, new_entry], ignore_index=True)
        monthly_df = pd.concat([monthly_df, new_entry], ignore_index=True)
    save_weekly_report(weekly_df)
    save_monthly_report(monthly_df)

def complete_order(order_number):
    orders_df = load_orders()
    orders_df.loc[orders_df['order_number'] == order_number, 'status'] = 'completed'
    save_orders(orders_df)
    weekly_df = load_weekly_report()
    if not weekly_df.empty and 'order_number' in weekly_df.columns:
        weekly_df.loc[weekly_df['order_number'] == order_number, 'status'] = 'completed'
        save_weekly_report(weekly_df)
    monthly_df = load_monthly_report()
    if not monthly_df.empty and 'order_number' in monthly_df.columns:
        monthly_df.loc[monthly_df['order_number'] == order_number, 'status'] = 'completed'
        save_monthly_report(monthly_df)

def get_pending_orders():
    orders_df = load_orders()
    if not orders_df.empty and 'status' in orders_df.columns:
        return orders_df[orders_df['status'] == 'pending']
    return pd.DataFrame()

def get_completed_orders():
    orders_df = load_orders()
    if not orders_df.empty and 'status' in orders_df.columns:
        return orders_df[orders_df['status'] == 'completed']
    return pd.DataFrame()

# --- QR Code Generation ---
def generate_qr(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def generate_payment_qr(order_id, amount):
    payment_data = f"PAYMENT:{order_id}:{amount}:{int(time.time())}"
    return generate_qr(payment_data)

def generate_chef_qr():
    chef_data = f"CHEF_QR:{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    return generate_qr(chef_data)

# --- Chef Authentication ---
def verify_chef_password(input_password):
    return input_password == "123*"

# --- Main App ---
def main():
    ensure_directories()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <div style="background-color: #f97316; display: inline-block; padding: 0.75rem; border-radius: 1.5rem; margin-bottom: 1rem;">🍽️</div>
                <h1 style="font-size: 2rem; font-weight: 900; letter-spacing: -0.025em;">Столовая школы</h1>
                <p style="color: #64748b;">Закажи обед онлайн</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Session state
    if 'role' not in st.session_state:
        st.session_state.role = "student"
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    if 'chef_authenticated' not in st.session_state:
        st.session_state.chef_authenticated = False
    if 'last_order_number' not in st.session_state:
        st.session_state.last_order_number = None
    if 'selected_week' not in st.session_state:
        today = datetime.datetime.now()
        if today.day <= 7:
            current_week = 1
        elif today.day <= 14:
            current_week = 2
        elif today.day <= 21:
            current_week = 3
        else:
            current_week = 4
        st.session_state.selected_week = current_week
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎯 Режим работы")
        role = st.radio("Выберите роль:", ["Ученик", "Повар"], horizontal=True)
        st.session_state.role = "student" if role == "Ученик" else "chef"
        
        if st.session_state.role == "student":
            st.markdown("---")
            st.markdown("### 🛒 Ваш заказ")
            if st.session_state.cart:
                total = sum(item['price'] * item['quantity'] for item in st.session_state.cart)
                for i, item in enumerate(st.session_state.cart):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    with c1:
                        st.write(f"{item['name']}")
                    with c2:
                        st.write(f"{item['quantity']} x {item['price']}₸")
                    with c3:
                        if st.button("❌", key=f"remove_{i}_{item['name']}"):
                            st.session_state.cart.pop(i)
                            st.rerun()
                st.markdown(f"**Итого: {total}₸**")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🗑️ Очистить", use_container_width=True):
                        st.session_state.cart = []
                        st.rerun()
                with c2:
                    if st.button("✅ Оформить", use_container_width=True):
                        st.session_state.show_checkout = True
            else:
                st.info("Корзина пуста.")
    
    # --- Student View ---
    if st.session_state.role == "student":
        if st.session_state.last_order_number:
            st.markdown(f"""
                <div class="order-number">
                    🎫 Ваш номер заказа: <strong>{st.session_state.last_order_number}</strong><br>
                    <small>Сохраните этот номер!</small>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 📅 Выберите неделю")
        week_options = {1: "1-я неделя", 2: "2-я неделя", 3: "3-я неделя", 4: "4-я неделя"}
        week_cols = st.columns(4)
        for i, (week_num, week_label) in enumerate(week_options.items()):
            with week_cols[i]:
                is_current = (week_num == st.session_state.selected_week)
                button_label = f"✅ {week_label}" if is_current else week_label
                if st.button(button_label, key=f"week_btn_{week_num}", use_container_width=True):
                    st.session_state.selected_week = week_num
                    st.rerun()
        
        st.markdown(f'<div class="week-badge">📆 Текущая неделя: {st.session_state.selected_week}-я неделя</div>', unsafe_allow_html=True)
        
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
        selected_day = st.selectbox("Выберите день:", days, index=0)
        
        menu_df = get_menu_by_week_and_day(st.session_state.selected_week, selected_day)
        
        if menu_df.empty:
            st.warning(f"Меню на {selected_day} ({st.session_state.selected_week}-я неделя) пока не загружено.")
        else:
            all_categories = ['Все'] + list(menu_df['category'].unique())
            selected_category = st.selectbox("Категория:", all_categories)
            
            filtered_menu = menu_df.copy()
            if selected_category != 'Все':
                filtered_menu = filtered_menu[filtered_menu['category'] == selected_category]
            
            st.markdown(f"### 🍽️ Меню на {selected_day} ({st.session_state.selected_week}-я неделя)")
            
            if not filtered_menu.empty:
                cols = st.columns(3)
                for idx, (_, item) in enumerate(filtered_menu.iterrows()):
                    if item['available']:
                        with cols[idx % 3]:
                            with st.container():
                                st.markdown(f"""
                                    <div class="card">
                                        <h4 style="font-weight: 800;">{item['item_name']}</h4>
                                        <p style="color: #64748b; font-size: 0.875rem;">{item['category']}</p>
                                        <div style="margin-top: 1rem;">
                                            <span style="font-size: 1.25rem; font-weight: 800; color: #f97316;">{item['price']}₸</span>
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
                                c1, c2 = st.columns([1, 1])
                                with c1:
                                    quantity = st.number_input("Кол-во", min_value=0, max_value=10,
                                        key=f"qty_{st.session_state.selected_week}_{item['item_name']}_{idx}",
                                        label_visibility="collapsed")
                                with c2:
                                    if st.button("➕ В корзину",
                                        key=f"add_{st.session_state.selected_week}_{item['item_name']}_{idx}",
                                        use_container_width=True):
                                        if quantity > 0:
                                            found = False
                                            for ci in st.session_state.cart:
                                                if ci['name'] == item['item_name']:
                                                    ci['quantity'] += quantity
                                                    found = True
                                                    break
                                            if not found:
                                                st.session_state.cart.append({
                                                    'name': item['item_name'],
                                                    'price': int(item['price']),
                                                    'quantity': quantity,
                                                    'category': item['category']
                                                })
                                            st.success(f"Добавлено {quantity} x {item['item_name']}")
                                            st.rerun()
            else:
                st.info(f"На {selected_day} пока нет блюд в этой категории")
        
        # --- Checkout ---
        if st.session_state.get('show_checkout', False):
            with st.expander("Оформление заказа", expanded=True):
                st.markdown("### 📝 Информация о заказе")
                total = sum(item['price'] * item['quantity'] for item in st.session_state.cart)
                c1, c2 = st.columns(2)
                with c1:
                    student_name = st.text_input("Ваше имя")
                    student_class = st.text_input("Класс")
                with c2:
                    payment_method = st.radio("Способ оплаты:", ["Картой", "QR-код", "Наличными"])
                
                if st.button("Подтвердить заказ"):
                    if student_name and student_class:
                        if payment_method == "Картой":
                            st.markdown("""
                                ### 💳 Оплата картой
                                **Kaspi Gold:** 4400 4301 2345 6789
                                **Halyk Bank:** 4983 4567 8901 2345
                            """)
                            if st.button("✅ Оплачено"):
                                onum = place_order(student_name, student_class, st.session_state.cart, total, "card")
                                st.session_state.last_order_number = onum
                                st.success(f"✅ Заказ оформлен! Номер: {onum}")
                                st.session_state.cart = []
                                st.session_state.show_checkout = False
                                time.sleep(2)
                                st.rerun()
                        elif payment_method == "QR-код":
                            temp = generate_order_number()
                            qr_img = generate_payment_qr(temp, total)
                            buf = BytesIO()
                            qr_img.save(buf, format="PNG")
                            st.image(buf.getvalue(), caption="QR-код для оплаты", width=250)
                            if st.button("✅ Я оплатил(а)"):
                                onum = place_order(student_name, student_class, st.session_state.cart, total, "qr")
                                st.session_state.last_order_number = onum
                                st.success(f"✅ Заказ оформлен! Номер: {onum}")
                                st.session_state.cart = []
                                st.session_state.show_checkout = False
                                time.sleep(2)
                                st.rerun()
                        else:
                            onum = place_order(student_name, student_class, st.session_state.cart, total, "cash")
                            st.session_state.last_order_number = onum
                            st.success(f"✅ Заказ оформлен! Номер: {onum}")
                            st.info("💰 Оплата наличными при получении")
                            st.session_state.cart = []
                            st.session_state.show_checkout = False
                            time.sleep(2)
                            st.rerun()
                    else:
                        st.error("Пожалуйста, укажите имя и класс")
    
    # --- Chef View ---
    else:
        if not st.session_state.chef_authenticated:
            st.markdown("### 🔐 Доступ повара")
            password = st.text_input("Введите пароль:", type="password")
            if st.button("Войти", use_container_width=True):
                if verify_chef_password(password):
                    st.session_state.chef_authenticated = True
                    st.success("Добро пожаловать, повар!")
                    st.rerun()
                else:
                    st.error("Неверный пароль")
        else:
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Меню", "➕ Добавить блюдо", "📦 Заказы", "📊 Отчеты", "🔐 QR"])
            
            # --- TAB 1: Редактирование меню ---
            with tab1:
                st.markdown("### 📋 Редактирование меню по неделям")
                edit_week = st.selectbox("Выберите неделю для редактирования:", [1, 2, 3, 4],
                    format_func=lambda x: f"{x}-я неделя", key="chef_edit_week")
                
                menu_df = load_menu_from_sheet()
                week_menu = menu_df[menu_df['week'] == edit_week].copy()
                st.markdown(f"#### Меню на {edit_week}-ю неделю")
                
                if not week_menu.empty:
                    edited_df = st.data_editor(
                        week_menu,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "week": st.column_config.NumberColumn("Неделя", min_value=1, max_value=4, disabled=True),
                            "day": st.column_config.SelectboxColumn("День", options=['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']),
                            "item_name": "Блюдо",
                            "category": st.column_config.SelectboxColumn("Категория", options=['Завтрак', 'Обед', 'Выпечка', 'Напитки']),
                            "price": st.column_config.NumberColumn("Цена (₸)", min_value=0, step=10),
                            "available": st.column_config.CheckboxColumn("Доступно")
                        },
                        key=f"menu_editor_week_{edit_week}"
                    )
                    if st.button("💾 Сохранить изменения", key=f"save_menu_week_{edit_week}"):
                        other_weeks = menu_df[menu_df['week'] != edit_week]
                        updated_menu = pd.concat([other_weeks, edited_df], ignore_index=True)
                        save_menu_to_sheet(updated_menu)
                        st.success(f"Меню на {edit_week}-ю неделю обновлено!")
                        st.rerun()
                else:
                    st.info(f"Меню на {edit_week}-ю неделю пустое.")
            
            # --- TAB 2: Добавление блюда ---
            with tab2:
                st.markdown("### ➕ Добавление блюда")
                c1, c2 = st.columns(2)
                with c1:
                    new_week = st.selectbox("Неделя", [1, 2, 3, 4],
                        format_func=lambda x: f"{x}-я неделя", key="new_item_week")
                    new_day = st.selectbox("День", ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница'], key="new_item_day")
                    new_item_name = st.text_input("Название", key="new_item_name")
                with c2:
                    new_category = st.selectbox("Категория", ['Завтрак', 'Обед', 'Выпечка', 'Напитки'], key="new_item_cat")
                    new_price = st.number_input("Цена (₸)", min_value=0, step=10, key="new_item_price")
                
                if st.button("➕ Добавить", key="add_new_item_btn"):
                    if new_item_name and new_price > 0:
                        add_new_item(new_week, new_day, new_item_name, new_category, new_price)
                        st.success(f"Добавлено: {new_item_name}")
                        st.rerun()
                    else:
                        st.error("Заполните название и цену")
            
            # --- TAB 3: Заказы ---
            with tab3:
                st.markdown("### 📦 Выдача заказов")
                pending_orders = get_pending_orders()
                if not pending_orders.empty:
                    st.info(f"⏳ Ожидают выдачи: {len(pending_orders)} заказов")
                    for idx, (_, order) in enumerate(pending_orders.iterrows()):
                        with st.expander(f"🎫 {order.get('order_number', 'N/A')} - {order.get('student_name', 'Unknown')}"):
                            c1, c2 = st.columns(2)
                            with c1:
                                st.markdown(f"**📅 Дата:** {order.get('date', 'N/A')}")
                                st.markdown(f"**💰 Сумма:** {order.get('total_price', 0)}₸")
                                st.markdown(f"**💳 Оплата:** {order.get('payment_method', 'N/A')}")
                            with c2:
                                st.markdown(f"**🍽️ Заказ:** {order.get('items', 'N/A')}")
                            if st.button("✅ Выдать заказ", key=f"complete_{order.get('order_number', idx)}_{idx}"):
                                complete_order(order['order_number'])
                                st.success(f"Заказ выдан!")
                                st.rerun()
                else:
                    st.success("🎉 Нет заказов, ожидающих выдачи!")
                
                st.markdown("---")
                st.markdown("### ✅ Выданные заказы")
                completed_orders = get_completed_orders()
                if not completed_orders.empty:
                    for _, order in completed_orders.iterrows():
                        st.markdown(f"- **{order.get('order_number', 'N/A')}** - {order.get('student_name', 'Unknown')} - {order.get('date', 'N/A')}")
            
            # --- TAB 4: Отчеты ---
            with tab4:
                st.markdown("### 📊 Отчеты")
                report_type = st.radio("Тип отчета:", ["Недельный", "Месячный"], horizontal=True)
                
                if report_type == "Недельный":
                    df = load_weekly_report()
                else:
                    df = load_monthly_report()
                
                if not df.empty and 'order_number' in df.columns:
                    completed_count = 0
                    pending_count = 0
                    total_revenue = 0
                    if 'status' in df.columns:
                        completed_count = len(df[df['status'] == 'completed']['order_number'].unique())
                        pending_count = len(df[df['status'] == 'pending']['order_number'].unique())
                    if 'order_total' in df.columns:
                        total_revenue = df['order_total'].sum()
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("✅ Выдано", completed_count)
                    with c2:
                        st.metric("⏳ Ожидают", pending_count)
                    with c3:
                        st.metric("💰 Выручка", f"{total_revenue:,.0f}₸")
                    
                    display_cols = [x for x in ['order_number', 'date', 'student_name', 'total_price', 'payment_method', 'status'] if x in df.columns]
                    if display_cols:
                        display_df = df[display_cols].drop_duplicates(subset=['order_number']) if 'order_number' in display_cols else df[display_cols]
                        st.dataframe(display_df, use_container_width=True)
                    
                    csv_data = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 Скачать отчет", csv_data,
                        WEEKLY_REPORT_FILE if report_type == "Недельный" else MONTHLY_REPORT_FILE, "text/csv")
                else:
                    st.info(f"Нет данных за {'неделю' if report_type == 'Недельный' else 'месяц'}")
            
            # --- TAB 5: QR ---
            with tab5:
                st.markdown("### 🔐 QR-код повара")
                if st.button("🔄 Сгенерировать QR"):
                    qr_img = generate_chef_qr()
                    buf = BytesIO()
                    qr_img.save(buf, format="PNG")
                    st.session_state.chef_qr = buf.getvalue()
                if st.session_state.get('chef_qr'):
                    st.image(st.session_state.chef_qr, caption="QR повара", width=250)
                    st.download_button("📥 Скачать QR", st.session_state.chef_qr, "chef_qr.png", "image/png")
                st.markdown("---")
                if st.button("🚪 Выйти"):
                    st.session_state.chef_authenticated = False
                    st.rerun()

if __name__ == "__main__":
    main()