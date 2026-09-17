import streamlit as st
import pandas as pd
import os
import datetime
import time

st.set_page_config(page_title="SchoolEats", page_icon="🍽️", layout="wide")

REPORT_DIR = "reports"
DATA_DIR = "data"
WEEKLY_REPORT_FILE = "Stolovaia ZHD1.csv"
MONTHLY_REPORT_FILE = "Stol_Zhd month1.csv"
ORDERS_FILE = "orders.csv"
MENU_FILE = "menu.csv"
MENU_COLS = ['week','day','menu_type','item_name','category','price','weight','calories','available']


def ensure_directories():
    if not os.path.exists('reports'):
        os.makedirs('reports')
    if not os.path.exists('data'):
        os.makedirs('data')


def save_weekly_report(data):
    ensure_directories()
    pd.DataFrame(data).to_csv(f"{REPORT_DIR}/{WEEKLY_REPORT_FILE}", index=False, encoding='utf-8-sig')


def save_monthly_report(data):
    ensure_directories()
    pd.DataFrame(data).to_csv(f"{REPORT_DIR}/{MONTHLY_REPORT_FILE}", index=False, encoding='utf-8-sig')


def load_weekly_report():
    ensure_directories()
    fp = f"{REPORT_DIR}/{WEEKLY_REPORT_FILE}"
    cols = ['order_number','date','day','student_name','student_class','item','category','quantity','price','total_item_price','order_total','payment_method','status']
    try:
        if os.path.exists(fp):
            return pd.read_csv(fp, encoding='utf-8-sig')
    except Exception:
        pass
    return pd.DataFrame(columns=cols)


def load_monthly_report():
    ensure_directories()
    fp = f"{REPORT_DIR}/{MONTHLY_REPORT_FILE}"
    cols = ['order_number','date','day','student_name','student_class','item','category','quantity','price','total_item_price','order_total','payment_method','status']
    try:
        if os.path.exists(fp):
            return pd.read_csv(fp, encoding='utf-8-sig')
    except Exception:
        pass
    return pd.DataFrame(columns=cols)


def load_orders():
    ensure_directories()
    fp = f"{REPORT_DIR}/{ORDERS_FILE}"
    cols = ['order_number','date','day','student_name','student_class','items','total_price','payment_method','status']
    try:
        if os.path.exists(fp):
            df = pd.read_csv(fp, encoding='utf-8-sig')
            for c in cols:
                if c not in df.columns:
                    df[c] = ''
            return df
    except Exception:
        pass
    return pd.DataFrame(columns=cols)


def save_orders(odf):
    ensure_directories()
    odf.to_csv(f"{REPORT_DIR}/{ORDERS_FILE}", index=False, encoding='utf-8-sig')


def create_default_menu():
    ensure_directories()
    rows = []
    for week in [1,2,3,4]:
        for day in ['Понедельник','Вторник','Среда','Четверг','Пятница']:
            jr = []
            sr = []
            if day == 'Понедельник':
                jr = [('Каша манная','Завтрак',200,210),('Борщ','Обед',250,180),('Котлета с пюре','Обед',180,320),('Компот','Напитки',200,80)]
                sr = [('Борщ','Обед',450),('Котлета с пюре','Обед',550),('Компот','Напитки',150)]
            elif day == 'Вторник':
                jr = [('Овсяная каша','Завтрак',200,220),('Суп куриный','Обед',250,190),('Плов','Обед',180,340),('Чай с молоком','Напитки',200,90)]
                sr = [('Суп куриный','Обед',400),('Плов','Обед',600),('Чай','Напитки',100)]
            elif day == 'Среда':
                jr = [('Рисовая каша','Завтрак',200,230),('Солянка','Обед',250,200),('Рыба с рисом','Обед',180,310),('Кисель','Напитки',200,100)]
                sr = [('Солянка','Обед',480),('Рыба с рисом','Обед',650),('Кисель','Напитки',120)]
            elif day == 'Четверг':
                jr = [('Пшённая каша','Завтрак',200,215),('Рассольник','Обед',250,185),('Гречка с мясом','Обед',180,330),('Сок','Напитки',200,110)]
                sr = [('Рассольник','Обед',470),('Гречка с мясом','Обед',550),('Сок','Напитки',200)]
            else:
                jr = [('Кукурузная каша','Завтрак',200,225),('Лагман','Обед',250,260),('Макароны','Обед',180,300),('Кофейный напиток','Напитки',200,95)]
                sr = [('Лагман','Обед',700),('Макароны','Обед',500),('Кофе','Напитки',250)]
            for n,c,w,cal in jr:
                rows.append({'week':week,'day':day,'menu_type':'junior','item_name':n,'category':c,'price':0,'weight':w,'calories':cal,'available':True})
            for n,c,p in sr:
                rows.append({'week':week,'day':day,'menu_type':'senior','item_name':n,'category':c,'price':p,'weight':0,'calories':0,'available':True})
    df = pd.DataFrame(rows)
    df.to_csv(f"{DATA_DIR}/{MENU_FILE}", index=False, encoding='utf-8-sig')
    return df


def load_menu_from_sheet():
    ensure_directories()
    fp = f"{DATA_DIR}/{MENU_FILE}"
    try:
        if os.path.exists(fp):
            for enc in ['utf-8-sig','utf-8','cp1251','latin1']:
                try:
                    df = pd.read_csv(fp, encoding=enc)
                    if not df.empty and 'day' in df.columns:
                        if 'week' not in df.columns: df['week'] = 1
                        if 'menu_type' not in df.columns: df['menu_type'] = 'senior'
                        if 'weight' not in df.columns: df['weight'] = 0
                        if 'calories' not in df.columns: df['calories'] = 0
                        df.to_csv(fp, index=False, encoding='utf-8-sig')
                        return df
                except Exception:
                    continue
            return create_default_menu()
        return create_default_menu()
    except Exception:
        return create_default_menu()


def save_menu_to_sheet(mdf):
    ensure_directories()
    for col in MENU_COLS:
        if col not in mdf.columns:
            mdf[col] = 0 if col in ['price','weight','calories'] else ''
    mdf = mdf[MENU_COLS]
    mdf.to_csv(f"{DATA_DIR}/{MENU_FILE}", index=False, encoding='utf-8-sig')


def add_new_item(week, day, mtype, name, cat, price=0, weight=0, cal=0, avail=True):
    df = load_menu_from_sheet()
    new = pd.DataFrame({'week':[week],'day':[day],'menu_type':[mtype],'item_name':[name],'category':[cat],'price':[price],'weight':[weight],'calories':[cal],'available':[avail]})
    df = pd.concat([df, new], ignore_index=True)
    save_menu_to_sheet(df)
    return True


def get_menu_by_week_day_type(week, day, mtype):
    df = load_menu_from_sheet()
    if df.empty:
        return pd.DataFrame()
    return df[(df['week']==week)&(df['day']==day)&(df['menu_type']==mtype)]


def is_junior_class(cls):
    try:
        s = ''.join(filter(str.isdigit, str(cls)))
        if s:
            return 1 <= int(s) <= 4
    except Exception:
        pass
    return False


def generate_order_number():
    return f"ORD-{datetime.datetime.now().strftime('%Y%m%d')}-{str(int(time.time()))[-4:]}"


def place_order(name, cls, items, total, pm):
    ensure_directories()
    num = generate_order_number()
    now = datetime.datetime.now()
    tr = {'Monday':'Понедельник','Tuesday':'Вторник','Wednesday':'Среда','Thursday':'Четверг','Friday':'Пятница','Saturday':'Суббота','Sunday':'Воскресенье'}
    day_ru = tr.get(now.strftime("%A"), now.strftime("%A"))
    items_str = ", ".join([f"{i['name']} x{i['quantity']}" for i in items])
    data = {'order_number':num,'date':now.strftime("%Y-%m-%d %H:%M:%S"),'day':day_ru,'student_name':name,'student_class':cls,'items':items_str,'total_price':total,'payment_method':pm,'status':'pending'}
    odf = load_orders()
    odf = pd.concat([odf, pd.DataFrame([data])], ignore_index=True)
    save_orders(odf)
    wdf = load_weekly_report()
    mdf = load_monthly_report()
    ds = now.date().strftime("%Y-%m-%d")
    for item in items:
        entry = pd.DataFrame([{'order_number':num,'date':ds,'day':day_ru,'student_name':name,'student_class':cls,'item':item['name'],'category':item.get('category',''),'quantity':item['quantity'],'price':item.get('price',0),'total_item_price':item.get('price',0)*item['quantity'],'order_total':total,'payment_method':pm,'status':'pending'}])
        wdf = pd.concat([wdf, entry], ignore_index=True)
        mdf = pd.concat([mdf, entry], ignore_index=True)
    save_weekly_report(wdf)
    save_monthly_report(mdf)
    return num


def complete_order(num):
    odf = load_orders()
    odf.loc[odf['order_number']==num,'status'] = 'completed'
    save_orders(odf)
    wdf = load_weekly_report()
    if not wdf.empty and 'order_number' in wdf.columns:
        wdf.loc[wdf['order_number']==num,'status'] = 'completed'
        save_weekly_report(wdf)
    mdf = load_monthly_report()
    if not mdf.empty and 'order_number' in mdf.columns:
        mdf.loc[mdf['order_number']==num,'status'] = 'completed'
        save_monthly_report(mdf)


def get_pending_orders():
    odf = load_orders()
    if not odf.empty and 'status' in odf.columns:
        return odf[odf['status']=='pending']
    return pd.DataFrame()


def get_completed_orders():
    odf = load_orders()
    if not odf.empty and 'status' in odf.columns:
        return odf[odf['status']=='completed']
    return pd.DataFrame()


def verify_chef_password(p):
    return p == "123*"


st.markdown("""
<style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1200px; }
    .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
        border-radius: 1rem !important; font-weight: 700 !important;
        background-color: #f97316 !important; color: white !important; border: none !important;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover {
        background-color: #ea580c !important;
    }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


def render_student():
    st.markdown("# 🍽️ Столовая школы имени Бауыржана Момышулы ")
    st.caption("Закажи обед онлайн")

    if 'last_order_number' not in st.session_state:
        st.session_state.last_order_number = None
    if 'selected_week' not in st.session_state:
        d = datetime.datetime.now().day
        st.session_state.selected_week = 1 if d <= 7 else 2 if d <= 14 else 3 if d <= 21 else 4
    if 'student_class' not in st.session_state:
        st.session_state.student_class = ""
    if 'qty_state' not in st.session_state:
        st.session_state.qty_state = {}

    if st.session_state.last_order_number:
        st.success(f"🎫 Номер заказа: {st.session_state.last_order_number}")

    st.markdown("### 🎓 Введите ваш класс")
    ci = st.text_input("Класс (например, 3А или 7Б):", value=st.session_state.student_class, key="ci")
    if ci != st.session_state.student_class:
        st.session_state.student_class = ci
        st.rerun()

    is_jr = is_junior_class(st.session_state.student_class) if st.session_state.student_class else False
    mtype = 'junior' if is_jr else 'senior'

    if st.session_state.student_class:
        if is_jr:
            st.success(f"🍎 Младшие классы (1-4): {st.session_state.student_class}")
        else:
            st.info(f"🎓 Старшие классы (5-11): {st.session_state.student_class}")
    else:
        st.info("👆 Укажите класс")

    st.markdown("### 📅 Выберите неделю")
    wopts = {1:"1-я неделя", 2:"2-я неделя", 3:"3-я неделя", 4:"4-я неделя"}
    wcols = st.columns(4)
    for i, (wn, wl) in enumerate(wopts.items()):
        with wcols[i]:
            lbl = f"✅ {wl}" if wn == st.session_state.selected_week else wl
            if st.button(lbl, key=f"wb_{wn}", use_container_width=True):
                st.session_state.selected_week = wn
                st.rerun()

    days = ['Понедельник','Вторник','Среда','Четверг','Пятница']
    sday = st.selectbox("День:", days, index=0)

    if not st.session_state.student_class:
        st.warning("⚠️ Введите класс")
    else:
        mdf = get_menu_by_week_day_type(st.session_state.selected_week, sday, mtype)
        if mdf.empty:
            st.warning(f"Меню на {sday} пока не загружено")
        else:
            cats = ['Все'] + list(mdf['category'].unique())
            scat = st.selectbox("Категория:", cats)
            fm = mdf.copy()
            if scat != 'Все':
                fm = fm[fm['category'] == scat]

            st.markdown(f"### 🍽️ Меню на {sday}")
            if not fm.empty:
                cols = st.columns(3)
                for idx, (_, item) in enumerate(fm.iterrows()):
                    if item['available']:
                        with cols[idx % 3]:
                            with st.container():
                                if is_jr:
                                    w = int(item.get('weight', 0)) if pd.notna(item.get('weight', 0)) else 0
                                    cal = int(item.get('calories', 0)) if pd.notna(item.get('calories', 0)) else 0
                                    st.markdown(f"**{item['item_name']}**  \n*{item['category']}*  \n🔢 Кол-во: {w} • 🔥 {cal} ккал")
                                else:
                                    st.markdown(f"**{item['item_name']}**  \n*{item['category']}*  \n💰 {int(item['price'])}₸")

                                qty_key = f"qty_{st.session_state.selected_week}_{item['item_name']}_{idx}"
                                if qty_key not in st.session_state.qty_state:
                                    st.session_state.qty_state[qty_key] = 1

                                c1, c2, c3 = st.columns([1, 2, 1])
                                with c1:
                                    if st.button("➖", key=f"minus_{qty_key}", use_container_width=True):
                                        cur = st.session_state.qty_state.get(qty_key, 1)
                                        if cur > 0:
                                            st.session_state.qty_state[qty_key] = cur - 1
                                        st.rerun()
                                with c2:
                                    q = st.number_input(
                                        "Кол-во",
                                        min_value=0,
                                        step=1,
                                        key=f"num_{qty_key}",
                                        value=st.session_state.qty_state.get(qty_key, 1),
                                        label_visibility="collapsed"
                                    )
                                    st.session_state.qty_state[qty_key] = q
                                with c3:
                                    if st.button("➕", key=f"plus_{qty_key}", use_container_width=True):
                                        cur = st.session_state.qty_state.get(qty_key, 1)
                                        st.session_state.qty_state[qty_key] = cur + 1
                                        st.rerun()

                                if st.button("🛒 В корзину", key=f"add_{qty_key}", use_container_width=True):
                                    qval = st.session_state.qty_state.get(qty_key, 1)
                                    if qval > 0:
                                        found = False
                                        for x in st.session_state.cart:
                                            if x['name'] == item['item_name']:
                                                x['quantity'] += qval
                                                found = True
                                                break
                                        if not found:
                                            st.session_state.cart.append({
                                                'name': item['item_name'],
                                                'price': int(item['price']) if not is_jr else 0,
                                                'quantity': qval,
                                                'category': item['category']
                                            })
                                        st.success(f"Добавлено {qval} x {item['item_name']}")
                                        st.session_state.qty_state[qty_key] = 1
                                        st.rerun()

    if st.session_state.get('show_checkout', False):
        with st.expander("Оформление", expanded=True):
            total = sum(i['price']*i['quantity'] for i in st.session_state.cart)
            sname = st.text_input("Ваше имя")
            sclass = st.text_input("Класс", value=st.session_state.student_class)

            if is_jr:
                st.info("🍎 Для 1-4 классов питание бесплатное")
                if st.button("Подтвердить заказ"):
                    if sname and sclass:
                        onum = place_order(sname, sclass, st.session_state.cart, 0, "free")
                        st.session_state.last_order_number = onum
                        st.success(f"✅ Номер: {onum}")
                        st.session_state.cart = []
                        st.session_state.show_checkout = False
                        time.sleep(2)
                        st.rerun()
            else:
                pm = st.radio("Оплата:", ["Картой", "QR-код", "Наличными"])
                if st.button("Подтвердить заказ"):
                    if sname and sclass:
                        onum = place_order(sname, sclass, st.session_state.cart, total, pm)
                        st.session_state.last_order_number = onum
                        st.success(f"✅ Номер: {onum}")
                        st.session_state.cart = []
                        st.session_state.show_checkout = False
                        time.sleep(2)
                        st.rerun()


def render_chef():
    st.markdown("# 👨‍🍳 Панель повара")

    if not st.session_state.get('chef_authenticated', False):
        st.markdown("### 🔐 Вход")
        pwd = st.text_input("Пароль:", type="password")
        if st.button("Войти", use_container_width=True):
            if verify_chef_password(pwd):
                st.session_state.chef_authenticated = True
                st.rerun()
            else:
                st.error("Неверный пароль")
        return

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Меню", "➕ Добавить", "📦 Заказы", "📊 Отчеты"])

    with tab1:
        st.markdown("### 📋 Редактирование меню")
        c1, c2 = st.columns(2)
        with c1:
            ew = st.selectbox("Неделя:", [1,2,3,4], format_func=lambda x: f"{x}-я неделя", key="ew")
        with c2:
            et = st.selectbox("Тип:", ['junior','senior'],
                format_func=lambda x: "🍎 1-4 классы" if x=='junior' else "🎓 5-11 классы", key="et")

        st.caption("💡 Двойной клик — редактирование. Галочка в 🗑️ — пометка на удаление.")

        mdf = load_menu_from_sheet()
        mask = (mdf['week']==ew) & (mdf['menu_type']==et)
        fm = mdf[mask].copy()

        if fm.empty:
            st.info("Меню пустое. Добавьте блюда ниже или во вкладке «➕ Добавить».")
        else:
            disp = fm.copy()
            disp.insert(0, '_del', False)
            edited = st.data_editor(
                disp,
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                column_config={
                    "_del": st.column_config.CheckboxColumn("🗑️", default=False, width="small"),
                    "week": st.column_config.NumberColumn("Нед.", disabled=True, width="small"),
                    "day": st.column_config.SelectboxColumn("День",
                        options=['Понедельник','Вторник','Среда','Четверг','Пятница'], required=True),
                    "menu_type": st.column_config.SelectboxColumn("Тип",
                        options=['junior','senior'], disabled=True, width="small"),
                    "item_name": st.column_config.TextColumn("Блюдо", required=True),
                    "category": st.column_config.SelectboxColumn("Категория",
                        options=['Завтрак','Обед','Выпечка','Напитки','Салаты','Первое','Второе']),
                    "price": st.column_config.NumberColumn("Цена ₸", min_value=0, step=10),
                    "weight": st.column_config.NumberColumn("Кол-во", min_value=0, step=10),
                    "calories": st.column_config.NumberColumn("Ккал", min_value=0, step=10),
                    "available": st.column_config.CheckboxColumn("Дост.", default=True)
                },
                key=f"ed_{ew}_{et}"
            )

            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button("💾 Сохранить", key=f"sv_{ew}_{et}", use_container_width=True):
                    to_del = edited[edited['_del'] == True]
                    to_keep = edited[edited['_del'] == False].copy()
                    if '_del' in to_keep.columns:
                        to_keep = to_keep.drop(columns=['_del'])
                    others = mdf[~mask].copy()
                    to_keep['week'] = ew
                    to_keep['menu_type'] = et
                    upd = pd.concat([others, to_keep], ignore_index=True)
                    save_menu_to_sheet(upd)
                    if len(to_del) > 0:
                        st.success(f"✅ Сохранено! Удалено: {len(to_del)}")
                    else:
                        st.success("✅ Сохранено!")
                    time.sleep(1)
                    st.rerun()
            with bc2:
                if st.button("🗑️ Удалить выделенные", key=f"dl_{ew}_{et}", use_container_width=True):
                    to_del = edited[edited['_del'] == True]
                    if to_del.empty:
                        st.warning("⚠️ Отметьте строки в столбце 🗑️")
                    else:
                        to_keep = edited[edited['_del'] == False].copy()
                        if '_del' in to_keep.columns:
                            to_keep = to_keep.drop(columns=['_del'])
                        others = mdf[~mask].copy()
                        to_keep['week'] = ew
                        to_keep['menu_type'] = et
                        upd = pd.concat([others, to_keep], ignore_index=True)
                        save_menu_to_sheet(upd)
                        st.success(f"🗑️ Удалено: {len(to_del)}")
                        time.sleep(1)
                        st.rerun()

        st.markdown("---")
        st.markdown("##### ➕ Быстрое добавление")
        with st.form(key=f"qa_{ew}_{et}", clear_on_submit=True):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                qn = st.text_input("Название")
            with fc2:
                qc = st.selectbox("Категория", ['Завтрак','Обед','Выпечка','Напитки','Салаты','Первое','Второе'])
            with fc3:
                qd = st.selectbox("День", ['Понедельник','Вторник','Среда','Четверг','Пятница'])
            fc4, fc5, fc6 = st.columns(3)
            with fc4:
                qp = st.number_input("Цена ₸", min_value=0, step=10)
            with fc5:
                qw = st.number_input("Кол-во", min_value=0, step=10)
            with fc6:
                qcal = st.number_input("Ккал", min_value=0, step=10)
            if st.form_submit_button("➕ Добавить", use_container_width=True):
                if qn:
                    if et == 'senior':
                        add_new_item(ew, qd, et, qn, qc, qp, 0, 0)
                    else:
                        add_new_item(ew, qd, et, qn, qc, 0, qw, qcal)
                    st.success(f"✅ {qn}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Введите название")

    with tab2:
        st.markdown("### ➕ Добавить блюдо")
        c1, c2 = st.columns(2)
        with c1:
            nw = st.selectbox("Неделя", [1,2,3,4], format_func=lambda x: f"{x}-я неделя", key="nw")
            nd = st.selectbox("День", ['Понедельник','Вторник','Среда','Четверг','Пятница'], key="nd")
            nt = st.selectbox("Тип", ['junior','senior'],
                format_func=lambda x: "🍎 1-4 классы" if x=='junior' else "🎓 5-11 классы", key="nt")
            nn = st.text_input("Название", key="nn")
        with c2:
            nc = st.selectbox("Категория",
                ['Завтрак','Обед','Выпечка','Напитки','Салаты','Первое','Второе'], key="nc")
            np = st.number_input("Цена ₸", min_value=0, step=10, key="np")
            nwt = st.number_input("Кол-во", min_value=0, step=10, key="nwt")
            ncl = st.number_input("Ккал", min_value=0, step=10, key="ncl")
        if st.button("➕ Добавить", key="addbtn"):
            if nn:
                add_new_item(nw, nd, nt, nn, nc, np, nwt, ncl)
                st.success(f"✅ {nn}")
                st.rerun()
            else:
                st.error("Введите название")

    with tab3:
        st.markdown("### 📦 Заказы")
        po = get_pending_orders()
        if not po.empty:
            st.info(f"Ожидают: {len(po)}")
            for idx, (_, o) in enumerate(po.iterrows()):
                with st.expander(f"🎫 {o.get('order_number','')} — {o.get('student_name','')}"):
                    st.markdown(f"**Класс:** {o.get('student_class','')}")
                    st.markdown(f"**Сумма:** {o.get('total_price',0)}₸")
                    st.markdown(f"**Заказ:** {o.get('items','')}")
                    st.markdown(f"**Оплата:** {o.get('payment_method','')}")
                    if st.button("✅ Выдать", key=f"c_{idx}"):
                        complete_order(o['order_number'])
                        st.rerun()
        else:
            st.success("🎉 Нет активных заказов")

    with tab4:
        st.markdown("### 📊 Отчеты")
        rt = st.radio("Тип:", ["Недельный", "Месячный"], horizontal=True)

        if rt == "Недельный":
            df = load_weekly_report()
            fname = WEEKLY_REPORT_FILE
        else:
            df = load_monthly_report()
            fname = MONTHLY_REPORT_FILE

        if not df.empty and 'order_number' in df.columns:
            if 'status' in df.columns:
                cc = len(df[df['status'] == 'completed']['order_number'].unique())
                pc = len(df[df['status'] == 'pending']['order_number'].unique())
            else:
                cc = 0
                pc = 0
            if 'order_total' in df.columns:
                tr = df['order_total'].sum()
            else:
                tr = 0

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("✅ Выдано", cc)
            with c2:
                st.metric("⏳ Ожидают", pc)
            with c3:
                st.metric("💰 Выручка", f"{tr:,.0f}₸")

            csv_data = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Скачать", csv_data, fname, "text/csv")
        else:
            st.info("Нет данных")


def main():
    ensure_directories()

    if 'role' not in st.session_state:
        st.session_state.role = "student"
    if 'cart' not in st.session_state:
        st.session_state.cart = []

    with st.sidebar:
        st.markdown("### 🎯 Режим работы")
        role = st.radio("Роль:", ["Ученик", "Повар"], horizontal=True)
        st.session_state.role = "student" if role == "Ученик" else "chef"

        if st.session_state.role == "student":
            st.markdown("---")
            st.markdown("### 🛒 Корзина")
            if st.session_state.cart:
                total = sum(i['price'] * i['quantity'] for i in st.session_state.cart)
                for i, item in enumerate(st.session_state.cart):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    with c1:
                        st.write(item['name'])
                    with c2:
                        if item['price'] > 0:
                            st.write(f"{item['quantity']} x {item['price']}₸")
                        else:
                            st.write(f"{item['quantity']} порц.")
                    with c3:
                        if st.button("❌", key=f"rm_{i}_{item['name']}"):
                            st.session_state.cart.pop(i)
                            st.rerun()
                if total > 0:
                    st.markdown(f"**Итого: {total}₸**")
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button("🗑️ Очистить", use_container_width=True):
                        st.session_state.cart = []
                        st.rerun()
                with cc2:
                    if st.button("✅ Оформить", use_container_width=True):
                        st.session_state.show_checkout = True
            else:
                st.info("Корзина пуста")

    if st.session_state.role == "student":
        render_student()
    else:
        render_chef()


if __name__ == "__main__":
    main()
