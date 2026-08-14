# app/i18n.py
# Save as UTF-8

DEFAULT_LANG = "fa"
SUPPORTED_LANGS = {"fa", "en", "hy"}

TRANSLATIONS = {
    "fa": {
        "app_name": "Smart Weighbridge",

        # Login
        "login": "ورود",
        "login_subtitle": "سیستم مدیریت باسکول",
        "username": "نام کاربری",
        "password": "رمز عبور",
        "submit_login": "ورود",
        "login_error": "نام کاربری یا رمز عبور اشتباه است.",

        # Nav
        "dashboard": "داشبورد",
        "weigh": "ثبت وزن",
        "records": "سوابق",
        "logout": "خروج",

        # Dashboard
        "welcome": "خوش آمدید",
        "new_weighment": "ثبت وزن جدید",
        "records_count": "تعداد ثبت‌ها",
        "total_weight": "مجموع وزن",
        "scale": "باسکول",
        "stable": "پایدار",
        "waiting": "ناپایدار",
        "latest_weighments": "آخرین وزن‌کشی‌ها",

        # Common table/fields
        "ticket": "قبض",
        "plate": "پلاک",
        "weight": "وزن",
        "date": "تاریخ",
        "status": "وضعیت",
        "saved": "ذخیره شد",

        # Detail (ticket page)
        "weighment_details": "جزئیات وزن‌کشی",
        "print": "چاپ",
        "operator": "اپراتور",
        "datetime": "تاریخ و ساعت",
        "no_photo": "بدون عکس",

        # Weigh page
        "weigh_truck_title": "ثبت وزن کامیون",
        "weigh_subtitle": "اطلاعات را بررسی و ثبت کنید.",
        "current_scale_weight": "وزن فعلی باسکول",
        "truck_plate": "پلاک کامیون",
        "weight_kg": "وزن (کیلوگرم)",
        "truck_photo": "عکس کامیون",
        "hint_camera": "در گوشی، با انتخاب این قسمت دوربین باز می‌شود.",
        "submit_weigh": "ثبت وزن و عکس",

        # NEW (Weigh page - extra UI strings)
        "plate_placeholder": "مثلاً 12A345",
        "copy_scale_weight": "کپی وزن باسکول",
        "copy_scale_weight_title": "کپی وزن باسکول داخل فیلد وزن",
        "clear_form": "پاک کردن",
        "clear_form_title": "پاک کردن فرم",
        "live_on": "LIVE: ON",
        "live_off": "LIVE: OFF",

        # Records page
        "records_title": "سوابق",
        "records_subtitle": "جستجو و مشاهده همه ثبت‌ها",
        "search": "جستجو",
        "search_placeholder": "پلاک یا شماره قبض...",
        "clear": "پاک کردن",
        "no_results": "موردی پیدا نشد.",

        # Delete
        "actions": "عملیات",
        "delete": "حذف",
        "confirm_delete": "آیا از حذف این قبض مطمئن هستید؟",
    },

    "en": {
        "app_name": "Smart Weighbridge",

        "login": "Login",
        "login_subtitle": "Weighbridge management system",
        "username": "Username",
        "password": "Password",
        "submit_login": "Sign in",
        "login_error": "Invalid username or password.",

        "dashboard": "Dashboard",
        "weigh": "Weigh",
        "records": "Records",
        "logout": "Logout",

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

        "weighment_details": "Weighment details",
        "print": "Print",
        "operator": "Operator",
        "datetime": "Date & time",
        "no_photo": "No photo",

        "weigh_truck_title": "Truck weigh-in",
        "weigh_subtitle": "Review and submit the information.",
        "current_scale_weight": "Current scale weight",
        "truck_plate": "Truck plate",
        "weight_kg": "Weight (kg)",
        "truck_photo": "Truck photo",
        "hint_camera": "On mobile, selecting this will open the camera.",
        "submit_weigh": "Submit weight & photo",

        # NEW (Weigh page - extra UI strings)
        "plate_placeholder": "e.g. 12A345",
        "copy_scale_weight": "Copy scale weight",
        "copy_scale_weight_title": "Copy live scale weight into the weight field",
        "clear_form": "Clear",
        "clear_form_title": "Clear the form",
        "live_on": "LIVE: ON",
        "live_off": "LIVE: OFF",

        "records_title": "Records",
        "records_subtitle": "Search and view all weighments",
        "search": "Search",
        "search_placeholder": "Plate or ticket number...",
        "clear": "Clear",
        "no_results": "No results found.",

        "actions": "Actions",
        "delete": "Delete",
        "confirm_delete": "Are you sure you want to delete this ticket?",
    },

    "hy": {
        "app_name": "Խելացի Կշռակայան",

        "login": "Մուտք",
        "login_subtitle": "Կշռակայանի կառավարման համակարգ",
        "username": "Օգտանուն",
        "password": "Գաղտնաբառ",
        "submit_login": "Մուտք գործել",
        "login_error": "Սխալ օգտանուն կամ գաղտնաբառ։",

        "dashboard": "Վահանակ",
        "weigh": "Կշռում",
        "records": "Գրառումներ",
        "logout": "Ելք",

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

        "weighment_details": "Կշռման մանրամասներ",
        "print": "Տպել",
        "operator": "Օպերատոր",
        "datetime": "Ամսաթիվ և ժամ",
        "no_photo": "Առանց լուսանկարի",

        "weigh_truck_title": "Բեռնատարի կշռում",
        "weigh_subtitle": "Ստուգեք տվյալները և ուղարկեք։",
        "current_scale_weight": "Ընթացիկ կշիռը",
        "truck_plate": "Մեքենայի համար",
        "weight_kg": "Քաշ (կգ)",
        "truck_photo": "Մեքենայի լուսանկար",
        "hint_camera": "Հեռախոսով ընտրելիս տեսախցիկը կբացվի։",
        "submit_weigh": "Ուղարկել",

        # NEW (Weigh page - extra UI strings)
        "plate_placeholder": "օր. 12A345",
        "copy_scale_weight": "Պատճենել կշեռքի քաշը",
        "copy_scale_weight_title": "Պատճենել ընթացիկ քաշը քաշի դաշտում",
        "clear_form": "Մաքրել",
        "clear_form_title": "Մաքրել ձևը",
        "live_on": "LIVE: ON",
        "live_off": "LIVE: OFF",

        "records_title": "Գրառումներ",
        "records_subtitle": "Որոնել և դիտել բոլոր կշռումները",
        "search": "Որոնում",
        "search_placeholder": "Համարանիշ կամ տոմս...",
        "clear": "Մաքրել",
        "no_results": "Արդյունք չկա։",

        "actions": "Գործողություններ",
        "delete": "Ջնջել",
        "confirm_delete": "Վստա՞հ եք, որ ցանկանում եք ջնջել այս տոմսը։",
    },
}

RTL_LANGS = {"fa"}

def translate(lang: str, key: str) -> str:
    lang = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG

    if key in TRANSLATIONS.get(lang, {}):
        return TRANSLATIONS[lang][key]

    if key in TRANSLATIONS.get(DEFAULT_LANG, {}):
        return TRANSLATIONS[DEFAULT_LANG][key]

    return key

def get_dir(lang: str) -> str:
    lang = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG
    return "rtl" if lang in RTL_LANGS else "ltr"
