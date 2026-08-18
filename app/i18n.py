# app/i18n.py
# Save as UTF-8

DEFAULT_LANG = "fa"
SUPPORTED_LANGS = {"fa", "en", "hy"}


TRANSLATIONS = {

    # ========================================================
    # فارسی
    # ========================================================

    "fa": {

        "app_name": "Smart Weighbridge",

        # Login
        "login": "ورود",
        "login_subtitle": "سیستم مدیریت باسکول",
        "username": "نام کاربری",
        "password": "رمز عبور",
        "submit_login": "ورود",
        "login_error": "نام کاربری یا رمز عبور اشتباه است.",

        # Navigation
        "dashboard": "داشبورد",
        "weigh": "ثبت وزن",
        "records": "سوابق",
        "device": "دستگاه",
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

        # Common
        "ticket": "قبض",
        "plate": "پلاک",
        "weight": "وزن",
        "date": "تاریخ",
        "status": "وضعیت",
        "saved": "ذخیره شد",
        "completed": "تکمیل شده",

        # Detail
        "weighment_details": "جزئیات وزن‌کشی",
        "print": "چاپ",
        "operator": "اپراتور",
        "datetime": "تاریخ و ساعت",
        "no_photo": "بدون عکس",

        # ====================================================
        # Weigh page
        # ====================================================

        "weigh_truck_title": "ثبت وزن",
        "weigh_subtitle": "اطلاعات را بررسی و ثبت کنید.",

        "current_scale_weight": "وزن فعلی باسکول",

        "truck_plate": "پلاک ماشین",

        "plate_placeholder": "مثلاً 12ع365-11",

        "plate_letter": "حرف",

        "plate_incomplete":
            "لطفاً پلاک ماشین را کامل وارد کنید.",

        "weight_kg": "وزن (کیلوگرم)",

        "truck_photo": "عکس‌ها",

        "hint_camera":
            "در گوشی، با انتخاب این قسمت دوربین باز می‌شود.",

        # ====================================================
        # Single / Double Weigh
        # ====================================================

        "weighing_mode":
            "نوع توزین",

        "single_weigh":
            "تک توزین",

        "double_weigh":
            "دو توزین",

        "single_weigh_help":
            "ثبت یک وزن و تکمیل قبض",

        "double_weigh_help":
            "ثبت وزن اول و تکمیل قبض پس از وزن دوم",

        "submit_single_weigh":
            "ثبت تک توزین",

        "submit_first_weight":
            "ثبت وزن اول",

        "register_second_weight":
            "ثبت وزن دوم",

        "first_weight":
            "وزن اول",

        "second_weight":
            "وزن دوم",

        "net_weight":
            "وزن خالص",

        "waiting_second":
            "منتظر وزن دوم",

        "waiting_second_title":
            "خودروهای منتظر وزن دوم",

        "waiting_second_help":
            "پس از بازگشت خودرو، وزن زنده باسکول را به عنوان وزن دوم ثبت کنید.",

        "confirm_second_weigh":
            "وزن فعلی باسکول به عنوان وزن دوم ثبت شود؟",

        "no_waiting_second":
            "خودرویی در انتظار وزن دوم نیست.",

        # UI
        "copy_scale_weight":
            "کپی وزن باسکول",

        "copy_scale_weight_title":
            "کپی وزن باسکول داخل فیلد وزن",

        "clear_form":
            "پاک کردن",

        "clear_form_title":
            "پاک کردن فرم",

        "live_on":
            "LIVE: ON",

        "live_off":
            "LIVE: OFF",

        # ====================================================
        # Vehicle
        # ====================================================

        "vehicle_type":
            "نوع خودرو",

        "vehicle_type_placeholder":
            "مثلاً کامیون، تریلی، سواری",

        # قدیمی - برای سازگاری
        "vehicle_type_select":
            "انتخاب کنید...",

        "vehicle_type_truck":
            "کامیون",

        "vehicle_type_trailer":
            "تریلی",

        "vehicle_type_flatbed":
            "کفی",

        "vehicle_type_dump":
            "کمپرسی",

        "vehicle_type_other":
            "سایر",

        # ====================================================
        # Driver
        # ====================================================

        "driver_name":
            "نام راننده",

        "driver_name_placeholder":
            "مثلاً علی احمدی",

        "driver_phone":
            "شماره تماس راننده",

        "driver_phone_placeholder":
            "مثلاً 0912xxxxxxx",

        # ====================================================
        # Cargo
        # ====================================================

        "cargo_type":
            "نوع بار / محصول",

        "cargo_type_placeholder":
            "مثلاً سیمان / گندم / شن",

        "cargo_owner":
            "صاحب بار (شرکت/شخص)",

        "cargo_owner_placeholder":
            "نام شرکت یا شخص",

        # ====================================================
        # Route
        # ====================================================

        "origin":
            "مبدأ",

        "origin_placeholder":
            "مثلاً تهران",

        "destination":
            "مقصد",

        "destination_placeholder":
            "مثلاً اصفهان",

        # Documents
        "document_no":
            "شماره بارنامه / حواله / سفارش",

        "document_no_placeholder":
            "مثلاً 12345",

        # Notes
        "notes":
            "توضیحات",

        "notes_placeholder":
            "توضیحات تکمیلی...",

        # Old submit key
        "submit_weigh":
            "ثبت وزن و عکس",

        # ====================================================
        # Device / RS232
        # ====================================================

        "device_title":
            "دستگاه / RS232",

        "device_subtitle":
            "تنظیمات اتصال اندیکاتور و خواندن وزن",

        "device_enabled":
            "وضعیت",

        "device_off":
            "خاموش",

        "device_on":
            "روشن",

        "device_port":
            "پورت سریال (COM)",

        "device_autodetect":
            "تشخیص خودکار",

        "device_baud":
            "نرخ Baud",

        "device_indicator":
            "نوع اندیکاتور",

        "device_stable_tol":
            "تلورانس پایداری",

        "device_stable_seconds":
            "زمان پایداری (ثانیه)",

        "device_send_every":
            "ارسال هر (ثانیه)",

        "device_scale_id":
            "شناسه باسکول",

        "device_save":
            "ذخیره",

        "device_start":
            "شروع",

        "device_stop":
            "توقف",

        "device_running":
            "در حال اجرا",

        "device_last_weight":
            "آخرین وزن",

        "device_last_raw":
            "آخرین RAW",

        "device_raw_lines":
            "خطوط RAW",

        # ====================================================
        # Records
        # ====================================================

        "records_title":
            "سوابق",

        "records_subtitle":
            "جستجو و مشاهده همه ثبت‌ها",

        "search":
            "جستجو",

        "search_placeholder":
            "پلاک، قبض، راننده، بار و...",

        "clear":
            "پاک کردن",

        "no_results":
            "موردی پیدا نشد.",

        # Delete
        "actions":
            "عملیات",

        "delete":
            "حذف",

        "confirm_delete":
            "آیا از حذف این قبض مطمئن هستید؟",
    },


    # ========================================================
    # English
    # ========================================================

    "en": {

        "app_name": "Smart Weighbridge",

        # Login
        "login": "Login",
        "login_subtitle": "Weighbridge management system",
        "username": "Username",
        "password": "Password",
        "submit_login": "Sign in",
        "login_error": "Invalid username or password.",

        # Navigation
        "dashboard": "Dashboard",
        "weigh": "Weigh",
        "records": "Records",
        "device": "Device",
        "logout": "Logout",

        # Dashboard
        "welcome": "Welcome",
        "new_weighment": "New weighment",
        "records_count": "Records count",
        "total_weight": "Total weight",
        "scale": "Scale",
        "stable": "Stable",
        "waiting": "Unstable",
        "latest_weighments": "Latest weighments",

        # Common
        "ticket": "Ticket",
        "plate": "Plate",
        "weight": "Weight",
        "date": "Date",
        "status": "Status",
        "saved": "Saved",
        "completed": "Completed",

        # Detail
        "weighment_details": "Weighment details",
        "print": "Print",
        "operator": "Operator",
        "datetime": "Date & time",
        "no_photo": "No photo",

        # Weigh page
        "weigh_truck_title": "Weigh-in",
        "weigh_subtitle":
            "Review and submit the information.",

        "current_scale_weight":
            "Current scale weight",

        "truck_plate":
            "Vehicle plate",

        "plate_placeholder":
            "e.g. 12A365-11",

        "plate_letter":
            "Letter",

        "plate_incomplete":
            "Please enter the complete vehicle plate.",

        "weight_kg":
            "Weight (kg)",

        "truck_photo":
            "Photos",

        "hint_camera":
            "On mobile, selecting this will open the camera.",

        # ====================================================
        # Single / Double
        # ====================================================

        "weighing_mode":
            "Weighing mode",

        "single_weigh":
            "Single weigh",

        "double_weigh":
            "Double weigh",

        "single_weigh_help":
            "Record one weight and complete the ticket",

        "double_weigh_help":
            "Record the first weight and complete the ticket after the second weigh",

        "submit_single_weigh":
            "Save single weigh",

        "submit_first_weight":
            "Save first weight",

        "register_second_weight":
            "Record second weight",

        "first_weight":
            "First weight",

        "second_weight":
            "Second weight",

        "net_weight":
            "Net weight",

        "waiting_second":
            "Waiting for second weight",

        "waiting_second_title":
            "Vehicles waiting for second weight",

        "waiting_second_help":
            "When the vehicle returns, record the live scale weight as the second weight.",

        "confirm_second_weigh":
            "Record the current scale weight as the second weight?",

        "no_waiting_second":
            "No vehicles are waiting for a second weight.",

        # UI
        "copy_scale_weight":
            "Copy scale weight",

        "copy_scale_weight_title":
            "Copy live scale weight into the weight field",

        "clear_form":
            "Clear",

        "clear_form_title":
            "Clear the form",

        "live_on":
            "LIVE: ON",

        "live_off":
            "LIVE: OFF",

        # Vehicle
        "vehicle_type":
            "Vehicle type",

        "vehicle_type_placeholder":
            "e.g. Truck, Trailer, Car",

        "vehicle_type_select":
            "Select...",

        "vehicle_type_truck":
            "Truck",

        "vehicle_type_trailer":
            "Trailer",

        "vehicle_type_flatbed":
            "Flatbed",

        "vehicle_type_dump":
            "Dump truck",

        "vehicle_type_other":
            "Other",

        # Driver
        "driver_name":
            "Driver name",

        "driver_name_placeholder":
            "e.g. Ali Ahmadi",

        "driver_phone":
            "Driver phone",

        "driver_phone_placeholder":
            "e.g. +98...",

        # Cargo
        "cargo_type":
            "Cargo / product",

        "cargo_type_placeholder":
            "e.g. Cement / Wheat",

        "cargo_owner":
            "Cargo owner (Company/Person)",

        "cargo_owner_placeholder":
            "Company or person name",

        # Route
        "origin":
            "Origin",

        "origin_placeholder":
            "e.g. Tehran",

        "destination":
            "Destination",

        "destination_placeholder":
            "e.g. Isfahan",

        # Documents
        "document_no":
            "Waybill / Order No.",

        "document_no_placeholder":
            "e.g. 12345",

        # Notes
        "notes":
            "Notes",

        "notes_placeholder":
            "Additional notes...",

        "submit_weigh":
            "Submit weight & photo",

        # Device
        "device_title":
            "Device / RS232",

        "device_subtitle":
            "Indicator connection settings & live reading",

        "device_enabled":
            "Status",

        "device_off":
            "Off",

        "device_on":
            "On",

        "device_port":
            "Serial port (COM)",

        "device_autodetect":
            "Auto Detect",

        "device_baud":
            "Baud rate",

        "device_indicator":
            "Indicator type",

        "device_stable_tol":
            "Stable tolerance",

        "device_stable_seconds":
            "Stable seconds",

        "device_send_every":
            "Send every (sec)",

        "device_scale_id":
            "Scale ID",

        "device_save":
            "Save",

        "device_start":
            "Start",

        "device_stop":
            "Stop",

        "device_running":
            "Running",

        "device_last_weight":
            "Last weight",

        "device_last_raw":
            "Last RAW",

        "device_raw_lines":
            "RAW lines",

        # Records
        "records_title":
            "Records",

        "records_subtitle":
            "Search and view all weighments",

        "search":
            "Search",

        "search_placeholder":
            "Plate, ticket, driver, cargo...",

        "clear":
            "Clear",

        "no_results":
            "No results found.",

        # Delete
        "actions":
            "Actions",

        "delete":
            "Delete",

        "confirm_delete":
            "Are you sure you want to delete this ticket?",
    },


    # ========================================================
    # Armenian
    # ========================================================

    "hy": {

        "app_name": "Խելացի Կշռակայան",

        # Login
        "login": "Մուտք",
        "login_subtitle": "Կշռակայանի կառավարման համակարգ",
        "username": "Օգտանուն",
        "password": "Գաղտնաբառ",
        "submit_login": "Մուտք գործել",
        "login_error": "Սխալ օգտանուն կամ գաղտնաբառ։",

        # Navigation
        "dashboard": "Վահանակ",
        "weigh": "Կշռում",
        "records": "Գրառումներ",
        "device": "Սարք",
        "logout": "Ելք",

        # Dashboard
        "welcome": "Բարի գալուստ",
        "new_weighment": "Նոր կշռում",
        "records_count": "Գրառումների քանակը",
        "total_weight": "Ընդհանուր քաշ",
        "scale": "Կշեռք",
        "stable": "Կայուն",
        "waiting": "Անկայուն",
        "latest_weighments": "Վերջին կշռումները",

        # Common
        "ticket": "Տոմս",
        "plate": "Համարանիշ",
        "weight": "Քաշ",
        "date": "Ամսաթիվ",
        "status": "Կարգավիճակ",
        "saved": "Պահպանված է",
        "completed": "Ավարտված",

        # Detail
        "weighment_details": "Կշռման մանրամասներ",
        "print": "Տպել",
        "operator": "Օպերատոր",
        "datetime": "Ամսաթիվ և ժամ",
        "no_photo": "Առանց լուսանկարի",

        # Weigh
        "weigh_truck_title": "Կշռում",

        "weigh_subtitle":
            "Ստուգեք տվյալները և գրանցեք։",

        "current_scale_weight":
            "Ընթացիկ կշիռը",

        "truck_plate":
            "Մեքենայի համարանիշ",

        "plate_placeholder":
            "օր. 12A365-11",

        "plate_letter":
            "Տառ",

        "plate_incomplete":
            "Խնդրում ենք ամբողջությամբ մուտքագրել մեքենայի համարանիշը։",

        "weight_kg":
            "Քաշ (կգ)",

        "truck_photo":
            "Լուսանկարներ",

        "hint_camera":
            "Հեռախոսով ընտրելիս տեսախցիկը կբացվի։",

        # ====================================================
        # Single / Double
        # ====================================================

        "weighing_mode":
            "Կշռման տեսակ",

        "single_weigh":
            "Մեկ կշռում",

        "double_weigh":
            "Կրկնակի կշռում",

        "single_weigh_help":
            "Գրանցել մեկ քաշ և ավարտել կտրոնը",

        "double_weigh_help":
            "Գրանցել առաջին քաշը և ավարտել երկրորդ կշռումից հետո",

        "submit_single_weigh":
            "Գրանցել մեկ կշռումը",

        "submit_first_weight":
            "Գրանցել առաջին քաշը",

        "register_second_weight":
            "Գրանցել երկրորդ քաշը",

        "first_weight":
            "Առաջին քաշ",

        "second_weight":
            "Երկրորդ քաշ",

        "net_weight":
            "Զուտ քաշ",

        "waiting_second":
            "Սպասում է երկրորդ քաշին",

        "waiting_second_title":
            "Երկրորդ կշռմանը սպասող մեքենաներ",

        "waiting_second_help":
            "Մեքենայի վերադարձից հետո գրանցեք ընթացիկ քաշը որպես երկրորդ քաշ։",

        "confirm_second_weigh":
            "Գրանցե՞լ ընթացիկ քաշը որպես երկրորդ քաշ։",

        "no_waiting_second":
            "Երկրորդ կշռմանը սպասող մեքենա չկա։",

        # UI
        "copy_scale_weight":
            "Պատճենել կշեռքի քաշը",

        "copy_scale_weight_title":
            "Պատճենել ընթացիկ քաշը",

        "clear_form":
            "Մաքրել",

        "clear_form_title":
            "Մաքրել ձևը",

        "live_on":
            "LIVE: ON",

        "live_off":
            "LIVE: OFF",

        # Vehicle
        "vehicle_type":
            "Տրանսպորտի տեսակ",

        "vehicle_type_placeholder":
            "օր. բեռնատար, կցորդ, մեքենա",

        "vehicle_type_select":
            "Ընտրել...",

        "vehicle_type_truck":
            "Բեռնատար",

        "vehicle_type_trailer":
            "Կցորդ",

        "vehicle_type_flatbed":
            "Հարթակ",

        "vehicle_type_dump":
            "Ինքնաթափ",

        "vehicle_type_other":
            "Այլ",

        # Driver
        "driver_name":
            "Վարորդի անունը",

        "driver_name_placeholder":
            "օր. ...",

        "driver_phone":
            "Վարորդի հեռախոս",

        "driver_phone_placeholder":
            "օր. +374...",

        # Cargo
        "cargo_type":
            "Բեռ / Ապրանք",

        "cargo_type_placeholder":
            "օր. ցորեն / ցեմենտ",

        "cargo_owner":
            "Բեռի սեփականատեր",

        "cargo_owner_placeholder":
            "Ընկերության կամ անձի անուն",

        # Route
        "origin":
            "Մեկնարկ",

        "origin_placeholder":
            "օր. ...",

        "destination":
            "Նպատակակետ",

        "destination_placeholder":
            "օր. ...",

        # Document
        "document_no":
            "Փաստաթուղթ №",

        "document_no_placeholder":
            "օր. 12345",

        # Notes
        "notes":
            "Նշումներ",

        "notes_placeholder":
            "Լրացուցիչ նշումներ...",

        "submit_weigh":
            "Գրանցել քաշը",

        # Device
        "device_title":
            "Սարք / RS232",

        "device_subtitle":
            "Միացման կարգավորումներ և կենդանի ընթերցում",

        "device_enabled":
            "Կարգավիճակ",

        "device_off":
            "Անջատված",

        "device_on":
            "Միացված",

        "device_port":
            "Սերիական պորտ (COM)",

        "device_autodetect":
            "Ավտոմատ գտնել",

        "device_baud":
            "Baud արագություն",

        "device_indicator":
            "Ցուցիչի տեսակ",

        "device_stable_tol":
            "Կայունության շեմ",

        "device_stable_seconds":
            "Կայունության ժամանակ (վրկ)",

        "device_send_every":
            "Ուղարկել ամեն (վրկ)",

        "device_scale_id":
            "Կշեռքի ID",

        "device_save":
            "Պահպանել",

        "device_start":
            "Սկսել",

        "device_stop":
            "Կանգնեցնել",

        "device_running":
            "Աշխատում է",

        "device_last_weight":
            "Վերջին քաշ",

        "device_last_raw":
            "Վերջին RAW",

        "device_raw_lines":
            "RAW տողեր",

        # Records
        "records_title":
            "Գրառումներ",

        "records_subtitle":
            "Որոնել և դիտել բոլոր կշռումները",

        "search":
            "Որոնում",

        "search_placeholder":
            "Համարանիշ, տոմս, վարորդ, բեռ...",

        "clear":
            "Մաքրել",

        "no_results":
            "Արդյունք չկա։",

        # Delete
        "actions":
            "Գործողություններ",

        "delete":
            "Ջնջել",

        "confirm_delete":
            "Վստա՞հ եք, որ ցանկանում եք ջնջել այս տոմսը։",
    },
}


# ============================================================
# TEXT DIRECTION
# ============================================================

RTL_LANGS = {
    "fa",
}


# ============================================================
# TRANSLATE
# ============================================================

def translate(
    lang: str,
    key: str,
) -> str:

    lang = (
        lang
        if lang in SUPPORTED_LANGS
        else DEFAULT_LANG
    )

    if key in TRANSLATIONS.get(
        lang,
        {},
    ):
        return TRANSLATIONS[
            lang
        ][
            key
        ]

    if key in TRANSLATIONS.get(
        DEFAULT_LANG,
        {},
    ):
        return TRANSLATIONS[
            DEFAULT_LANG
        ][
            key
        ]

    return key


# ============================================================
# DIRECTION
# ============================================================

def get_dir(
    lang: str,
) -> str:

    lang = (
        lang
        if lang in SUPPORTED_LANGS
        else DEFAULT_LANG
    )

    return (
        "rtl"
        if lang in RTL_LANGS
        else "ltr"
    )
