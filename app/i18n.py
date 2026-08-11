# app/i18n.py

TRANSLATIONS = {
    "fa": {
        "app_name": "Smart Weighbridge",

        "login": "ورود",
        "login_subtitle": "سیستم مدیریت باسکول",
        "username": "نام کاربری",
        "password": "رمز عبور",
        "submit_login": "ورود",

        "dashboard": "داشبورد",
        "welcome": "خوش آمدید",
        "new_weighment": "ثبت وزن جدید",
        "records_count": "تعداد ثبت‌ها",
        "total_weight": "مجموع وزن",
        "scale": "باسکول",
        "stable": "پایدار",
        "waiting": "ناپایدار",
        "latest_weighments": "آخرین وزن‌کشی‌ها",

        "ticket": "قبض",
        "plate": "پلاک",
        "weight": "وزن",
        "date": "تاریخ",
        "status": "وضعیت",
        "saved": "ذخیره شد",

        "weigh": "ثبت وزن",
        "records": "سوابق",
        "logout": "خروج",
    },

    "en": {
        "app_name": "Smart Weighbridge",

        "login": "Login",
        "login_subtitle": "Weighbridge management system",
        "username": "Username",
        "password": "Password",
        "submit_login": "Sign in",

        "dashboard": "Dashboard",
        "welcome": "Welcome",
        "new_weighment": "New weighment",
        "records_count": "Records count",
        "total_weight": "Total weight",
        "scale": "Scale",
        "stable": "Stable",
        "waiting": "Waiting",
        "latest_weighments": "Latest weighments",

        "ticket": "Ticket",
        "plate": "Plate",
        "weight": "Weight",
        "date": "Date",
        "status": "Status",
        "saved": "Saved",

        "weigh": "Weigh",
        "records": "Records",
        "logout": "Logout",
    },

    "hy": {
        "app_name": "Խելացի Կշռակայան",

        "login": "Մուտք",
        "login_subtitle": "Կշռակայանի կառավարման համակարգ",
        "username": "Օգտանուն",
        "password": "Գաղտնաբառ",
        "submit_login": "Մուտք գործել",

        "dashboard": "Վահանակ",
        "welcome": "Բարի գալուստ",
        "new_weighment": "Նոր կշռում",
        "records_count": "Գրառումների քանակը",
        "total_weight": "Ընդհանուր քաշ",
        "scale": "Կշեռք",
        "stable": "Կայուն",
        "waiting": "Սպասում",
        "latest_weighments": "Վերջին կշռումները",

        "ticket": "Տոմս",
        "plate": "Համարանիշ",
        "weight": "Քաշ",
        "date": "Ամսաթիվ",
        "status": "Կարգավիճակ",
        "saved": "Պահպանված է",

        "weigh": "Կշռում",
        "records": "Գրառումներ",
        "logout": "Ելք",
    },
}

RTL_LANGS = {"fa"}

def translate(lang: str, key: str) -> str:
    lang_map = TRANSLATIONS.get(lang) or TRANSLATIONS["fa"]
    return lang_map.get(key, key)

def get_dir(lang: str) -> str:
    return "rtl" if lang in RTL_LANGS else "ltr"