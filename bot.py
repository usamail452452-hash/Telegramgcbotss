import os
import random
import time
from datetime import datetime
import pytz
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = "8312816041:AAFavkODcQfygSqAr__DGm8udg5GVUu7JZ8"
ADMIN_URL = "https://t.me/vanilarefu"
SUPPORT_URL = "https://t.me/Vanilagcm"
TON_ADDRESSES = [
    "UQCgPsBnvSib5rYln5vK0rNfYo__xjfk5OD-0mKU7-n1ACnT",
    "UQCCTTF03CCeyNKov1azQty5iNcNMnwH72J7pcb7MUaDKXsd",
    "UQAZjMCIT6MEMUgvKmweTySPrGqxnUrgvG5JQVUfnR-d_tke",
    "UQBwwD_2VekRaM-7_6wwltzkboxbTiYDqif40G9Tbnq76Td1",
    "UQAMBt7k1FZHvewkpB1IHMLiOMLZR63rO_NKv-fiQ0n5EGW_",
    "UQC9OvldFlHMbxKRq-6yRTm9uWv-YWFcsywHQAZz6p9dtonc"
]

BINS = {
    "JOKER": ["533985xx", "461126xx"],
    "AMEX": ["373778xx", "377935xx", "375163xx"],
    "VANILA": ["411810xx", "409758xx", "520356xx", "525362xx", "484718xx", "545660xx"],
    "CARDBALANCE": ["428313xx", "432465xx", "457824xx"],
    "WALMART": ["485246xx"],
    "GCM": ["451129xx", "403446xx", "435880xx", "511332xx"],
    "OTHER": ["435880xx", "491277xx", "428313xx", "520356xx", "409758xx", "525362xx", "451129xx", "434340xx", "426370xx", "411810xx", "403446xx", "533621xx", "446317xx", "457824xx", "545660xx", "432465xx", "516612xx", "484718xx", "485246xx", "402372xx", "457851xx"]
}

# --- GLOBAL DATA ---
cached_cards = []
last_update_day = ""

# --- FLASK SERVER FOR RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

# --- BOT LOGIC ---

def is_updating():
    tz = pytz.timezone('Asia/Dhaka')
    now = datetime.now(tz)
    start_update = now.replace(hour=3, minute=0, second=0, microsecond=0)
    end_update = now.replace(hour=3, minute=10, second=0, microsecond=0)
    return start_update <= now <= end_update

def generate_daily_cards():
    global cached_cards
    cards = []
    total_count = random.randint(200, 250)
    
    # Pre-defined Logic for amounts
    # High balance cards ($300-$500)
    for _ in range(random.randint(10, 15)):
        cards.append(create_card(300, 500, no_sticker=True))
    
    # $20 range cards
    for _ in range(random.randint(20, 30)):
        cards.append(create_card(15, 25))
        
    # $5-$40 range (most common)
    for _ in range(100):
        cards.append(create_card(5, 40))

    # Cents cards
    for _ in range(random.randint(15, 20)):
        cards.append(create_card(0.10, 0.99))

    # Fill remaining
    while len(cards) < total_count:
        cards.append(create_card(1, 100))

    # Sort: Highest to Lowest
    cards.sort(key=lambda x: x['balance'], reverse=True)
    cached_cards = cards

def create_card(min_bal, max_bal, no_sticker=False):
    all_bins = [bin for sublist in BINS.values() for bin in sublist]
    bin_num = random.choice(all_bins)
    currency = "CAD" if bin_num in ["533985xx", "461126xx"] else "USD"
    if bin_num in ["373778xx", "377935xx", "375163xx"]: currency = "AUD"
    
    balance = round(random.uniform(min_bal, max_bal), 2)
    
    sticker = ""
    if not no_sticker:
        chance = random.random()
        if chance < 0.10: sticker = "🔄"
        elif chance < 0.15: sticker = "🅶 🅿"
        elif chance < 0.23: sticker = "🔄 🅶"
        elif chance < 0.27: sticker = "🅿"
        elif chance < 0.35: sticker = "🅶"
    
    return {
        "bin": bin_num,
        "currency": currency,
        "balance": balance,
        "sticker": sticker,
        "stock": True,
        "is_unreg": balance < 15 and random.random() < 0.2
    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (f"⚡️ Welcome {user.first_name} to Vanila exchange !\n"
            f"Sell, Buy, and strike deals in seconds!!\n"
            f"All transactions are secure and transparent.\n"
            f"All types of cards are available here at best rates. Current rate is 37%")
    
    keyboard = [
        [InlineKeyboardButton("💳 Stock", callback_data="view_stock")],
        [InlineKeyboardButton("📞 Contact Admin", url=ADMIN_URL)]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def stock_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if is_updating():
        await query.answer("The bot is currently updating, please wait", show_alert=True)
        return

    await query.answer()
    await show_page(query, context, 0)

async def show_page(query, context, page_num, filter_name="None"):
    cards = cached_cards
    
    if filter_name != "None":
        filter_bins = BINS.get(filter_name, [])
        cards = [c for c in cards if c["bin"] in filter_bins]
    
    per_page = 10
    total_pages = max(1, (len(cards) + per_page - 1) // per_page)
    page_num = max(0, min(page_num, total_pages - 1))
    
    start_idx = page_num * per_page
    page_cards = cards[start_idx:start_idx + per_page]
    
    lines = [f"💳 *Card Stock* — Page {page_num + 1}/{total_pages}\n"]
    for i, card in enumerate(page_cards, start=start_idx + 1):
        sticker = card["sticker"] + " " if card["sticker"] else ""
        unreg = " _(unregistered)_" if card["is_unreg"] else ""
        lines.append(f"{i}. {sticker}`{card['bin']}` — *{card['currency']} {card['balance']:.2f}*{unreg}")
    
    text = "\n".join(lines)
    
    nav_buttons = []
    if page_num > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page_{page_num - 1}_{filter_name}"))
    if page_num < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_{page_num + 1}_{filter_name}"))
    
    filter_buttons = [
        InlineKeyboardButton(name, callback_data=f"filter_{name}")
        for name in BINS.keys()
    ]
    filter_rows = [filter_buttons[i:i+3] for i in range(0, len(filter_buttons), 3)]
    
    keyboard = []
    if nav_buttons:
        keyboard.append(nav_buttons)
    keyboard.extend(filter_rows)
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_main")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def page_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_", 2)
    page_num = int(parts[1])
    filter_name = parts[2] if len(parts) > 2 else "None"
    await show_page(query, context, page_num, filter_name)

async def filter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    filter_name = query.data.split("_", 1)[1]
    await show_page(query, context, 0, filter_name)

async def back_main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    text = (f"⚡️ Welcome {user.first_name} to Vanila exchange !\n"
            f"Sell, Buy, and strike deals in seconds!!\n"
            f"All transactions are secure and transparent.\n"
            f"All types of cards are available here at best rates. Current rate is 37%")
    keyboard = [
        [InlineKeyboardButton("💳 Stock", callback_data="view_stock")],
        [InlineKeyboardButton("📞 Contact Admin", url=ADMIN_URL)]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def main():
    generate_daily_cards()
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(stock_handler, pattern="^view_stock$"))
    application.add_handler(CallbackQueryHandler(page_handler, pattern="^page_"))
    application.add_handler(CallbackQueryHandler(filter_handler, pattern="^filter_"))
    application.add_handler(CallbackQueryHandler(back_main_handler, pattern="^back_main$"))

    Thread(target=run).start()
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    import asyncio
    await asyncio.Event().wait()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
