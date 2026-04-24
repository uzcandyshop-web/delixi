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
              "/update_rate — обновить курс с cbu.uz\n"
              "/report — оборот за 7 дней",
        "uz": "🛠 <b>Admin paneli</b>\n\n"
              "/pending — sovg'a arizalari\n"
              "/sellers — sotuvchilar ro'yxati\n"
              "/make_seller &lt;telegram_id&gt; &lt;region_code&gt; — sotuvchi tayinlash\n"
              "/rate — joriy USD kursi\n"
              "/update_rate — kursni cbu.uz dan yangilash\n"
              "/report — 7 kunlik aylanma",
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
