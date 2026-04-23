"""Seller handlers: WebApp scanner launch + today's report."""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
)
from sqlalchemy import func
from app.config import get_settings
from app.db import SessionLocal
from app.models import User, Transaction, UserRole

router = Router()
settings = get_settings()


def _seller_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text="📸 Сканировать QR",
                web_app=WebAppInfo(url=settings.webapp_url),
            )],
            [KeyboardButton(text="📊 Сегодня")],
        ],
        resize_keyboard=True,
    )


def _fmt(n: Decimal) -> str:
    q = n.quantize(Decimal("1")) if n == n.to_integral_value() else n
    return f"{q:,}".replace(",", " ")


@router.message(Command("seller"))
async def seller_menu(m: Message):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
    if not user or user.role != UserRole.SELLER.value:
        await m.answer("У вас нет роли продавца. Обратитесь к администратору.")
        return
    await m.answer(
        "📸 Меню продавца. Нажмите «Сканировать QR» чтобы открыть камеру.",
        reply_markup=_seller_kb(),
    )


@router.message(F.text == "📱 Открыть меню")
async def seller_open(m: Message):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
    if user and user.role == UserRole.SELLER.value:
        await m.answer("Меню продавца:", reply_markup=_seller_kb())


@router.message(F.text == "📊 Сегодня")
async def today_report(m: Message):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
        if not user or user.role != UserRole.SELLER.value:
            await m.answer("Только для продавцов.")
            return

        # "Today" = last 24 hours (simple; timezone-safe)
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        agg = (
            db.query(
                func.count(Transaction.id),
                func.coalesce(func.sum(Transaction.amount), 0),
                func.coalesce(func.sum(Transaction.bonus_amount), 0),
            )
            .filter(
                Transaction.seller_id == user.id,
                Transaction.created_at >= since,
            )
            .one()
        )
        count, total, bonus = agg

    if count == 0:
        await m.answer("За последние 24 часа транзакций не было.")
        return
    await m.answer(
        f"📊 <b>За последние 24 часа:</b>\n\n"
        f"Транзакций: <b>{count}</b>\n"
        f"Оборот: <b>{_fmt(Decimal(total))}</b> сум\n"
        f"Начислено бонусов: <b>{_fmt(Decimal(bonus))}</b>"
    )
