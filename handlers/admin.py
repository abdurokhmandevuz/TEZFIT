import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from sqlalchemy import select, func
from config import settings
from database.session import AsyncSessionLocal
from database.models import User, Meal

logger = logging.getLogger(__name__)
router = Router()

ADMIN_IDS = [7225597812, 123456789]

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS or user_id in getattr(settings, 'ADMIN_IDS', [])

def get_admin_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Umumiy Statistika", callback_data="admin_stats"),
                InlineKeyboardButton(text="👑 VIP Status Boshqaruvi", callback_data="admin_vip_menu")
            ],
            [
                InlineKeyboardButton(text="📢 Xabar Tarqatish (Rassilka)", callback_data="admin_broadcast_help"),
                InlineKeyboardButton(text="❓ Help / Yordam", callback_data="admin_help")
            ],
            [
                InlineKeyboardButton(text="🌐 Web Admin Panel (Jazzmin)", url=f"{settings.WEB_APP_URL.replace('/web_app', '')}/admin/")
            ]
        ]
    )

@router.message(Command("admin"))
async def admin_command_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⚠️ Kechirasiz, ushbu buyruq faqat bot administratorlari uchun mo'ljallangan.")
        return

    await message.answer(
        "🛠 **TezFIT Telegram Bot Admin Paneli**\n\n"
        f"Xush kelibsiz, Admin `{message.from_user.first_name}`!\n"
        "Quyidagi bo'limlardan birini tanlang:",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard()
    )

@router.callback_query(F.data == "admin_help")
async def admin_help_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat yo'q!", show_alert=True)
        return

    help_text = (
        "❓ **TEZFIT BOT ADMIN YO'RIQNOMASI**\n\n"
        "1. ⚙️ **Interaktiv Admin Menyusi:**\n"
        "`/admin` — Telegram bot ichida maxsus tugmalardan iborat interaktiv admin panelni ochadi:\n"
        "• 📊 **Umumiy Statistika:** Real vaqtdagi foydalanuvchilar soni, VIP-lar va kiritilgan taomlar statistikasini ko'rsatadi.\n"
        "• 👑 **VIP Status Boshqaruvi:** VIP foydalanuvchilarni boshqarish bo'yicha yo'riqnoma.\n"
        "• 📢 **Xabar Tarqatish:** Barcha foydalanuvchilarga e'lon yuborish.\n"
        "• 🌐 **Web Admin Panel (Jazzmin):** Django Web Admin paneliga to'g'ridan-to'g'ri o'tish tugmasi.\n\n"
        "2. 👑 **VIP Status Berish / Olib Tashlash:**\n"
        "• `/vip 7225597812` — Istalgan foydalanuvchiga Telegram ID orqali VIP status beradi.\n"
        "• `/unvip 7225597812` — VIP statusni bekor qiladi.\n\n"
        "3. 📢 **Barcha Foydalanuvchilarga Xabar Yuborish (Rassilka):**\n"
        "• `/sendall Assalomu alaykum! TezFIT botimizda yangi imkoniyatlar qo'shildi! 🚀`\n"
        "Bazadagi barcha foydalanuvchilarga bir zumda e'lon yuboradi va yakunda qanchasiga muvaffaqiyatli borganini hisobot qilib beradi."
    )

    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_main_menu")]
        ]
    )

    await call.message.edit_text(help_text, parse_mode="Markdown", reply_markup=back_kb)
    await call.answer()

@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat yo'q!", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        total_users = (await session.execute(select(func.count(User.id)))).scalar() or 0
        vip_users = (await session.execute(select(func.count(User.id)).where(User.is_vip == True))).scalar() or 0
        total_meals = (await session.execute(select(func.count(Meal.id)))).scalar() or 0

    stats_text = (
        "📊 **BOTNING HARAKATDAGI STATISTIKASI**\n\n"
        f"👥 **Jami foydalanuvchilar:** {total_users} ta\n"
        f"👑 **VIP foydalanuvchilar:** {vip_users} ta\n"
        f"🍽 **Jami kiritilgan taomlar:** {total_meals} ta\n\n"
        f"🌐 **Django Admin:** {settings.WEB_APP_URL.replace('/web_app', '')}/admin/\n"
        f"🔑 **Log/Parol:** `admin` / `admin`"
    )

    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_main_menu")]
        ]
    )

    await call.message.edit_text(stats_text, parse_mode="Markdown", reply_markup=back_kb)
    await call.answer()

@router.callback_query(F.data == "admin_vip_menu")
async def admin_vip_menu_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat yo'q!", show_alert=True)
        return

    vip_info = (
        "👑 **VIP STATUS BOSHQARUVI**\n\n"
        "Foydalanuvchiga VIP berish yoki bekor qilish uchun quyidagi buyruqdan foydalaning:\n\n"
        "👉 `/vip 7225597812` — VIP status berish\n"
        "👉 `/unvip 7225597812` — VIP statusni olib tashlash\n"
    )

    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_main_menu")]
        ]
    )

    await call.message.edit_text(vip_info, parse_mode="Markdown", reply_markup=back_kb)
    await call.answer()

@router.callback_query(F.data == "admin_broadcast_help")
async def admin_broadcast_help_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat yo'q!", show_alert=True)
        return

    broadcast_info = (
        "📢 **Barcha Foydalanuvchilarga Xabar Yuborish**\n\n"
        "Barcha ro'yxatdan o'tgan foydalanuvchilarga bildirishnoma yuborish uchun buyruq:\n\n"
        "👉 `/sendall Salom! TezFIT ilovamizda yangi imkoniyatlar qo'shildi! 🚀`"
    )

    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_main_menu")]
        ]
    )

    await call.message.edit_text(broadcast_info, parse_mode="Markdown", reply_markup=back_kb)
    await call.answer()

@router.callback_query(F.data == "admin_main_menu")
async def admin_main_menu_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat yo'q!", show_alert=True)
        return

    await call.message.edit_text(
        "🛠 **TezFIT Telegram Bot Admin Paneli**\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard()
    )
    await call.answer()

@router.message(Command("vip"))
async def set_vip_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ Qoida: `/vip <user_telegram_id>` (Masalan: `/vip 7225597812`)", parse_mode="Markdown")
        return

    target_tg_id = int(args[1])
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == target_tg_id))
        user = result.scalar_one_or_none()

        if not user:
            await message.answer(f"❌ ID `{target_tg_id}` bo'yicha foydalanuvchi bazadan topilmadi.", parse_mode="Markdown")
            return

        user.is_vip = True
        await session.commit()

    await message.answer(f"👑 Foydalanuvchi `{target_tg_id}` (`{user.name or user.username}`) ga **VIP STATUS** berildi!", parse_mode="Markdown")

@router.message(Command("unvip"))
async def remove_vip_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ Qoida: `/unvip <user_telegram_id>` (Masalan: `/unvip 7225597812`)", parse_mode="Markdown")
        return

    target_tg_id = int(args[1])
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == target_tg_id))
        user = result.scalar_one_or_none()

        if not user:
            await message.answer(f"❌ ID `{target_tg_id}` bo'yicha foydalanuvchi bazadan topilmadi.", parse_mode="Markdown")
            return

        user.is_vip = False
        await session.commit()

    await message.answer(f"❌ Foydalanuvchi `{target_tg_id}` dan VIP status olib tashlandi.", parse_mode="Markdown")

def parse_broadcast_text_and_kb(raw_text: str):
    web_app_url = f"{settings.WEB_APP_URL}?v=2.8.2"
    kb_rows = []
    
    if "|" in raw_text:
        parts = raw_text.split("|")
        clean_text = parts[0].strip()
        button_part = parts[1].strip()
        
        if "->" in button_part:
            btn_title, btn_url = button_part.split("->", 1)
            btn_title = btn_title.strip()
            btn_url = btn_url.strip()
            if btn_url.startswith("http"):
                kb_rows.append([InlineKeyboardButton(text=btn_title, url=btn_url)])
            else:
                kb_rows.append([InlineKeyboardButton(text=btn_title, callback_data="none")])
        else:
            kb_rows.append([InlineKeyboardButton(text=button_part, web_app=WebAppInfo(url=web_app_url))])
    else:
        clean_text = raw_text.strip()
    
    kb_rows.append([InlineKeyboardButton(text="📱 Web App-da Ochish", web_app=WebAppInfo(url=web_app_url))])
    return clean_text, InlineKeyboardMarkup(inline_keyboard=kb_rows)

@router.message(Command("sendall"))
async def broadcast_message_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    raw_text = (message.caption or message.text or "").replace("/sendall", "").strip()
    
    photo_file_id = None
    if message.photo:
        photo_file_id = message.photo[-1].file_id
    elif message.reply_to_message and message.reply_to_message.photo:
        photo_file_id = message.reply_to_message.photo[-1].file_id
        if not raw_text and message.reply_to_message.caption:
            raw_text = message.reply_to_message.caption

    if not raw_text and not photo_file_id:
        await message.answer(
            "⚠️ **Matn yoki Rasm topilmadi!**\n\n"
            "📌 **Qanday ishlatiladi:**\n"
            "1. **Oddiy Matn:** `/sendall Assalomu alaykum!`\n"
            "2. **HTML Shriftlar:** `/sendall <b>Qalin</b>, <i>Qiya</i>, <code>Kod</code> matn`\n"
            "3. **Tugma Bilan:** `/sendall Xabar matni... | Kanalimiz -> https://t.me/tezfit`\n"
            "4. **Rasm Bilan:** Rasmni yuklab izohiga `/sendall Matn` yozing yoki rasmga `/sendall` deb javob bering!",
            parse_mode="Markdown"
        )
        return

    clean_text, broadcast_kb = parse_broadcast_text_and_kb(raw_text if raw_text else " ")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User.telegram_id))
        user_ids = result.scalars().all()

    success_count = 0
    fail_count = 0

    status_msg = await message.answer(f"⏳ `{len(user_ids)}` ta foydalanuvchiga xabar tarqatilmoqda...", parse_mode="Markdown")

    for tg_id in user_ids:
        try:
            if photo_file_id:
                await message.bot.send_photo(
                    chat_id=tg_id,
                    photo=photo_file_id,
                    caption=clean_text if clean_text != " " else None,
                    parse_mode="HTML",
                    reply_markup=broadcast_kb
                )
            else:
                await message.bot.send_message(
                    chat_id=tg_id,
                    text=clean_text,
                    parse_mode="HTML",
                    reply_markup=broadcast_kb
                )
            success_count += 1
        except Exception:
            try:
                if photo_file_id:
                    await message.bot.send_photo(chat_id=tg_id, photo=photo_file_id, caption=clean_text, reply_markup=broadcast_kb)
                else:
                    await message.bot.send_message(chat_id=tg_id, text=clean_text, reply_markup=broadcast_kb)
                success_count += 1
            except Exception:
                fail_count += 1

    await status_msg.edit_text(
        f"📢 **XABAR TARQATISH YAKUNLANDI!**\n\n"
        f"🖼 **Format:** {'Rasm + Matn' if photo_file_id else 'Matn'}\n"
        f"✅ Muvaffaqiyatli yuborildi: {success_count} ta\n"
        f"❌ Yetib bormadi (bloklangan): {fail_count} ta\n\n"
        f"📱 *Bot va Web App foydalanuvchilariga yetkazildi!*",
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("approve_vip_"))
async def approve_vip_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat yo'q!", show_alert=True)
        return

    parts = call.data.split("_")
    target_tg_id = int(parts[2])
    plan_type = parts[3] if len(parts) > 3 else "monthly"

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == target_tg_id))
        user = result.scalar_one_or_none()

        if user:
            user.is_vip = True
            await session.commit()

    try:
        await call.bot.send_message(
            chat_id=target_tg_id,
            text=(
                f"🎉 **TABRIKLAYMIZ! TEZFIT PREMIUM STATUSINGIZ FAOLLASHTIRILDI!** 👑\n\n"
                f"Sizning **{plan_type.upper()}** Premium to'lov chekingiz admin tomonidan muvaffaqiyatli tasdiqlandi!\n\n"
                f"✨ **Yangi imkoniyatlaringiz:**\n"
                f"• ♾️ Cheksiz AI taom skanerlash\n"
                f"• 🧬 Chuqur Vitamin & Mineral tahlili\n"
                f"• 📅 Barcha o'tgan kunlar tarixi\n"
                f"• 📄 Haftalik PDF hisobot yuklab olish\n"
                f"• 👑 Oltin nishon va profil ramkasi!\n\n"
                f"Ilovaga kirib cheksiz imkoniyatlardan foydalanishingiz mumkin! 🚀"
            ),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="📱 Web App-da Ochish", web_app=WebAppInfo(url=f"{settings.WEB_APP_URL}?v=2.9.0"))]]
            )
        )
    except Exception:
        pass

    if call.message.caption:
        await call.message.edit_caption(
            caption=f"{call.message.caption}\n\n✅ **ADMIN TOMONIDAN TASDIQLANDI! (PREMIUM BERILDI)**",
            reply_markup=None
        )
    else:
        await call.message.edit_text(
            text=f"{call.message.text}\n\n✅ **ADMIN TOMONIDAN TASDIQLANDI! (PREMIUM BERILDI)**",
            reply_markup=None
        )
    await call.answer("Premium muvaffaqiyatli berildi!")

@router.callback_query(F.data.startswith("reject_vip_"))
async def reject_vip_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat yo'q!", show_alert=True)
        return

    parts = call.data.split("_")
    target_tg_id = int(parts[2])

    try:
        await call.bot.send_message(
            chat_id=target_tg_id,
            text="⚠️ Sizning TezFIT Premium to'lov chekingiz tekshirildi, lekin tasdiqlanmadi. Savollar bo'lsa @abdurokhman_dev ga murojaat qiling.",
        )
    except Exception:
        pass

    if call.message.caption:
        await call.message.edit_caption(
            caption=f"{call.message.caption}\n\n❌ **TO'LOV RAD ETILDI**",
            reply_markup=None
        )
    else:
        await call.message.edit_text(
            text=f"{call.message.text}\n\n❌ **TO'LOV RAD ETILDI**",
            reply_markup=None
        )
    await call.answer("To'lov rad etildi.")
