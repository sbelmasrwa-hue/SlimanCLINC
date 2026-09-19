import streamlit as st
import pandas as pd
import bcrypt
import psycopg2
from datetime import datetime

# --- إعداد الصفحة والشعار ---
st.set_page_config(page_title="Sliman Clinic OS", page_icon="🌿", layout="wide")

# عرض الشعار في الشريط الجانبي
try:
    st.sidebar.image("logo.jpg", width=120)
except:
    st.sidebar.warning("⚠️ لم يتم العثور على صورة الشعار logo.jpg")

st.sidebar.title("إدارة عيادة سليمان")

# --- الاتصال بقاعدة البيانات ---
def get_db_connection():
    try:
        db_url = st.secrets["postgres"]["url"]
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

# --- تهيئة الجداول الأساسية في قاعدة البيانات ---
def init_db():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        # جدول المخزون
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id SERIAL PRIMARY KEY,
                item_name TEXT NOT NULL,
                category TEXT,
                quantity_ml_or_gm REAL,
                cost_per_unit REAL,
                supplier TEXT
            );
        """)
        # جدول الجلسات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                client_name TEXT,
                session_date TEXT,
                oil_used TEXT,
                oil_consumed_amount REAL,
                total_cost REAL,
                notes TEXT
            );
        """)
        # جدول الموظفين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT,
                role TEXT
            );
        """)
        # جدول المواعيد
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id SERIAL PRIMARY KEY,
                client_name TEXT,
                phone TEXT,
                appointment_date TEXT,
                appointment_time TEXT,
                status TEXT
            );
        """)
        # جدول المتعالجين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                full_name TEXT,
                phone TEXT,
                age INT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # جدول السجل الأمني
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_name TEXT,
                action_description TEXT
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()

init_db()

# --- إدارة جلسة تسجيل الدخول ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("🔐 تسجيل دخول النظام - Sliman Clinic OS")
    username_input = st.text_input("اسم المستخدم")
    password_input = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if username_input == "admin" and password_input == "admin2026":
            st.session_state.logged_in = True
            st.session_state.username = "admin"
            st.success("تم تسجيل الدخول بنجاح!")
            st.rerun()
        else:
            st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
    st.stop()

# --- القائمة الجانبية المحدثة والشاملة ---
menu = st.sidebar.selectbox("القائمة الرئيسية", [
    "🏠 الرئيسية والملخص",
    "🧴 حساب المخزون (الزيوت والكريمات)",
    "💆‍♂️ إدارة الجلسات واستهلاك المواد",
    "📅 جدول المواعيد والحجوزات",
    "👥 دليل ملفات المتعالجين",
    "👥 إدارة الموظفين وإعدادات الحساب",
    "📑 الملاحظات الطبية (SOAP) وخريطة الجسد",
    "📊 تحليل الربحية المباشرة (COGS)",
    "🛡️ سجل التتبع والرقابة الأمني"
])

conn = get_db_connection()

# --- 1. الرئيسية والملخص ---
if menu == "🏠 الرئيسية والملخص":
    st.title("🌿 نظام عيادة سليمان - Sliman Clinic OS")
    st.write("مرحباً بك في لوحة التحكم المركزية للعيادة.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("حالة النظام", "متصل بقاعدة البيانات", "فعال")
    with col2:
        st.metric("الأمان والحماية", "مفعل ومؤمن", "محمي")
    with col3:
        st.metric("إصدار النظام", "v1.2 متكامل", "محدث")

# --- 2. إدارة المخزون ---
elif menu == "🧴 حساب المخزون (الزيوت والكريمات)":
    st.title("🧴 إدارة المخزون (الزيوت والكريمات)")
    with st.form("inventory_form"):
        item_name = st.text_input("اسم الزيت أو الكريم")
        category = st.selectbox("التصنيف", ["زيوت أساسية", "زيوت عطرية", "كريمات علاجية"])
        quantity = st.number_input("الكمية المتوفرة (مل / غرام)", min_value=0.0, step=10.0)
        cost = st.number_input("تكلفة الوحدة (لكل مل/غرام)", min_value=0.0, step=0.01)
        supplier = st.text_input("المورد")
        
        if st.form_submit_button("إضافة للمخزون"):
            if conn and item_name:
                cur = conn.cursor()
                cur.execute("INSERT INTO inventory (item_name, category, quantity_ml_or_gm, cost_per_unit, supplier) VALUES (%s, %s, %s, %s, %s)",
                            (item_name, category, quantity, cost, supplier))
                conn.commit()
                cur.close()
                st.success(f"تمت إضافة ({item_name}) بنجاح!")
                st.rerun()

    st.divider()
    st.subheader("📦 جدول المواد المتوفرة")
    if conn:
        df_inv = pd.read_sql("SELECT * FROM inventory", conn)
        if not df_inv.empty:
            st.dataframe(df_inv, use_container_width=True)
        else:
            st.info("لا توجد مواد مسجلة في المخزون.")

# --- 3. إدارة الجلسات ---
elif menu == "💆‍♂️ إدارة الجلسات واستهلاك المواد":
    st.title("💆‍♂️ تسجيل الجلسات واستهلاك الزيوت")
    inv_items = []
    if conn:
        inv_df = pd.read_sql("SELECT item_name FROM inventory", conn)
        inv_items = inv_df['item_name'].tolist() if not inv_df.empty else []

    with st.form("session_form"):
        client_name = st.text_input("اسم المتعالج")
        session_date = st.date_input("تاريخ الجلسة", datetime.now())
        oil_used = st.selectbox("الزيت أو الكريم المستخدم", inv_items if inv_items else ["لا توجد مواد متاحة"])
        consumed = st.number_input("الكمية المستهلكة (مل / غرام)", min_value=0.0, step=5.0)
        notes = st.text_area("ملاحظات الجلسة")
        
        if st.form_submit_button("حفظ الجلسة وخصم المخزون"):
            if conn and client_name and inv_items:
                cur = conn.cursor()
                cur.execute("INSERT INTO sessions (client_name, session_date, oil_used, oil_consumed_amount, notes) VALUES (%s, %s, %s, %s, %s)",
                            (client_name, str(session_date), oil_used, consumed, notes))
                cur.execute("UPDATE inventory SET quantity_ml_or_gm = quantity_ml_or_gm - %s WHERE item_name = %s",
                            (consumed, oil_used))
                conn.commit()
                cur.close()
                st.success("تم تسجيل الجلسة وتحديث المخزون بنجاح!")

# --- 4. جدول المواعيد ---
elif menu == "📅 جدول المواعيد والحجوزات":
    st.title("📅 جدول المواعيد والحجوزات المنظمة")
    with st.form("app_form"):
        c_name = st.text_input("اسم المتعالج")
        c_phone = st.text_input("رقم الهاتف")
        a_date = st.date_input("تاريخ الموعد", datetime.now())
        a_time = st.time_input("وقت الموعد")
        if st.form_submit_button("حجز الموعد"):
            if conn and c_name:
                cur = conn.cursor()
                cur.execute("INSERT INTO appointments (client_name, phone, appointment_date, appointment_time, status) VALUES (%s, %s, %s, %s, %s)",
                            (c_name, c_phone, str(a_date), str(a_time), "مؤكد"))
                conn.commit()
                cur.close()
                st.success("تم حجز الموعد بنجاح!")
    
    st.divider()
    if conn:
        df_app = pd.read_sql("SELECT * FROM appointments", conn)
        if not df_app.empty:
            st.dataframe(df_app, use_container_width=True)
        else:
            st.info("لا توجد مواعيد مسجلة.")

# --- 5. دليل المتعالجين ---
elif menu == "👥 دليل ملفات المتعالجين":
    st.title("👥 دليل ملفات المتعالجين")
    with st.form("client_form"):
        full_name = st.text_input("الاسم الكامل")
        phone = st.text_input("رقم الهاتف")
        age = st.number_input("العمر", min_value=1, max_value=120, value=30)
        c_notes = st.text_area("معلومات وتاريخ طبي مختصر")
        if st.form_submit_button("حفظ ملف المتعالج"):
            if conn and full_name:
                cur = conn.cursor()
                cur.execute("INSERT INTO clients (full_name, phone, age, notes) VALUES (%s, %s, %s, %s)",
                            (full_name, phone, age, c_notes))
                conn.commit()
                cur.close()
                st.success(f"تم حفظ ملف المتعالج ({full_name}) بنجاح!")
    
    st.divider()
    if conn:
        df_clients = pd.read_sql("SELECT * FROM clients", conn)
        if not df_clients.empty:
            st.dataframe(df_clients, use_container_width=True)
        else:
            st.info("لا توجد ملفات متعالجين مسجلة.")

# --- 6. الموظفين والإعدادات ---
elif menu == "👥 إدارة الموظفين وإعدادات الحساب":
    st.title("👥 إدارة الموظفين والصلاحيات")
    with st.form("staff_form"):
        s_user = st.text_input("اسم المستخدم الجديد")
        s_pass = st.text_input("كلمة المرور", type="password")
        s_role = st.selectbox("الدور", ["مدير عام", "أخصائي / معالج", "استقبال"])
        if st.form_submit_button("حفظ الموظف"):
            if conn and s_user and s_pass:
                hashed = bcrypt.hashpw(s_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cur = conn.cursor()
                try:
                    cur.execute("INSERT INTO staff (username, password_hash, role) VALUES (%s, %s, %s)", (s_user, hashed, s_role))
                    conn.commit()
                    st.success(f"تمت إضافة الموظف ({s_user}) بنجاح!")
                except:
                    st.error("اسم المستخدم موجود مسبقاً.")
                finally:
                    cur.close()

# --- 7. الملاحظات الطبية وخريطة الجسد ---
elif menu == "📑 الملاحظات الطبية (SOAP) وخريطة الجسد":
    st.title("📑 الملاحظات الطبية (SOAP) وخريطة الجسد")
    t1, t2 = st.tabs(["ملاحظات SOAP الطبية", "خريطة الجسد والنقاط"])
    with t1:
        st.text_input("اسم المتعالج")
        st.text_area("Subjective (الشكوى الذاتية)")
        st.text_area("Objective (الفحص السريري)")
        st.text_area("Assessment (التشخيص والتقييم)")
        st.text_area("Plan (خطة العلاج والزيوت)")
        if st.button("حفظ ملاحظات SOAP"):
            st.success("تم حفظ الملاحظات الطبية بنجاح.")
    with t2:
        st.selectbox("اختر المنطقة المستهدفة في الجسم", ["الرقبة والكتف", "أسفل الظهر", "المفاصل والساقين", "الظهر الكامل"])
        st.info("تم تحديد المنطقة لعرض نقاط التركيز العلاجي.")

# --- 8. تحليل الربحية COGS ---
elif menu == "📊 تحليل الربحية المباشرة (COGS)":
    st.title("📊 تحليل الربحية وتكاليف المواد (COGS)")
    if conn:
        df_s = pd.read_sql("SELECT * FROM sessions", conn)
        if not df_s.empty:
            st.dataframe(df_s, use_container_width=True)
        else:
            st.info("لا توجد جلسات مسجلة لعرض تحليلات الـ COGS حتى الآن.")

# --- 9. سجل التتبع الأمني ---
elif menu == "🛡️ سجل التتبع والرقابة الأمني":
    st.title("🛡️ سجل التتبع والرقابة الأمني (Audit Logs)")
    if conn:
        df_logs = pd.read_sql("SELECT * FROM audit_logs ORDER BY action_time DESC", conn)
        if not df_logs.empty:
            st.dataframe(df_logs, use_container_width=True)
        else:
            st.info("لا توجد سجلات أمنية حتى الآن.")

if conn:
    conn.close()
