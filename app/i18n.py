TRANSLATIONS = {
    "fa": {
        "app_name": "Smart Weighbridge",
        "login": "ورود",
        "login_subtitle": "سیستم مدیریت باسکول",
        "username": "نام کاربری",
        "password": "رمز عبور",
        "submit_login": "ورود",

        "dashboard": "داشبورد",
        "weigh": "ثبت وزن",
        "records": "سوابق",
        "logout": "خروج",

        # (اختیاری برای بعد)
        "new_weighment": "ثبت وزن جدید",
    },

    "en": {
        "app_name": "Smart Weighbridge",
        "login": "Login",
        "login_subtitle": "Weighbridge management system",
        "username": "Username",
        "password": "Password",
        "submit_login": "Sign in",

        "dashboard": "Dashboard",
        "weigh": "Weigh",
        "records": "Records",
        "logout": "Logout",

        # (optional)
        "new_weighment": "New weighment",
    },

    "hy": {
        "app_name": "Խելացի Կշռակայան",
        "login": "Մուտք",
        "login_subtitle": "Կշռակայանի կառավարման համակարգ",
        "username": "Օգտանուն",
        "password": "Գաղտնաբառ",
        "submit_login": "Մուտք գործել",

        "dashboard": "Վահանակ",
        "weigh": "Կշռում",
        "records": "Գրառումներ",
        "logout": "Ելք",

        # (optional)
        "new_weighment": "Նոր կշռում",
    },
}

RTL_LANGS = {"fa"}

def translate(lang: str, key: str) -> str:
    lang_map = TRANSLATIONS.get(lang) or TRANSLATIONS["fa"]
    return lang_map.get(key, key)

def get_dir(lang: str) -> str:
    return "rtl" if lang in RTL_LANGS else "ltr"
