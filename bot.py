import sqlite3
import logging
import re
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Sizning Admin ID raqamingiz
ADMIN_ID = 7807649802 
BOT_TOKEN = "9115969021:AAGHuVQ3kMxg_jRptAChuKjOhAT2hudvYFE"

# 1. Ma'lumotlar bazasi
conn = sqlite3.connect('challenge.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        points INTEGER DEFAULT 0
    )
''')
conn.commit()

logging.basicConfig(level=logging.INFO)

# 2. /start buyrug'i
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if user.id == ADMIN_ID:
        await update.message.reply_text(
            "Assalomu alaykum, Xonim! 👑 Bot boshqaruvchisi sifatida tayyorsiz.\n\n"
            "Barcha ishtirokchilarning umumiy bazasini ko'rish uchun quyidagi buyruqni yuboring:\n"
            "👉 /admin"
        )
        return

    cursor.execute('SELECT full_name FROM users WHERE user_id = ?', (user.id,))
    result = cursor.fetchone()
    
    if result and result[0]:
        await update.message.reply_text(
            f"Salom, {result[0]}! Siz allaqachon ro'yxatdan o'tgansiz. ✅\n\n"
            "Vazifalaringizni hashtaglar orqali yuborishingiz mumkin:\n"
            "• #tong — 10 ball\n"
            "• #kardio — 20 ball\n"
            "• #dars [soat] — 10 ball/soat\n"
            "• #tahlil — 20 ball\n\n"
            "/statistika — Shaxsiy ballingiz"
        )
    else:
        await update.message.reply_text(
            "Assalomu alaykum! 21 kunlik Challenge botiga xush kelibsiz. 🏆\n\n"
            "Iltimos, ro'yxatdan o'tish uchun **Ism va Familiyangizni** yuboring (Masalan: *Aziza Qudratova*):",
            parse_mode="Markdown"
        )

# 3. /admin buyrug'i
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Kechirasiz, bu buyruq faqat bot boshqaruvchisi uchun!")
        return
    
    cursor.execute('SELECT full_name, username, points FROM users ORDER BY points DESC')
    all_users = cursor.fetchall()
    
    text = "👑 **ADMIN BAZASI: BARCHA ISHTIROKCHILAR** 👑\n\n"
    if not all_users:
        text += "Hozircha bazada ro'yxatdan o'tgan ishtirokchilar yo'q."
    else:
        for idx, (name, uname, pts) in enumerate(all_users, start=1):
            username_str = f"(@{uname})" if uname else ""
            text += f"{idx}. **{name or 'Noma\'lum'}** {username_str} — 🏆 **{pts or 0} ball**\n"

    await update.message.reply_text(text, parse_mode="Markdown")

# 4. /statistika buyrug'i
async def statistika(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == ADMIN_ID:
        await update.message.reply_text("Siz bot boshqaruvchisisiz. Ishtirokchilar bazasini ko'rish uchun /admin buyrug'ini yuboring.")
        return

    cursor.execute('SELECT full_name, points FROM users WHERE user_id = ?', (user.id,))
    result = cursor.fetchone()
    
    if result and result[0]:
        name, points = result
        await update.message.reply_text(f"👤 Ism: {name}\n🏆 To'plagan ballingiz: {points} ball")
    else:
        await update.message.reply_text("Siz hali ro'yxatdan o'tmagansiz. /start buyrug'ini bosing.")

# 5. Xabarlar va hashtaglar orqali ball hisoblash
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or ""
    
    if user.id == ADMIN_ID:
        await update.message.reply_text("Buyruqlardan foydalaning. Masalan: /admin")
        return

    cursor.execute('SELECT full_name, points FROM users WHERE user_id = ?', (user.id,))
    user_row = cursor.fetchone()
    
    if not user_row or not user_row[0]:
        full_name = text.strip()
        if len(full_name) < 3:
            await update.message.reply_text("⚠️ Iltimos, to'liq Ism va Familiyangizni kiriting:")
            return
        
        cursor.execute('''
            INSERT INTO users (user_id, username, full_name, points)
            VALUES (?, ?, ?, 0)
            ON CONFLICT(user_id) DO UPDATE SET full_name = ?
        ''', (user.id, user.username, full_name, full_name))
        conn.commit()
        
        await update.message.reply_text(
            f"✅ Rahmat, {full_name}! Muvaffaqiyatli ro'yxatdan o'tdingiz.\n\n"
            "Vazifalaringizni hashtaglar orqali yuborishingiz mumkin!"
        )
        return

    current_points = user_row[1] or 0
    added_points = 0
    response_msg = ""
    text_lower = text.lower()

    if "#tong" in text_lower:
        added_points += 10
        response_msg += "☀️ #tong uchun +10 ball qo'shildi!\n"
    
    if "#kardio" in text_lower:
        added_points += 20
        response_msg += "❤️ #kardio uchun +20 ball qo'shildi!\n"
        +
    if "#tahlil" in text_lower:
        added_points += 20
        response_msg += "📊 #tahlil uchun +20 ball qo'shildi!\n"

    dars_match = re.search(r'#dars\s+(\d+)', text_lower)
    if dars_match:
        hours = int(dars_match.group(1))
        dars_pts = hours * 10
        added_points += dars_pts
        response_msg += f"📚 #dars ({hours} soat) uchun +{dars_pts} ball qo'shildi!\n"

    if added_points > 0:
        new_total = current_points + added_points
        cursor.execute('UPDATE users SET points = ? WHERE user_id = ?', (new_total, user.id))
        conn.commit()
        await update.message.reply_text(
            f"✅ Hisobingiz yangilandi!\n\n{response_msg}\n🏆 Jami ballingiz: **{new_total} ball**",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("📝 Xabaringiz qabul qilindi! Ball olish uchun to'g'ri hashtag yuboring.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("statistika", statistika))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot ishga tushdi...")
    app.run_polling()

if __name__ == '__main__':
    main()
