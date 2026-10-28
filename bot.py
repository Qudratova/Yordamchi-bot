import os
import sqlite3
from datetime import datetime
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

TOKEN = os.getenv("9115969021:AAGHuVQ3kMxg_jRptAChuKjOhAT2hudvYFE")
ADMIN_ID = 7807649802  # O'zingizning Telegram ID raqamingizni yozing

# Ro'yxatdan o'tish holati uchun bosqich
GET_NAME = 1

# --- BAZA BILAN ISHLASH QISMI ---
def init_db():
    conn = sqlite3.connect('challenge.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            points INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('challenge.db')
    cursor = conn.cursor()
    cursor.execute('SELECT full_name, points FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def register_user(user_id, full_name):
    conn = sqlite3.connect('challenge.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO users (user_id, full_name, points) VALUES (?, ?, COALESCE((SELECT points FROM users WHERE user_id = ?), 0))', 
                   (user_id, full_name, user_id))
    conn.commit()
    conn.close()

def add_points(user_id, earned_points):
    conn = sqlite3.connect('challenge.db')
    cursor = conn.cursor()
    cursor.execute('SELECT points FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if user:
        new_points = user[0] + earned_points
        cursor.execute('UPDATE users SET points = ? WHERE user_id = ?', (new_points, user_id))
    else:
        new_points = earned_points
    conn.commit()
    conn.close()
    return new_points

def get_leaderboard():
    conn = sqlite3.connect('challenge.db')
    cursor = conn.cursor()
    cursor.execute('SELECT full_name, points FROM users ORDER BY points DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()
    return rows

# /start buyrug'i va ro'yxatdan o'tishni boshlash
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if user:
        # Agar oldindan ro'yxatdan o'tgan bo'lsa
        full_name = user[0]
        text = (
            f"Salom, <b>{full_name}</b>!\n\n"
            "🏆 <b>21 kunlik Challenge botiga xush kelibsiz!</b>\n"
            "Vazifalaringizni rasm va tegishli heshteg bilan yuboring:\n"
            "• <b>#tong</b> (03:00 - 06:00) — 10 ball\n"
            "• <b>#kardio</b> (07:00 gacha) — 20 ball\n"
            "• <b>#dars [soat]</b> (23:59 gacha) — Har bir soat uchun 10 ball\n"
            "• <b>#tahlil</b> (23:59 gacha) — 20 ball\n\n"
            "📊 O'z ballaringizni ko'rish uchun /reyting buyrug'ini yuboring."
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return ConversationHandler.END
    else:
        # Ro'yxatdan o'tmagan bo'lsa, ism-familiya so'raymiz
        await update.message.reply_text(
            "🏆 <b>21 kunlik Challenge botiga xush kelibsiz!</b>\n\n"
            "Ishtirok etish uchun iltimos, **Ism va Familiyangizni** kiriting (masalan: <i>Azizbek Rahimov</i>):",
            parse_mode="HTML"
        )
        return GET_NAME

# Ism-familiyani qabul qilib saqlash
async def save_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    full_name = update.message.text.strip()
    
    if len(full_name) < 3:
        await update.message.reply_text("⚠️ Iltimos, haqiqiy Ism va Familiyangizni to'liq kiriting:")
        return GET_NAME

    register_user(user_id, full_name)
    
    await update.message.reply_text(
        f"✅ Rahmat, <b>{full_name}</b>! Siz muvaffaqiyatli ro'yxatdan o'tdingiz.\n\n"
        "Endi har kuni vazifalaringizni rasm va heshteg bilan yuborishingiz mumkin:\n"
        "• <b>#tong</b> (03:00 - 06:00) — 10 ball\n"
        "• <b>#kardio</b> (07:00 gacha) — 20 ball\n"
        "• <b>#dars [soat]</b> (23:59 gacha) — Har bir soat uchun 10 ball\n"
        "• <b>#tahlil</b> (23:59 gacha) — 20 ball\n\n"
        "Reytingni ko'rish uchun /reyting buyrug'idan foydalaning.",
        parse_mode="HTML"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Jarayon bekor qilindi. Qaytadan boshlash uchun /start bosing.")
    return ConversationHandler.END

# /help buyrug'i
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>📌 Challenge qoidalari va vaqtlari:</b>\n\n"
        "1. <b>#tong</b>: 03:00 - 06:00 (+10 ball)\n"
        "2. <b>#kardio</b>: 07:00 gacha (+20 ball)\n"
        "3. <b>#dars [soat]</b>: 23:59 gacha (Masalan: <i>#dars 2</i> — 2 soat uchun 20 ball)\n"
        "4. <b>#tahlil</b>: 23:59 gacha (+20 ball)\n\n"
        "📊 /reyting - Ishtirokchilar reytingini ko'rish"
    )
    await update.message.reply_text(text, parse_mode="HTML")

# /reyting buyrug'i
async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    leaders = get_leaderboard()
    if not leaders:
        await update.message.reply_text("Hozircha reytingda ishtirokchilar yo'q.")
        return
    
    text = "🏆 <b>Top Ishtirokchilar Reytingi:</b>\n\n"
    for index, (full_name, points) in enumerate(leaders, start=1):
        text += f"{index}. {full_name} — <b>{points} ball</b>\n"
    
    await update.message.reply_text(text, parse_mode="HTML")

# Xabarlar va vazifalarni qabul qilish
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("⚠️ Avval ro'yxatdan o'tishingiz kerak! Iltimos, /start buyrug'ini yuboring.")
        return

    full_name = user[0]
    message = update.message
    caption = message.caption or message.text or ""
    caption_lower = caption.lower()
    
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    total_minutes = current_hour * 60 + current_minute

    points = 0
    task_name = ""

    # 1. #tong (03:00 - 06:00) -> 10 ball
    if "#tong" in caption_lower:
        task_name = "#tong"
        if 180 <= total_minutes <= 360:
            points = 10
        else:
            await message.reply_text("❌ #tong vazifasi faqat 03:00 dan 06:00 gacha qabul qilinadi!")
            return

    # 2. #kardio (07:00 gacha) -> 20 ball
    elif "#kardio" in caption_lower:
        task_name = "#kardio"
        if total_minutes <= 420:
            points = 20
        else:
            await message.reply_text("❌ #kardio vazifasi 07:00 dan keyin qabul qilinmaydi!")
            return

    # 3. #dars (23:59 gacha) -> Har bir soat uchun 10 ball
    elif "#dars" in caption_lower:
        task_name = "#dars"
        if total_minutes <= 1439:
            parts = caption_lower.split()
            hours = 1
            for i, p in enumerate(parts):
                if "#dars" in p and i + 1 < len(parts):
                    try:
                        hours = int(parts[i+1])
                    except ValueError:
                        hours = 1
            points = hours * 10
        else:
            await message.reply_text("❌ Vaqt tugadi! #dars 23:59 gacha qabul qilinadi.")
            return

    # 4. #tahlil (23:59 gacha) -> 20 ball
    elif "#tahlil" in caption_lower:
        task_name = "#tahlil"
        if total_minutes <= 1439:
            points = 20
        else:
            await message.reply_text("❌ Vaqt tugadi! #tahlil 23:59 gacha qabul qilinadi.")
            return
    else:
        return

    # Agar ball berilsa, bazaga yozamiz
    if points > 0:
        total_user_points = add_points(user_id, points)
        
        await message.reply_text(
            f"✅ Vazifangiz qabul qilindi, {full_name}!\n"
            f"📌 {task_name} uchun +{points} ball qo'shildi.\n"
            f"⭐ Jami ballingiz: {total_user_points}"
        )
        
        # Adminga yo'naltirish
        if ADMIN_ID and ADMIN_ID != 123456789:
            try:
                user_info = f"👤 Ishtirokchi: {full_name}\n📌 Vazifa: {task_name} (+{points} ball)\n⭐ Jami: {total_user_points}"
                await context.bot.send_message(chat_id=ADMIN_ID, text=f"📥 <b>Yangi vazifa!</b>\n\n{user_info}", parse_mode="HTML")
                await message.forward(chat_id=ADMIN_ID)
            except Exception as e:
                print(f"Adminga yuborishda xatolik: {e}")

def main():
    if not TOKEN:
        print("Xatolik: TOKEN topilmadi!")
        return

    init_db()  # Ma'lumotlar bazasini yaratish

    application = ApplicationBuilder().token(TOKEN).build()

    # Ro'yxatdan o'tish dialogi uchun ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_name)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reyting", leaderboard_command))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    print("Bot to'liq tayyor va ishga tushdi...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
