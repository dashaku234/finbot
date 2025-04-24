
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from collections import defaultdict

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set!")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

user_data = defaultdict(lambda: {"balance": 0, "income": 0, "expense": 0})
allowed_users = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username not in allowed_users:
        button = [[InlineKeyboardButton("💳 Оплатить 349₽", url="https://pay.cloudtips.ru/p/e7e1cfae")]]
        reply_markup = InlineKeyboardMarkup(button)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Добро пожаловать в ФинБот 💼\n\nЗдесь ты можешь вести личный учёт доходов и расходов.\n\nДоступ открывается после разового платежа 349₽.",
            reply_markup=reply_markup
        )
        return
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="ФинБот готов. Введи доход или расход:\nНапример: Потратил 500 на еду"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username not in allowed_users:
        return

    text = update.message.text.lower()
    uid = user.username
    if any(word in text for word in ["потратил", "заплатил", "расход"]):
        amount = [int(s) for s in text.split() if s.isdigit()]
        if amount:
            user_data[uid]["expense"] += amount[0]
            user_data[uid]["balance"] -= amount[0]
            await update.message.reply_text(f"Записал расход: -{amount[0]}₽")
    elif any(word in text for word in ["получил", "доход", "заработал"]):
        amount = [int(s) for s in text.split() if s.isdigit()]
        if amount:
            user_data[uid]["income"] += amount[0]
            user_data[uid]["balance"] += amount[0]
            await update.message.reply_text(f"Записал доход: +{amount[0]}₽")
    else:
        await update.message.reply_text("Не понял формат. Напиши, например: Потратил 500 на еду")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username not in allowed_users:
        return
    uid = user.username
    stats = user_data[uid]
    msg = f"📊 Статистика:\nДоход: {stats['income']}₽\nРасход: {stats['expense']}₽\nБаланс: {stats['balance']}₽"
    await update.message.reply_text(msg)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username not in allowed_users:
        return
    user_data[user.username] = {"balance": 0, "income": 0, "expense": 0}
    await update.message.reply_text("Все данные сброшены.")

async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Если ты оплатил — жди активации. Я включу тебе доступ вручную.")

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != "your_admin_username":
        await update.message.reply_text("Недостаточно прав.")
        return
    if context.args:
        username = context.args[0].lstrip("@")
        allowed_users.add(username)
        await update.message.reply_text(f"Пользователь @{username} активирован.")
    else:
        await update.message.reply_text("Укажи username после команды.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("начать", start))
    app.add_handler(CommandHandler("оплатил", paid))
    app.add_handler(CommandHandler("активировать", activate))
    app.add_handler(CommandHandler("статистика", stats))
    app.add_handler(CommandHandler("сброс", reset))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
