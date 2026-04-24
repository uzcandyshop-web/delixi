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
