"""Simple i18n helper for the DELIXI bot.

Usage:
    from app.core.i18n import t
    text = t('welcome', lang='uz', name='Sanjar')

Supported languages: 'ru', 'uz'. Fallback language: 'ru'.
"""
from typing import Any

DEFAULT_LANG = "ru"
SUPPORTED_LANGS = ("ru", "uz")
LANG_NAMES = {
    "ru": "🇷🇺 Русский",
    "uz": "🇺🇿 O'zbek",
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    # ---------- Welcome / language selection ----------
    "choose_language": {
        "ru": "🌐 Выберите язык / Tilni tanlang:",
        "uz": "🌐 Выберите язык / Tilni tanlang:",
    },
    "language_set": {
        "ru": "✅ Язык установлен: русский.",
        "uz": "✅ Til o'rnatildi: o'zbekcha.",
    },
    "start_welcome": {
        "ru": "👋 Добро пожаловать в <b>DELIXI</b>!\n\n"
              "Это программа лояльности для постоянных клиентов. "
              "Поделитесь номером телефона, чтобы зарегистрироваться:",
        "uz": "👋 <b>DELIXI</b>ga xush kelibsiz!\n\n"
              "Bu doimiy mijozlar uchun sodiqlik dasturi. "
              "Ro'yxatdan o'tish uchun telefon raqamingizni yuboring:",
    },
    "send_phone_btn": {
        "ru": "📱 Отправить номер",
        "uz": "📱 Raqamni yuborish",
    },
    "send_own_contact": {
        "ru": "Пожалуйста, отправьте <b>свой</b> контакт.",
        "uz": "Iltimos, <b>o'zingizning</b> kontaktingizni yuboring.",
    },

    # ---------- Full name step ----------
    "ask_full_name": {
        "ru": "📝 Укажите ваше <b>ФИО</b> (Фамилия Имя Отчество).\n\n"
              "Например: <i>Рахимов Санжар Алишерович</i>",
        "uz": "📝 <b>F.I.O.</b> ni yozing (Familiya Ism Sharif).\n\n"
              "Masalan: <i>Rahimov Sanjar Alisherovich</i>",
    },
    "err_name_too_short": {
        "ru": "❌ Слишком короткое имя. Пожалуйста, введите ФИО полностью.",
        "uz": "❌ Ism juda qisqa. Iltimos, F.I.O.ni to'liq yozing.",
    },
    "err_name_too_long": {
        "ru": "❌ Слишком длинное имя. Сократите до 120 символов.",
        "uz": "❌ Ism juda uzun. 120 ta belgigacha qisqartiring.",
    },
    "err_name_need_two_words": {
        "ru": "❌ Укажите минимум <b>Фамилию и Имя</b> (через пробел).\n"
              "Например: <i>Рахимов Санжар</i>",
        "uz": "❌ Kamida <b>Familiya va Ism</b> kiriting (probel bilan).\n"
              "Masalan: <i>Rahimov Sanjar</i>",
    },
    "err_name_no_letters": {
        "ru": "❌ ФИО должно содержать буквы.",
        "uz": "❌ F.I.O. harflardan iborat bo'lishi kerak.",
    },

    # ---------- Region step ----------
    "thanks_choose_region": {
        "ru": "Спасибо, <b>{name}</b>!\n\nТеперь выберите ваш регион:",
        "uz": "Rahmat, <b>{name}</b>!\n\nEndi viloyatingizni tanlang:",
    },
    "no_regions": {
        "ru": "Регионы ещё не настроены. Свяжитесь с администратором.",
        "uz": "Viloyatlar hali sozlanmagan. Administrator bilan bog'laning.",
    },
    "region_not_found": {
        "ru": "Регион не найден",
        "uz": "Viloyat topilmadi",
    },
    "session_expired": {
        "ru": "Сессия истекла. Начните заново с /start",
        "uz": "Sessiya tugadi. /start orqali qaytadan boshlang",
    },

    # ---------- Post-registration ----------
    "qr_ready_customer": {
        "ru": "Готово, <b>{name}</b>! 🎉\n\n"
              "Показывайте этот QR-код продавцу при покупке — "
              "баллы начислятся автоматически.",
        "uz": "Tayyor, <b>{name}</b>! 🎉\n\n"
              "Xarid qilganingizda ushbu QR-kodni sotuvchiga ko'rsating — "
              "ballar avtomatik hisoblanadi.",
    },
    "welcome_staff": {
        "ru": "Добро пожаловать, <b>{name}</b>! Роль: <b>{role}</b>.",
        "uz": "Xush kelibsiz, <b>{name}</b>! Rol: <b>{role}</b>.",
    },
    "welcome_back": {
        "ru": "С возвращением, {name}!",
        "uz": "Qaytib kelganingizdan xursandmiz, {name}!",
    },

    # ---------- Customer main menu ----------
    "menu_qr": {"ru": "📱 Мой QR", "uz": "📱 Mening QR"},
    "menu_balance": {"ru": "💰 Баланс", "uz": "💰 Balans"},
    "menu_prizes": {"ru": "🎁 Призы", "uz": "🎁 Sovg'alar"},
    "menu_history": {"ru": "📜 История", "uz": "📜 Tarix"},
    "menu_help": {"ru": "❓ Помощь", "uz": "❓ Yordam"},
    "menu_contest": {"ru": "🏆 Конкурс", "uz": "🏆 Tanlov"},
    "menu_language": {"ru": "🌐 Язык", "uz": "🌐 Til"},

    # ---------- QR / balance / history ----------
    "not_registered": {
        "ru": "Сначала зарегистрируйтесь через /start",
        "uz": "Avval /start orqali ro'yxatdan o'ting",
    },
    "qr_caption": {
        "ru": "Ваш персональный QR-код",
        "uz": "Sizning shaxsiy QR-kodingiz",
    },
    "balance_label": {
        "ru": "💰 <b>Баланс:</b> {amount} баллов",
        "uz": "💰 <b>Balans:</b> {amount} ball",
    },
    "history_empty": {
        "ru": "История покупок пуста.",
        "uz": "Xaridlar tarixi bo'sh.",
    },
    "history_header": {
        "ru": "<b>Последние 10 покупок:</b>\n",
        "uz": "<b>Oxirgi 10 ta xarid:</b>\n",
    },
    "history_item_suffix_sum": {
        "ru": "сум",
        "uz": "so'm",
    },
    "history_item_suffix_bonus": {
        "ru": "баллов",
        "uz": "ball",
    },

    # ---------- Prizes ----------
    "prizes_header": {
        "ru": "🎁 <b>Каталог призов</b>\nВаш баланс: <b>{balance}</b>",
        "uz": "🎁 <b>Sovg'alar katalogi</b>\nSizning balansingiz: <b>{balance}</b>",
    },
    "prizes_empty": {
        "ru": "Каталог призов пока пуст.",
        "uz": "Sovg'alar katalogi hozircha bo'sh.",
    },
    "prize_cost": {
        "ru": "Стоимость: <b>{cost}</b> баллов",
        "uz": "Narxi: <b>{cost}</b> ball",
    },
    "prize_stock": {
        "ru": "В наличии: {stock} шт.",
        "uz": "Mavjud: {stock} dona",
    },
    "prize_order_btn": {
        "ru": "Заказать за {cost}",
        "uz": "Buyurtma ({cost} ball)",
    },
    "only_customers_redeem": {
        "ru": "Только клиенты могут заказывать призы",
        "uz": "Faqat mijozlar sovg'a buyurtma qila oladi",
    },
    "prize_not_found": {
        "ru": "Приз не найден",
        "uz": "Sovg'a topilmadi",
    },
    "prize_out_of_stock": {
        "ru": "Приз закончился",
        "uz": "Sovg'a tugagan",
    },
    "insufficient_balance": {
        "ru": "Недостаточно баллов (нужно {required}, у вас {balance})",
        "uz": "Ball yetarli emas (kerak: {required}, sizda: {balance})",
    },
    "redemption_submitted": {
        "ru": "✅ Заявка на <b>{prize}</b> оформлена!\n\n"
              "Админ рассмотрит её в ближайшее время. "
              "Баллы спишутся только после подтверждения.",
        "uz": "✅ <b>{prize}</b> uchun ariza yuborildi!\n\n"
              "Administrator yaqin vaqtda ko'rib chiqadi. "
              "Ballar faqat tasdiqlangandan keyin yechiladi.",
    },

    # ---------- Help ----------
    "help_text": {
        "ru": "<b>Как это работает:</b>\n\n"
              "1. Показывайте QR-код продавцу при каждой покупке\n"
              "2. Получайте баллы автоматически (1 балл = 1 USD по курсу ЦБ)\n"
              "3. Копите и меняйте на призы из каталога\n\n"
              "По вопросам: @delixi_support",
        "uz": "<b>Qanday ishlaydi:</b>\n\n"
              "1. Har bir xaridda sotuvchiga QR-kodni ko'rsating\n"
              "2. Avtomatik ball oling (1 ball = 1 USD, MB kursi bo'yicha)\n"
              "3. To'plang va katalogdan sovg'aga almashtiring\n\n"
              "Savollar: @delixi_support",
    },

    # ---------- Notifications ----------
    "notify_purchase": {
        "ru": "✅ <b>Покупка подтверждена</b>\n\n"
              "Сумма: <b>{amount}</b> сум\n"
              "Начислено баллов: <b>+{bonus}</b>\n"
              "Баланс: <b>{balance}</b>",
        "uz": "✅ <b>Xarid tasdiqlandi</b>\n\n"
              "Summa: <b>{amount}</b> so'm\n"
              "Qo'shilgan ball: <b>+{bonus}</b>\n"
              "Balans: <b>{balance}</b>",
    },
    "notify_redemption_approved": {
        "ru": "🎁 <b>Заявка на приз одобрена!</b>\n\n"
              "Приз: <b>{prize}</b>\n"
              "Вы можете забрать его в магазине.",
        "uz": "🎁 <b>Sovg'a arizasi tasdiqlandi!</b>\n\n"
              "Sovg'a: <b>{prize}</b>\n"
              "Do'kondan olib ketishingiz mumkin.",
    },
    "notify_redemption_rejected": {
        "ru": "❌ <b>Заявка на «{prize}» отклонена.</b>{extra}\n\n"
              "Бонусы остались на вашем балансе.",
        "uz": "❌ <b>«{prize}» arizasi rad etildi.</b>{extra}\n\n"
              "Bonuslar balansingizda qoldi.",
    },
    "rejection_reason": {
        "ru": "\n\nПричина: {note}",
        "uz": "\n\nSabab: {note}",
    },

    # ---------- Seller ----------
    "menu_scan": {
        "ru": "📸 Сканировать QR",
        "uz": "📸 QR skanerlash",
    },
    "menu_today": {
        "ru": "📊 Сегодня",
        "uz": "📊 Bugun",
    },
    "seller_menu_intro": {
        "ru": "📸 Меню продавца. Нажмите «Сканировать QR» чтобы открыть камеру.",
        "uz": "📸 Sotuvchi menyusi. Kamerani ochish uchun «QR skanerlash» tugmasini bosing.",
    },
    "seller_menu_reopen": {
        "ru": "Меню продавца:",
        "uz": "Sotuvchi menyusi:",
    },
    "not_seller": {
        "ru": "У вас нет роли продавца. Обратитесь к администратору.",
        "uz": "Sizda sotuvchi roli yo'q. Administrator bilan bog'laning.",
    },
    "only_sellers": {
        "ru": "Только для продавцов.",
        "uz": "Faqat sotuvchilar uchun.",
    },
    "today_empty": {
        "ru": "За последние 24 часа транзакций не было.",
        "uz": "So'nggi 24 soatda tranzaksiya bo'lmagan.",
    },
    "today_report": {
        "ru": "📊 <b>За последние 24 часа:</b>\n\n"
              "Транзакций: <b>{count}</b>\n"
              "Оборот: <b>{total}</b> сум\n"
              "Начислено бонусов: <b>{bonus}</b>",
        "uz": "📊 <b>So'nggi 24 soat:</b>\n\n"
              "Tranzaksiyalar: <b>{count}</b>\n"
              "Aylanma: <b>{total}</b> so'm\n"
              "Qo'shilgan bonus: <b>{bonus}</b>",
    },
    "menu_open": {
        "ru": "📱 Открыть меню",
        "uz": "📱 Menyuni ochish",
    },

    # ---------- Admin ----------
    "admin_menu": {
        "ru": "🛠 <b>Админ-панель</b>\n\n"
              "/pending — заявки на призы\n"
              "/sellers — список продавцов\n"
              "/make_seller &lt;telegram_id&gt; &lt;region_code&gt; — назначить продавца\n"
              "/rate — текущий курс USD\n"
              "/update_rate — обновить курс с cbu.uz\n\n"
              "<b>Конкурс:</b>\n"
              "/start_contest Название | Описание — запустить\n"
              "/end_contest — завершить + топ-10\n"
              "/make_judge &lt;telegram_id&gt; — назначить судью\n"
              "/judges — список судей",
        "uz": "🛠 <b>Admin paneli</b>\n\n"
              "/pending — sovg'a arizalari\n"
              "/sellers — sotuvchilar ro'yxati\n"
              "/make_seller &lt;telegram_id&gt; &lt;region_code&gt; — sotuvchi tayinlash\n"
              "/rate — joriy USD kursi\n"
              "/update_rate — kursni cbu.uz dan yangilash\n\n"
              "<b>Tanlov:</b>\n"
              "/start_contest Nomi | Tavsif — boshlash\n"
              "/end_contest — yakunlash + top-10\n"
              "/make_judge &lt;telegram_id&gt; — hakam tayinlash\n"
              "/judges — hakamlar ro'yxati",
    },
    "no_pending": {
        "ru": "Нет заявок на рассмотрении.",
        "uz": "Ko'rib chiqiladigan arizalar yo'q.",
    },
    "pending_item": {
        "ru": "📨 <b>Заявка</b>\n"
              "Клиент: {customer}\n"
              "Приз: <b>{prize}</b>\n"
              "Стоимость: <b>{cost}</b> баллов",
        "uz": "📨 <b>Ariza</b>\n"
              "Mijoz: {customer}\n"
              "Sovg'a: <b>{prize}</b>\n"
              "Narxi: <b>{cost}</b> ball",
    },
    "approve_btn": {
        "ru": "✅ Одобрить",
        "uz": "✅ Tasdiqlash",
    },
    "reject_btn": {
        "ru": "❌ Отклонить",
        "uz": "❌ Rad etish",
    },
    "no_access": {
        "ru": "Нет доступа",
        "uz": "Ruxsat yo'q",
    },
    "register_first": {
        "ru": "Сначала зарегистрируйтесь через /start",
        "uz": "Avval /start orqali ro'yxatdan o'ting",
    },
    "done": {
        "ru": "Готово",
        "uz": "Bajarildi",
    },
    "redemption_approved": {
        "ru": "Заявка одобрена.",
        "uz": "Ariza tasdiqlandi.",
    },
    "redemption_rejected": {
        "ru": "Заявка отклонена.",
        "uz": "Ariza rad etildi.",
    },
    "sellers_empty": {
        "ru": "Продавцов пока нет. Используйте /make_seller",
        "uz": "Sotuvchilar hali yo'q. /make_seller dan foydalaning",
    },
    "sellers_header": {
        "ru": "<b>Продавцы:</b>\n",
        "uz": "<b>Sotuvchilar:</b>\n",
    },
    "make_seller_usage": {
        "ru": "Использование: <code>/make_seller &lt;telegram_id&gt; &lt;region_code&gt;</code>\n"
              "Пример: <code>/make_seller 123456789 TAS</code>",
        "uz": "Foydalanish: <code>/make_seller &lt;telegram_id&gt; &lt;region_code&gt;</code>\n"
              "Masalan: <code>/make_seller 123456789 TAS</code>",
    },
    "make_seller_id_must_be_number": {
        "ru": "telegram_id должен быть числом",
        "uz": "telegram_id raqam bo'lishi kerak",
    },
    "region_not_found_code": {
        "ru": "Регион <b>{code}</b> не найден",
        "uz": "Viloyat <b>{code}</b> topilmadi",
    },
    "user_not_found_ask_start": {
        "ru": "Пользователь {tg_id} не найден. "
              "Попросите его сначала зарегистрироваться через /start.",
        "uz": "{tg_id} foydalanuvchi topilmadi. "
              "Undan avval /start orqali ro'yxatdan o'tishni so'rang.",
    },
    "made_seller": {
        "ru": "✅ {name} теперь продавец в регионе {code}",
        "uz": "✅ {name} endi {code} viloyatida sotuvchi",
    },

    # ---------- Admin inline panel ----------
    "adm_panel_title": {
        "ru": "🛠 <b>Админ-панель</b>\n\nВыберите действие:",
        "uz": "🛠 <b>Admin paneli</b>\n\nAmalni tanlang:",
    },
    "adm_btn_pending": {"ru": "📨 Заявки на призы", "uz": "📨 Sovg'a arizalari"},
    "adm_btn_sellers": {"ru": "👥 Продавцы", "uz": "👥 Sotuvchilar"},
    "adm_btn_judges": {"ru": "🧑‍⚖️ Судьи", "uz": "🧑‍⚖️ Hakamlar"},
    "adm_btn_make_seller": {"ru": "➕ Продавец", "uz": "➕ Sotuvchi"},
    "adm_btn_make_judge": {"ru": "➕ Судья", "uz": "➕ Hakam"},
    "adm_btn_rate": {"ru": "💱 Курс USD", "uz": "💱 USD kursi"},
    "adm_btn_update_rate": {"ru": "🔄 Обновить курс", "uz": "🔄 Kursni yangilash"},
    "adm_btn_start_contest": {"ru": "🏆 Начать конкурс", "uz": "🏆 Tanlov boshlash"},
    "adm_btn_end_contest": {"ru": "🏁 Завершить конкурс", "uz": "🏁 Tanlovni yakunlash"},
    "adm_btn_report": {"ru": "📊 Отчёт за 7 дней", "uz": "📊 7 kunlik hisobot"},
    "adm_btn_back": {"ru": "◀️ Назад в меню", "uz": "◀️ Menyuga qaytish"},

    "adm_confirm_end_contest_q": {
        "ru": "⚠️ Завершить конкурс «{name}»?\n\n"
              "Все работы получат финальный статус, новые работы приниматься не будут. "
              "Будет показан топ-10 победителей.",
        "uz": "⚠️ «{name}» tanlovini yakunlaysizmi?\n\n"
              "Barcha ishlar yakuniy holatga o'tadi, yangi ishlar qabul qilinmaydi. "
              "Top-10 g'oliblar ko'rsatiladi.",
    },
    "adm_confirm_end_contest": {
        "ru": "✅ Да, завершить",
        "uz": "✅ Ha, yakunlash",
    },

    "regions_available": {
        "ru": "<b>Коды регионов:</b>",
        "uz": "<b>Viloyat kodlari:</b>",
    },

    # ---------- Admin reports ----------
    "report_header": {
        "ru": "📊 <b>Отчёт за 7 дней</b>\n\n"
              "Транзакций: <b>{count}</b>\n"
              "Оборот: <b>{total}</b> сум\n"
              "Начислено баллов: <b>{bonus}</b>",
        "uz": "📊 <b>7 kunlik hisobot</b>\n\n"
              "Tranzaksiyalar: <b>{count}</b>\n"
              "Aylanma: <b>{total}</b> so'm\n"
              "Qo'shilgan ballar: <b>{bonus}</b>",
    },
    "report_by_region": {
        "ru": "<b>По регионам:</b>",
        "uz": "<b>Viloyatlar bo'yicha:</b>",
    },

    # ---------- Period picker (seller + admin) ----------
    "rep_today": {"ru": "Сегодня", "uz": "Bugun"},
    "rep_week": {"ru": "Неделя", "uz": "Hafta"},
    "rep_month": {"ru": "Месяц", "uz": "Oy"},
    "rep_choose_period": {
        "ru": "📊 Выберите период:",
        "uz": "📊 Davrni tanlang:",
    },
    "rep_period_label_today": {"ru": "сегодня", "uz": "bugun"},
    "rep_period_label_week": {"ru": "за 7 дней", "uz": "7 kun ichida"},
    "rep_period_label_month": {"ru": "за 30 дней", "uz": "30 kun ichida"},
    "rep_done": {"ru": "✅ Готово", "uz": "✅ Tayyor"},

    # ---------- Seller summary ----------
    "rep_seller_summary": {
        "ru": "📊 <b>Ваш отчёт ({period})</b>\n\n"
              "Чеков: <b>{count}</b>\n"
              "Оборот: <b>{total}</b> сум\n"
              "Начислено баллов: <b>{bonus}</b>\n"
              "Средний чек: <b>{avg}</b> сум",
        "uz": "📊 <b>Hisobotingiz ({period})</b>\n\n"
              "Cheklar: <b>{count}</b>\n"
              "Aylanma: <b>{total}</b> so'm\n"
              "Qo'shilgan ballar: <b>{bonus}</b>\n"
              "O'rtacha chek: <b>{avg}</b> so'm",
    },
    "rep_seller_empty_today": {
        "ru": "📊 Сегодня у вас ещё не было продаж.",
        "uz": "📊 Bugun sizda hali sotuvlar yo'q.",
    },
    "rep_seller_empty_week": {
        "ru": "📊 За последние 7 дней продаж не было.",
        "uz": "📊 So'nggi 7 kunda sotuvlar bo'lmadi.",
    },
    "rep_seller_empty_month": {
        "ru": "📊 За последние 30 дней продаж не было.",
        "uz": "📊 So'nggi 30 kunda sotuvlar bo'lmadi.",
    },

    # ---------- Admin summary ----------
    "rep_admin_summary": {
        "ru": "📊 <b>Отчёт по системе ({period})</b>\n\n"
              "Транзакций: <b>{count}</b>\n"
              "Оборот: <b>{total}</b> сум\n"
              "Начислено баллов: <b>{bonus}</b>\n"
              "Средний чек: <b>{avg}</b> сум",
        "uz": "📊 <b>Tizim hisoboti ({period})</b>\n\n"
              "Tranzaksiyalar: <b>{count}</b>\n"
              "Aylanma: <b>{total}</b> so'm\n"
              "Qo'shilgan ballar: <b>{bonus}</b>\n"
              "O'rtacha chek: <b>{avg}</b> so'm",
    },
    "rep_admin_empty_today": {
        "ru": "📊 Сегодня в системе ещё не было транзакций.",
        "uz": "📊 Bugun tizimda hali tranzaksiyalar yo'q.",
    },
    "rep_admin_empty_week": {
        "ru": "📊 За последние 7 дней транзакций не было.",
        "uz": "📊 So'nggi 7 kunda tranzaksiyalar bo'lmadi.",
    },
    "rep_admin_empty_month": {
        "ru": "📊 За последние 30 дней транзакций не было.",
        "uz": "📊 So'nggi 30 kunda tranzaksiyalar bo'lmadi.",
    },

    # ---------- Chart titles ----------
    "rep_chart_title_week": {
        "ru": "Оборот за 7 дней", "uz": "7 kunlik aylanma",
    },
    "rep_chart_title_month": {
        "ru": "Оборот за 30 дней", "uz": "30 kunlik aylanma",
    },
    "rep_chart_subtitle": {
        "ru": "{count} транзакций · {total} сум",
        "uz": "{count} tranzaksiya · {total} so'm",
    },

    # ---------- Support requests ----------
    "support_choose_category": {
        "ru": "❓ <b>Помощь</b>\n\nВыберите категорию обращения:",
        "uz": "❓ <b>Yordam</b>\n\nMurojaat toifasini tanlang:",
    },
    "support_cat_engineer": {"ru": "🔧 Вызов инженера", "uz": "🔧 Muhandis chaqirish"},
    "support_cat_complaint": {"ru": "⚠️ Жалоба", "uz": "⚠️ Shikoyat"},
    "support_cat_techsupport": {"ru": "💬 Техподдержка", "uz": "💬 Texnik yordam"},

    "support_ask_text": {
        "ru": "📝 Опишите вашу проблему или вопрос:",
        "uz": "📝 Muammo yoki savolingizni yozing:",
    },
    "support_ask_photo": {
        "ru": "📷 При желании прикрепите фото (или нажмите «Пропустить»):",
        "uz": "📷 Istasangiz rasm biriktiring (yoki «O'tkazib yuborish» bosing):",
    },
    "support_skip_photo": {"ru": "Пропустить", "uz": "O'tkazib yuborish"},
    "support_send_photo_hint": {
        "ru": "Отправьте фото как изображение (не файл), или нажмите «Пропустить».",
        "uz": "Rasmni fayl sifatida emas, rasm sifatida yuboring yoki «O'tkazib yuborish» bosing.",
    },

    "err_text_empty": {
        "ru": "❌ Текст обращения не может быть пустым. Напишите описание проблемы.",
        "uz": "❌ Murojaat matni bo'sh bo'lmasligi kerak. Muammoni yozing.",
    },
    "err_text_too_long": {
        "ru": "❌ Слишком длинный текст (больше 4000 символов). Сократите.",
        "uz": "❌ Matn juda uzun (4000 belgidan oshmasin). Qisqartiring.",
    },
    "support_group_not_configured": {
        "ru": "⚠️ Эта категория поддержки временно недоступна. Попробуйте позже или свяжитесь с администратором.",
        "uz": "⚠️ Bu yordam toifasi vaqtincha mavjud emas. Keyinroq urinib ko'ring yoki administrator bilan bog'laning.",
    },
    "support_submitted": {
        "ru": "✅ <b>Заявка №{short_id} отправлена!</b>\n\n"
              "Мы свяжемся с вами после обработки обращения. "
              "Вы получите уведомление когда заявка будет закрыта.",
        "uz": "✅ <b>№{short_id} arizangiz yuborildi!</b>\n\n"
              "Murojaatingiz ko'rib chiqilgandan so'ng biz siz bilan bog'lanamiz. "
              "Ariza yopilganda xabar olasiz.",
    },

    # ---------- Group messages (in support Telegram groups) ----------
    "group_new_request": {
        "ru": "📨 <b>Новая заявка #{short_id}</b>\n"
              "Категория: {cat_emoji} {cat_name}\n"
              "От: <b>{name}</b>\n"
              "Телефон: {phone}\n"
              "Регион: {region}\n"
              "─────\n"
              "{text}",
        "uz": "📨 <b>Yangi ariza #{short_id}</b>\n"
              "Toifa: {cat_emoji} {cat_name}\n"
              "Kimdan: <b>{name}</b>\n"
              "Telefon: {phone}\n"
              "Viloyat: {region}\n"
              "─────\n"
              "{text}",
    },
    "group_btn_accept": {"ru": "✅ Принять", "uz": "✅ Qabul qilish"},
    "group_btn_in_progress": {"ru": "🔄 В работу", "uz": "🔄 Ish boshlash"},
    "group_btn_resolve": {"ru": "✔️ Решено", "uz": "✔️ Hal qilindi"},
    "group_btn_reject": {"ru": "❌ Отклонить", "uz": "❌ Rad etish"},
    "group_status_updated": {
        "ru": "\n\n📌 Статус: <b>{status}</b>\nОбновил: {resolver_name}",
        "uz": "\n\n📌 Holat: <b>{status}</b>\nYangiladi: {resolver_name}",
    },
    "group_status_accepted": {"ru": "Принята", "uz": "Qabul qilindi"},
    "group_status_in_progress": {"ru": "В работе", "uz": "Ish jarayonida"},
    "group_status_resolved": {"ru": "Решена ✔️", "uz": "Hal qilindi ✔️"},
    "group_status_rejected": {"ru": "Отклонена ❌", "uz": "Rad etildi ❌"},
    "group_already_closed": {"ru": "Заявка уже закрыта", "uz": "Ariza yopilgan"},

    # ---------- Customer notifications about support ----------
    "notify_support_resolved": {
        "ru": "✔️ <b>Ваша заявка №{short_id} ({category}) решена!</b>{extra}\n\n"
              "Если у вас остались вопросы — создайте новое обращение.",
        "uz": "✔️ <b>№{short_id} ({category}) arizangiz hal qilindi!</b>{extra}\n\n"
              "Agar savollaringiz qolsa — yangi ariza yuboring.",
    },
    "notify_support_rejected": {
        "ru": "❌ <b>Ваша заявка №{short_id} ({category}) отклонена.</b>{extra}",
        "uz": "❌ <b>№{short_id} ({category}) arizangiz rad etildi.</b>{extra}",
    },

    # ---------- /bind_support_group command ----------
    "bind_group_usage": {
        "ru": "Используйте в группе: <code>/bind_support_group engineer|complaint|techsupport</code>\n"
              "Или настройте ID групп в Environment Variables.",
        "uz": "Guruhda foydalaning: <code>/bind_support_group engineer|complaint|techsupport</code>\n"
              "Yoki Environment Variables da guruh ID larini sozlang.",
    },
    "bind_group_not_in_group": {
        "ru": "Команду нужно отправлять в групповом чате, куда должны приходить заявки.",
        "uz": "Buyruqni arizalar keladigan guruh chatida yuborish kerak.",
    },
    "bind_group_shown": {
        "ru": "ID этого чата: <code>{chat_id}</code>\n\n"
              "Добавьте его в Render Environment как:\n"
              "<code>SUPPORT_{CAT}_CHAT_ID={chat_id}</code>",
        "uz": "Ushbu chat ID: <code>{chat_id}</code>\n\n"
              "Uni Render Environment ga qo'shing:\n"
              "<code>SUPPORT_{CAT}_CHAT_ID={chat_id}</code>",
    },

    # ---------- Contest: customer-side ----------
    "contest_none_active": {
        "ru": "🏆 Сейчас нет активного конкурса. Следите за обновлениями!",
        "uz": "🏆 Hozir faol tanlov yo'q. Yangiliklarni kuzatib boring!",
    },
    "contest_info": {
        "ru": "🏆 <b>{name}</b>\n\n{description}\n\n"
              "Нажмите кнопку ниже, чтобы отправить работу на конкурс.",
        "uz": "🏆 <b>{name}</b>\n\n{description}\n\n"
              "Ishingizni tanlovga yuborish uchun pastdagi tugmani bosing.",
    },
    "contest_submit_btn": {"ru": "📤 Отправить работу", "uz": "📤 Ishni yuborish"},
    "contest_ask_photo": {
        "ru": "📷 Отправьте <b>фото</b> вашей работы:",
        "uz": "📷 Ishingizning <b>rasmini</b> yuboring:",
    },
    "contest_photo_hint": {
        "ru": "Пожалуйста, отправьте именно фото (как изображение, не файл).",
        "uz": "Iltimos, faqat rasm yuboring (fayl sifatida emas).",
    },
    "contest_ask_description": {
        "ru": "📝 Добавьте описание работы (или нажмите «Пропустить»):",
        "uz": "📝 Ish tavsifini qo'shing (yoki «O'tkazib yuborish» bosing):",
    },
    "contest_skip_description": {"ru": "Пропустить", "uz": "O'tkazib yuborish"},
    "contest_description_too_long": {
        "ru": "❌ Описание слишком длинное (максимум 2000 символов).",
        "uz": "❌ Tavsif juda uzun (maksimum 2000 belgi).",
    },
    "contest_submitted": {
        "ru": "✅ Работа №{short_id} отправлена на конкурс!\n\n"
              "Жюри оценит её в ближайшее время. Вы получите уведомление с итоговой оценкой.",
        "uz": "✅ №{short_id} ishingiz tanlovga yuborildi!\n\n"
              "Hakamlar yaqin vaqtda baholaydi. Yakuniy baho bilan xabar olasiz.",
    },
    "contest_judges_unavailable": {
        "ru": "⚠️ Группа жюри не настроена. Свяжитесь с администратором.",
        "uz": "⚠️ Hakamlar guruhi sozlanmagan. Administrator bilan bog'laning.",
    },

    # ---------- Contest: group-side messages ----------
    "group_new_work": {
        "ru": "🏆 <b>Работа #{short_id}</b>\n"
              "Автор: <b>{name}</b>\n"
              "Телефон: {phone}\n"
              "Регион: {region}\n"
              "─────\n"
              "{description}\n\n"
              "Оценили: {scored}/{total} судей",
        "uz": "🏆 <b>Ish #{short_id}</b>\n"
              "Muallif: <b>{name}</b>\n"
              "Telefon: {phone}\n"
              "Viloyat: {region}\n"
              "─────\n"
              "{description}\n\n"
              "Baholadi: {scored}/{total} hakam",
    },
    "group_work_finalized": {
        "ru": "🏁 <b>Работа #{short_id}</b> (финал)\n"
              "Автор: <b>{name}</b>\n"
              "Телефон: {phone}\n"
              "Регион: {region}\n"
              "─────\n"
              "{description}\n\n"
              "⭐ <b>Итоговая оценка: {avg}/10</b>",
        "uz": "🏁 <b>Ish #{short_id}</b> (yakun)\n"
              "Muallif: <b>{name}</b>\n"
              "Telefon: {phone}\n"
              "Viloyat: {region}\n"
              "─────\n"
              "{description}\n\n"
              "⭐ <b>Yakuniy baho: {avg}/10</b>",
    },
    "group_btn_score": {"ru": "⭐ Оценить", "uz": "⭐ Baholash"},
    "contest_work_not_found": {
        "ru": "Работа не найдена",
        "uz": "Ish topilmadi",
    },
    "contest_not_a_judge": {
        "ru": "У вас нет роли судьи",
        "uz": "Sizda hakam roli yo'q",
    },
    "contest_already_scored": {
        "ru": "Вы уже оценили эту работу",
        "uz": "Bu ishni allaqachon baholadingiz",
    },
    "score_open_dm_first": {
        "ru": "Сначала напишите боту в личные сообщения (/start)",
        "uz": "Avval botga shaxsiy xabar yozing (/start)",
    },

    # ---------- Scoring FSM prompts ----------
    "score_start": {
        "ru": "⭐ Оценка работы #{work_short}\n\nОцените работу по 5 критериям (от 1 до 10).",
        "uz": "⭐ #{work_short} ishni baholash\n\nIshni 5 mezon bo'yicha baholang (1 dan 10 gacha).",
    },
    "score_ask_c1": {
        "ru": "<b>1/5 Оригинальность</b>\nНасколько работа оригинальна и неповторима?",
        "uz": "<b>1/5 Originallik</b>\nIsh qanchalik original va betakror?",
    },
    "score_ask_c2": {
        "ru": "<b>2/5 Качество исполнения</b>\nНасколько качественно выполнена работа?",
        "uz": "<b>2/5 Bajarilish sifati</b>\nIsh qanchalik sifatli bajarilgan?",
    },
    "score_ask_c3": {
        "ru": "<b>3/5 Соответствие теме</b>\nНасколько работа соответствует теме конкурса?",
        "uz": "<b>3/5 Mavzuga muvofiqligi</b>\nIsh tanlov mavzusiga qanchalik mos?",
    },
    "score_ask_c4": {
        "ru": "<b>4/5 Креативность</b>\nНасколько творческий подход у автора?",
        "uz": "<b>4/5 Ijodkorlik</b>\nMuallifning ijodiy yondashuvi qanchalik yaxshi?",
    },
    "score_ask_c5": {
        "ru": "<b>5/5 Общее впечатление</b>\nВаше общее впечатление от работы?",
        "uz": "<b>5/5 Umumiy taassurot</b>\nIshdan umumiy taassurotingiz?",
    },
    "score_saved": {
        "ru": "✅ Спасибо! Ваша средняя оценка: <b>{avg}/10</b>.",
        "uz": "✅ Rahmat! Sizning o'rtacha bahoyingiz: <b>{avg}/10</b>.",
    },
    "score_err_already_scored": {
        "ru": "❌ Вы уже оценили эту работу.",
        "uz": "❌ Bu ishni allaqachon baholagansiz.",
    },
    "score_err_not_a_judge": {
        "ru": "❌ У вас нет роли судьи.",
        "uz": "❌ Sizda hakam roli yo'q.",
    },

    # ---------- Notification: contest result ----------
    "notify_contest_finalized": {
        "ru": "🏁 <b>Ваша работа №{short_id} получила итоговую оценку!</b>\n\n"
              "⭐ Средний балл: <b>{avg}/10</b>\n\n"
              "Спасибо за участие в конкурсе!",
        "uz": "🏁 <b>№{short_id} ishingiz yakuniy bahoni oldi!</b>\n\n"
              "⭐ O'rtacha ball: <b>{avg}/10</b>\n\n"
              "Tanlovda ishtirok etganingiz uchun rahmat!",
    },

    # ---------- Admin: contest commands ----------
    "contest_cmd_usage": {
        "ru": "Использование: <code>/start_contest Название конкурса | Описание</code>\n"
              "Команду нужно вызвать в группе жюри — тогда бот запомнит её как чат для отправки работ.",
        "uz": "Foydalanish: <code>/start_contest Tanlov nomi | Tavsif</code>\n"
              "Buyruqni hakamlar guruhida yuboring — bot uni ishlar yuboriladigan chat sifatida saqlaydi.",
    },
    "contest_started": {
        "ru": "✅ Конкурс «{name}» запущен.\nГруппа жюри: <code>{judges_chat}</code>",
        "uz": "✅ «{name}» tanlovi boshlandi.\nHakamlar guruhi: <code>{judges_chat}</code>",
    },
    "contest_results_header": {
        "ru": "🏆 <b>Итоги конкурса «{name}»</b>\n",
        "uz": "🏆 <b>«{name}» tanlovi natijalari</b>\n",
    },
    "contest_results_empty": {
        "ru": "Работ с финальной оценкой не было.",
        "uz": "Yakuniy baholangan ishlar bo'lmadi.",
    },
    "contest_results_line": {
        "ru": "{place}. {name} — <b>{avg}/10</b>",
        "uz": "{place}. {name} — <b>{avg}/10</b>",
    },
    "make_judge_usage": {
        "ru": "Использование: <code>/make_judge &lt;telegram_id&gt;</code>",
        "uz": "Foydalanish: <code>/make_judge &lt;telegram_id&gt;</code>",
    },
    "made_judge": {
        "ru": "✅ {name} теперь судья конкурса",
        "uz": "✅ {name} endi tanlov hakami",
    },
    "judges_empty": {
        "ru": "Судей пока нет. Используйте /make_judge",
        "uz": "Hakamlar hali yo'q. /make_judge dan foydalaning",
    },
    "judges_header": {
        "ru": "<b>Судьи:</b>\n",
        "uz": "<b>Hakamlar:</b>\n",
    },

    # ---------- USD rate ----------
    "rate_current": {
        "ru": "💱 Текущий курс USD: <b>{rate}</b> сум",
        "uz": "💱 Joriy USD kursi: <b>{rate}</b> so'm",
    },
    "rate_updating": {
        "ru": "⏳ Обновляю курс с cbu.uz...",
        "uz": "⏳ Kurs cbu.uz dan yangilanmoqda...",
    },
    "rate_updated": {
        "ru": "✅ Курс обновлён: <b>{rate}</b> сум/USD",
        "uz": "✅ Kurs yangilandi: <b>{rate}</b> so'm/USD",
    },
    "rate_update_failed": {
        "ru": "⚠️ Не удалось получить курс с cbu.uz. Используется последний сохранённый.",
        "uz": "⚠️ cbu.uz dan kursni olishda xatolik. Oxirgi saqlangan qiymat ishlatilmoqda.",
    },
}


def t(key: str, lang: str = DEFAULT_LANG, **kwargs: Any) -> str:
    """Translate a key into the given language."""
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG

    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key

    template = entry.get(lang) or entry.get(DEFAULT_LANG) or key
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            return template
    return template


def normalize_lang(raw: str | None) -> str:
    """Normalize arbitrary input into a supported language code."""
    if not raw:
        return DEFAULT_LANG
    raw = raw.strip().lower()
    if raw in SUPPORTED_LANGS:
        return raw
    aliases = {"ru-ru": "ru", "russian": "ru", "uz-uz": "uz", "uzbek": "uz"}
    return aliases.get(raw, DEFAULT_LANG)
