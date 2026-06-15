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

# --- Page Configuration ---
st.set_page_config(
    page_title="ZhD Eats - Школьная столовая",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- Custom CSS (from the provided HTML) ---
def load_css():
    st.markdown("""
    <style>
        /* Main container and background */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        body {
            background-color: #f8fafc;
        }
        /* Card styles */
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
        /* Button styling */
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
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: white;
            border-right: 1px solid #f1f5f9;
        }
        /* Header styling */
        .main-header {
            background: white/80;
            backdrop-filter: blur(12px);
            border-bottom: 1px solid #f1f5f9;
            padding: 1rem 2rem;
            border-radius: 0;
            margin-bottom: 2rem;
        }
        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 1rem;
            background-color: #f8fafc;
            border-radius: 2rem;
            padding: 0.5rem;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 1.5rem;
            padding: 0.5rem 1.5rem;
            font-weight: 700;
        }
        /* Metric cards */
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 1.5rem;
            padding: 1rem;
            color: white;
        }
        hr {
            margin: 1rem 0;
        }
        .menu-item {
            border-bottom: 1px solid #e2e8f0;
            padding: 1rem 0;
        }
        .badge {
            background-color: #f97316;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 2rem;
            font-size: 0.75rem;
            font-weight: 600;
        }
        footer {
            visibility: hidden;
        }
    </style>
    """, unsafe_allow_html=True)

load_css()

# --- Google Sheets Setup ---
def init_google_sheets():
    """Initialize connection to Google Sheets"""
    try:
        # Use st.secrets to securely store credentials
        # For local testing, you can use a service account key file
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Try to get credentials from secrets
        if 'gcp_service_account' in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            # Fallback for local development - you'll need to provide the path to your key file
            # This is a placeholder - you should upload your service account key to Streamlit secrets
            st.error("Google Sheets credentials not found in secrets. Please configure them.")
            return None, None
            
        client = gspread.authorize(creds)
        
        # Weekly menu sheet (for students to view)
        weekly_sheet = client.open_by_key("1PIpuFT2UNT00HDJsV-U74hod5KGNckqlmGADknlQaW8").sheet1
        
        # Orders sheet (for recording orders)
        orders_sheet = client.open_by_key("1Zo1APRjQ3hvyR1nYcYNeFn7j3WOnaUfFStVpICtTGYQ").sheet1
        
        return weekly_sheet, orders_sheet
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None, None

# --- CSV Report Setup ---
REPORT_DIR = "reports"
WEEKLY_REPORT_FILE = "Stolovaia ZHD1.csv"
MONTHLY_REPORT_FILE = "Stol_Zhd month1.csv"

def ensure_report_dir():
    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR)

def save_weekly_report(data):
    """Save weekly report to CSV"""
    ensure_report_dir()
    df = pd.DataFrame(data)
    df.to_csv(os.path.join(REPORT_DIR, WEEKLY_REPORT_FILE), index=False, encoding='utf-8-sig')

def save_monthly_report(data):
    """Save monthly report to CSV"""
    ensure_report_dir()
    df = pd.DataFrame(data)
    df.to_csv(os.path.join(REPORT_DIR, MONTHLY_REPORT_FILE), index=False, encoding='utf-8-sig')

def load_weekly_report():
    """Load weekly report from CSV"""
    try:
        return pd.read_csv(os.path.join(REPORT_DIR, WEEKLY_REPORT_FILE), encoding='utf-8-sig')
    except:
        return pd.DataFrame(columns=['date', 'day', 'item', 'category', 'price', 'orders_count', 'total_revenue'])

def load_monthly_report():
    """Load monthly report from CSV"""
    try:
        return pd.read_csv(os.path.join(REPORT_DIR, MONTHLY_REPORT_FILE), encoding='utf-8-sig')
    except:
        return pd.DataFrame(columns=['date', 'day', 'item', 'category', 'price', 'orders_count', 'total_revenue'])

# --- Menu Management (Chef only) ---
def load_menu_from_sheet():
    """Load weekly menu from CSV file instead of Google Sheets"""
    try:
        return pd.read_csv('menu.csv', encoding='utf-8')
    except:
        # Create default menu if file doesn't exist
        default_menu = pd.DataFrame({
            'day': ['Понедельник', 'Понедельник', 'Вторник', 'Среда'],
            'item_name': ['Борщ', 'Котлета', 'Суп', 'Рыба'],
            'category': ['Обед', 'Обед', 'Обед', 'Обед'],
            'price': [450, 550, 400, 600],
            'available': [True, True, True, True]
        })
        default_menu.to_csv('menu.csv', index=False, encoding='utf-8')
        return default_menu

def save_menu_to_sheet(menu_df):
    """Save updated menu to CSV file"""
    menu_df.to_csv('menu.csv', index=False, encoding='utf-8')
def update_menu_item(day, item_name, new_price=None, new_category=None, new_available=None):
    """Update a specific menu item"""
    menu_df = load_menu_from_sheet()
    mask = (menu_df['day'] == day) & (menu_df['item_name'] == item_name)
    if mask.any():
        if new_price is not None:
            menu_df.loc[mask, 'price'] = new_price
        if new_category is not None:
            menu_df.loc[mask, 'category'] = new_category
        if new_available is not None:
            menu_df.loc[mask, 'available'] = new_available
        save_menu_to_sheet(menu_df)
        return True
    return False

def add_new_item(day, item_name, category, price, available=True):
    """Add a new menu item"""
    menu_df = load_menu_from_sheet()
    new_item = pd.DataFrame({
        'day': [day],
        'item_name': [item_name],
        'category': [category],
        'price': [price],
        'available': [available]
    })
    menu_df = pd.concat([menu_df, new_item], ignore_index=True)
    save_menu_to_sheet(menu_df)
    return True

# --- Order Management ---
def place_order(student_name, student_class, items, total_price, payment_method):
    """Record an order"""
    _, orders_sheet = init_google_sheets()
    if orders_sheet:
        order_data = [
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            student_name,
            student_class,
            str(items),
            total_price,
            payment_method,
            "pending"
        ]
        orders_sheet.append_row(order_data)
        
        # Update reports
        update_reports(datetime.datetime.now().date(), items, total_price)
        return True
    return False

def update_reports(date, items, total_price):
    """Update weekly and monthly reports"""
    # Load existing reports
    weekly_df = load_weekly_report()
    monthly_df = load_monthly_report()
    
    day_name = date.strftime("%A")
    date_str = date.strftime("%Y-%m-%d")
    
    # Update weekly report
    for item in items:
        new_entry = {
            'date': date_str,
            'day': day_name,
            'item': item['name'],
            'category': item['category'],
            'price': item['price'],
            'orders_count': 1,
            'total_revenue': item['price']
        }
        weekly_df = pd.concat([weekly_df, pd.DataFrame([new_entry])], ignore_index=True)
    
    # Update monthly report
    for item in items:
        new_entry = {
            'date': date_str,
            'day': day_name,
            'item': item['name'],
            'category': item['category'],
            'price': item['price'],
            'orders_count': 1,
            'total_revenue': item['price']
        }
        monthly_df = pd.concat([monthly_df, pd.DataFrame([new_entry])], ignore_index=True)
    
    # Save updated reports
    save_weekly_report(weekly_df)
    save_monthly_report(monthly_df)

# --- QR Code Generation ---
def generate_qr(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def generate_payment_qr(order_id, amount):
    """Generate QR code for payment"""
    payment_data = f"PAYMENT:{order_id}:{amount}:{int(time.time())}"
    return generate_qr(payment_data)

def generate_chef_qr():
    """Generate QR code for chef"""
    chef_data = f"CHEF_QR:{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    return generate_qr(chef_data)

# --- Chef Authentication ---
def verify_chef_password(input_password):
    """Verify chef password"""
    # In production, use proper hashing
    expected_password = st.secrets.get("chef_password", "admin123")
    return input_password == expected_password

# --- Main App ---
def main():
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <div style="background-color: #f97316; display: inline-block; padding: 0.75rem; border-radius: 1.5rem; margin-bottom: 1rem;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"></path>
                        <path d="M7 2v20"></path>
                        <path d="M21 15V2a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"></path>
                    </svg>
                </div>
                <h1 style="font-size: 2rem; font-weight: 900; letter-spacing: -0.025em;">Столовая школы</h1>
                <p style="color: #64748b;">Закажи обед онлайн</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'role' not in st.session_state:
        st.session_state.role = "student"  # student or chef
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    if 'chef_authenticated' not in st.session_state:
        st.session_state.chef_authenticated = False
    
    # Sidebar for role selection and cart
    with st.sidebar:
        st.markdown("### 🎯 Режим работы")
        role = st.radio("Выберите роль:", ["Ученик", "Повар"], horizontal=True)
        st.session_state.role = "student" if role == "Ученик" else "chef"
        
        if st.session_state.role == "student":
            st.markdown("---")
            st.markdown("### 🛒 Ваш заказ")
            if st.session_state.cart:
                total = sum(item['price'] * item['quantity'] for item in st.session_state.cart)
                for item in st.session_state.cart:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"{item['name']}")
                    with col2:
                        st.write(f"{item['quantity']} x {item['price']}₸")
                    with col3:
                        if st.button("❌", key=f"remove_{item['name']}"):
                            st.session_state.cart.remove(item)
                            st.rerun()
                st.markdown(f"**Итого: {total}₸**")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Очистить", use_container_width=True):
                        st.session_state.cart = []
                        st.rerun()
                with col2:
                    if st.button("✅ Оформить", use_container_width=True):
                        st.session_state.show_checkout = True
            else:
                st.info("Корзина пуста. Добавьте блюда из меню!")
    
    # Student View
    if st.session_state.role == "student":
        # Contact button
        col1, col2, col3 = st.columns([3, 1, 1])
        with col3:
            st.markdown("""
                <button style="background-color: #f1f5f9; border: none; border-radius: 2rem; padding: 0.5rem 1rem; font-weight: 700; font-size: 0.75rem;">
                    📞 +7 (707) 123-4567
                </button>
            """, unsafe_allow_html=True)
        
        # Load menu
        menu_df = load_menu_from_sheet()
        
        if menu_df.empty:
            st.warning("Меню пока не загружено. Пожалуйста, зайдите позже.")
        else:
            # Day selector
            days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
            selected_day = st.selectbox("Выберите день:", days, index=0)
            
            # Category filter
            categories = ['Все'] + list(menu_df['category'].unique())
            selected_category = st.selectbox("Категория:", categories)
            
            # Filter menu
            filtered_menu = menu_df[menu_df['day'] == selected_day]
            if selected_category != 'Все':
                filtered_menu = filtered_menu[filtered_menu['category'] == selected_category]
            
            # Display menu items
            st.markdown(f"### 🍽️ Меню на {selected_day}")
            
            cols = st.columns(3)
            for idx, (_, item) in enumerate(filtered_menu.iterrows()):
                with cols[idx % 3]:
                    with st.container():
                        st.markdown(f"""
                            <div class="card">
                                <h4 style="font-weight: 800;">{item['item_name']}</h4>
                                <p style="color: #64748b; font-size: 0.875rem;">{item['category']}</p>
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;">
                                    <span style="font-size: 1.25rem; font-weight: 800; color: #f97316;">{item['price']}₸</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            quantity = st.number_input("Кол-во", min_value=0, max_value=10, key=f"qty_{item['item_name']}_{idx}", label_visibility="collapsed")
                        with col2:
                            if st.button("➕ В корзину", key=f"add_{item['item_name']}_{idx}", use_container_width=True):
                                if quantity > 0:
                                    # Check if item already in cart
                                    found = False
                                    for cart_item in st.session_state.cart:
                                        if cart_item['name'] == item['item_name']:
                                            cart_item['quantity'] += quantity
                                            found = True
                                            break
                                    if not found:
                                        st.session_state.cart.append({
                                            'name': item['item_name'],
                                            'price': item['price'],
                                            'quantity': quantity,
                                            'category': item['category']
                                        })
                                    st.success(f"Добавлено {quantity} x {item['item_name']}")
                                    st.rerun()
                                elif quantity == 0:
                                    st.warning("Выберите количество")
            
            # Checkout modal
            if st.session_state.get('show_checkout', False):
                with st.expander("Оформление заказа", expanded=True):
                    st.markdown("### 📝 Информация о заказе")
                    
                    total = sum(item['price'] * item['quantity'] for item in st.session_state.cart)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        student_name = st.text_input("Ваше имя")
                        student_class = st.text_input("Класс")
                    with col2:
                        payment_method = st.radio("Способ оплаты:", ["Картой", "QR-код"])
                    
                    if st.button("Подтвердить заказ"):
                        if student_name and student_class:
                            order_id = hashlib.md5(f"{student_name}{time.time()}".encode()).hexdigest()[:8]
                            
                            if payment_method == "Картой":
                                # Show payment info for card payment
                                st.markdown("""
                                    ### 💳 Оплата картой
                                    Для оплаты переведите сумму на карту:
                                    
                                    **Kaspi Gold:** 4400 4301 2345 6789
                                    **Halyk Bank:** 4983 4567 8901 2345
                                    **Jusan Bank:** 4405 6789 0123 4567
                                    
                                    **Получатель:** ТОО "Школьная столовая"
                                    **БИН:** 123456789012
                                    **Назначение платежа:** Заказ обедов
                                """)
                                if st.button("Оплачено"):
                                    place_order(student_name, student_class, st.session_state.cart, total, "card")
                                    st.success("Заказ оформлен! Спасибо за покупку!")
                                    st.session_state.cart = []
                                    st.session_state.show_checkout = False
                                    time.sleep(2)
                                    st.rerun()
                            else:
                                # Generate QR code for payment
                                qr_img = generate_payment_qr(order_id, total)
                                buf = BytesIO()
                                qr_img.save(buf, format="PNG")
                                st.image(buf.getvalue(), caption="QR-код для оплаты")
                                st.info("Отсканируйте QR-код для оплаты через Kaspi.kz или другой банкинг")
                                if st.button("Я оплатил(а)"):
                                    place_order(student_name, student_class, st.session_state.cart, total, "qr")
                                    st.success("Заказ оформлен! Спасибо за покупку!")
                                    st.session_state.cart = []
                                    st.session_state.show_checkout = False
                                    time.sleep(2)
                                    st.rerun()
                        else:
                            st.error("Пожалуйста, укажите имя и класс")
    
    # Chef View
    else:
        if not st.session_state.chef_authenticated:
            st.markdown("### 🔐 Доступ повара")
            password = st.text_input("Введите пароль:", type="password")
            if st.button("Войти"):
                if verify_chef_password(password):
                    st.session_state.chef_authenticated = True
                    st.success("Добро пожаловать, повар!")
                    st.rerun()
                else:
                    st.error("Неверный пароль")
        else:
            # Chef dashboard tabs
            tab1, tab2, tab3, tab4 = st.tabs(["📋 Меню", "➕ Добавить блюдо", "📊 Отчеты", "🔐 QR Повара"])
            
            with tab1:
                st.markdown("### Редактирование меню")
                menu_df = load_menu_from_sheet()
                
                if not menu_df.empty:
                    edited_df = st.data_editor(
                        menu_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "day": st.column_config.SelectboxColumn("День", options=['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']),
                            "item_name": "Блюдо",
                            "category": st.column_config.SelectboxColumn("Категория", options=['Завтрак', 'Обед', 'Выпечка', 'Напитки']),
                            "price": st.column_config.NumberColumn("Цена (₸)", min_value=0, step=10),
                            "available": st.column_config.CheckboxColumn("Доступно")
                        }
                    )
                    
                    if st.button("💾 Сохранить изменения"):
                        save_menu_to_sheet(edited_df)
                        st.success("Меню обновлено!")
                        st.rerun()
                else:
                    st.info("Меню пусто. Добавьте блюда через вкладку 'Добавить блюдо'")
            
            with tab2:
                st.markdown("### Добавление нового блюда")
                col1, col2 = st.columns(2)
                with col1:
                    new_day = st.selectbox("День", ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница'])
                    new_item_name = st.text_input("Название блюда")
                with col2:
                    new_category = st.selectbox("Категория", ['Завтрак', 'Обед', 'Выпечка', 'Напитки'])
                    new_price = st.number_input("Цена (₸)", min_value=0, step=10)
                
                if st.button("➕ Добавить блюдо"):
                    if new_item_name and new_price > 0:
                        add_new_item(new_day, new_item_name, new_category, new_price)
                        st.success(f"Блюдо '{new_item_name}' добавлено в меню на {new_day}")
                        st.rerun()
                    else:
                        st.error("Пожалуйста, заполните все поля")
            
            with tab3:
                st.markdown("### 📊 Отчеты")
                
                report_type = st.radio("Тип отчета:", ["Недельный", "Месячный"], horizontal=True)
                
                if report_type == "Недельный":
                    df = load_weekly_report()
                    if not df.empty:
                        # Summary metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Всего заказов", df['orders_count'].sum())
                        with col2:
                            st.metric("Общая выручка", f"{df['total_revenue'].sum():,.0f}₸")
                        with col3:
                            st.metric("Популярное блюдо", df.groupby('item')['orders_count'].sum().idxmax())
                        
                        st.markdown("#### Детализация по дням")
                        daily_summary = df.groupby('day').agg({'orders_count': 'sum', 'total_revenue': 'sum'}).reset_index()
                        st.dataframe(daily_summary, use_container_width=True)
                        
                        # Chart
                        fig = px.bar(daily_summary, x='day', y='total_revenue', title="Выручка по дням", color='day')
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Download button
                        csv = df.to_csv(index=False).encode('utf-8-sig')
                        st.download_button("📥 Скачать недельный отчет", csv, WEEKLY_REPORT_FILE, "text/csv")
                    else:
                        st.info("Данные за неделю отсутствуют")
                
                else:  # Monthly report
                    df = load_monthly_report()
                    if not df.empty:
                        # Summary
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Всего заказов", df['orders_count'].sum())
                        with col2:
                            st.metric("Общая выручка", f"{df['total_revenue'].sum():,.0f}₸")
                        with col3:
                            popular = df.groupby('item')['orders_count'].sum().idxmax() if not df.empty else "Нет данных"
                            st.metric("Популярное блюдо", popular)
                        
                        st.markdown("#### Выручка по категориям")
                        category_summary = df.groupby('category').agg({'total_revenue': 'sum'}).reset_index()
                        fig = px.pie(category_summary, values='total_revenue', names='category', title="Распределение выручки по категориям")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Monthly trend
                        st.markdown("#### Динамика по дням")
                        daily_trend = df.groupby('date').agg({'total_revenue': 'sum'}).reset_index()
                        fig = px.line(daily_trend, x='date', y='total_revenue', title="Ежедневная выручка")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Download
                        csv = df.to_csv(index=False).encode('utf-8-sig')
                        st.download_button("📥 Скачать месячный отчет", csv, MONTHLY_REPORT_FILE, "text/csv")
                    else:
                        st.info("Данные за месяц отсутствуют")
            
            with tab4:
                st.markdown("### 🔐 QR-код повара")
                st.info("Этот QR-код используется для подтверждения получения заказов")
                
                if st.button("🔄 Сгенерировать новый QR-код"):
                    qr_img = generate_chef_qr()
                    buf = BytesIO()
                    qr_img.save(buf, format="PNG")
                    st.session_state.chef_qr = buf.getvalue()
                
                if st.session_state.get('chef_qr'):
                    st.image(st.session_state.chef_qr, caption="QR-код повара", width=300)
                    st.download_button("📥 Скачать QR-код", st.session_state.chef_qr, "chef_qr.png", "image/png")
                else:
                    st.warning("Нажмите кнопку выше, чтобы сгенерировать QR-код")
                
                st.markdown("---")
                if st.button("🚪 Выйти из режима повара"):
                    st.session_state.chef_authenticated = False
                    st.rerun()

if __name__ == "__main__":
    main()