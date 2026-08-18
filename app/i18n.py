# app/i18n.py
# UTF-8

DEFAULT_LANG = "fa"
SUPPORTED_LANGS = {
    "fa",
    "en",
    "hy",
}


TRANSLATIONS = {

    # ========================================================
    # FA
    # ========================================================

    "fa": {

        "app_name":
            "Smart Weighbridge",

        # Login
        "login":
            "ورود",

        "login_subtitle":
            "سیستم مدیریت باسکول",

        "username":
            "نام کاربری",

        "password":
            "رمز عبور",

        "submit_login":
            "ورود",

        "login_error":
            "نام کاربری یا رمز عبور اشتباه است.",

        # Nav
        "dashboard":
            "داشبورد",

        "weigh":
            "ثبت وزن",

        "records":
            "سوابق",

        "vehicle_profiles":
            "تعرفه خودروها",

        "device":
            "دستگاه",

        "logout":
            "خروج",

        # Dashboard
        "welcome":
            "خوش آمدید",

        "new_weighment":
            "ثبت وزن جدید",

        "records_count":
            "تعداد ثبت‌ها",

        "total_weight":
            "مجموع وزن",

        "scale":
            "باسکول",

        "stable":
            "پایدار",

        "waiting":
            "ناپایدار",

        "latest_weighments":
            "آخرین وزن‌کشی‌ها",

        # Common
        "ticket":
            "قبض",

        "plate":
            "پلاک",

        "weight":
            "وزن",

        "date":
            "تاریخ",

        "status":
            "وضعیت",

        "saved":
            "ذخیره شد",

        "completed":
            "تکمیل شده",

        "actions":
            "عملیات",

        "delete":
            "حذف",

        "edit":
            "ویرایش",

        # Detail
        "weighment_details":
            "جزئیات وزن‌کشی",

        "print":
            "چاپ",

        "operator":
            "اپراتور",

        "datetime":
            "تاریخ و ساعت",

        "no_photo":
            "بدون عکس",

        # Weigh
        "weigh_truck_title":
            "ثبت وزن",

        "weigh_subtitle":
            "اطلاعات را بررسی و ثبت کنید.",

        "current_scale_weight":
            "وزن فعلی باسکول",

        "truck_plate":
            "پلاک ماشین",

        "plate_letter":
            "حرف",

        "plate_incomplete":
            "لطفاً پلاک ماشین را کامل وارد کنید.",

        "weight_kg":
            "وزن (کیلوگرم)",

        "truck_photo":
            "عکس‌ها",

        "hint_camera":
            "در گوشی، با انتخاب این قسمت دوربین باز می‌شود.",

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

        # Single / Double
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

        # Vehicle
        "vehicle_type":
            "نوع خودرو",

        "vehicle_type_placeholder":
            "مثلاً سمند، کامیون، تریلی",

        "weighing_fee":
            "هزینه توزین",

        "weighing_fee_placeholder":
            "مبلغ را وارد کنید",

        "vehicle_weight":
            "وزن خودرو",

        "vehicle_weight_placeholder":
            "وزن مرجع خودرو",

        "rial":
            "ریال",

        "vehicle_information":
            "اطلاعات خودرو",

        # Vehicle memory
        "previous_vehicle_profile":
            "اطلاعات قبلی این نوع خودرو",

        "use_previous_values":
            "استفاده از مقادیر قبلی",

        "vehicle_profile_auto_save_note":
            "پس از ثبت، هزینه و وزن واردشده برای این نوع خودرو در حافظه تعرفه‌ها ذخیره یا به‌روزرسانی می‌شود.",

        # Vehicle profile page
        "vehicle_profiles_subtitle":
            "تعریف، ویرایش و حذف هزینه توزین و وزن مرجع انواع خودرو",

        "vehicle_profile_form_title":
            "تعریف تعرفه خودرو",

        "save_vehicle_profile":
            "ذخیره تعرفه",

        "saved_vehicle_profiles":
            "تعرفه‌های ذخیره‌شده",

        "editing_vehicle_profile":
            "در حال ویرایش تعرفه ذخیره‌شده",

        "cancel_edit":
            "لغو ویرایش",

        "last_update":
            "آخرین بروزرسانی",

        "vehicle_profile_note":
            "حذف تعرفه از این صفحه فقط حافظه پیشنهاد را حذف می‌کند و اطلاعات قبض‌ها و سوابق قبلی تغییر نمی‌کند.",

        "confirm_delete_vehicle_profile":
            "این تعرفه خودرو از حافظه پیشنهاد حذف شود؟ سوابق قبلی حذف نخواهند شد.",

        "no_vehicle_profiles":
            "هنوز تعرفه خودرویی تعریف نشده است.",

        # Driver
        "driver_name":
            "نام راننده",

        "driver_name_placeholder":
            "مثلاً علی احمدی",

        "driver_phone":
            "شماره تماس راننده",

        "driver_phone_placeholder":
            "مثلاً 0912xxxxxxx",

        # Cargo
        "cargo_type":
            "نوع بار / محصول",

        "cargo_type_placeholder":
            "مثلاً سیمان / گندم / شن",

        "cargo_owner":
            "صاحب بار (شرکت/شخص)",

        "cargo_owner_placeholder":
            "نام شرکت یا شخص",

        # Route
        "origin":
            "مبدأ",

        "origin_placeholder":
            "مثلاً تهران",

        "destination":
            "مقصد",

        "destination_placeholder":
            "مثلاً اصفهان",

        "document_no":
            "شماره بارنامه / حواله / سفارش",

        "document_no_placeholder":
            "مثلاً 12345",

        "notes":
            "توضیحات",

        "notes_placeholder":
            "توضیحات تکمیلی...",

        # Records
        "records_title":
            "سوابق",

        "records_subtitle":
            "جستجو و مشاهده همه ثبت‌ها",

        "search":
            "جستجو",

        "search_placeholder":
            "پلاک، قبض، خودرو، راننده، بار و...",

        "clear":
            "پاک کردن",

        "no_results":
            "موردی پیدا نشد.",

        "confirm_delete":
            "آیا از حذف این قبض مطمئن هستید؟",

        # Device
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
    },


    # ========================================================
    # EN
    # ========================================================

    "en": {

        "app_name":
            "Smart Weighbridge",

        "login":
            "Login",

        "login_subtitle":
            "Weighbridge management system",

        "username":
            "Username",

        "password":
            "Password",

        "submit_login":
            "Sign in",

        "login_error":
            "Invalid username or password.",

        "dashboard":
            "Dashboard",

        "weigh":
            "Weigh",

        "records":
            "Records",

        "vehicle_profiles":
            "Vehicle tariffs",

        "device":
            "Device",

        "logout":
            "Logout",

        "welcome":
            "Welcome",

        "new_weighment":
            "New weighment",

        "records_count":
            "Records count",

        "total_weight":
            "Total weight",

        "scale":
            "Scale",

        "stable":
            "Stable",

        "waiting":
            "Unstable",

        "latest_weighments":
            "Latest weighments",

        "ticket":
            "Ticket",

        "plate":
            "Plate",

        "weight":
            "Weight",

        "date":
            "Date",

        "status":
            "Status",

        "saved":
            "Saved",

        "completed":
            "Completed",

        "actions":
            "Actions",

        "delete":
            "Delete",

        "edit":
            "Edit",

        "weighment_details":
            "Weighment details",

        "print":
            "Print",

        "operator":
            "Operator",

        "datetime":
            "Date & time",

        "no_photo":
            "No photo",

        "weigh_truck_title":
            "Weigh-in",

        "weigh_subtitle":
            "Review and submit the information.",

        "current_scale_weight":
            "Current scale weight",

        "truck_plate":
            "Vehicle plate",

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

        "weighing_mode":
            "Weighing mode",

        "single_weigh":
            "Single weigh",

        "double_weigh":
            "Double weigh",

        "single_weigh_help":
            "Record one weight and complete the ticket",

        "double_weigh_help":
            "Record the first weight and complete after the second weigh",

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
            "When the vehicle returns, record the live scale weight as its second weight.",

        "confirm_second_weigh":
            "Record the current scale weight as the second weight?",

        "no_waiting_second":
            "No vehicles are waiting for a second weight.",

        "vehicle_type":
            "Vehicle type",

        "vehicle_type_placeholder":
            "e.g. Sedan, Truck, Trailer",

        "weighing_fee":
            "Weighing fee",

        "weighing_fee_placeholder":
            "Enter fee",

        "vehicle_weight":
            "Vehicle weight",

        "vehicle_weight_placeholder":
            "Reference vehicle weight",

        "rial":
            "Rial",

        "vehicle_information":
            "Vehicle information",

        "previous_vehicle_profile":
            "Previous values for this vehicle type",

        "use_previous_values":
            "Use previous values",

        "vehicle_profile_auto_save_note":
            "After saving, the entered fee and vehicle weight will be remembered or updated for this vehicle type.",

        "vehicle_profiles_subtitle":
            "Create, edit and remove weighing fees and reference weights for vehicle types",

        "vehicle_profile_form_title":
            "Vehicle tariff",

        "save_vehicle_profile":
            "Save tariff",

        "saved_vehicle_profiles":
            "Saved vehicle tariffs",

        "editing_vehicle_profile":
            "Editing saved vehicle tariff",

        "cancel_edit":
            "Cancel edit",

        "last_update":
            "Last update",

        "vehicle_profile_note":
            "Deleting a tariff here only removes the saved suggestion. Previous tickets and records remain unchanged.",

        "confirm_delete_vehicle_profile":
            "Delete this vehicle tariff from saved suggestions? Previous records will not be deleted.",

        "no_vehicle_profiles":
            "No vehicle tariffs have been defined yet.",

        "driver_name":
            "Driver name",

        "driver_name_placeholder":
            "e.g. Ali Ahmadi",

        "driver_phone":
            "Driver phone",

        "driver_phone_placeholder":
            "e.g. +98...",

        "cargo_type":
            "Cargo / product",

        "cargo_type_placeholder":
            "e.g. Cement / Wheat",

        "cargo_owner":
            "Cargo owner (Company/Person)",

        "cargo_owner_placeholder":
            "Company or person name",

        "origin":
            "Origin",

        "origin_placeholder":
            "e.g. Tehran",

        "destination":
            "Destination",

        "destination_placeholder":
            "e.g. Isfahan",

        "document_no":
            "Waybill / Order No.",

        "document_no_placeholder":
            "e.g. 12345",

        "notes":
            "Notes",

        "notes_placeholder":
            "Additional notes...",

        "records_title":
            "Records",

        "records_subtitle":
            "Search and view all weighments",

        "search":
            "Search",

        "search_placeholder":
            "Plate, ticket, vehicle, driver, cargo...",

        "clear":
            "Clear",

        "no_results":
            "No results found.",

        "confirm_delete":
            "Are you sure you want to delete this ticket?",

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
    },


    # ========================================================
    # HY
    # ========================================================

    "hy": {

        "app_name":
            "Խելացի Կշռակայան",

        "login":
            "Մուտք",

        "login_subtitle":
            "Կշռակայանի կառավարման համակարգ",

        "username":
            "Օգտանուն",

        "password":
            "Գաղտնաբառ",

        "submit_login":
            "Մուտք գործել",

        "login_error":
            "Սխալ օգտանուն կամ գաղտնաբառ։",

        "dashboard":
            "Վահանակ",

        "weigh":
            "Կշռում",

        "records":
            "Գրառումներ",

        "vehicle_profiles":
            "Տրանսպորտի սակագներ",

        "device":
            "Սարք",

        "logout":
            "Ելք",

        "welcome":
            "Բարի գալուստ",

        "new_weighment":
            "Նոր կշռում",

        "records_count":
            "Գրառումների քանակը",

        "total_weight":
            "Ընդհանուր քաշ",

        "scale":
            "Կշեռք",

        "stable":
            "Կայուն",

        "waiting":
            "Անկայուն",

        "latest_weighments":
            "Վերջին կշռումները",

        "ticket":
            "Տոմս",

        "plate":
            "Համարանիշ",

        "weight":
            "Քաշ",

        "date":
            "Ամսաթիվ",

        "status":
            "Կարգավիճակ",

        "saved":
            "Պահպանված է",

        "completed":
            "Ավարտված",

        "actions":
            "Գործողություններ",

        "delete":
            "Ջնջել",

        "edit":
            "Խմբագրել",

        "weighment_details":
            "Կշռման մանրամասներ",

        "print":
            "Տպել",

        "operator":
            "Օպերատոր",

        "datetime":
            "Ամսաթիվ և ժամ",

        "no_photo":
            "Առանց լուսանկարի",

        "weigh_truck_title":
            "Կշռում",

        "weigh_subtitle":
            "Ստուգեք տվյալները և գրանցեք։",

        "current_scale_weight":
            "Ընթացիկ կշիռը",

        "truck_plate":
            "Մեքենայի համարանիշ",

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

        "vehicle_type":
            "Տրանսպորտի տեսակ",

        "vehicle_type_placeholder":
            "օր. մեքենա, բեռնատար, կցորդ",

        "weighing_fee":
            "Կշռման վճար",

        "weighing_fee_placeholder":
            "Մուտքագրեք վճարը",

        "vehicle_weight":
            "Տրանսպորտի քաշ",

        "vehicle_weight_placeholder":
            "Տրանսպորտի հղումային քաշ",

        "rial":
            "Ռիալ",

        "vehicle_information":
            "Տրանսպորտի տվյալներ",

        "previous_vehicle_profile":
            "Այս տեսակի նախկին տվյալները",

        "use_previous_values":
            "Օգտագործել նախկին արժեքները",

        "vehicle_profile_auto_save_note":
            "Գրանցումից հետո վճարը և մեքենայի քաշը կհիշվեն կամ կթարմացվեն այս տեսակի համար։",

        "vehicle_profiles_subtitle":
            "Ստեղծել, խմբագրել և ջնջել տրանսպորտի կշռման սակագներն ու հղումային քաշերը",

        "vehicle_profile_form_title":
            "Տրանսպորտի սակագին",

        "save_vehicle_profile":
            "Պահպանել սակագինը",

        "saved_vehicle_profiles":
            "Պահպանված սակագներ",

        "editing_vehicle_profile":
            "Պահպանված սակագնի խմբագրում",

        "cancel_edit":
            "Չեղարկել խմբագրումը",

        "last_update":
            "Վերջին թարմացում",

        "vehicle_profile_note":
            "Այստեղ սակագնի ջնջումը միայն հեռացնում է առաջարկը։ Նախկին կտրոններն ու գրառումները չեն փոխվում։",

        "confirm_delete_vehicle_profile":
            "Ջնջե՞լ այս սակագինը պահպանված առաջարկներից։ Նախկին գրառումները չեն ջնջվի։",

        "no_vehicle_profiles":
            "Դեռ տրանսպորտի սակագներ սահմանված չեն։",

        "driver_name":
            "Վարորդի անունը",

        "driver_name_placeholder":
            "օր. ...",

        "driver_phone":
            "Վարորդի հեռախոս",

        "driver_phone_placeholder":
            "օր. +374...",

        "cargo_type":
            "Բեռ / Ապրանք",

        "cargo_type_placeholder":
            "օր. ցեմենտ / ցորեն",

        "cargo_owner":
            "Բեռի սեփականատեր",

        "cargo_owner_placeholder":
            "Ընկերության կամ անձի անուն",

        "origin":
            "Մեկնարկ",

        "origin_placeholder":
            "օր. ...",

        "destination":
            "Նպատակակետ",

        "destination_placeholder":
            "օր. ...",

        "document_no":
            "Փաստաթուղթ №",

        "document_no_placeholder":
            "օր. 12345",

        "notes":
            "Նշումներ",

        "notes_placeholder":
            "Լրացուցիչ նշումներ...",

        "records_title":
            "Գրառումներ",

        "records_subtitle":
            "Որոնել և դիտել բոլոր կշռումները",

        "search":
            "Որոնում",

        "search_placeholder":
            "Համարանիշ, տոմս, մեքենա, վարորդ, բեռ...",

        "clear":
            "Մաքրել",

        "no_results":
            "Արդյունք չկա։",

        "confirm_delete":
            "Վստա՞հ եք, որ ցանկանում եք ջնջել այս տոմսը։",

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
    },
}


RTL_LANGS = {
    "fa",
}


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
        ][key]

    if key in TRANSLATIONS.get(
        DEFAULT_LANG,
        {},
    ):
        return TRANSLATIONS[
            DEFAULT_LANG
        ][key]

    return key


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
