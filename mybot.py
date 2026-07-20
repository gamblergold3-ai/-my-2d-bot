import logging
import sqlite3
import requests
from datetime import datetime, timedelta

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters
)

logging.basicConfig(level=logging.INFO)

TOKEN = "8981174805:AAH7wymmdjVyZe-jkf1U0-EiJaM94Dl-sgM"
ADMIN_ID = 6525812489
vip_users = []

main_keyboard = ReplyKeyboardMarkup(
    [
        ["🎯 Crypto ထိုးရန်", "⭐ ShineHope ထိုးရန်"],
        ["💰 Crypto2d Ngweသွင်းရန်", "💰 Shinehope2d Ngweသွင်းရန်"]
    ],
    resize_keyboard=True
)

# ===== Database =====

def init_db():
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pages(
        name TEXT PRIMARY KEY,
        text TEXT
    )""")
    
    # ⏱️ VIP သက်တမ်းနှင့် ကြည့်ရှုကြိမ်ရေ သိမ်းမည့် Table အသစ် (အဟောင်းနေရာတွင် ထပ်မံပြင်ဆင်ခြင်း)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vip(
        user_id INTEGER PRIMARY KEY,
        joined_date TEXT,
        view_count INTEGER DEFAULT 0
    )""")
    
    # 📊 Admin တင်မည့် VIP ဂဏန်းများ သိမ်းဆည်းရန် Table အသစ်
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vip_data(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_text TEXT,
        main_numbers TEXT,
        hot_numbers TEXT
    )""")
    
    conn.commit()
    conn.close()


init_db()

def get_live_data():
    try:
        url = "https://api.thaistock2d.com/live"
        data = requests.get(url, timeout=10).json()

        live = data["live"]["twod"]
        result = data["result"]

        text = f"📊 2D LIVE\n\n"
        text += f"🔴 Live : {live}\n\n"
        text += "🏆 MAIN RESULT\n\n"

        main = {"12:01": "", "4:30": ""}
        other = ""

        times = {
            "11:00:00": "11:00",
            "12:01:00": "12:01",
            "15:00:00": "3:00",
            "16:30:00": "4:30"
        }

        for r in result:
            t = times.get(r["open_time"], r["open_time"])
            if t in main:
               main[t] = r["twod"]
            else:
               other += f"{t} ➜ {r['twod']}\n"

        text += f"🟢 12:01 ➜ {main['12:01']}\n"
        text += f"🔵 4:30 ➜ {main['4:30']}\n\n"
        text += "────────────\n"
        text += other

        return text
    except Exception:
        return "❌ Live Data မရရှိနိုင်ပါ။"

def get_crypto_live_data():
    try:
        # 🔗 အာရှဆာဗာနှင့် 2d_result လမ်းကြောင်းအမှန်ကို ကွက်တိ ထည့်သွင်းထားပါသည်
        url = "https://admin-18bf0-default-rtdb.asia-southeast1.firebasedatabase.app/2d_result.json"
        data = requests.get(url, timeout=10).json()
        
        if not data:
            return "❌ Firebase ထဲတွင် မည်သည့်ဒေတာမျှ ရှာမတွေ့ပါ။"
            
        # 🎯 displaynumber -> Live_Now -> number လမ်းကြောင်းအတိုင်း Live ဂဏန်းယူခြင်း
        disp_data = data.get("displaynumber", {})
        live_now_data = disp_data.get("Live_Now", {})
        live = live_now_data.get("number", "-")
        
        from datetime import datetime

        # 🎯 ဒီနေ့ daily_history ပဲယူမည်
        today = datetime.now().strftime("%Y-%m-%d")

        daily_history = data.get("daily_history", {})
        result = daily_history.get(today, {})
        
        times = [
            "05:00PM", "06:00PM", "07:00PM", "08:00PM", "09:00PM",
            "10:00PM", "10:30PM", "11:00PM", "11:30PM", "12:00PM"
        ]
        
        text = "🔴 **CRYPTO 2D LIVE**\n\n"
        text += f"🔴 Live : **{live}**\n\n"
        text += "🏆 **RESULT**\n\n"
        
        # အချိန်အလိုက် ရလဒ်များကို ရှာဖွေပြီး စာသားစီခြင်း
        for t in times:
            number = result.get(t, "")
            if number:
                text += f"🟢 {t} ➜ **{number}**\n"
            else:
                text += f"⚪ {t} ➜ **-**\n"
                
        return text


    except Exception:
        return "❌ Crypto Data မရရှိပါ"

def get_page(name):
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    cur.execute(
        "SELECT text FROM pages WHERE name=?",
        (name,)
    )

    row = cur.fetchone()

    conn.close()

    return row[0] if row else "စာမရှိသေးပါ"


# ===== Start Menu =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [

        ["📊 2D LIVE"],

        ["🔴 CRYPTO2D LIVE"],

        ["🎯 Crypto ထိုးရန်",
         "⭐ ShineHope ထိုးရန်"],

        ["💰 အထိုးဇယား / ငွေလွှဲ"],

        ["🔮 VIP အခန်း"],

        ["💳 Member ကြေးလွှဲရန်"],

        ["📚 အခြား 2D"],

        ["👨‍💻 Admin သို့"]

    ]

    menu = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


    await update.message.reply_text(
        "မင်္ဂလာပါ\nMenu ရွေးပါ",
        reply_markup=menu
    )
# ===== Button Reply System =====

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text


    if text == "📊 2D LIVE":
        await update.message.reply_text(get_live_data())

    elif text == "🔴 CRYPTO2D LIVE":

        await update.message.reply_text(
          get_crypto_live_data()
        )

    elif text == "🎯 Crypto ထိုးရန်":

        context.user_data["waiting_crypto"] = True

        await update.message.reply_text(
            "🎯 Crypto 2D ထိုးရန်\n\n"
            "ဂဏန်းနှင့် ပမာဏ ပို့ပါ။\n\n"
            "ဥပမာ - 00 700"
        )

    elif context.user_data.get("waiting_crypto"):

        context.user_data["waiting_crypto"] = False

        user = update.effective_user
        bet = text

        admin_text = (
            f"🎯 Crypto 2D\n\n"
            f"👤 Name : {user.first_name}\n"
            f"📛 Username : @{user.username}\n"
            f"🆔 User ID : {user.id}\n\n"
            f"📝 ထိုးကွက် :\n{bet}"
        )

        keyboard = InlineKeyboardMarkup([
          [
            InlineKeyboardButton("✅ အတည်ပြု",
        callback_data=f"ok_{user.id}"),
            InlineKeyboardButton("❌ ပယ်ဖျက်",
        callback_data=f"no_{user.id}")
          ]
        ])

        await context.bot.send_message(
           chat_id=ADMIN_ID,
           text=admin_text,
           reply_markup=keyboard
        )

        # Crypto ထိုးကွက် ပို့လာပါက ပြန်မည့် စာသားအသစ်
        await update.message.reply_text(
            "👉 ထိုးကြေးကျသင့်ငွေပေးသွင်းရန်(အထိုးဇယား/ငွေလွှဲ)ခလုတ်ကိုနှိပ်ပါ။",
        )


    elif text == "⭐ ShineHope ထိုးရန်":

        context.user_data["waiting_shinehope"] = True

        await update.message.reply_text(
            "⭐ Shinehope 2D ထိုးရန်\n\n"
            "ဂဏန်းနှင့် ပမာဏ ပို့ပါ။\n\n"
            "ဥပမာ - 00 700"
        )

    elif context.user_data.get("waiting_shinehope"):

        context.user_data["waiting_shinehope"] = False

        user = update.effective_user
        bet = text

        admin_text = (
            f"🎯 Shinehope 2D\n\n"
            f"👤 Name : {user.first_name}\n"
            f"📛 Username : @{user.username}\n"
            f"🆔 User ID : {user.id}\n\n"
            f"📝 ထိုးကွက် :\n{bet}"
        )

        keyboard = InlineKeyboardMarkup([
          [
            InlineKeyboardButton("✅ အတည်ပြု",
        callback_data=f"shineok_{user.id}"),
            InlineKeyboardButton("❌ ပယ်ဖျက်",
        callback_data=f"shineno_{user.id}")
          ]
        ])

        await context.bot.send_message(
           chat_id=ADMIN_ID,
           text=admin_text,
           reply_markup=keyboard
        )

        await update.message.reply_text(
            "👉 ထိုးကြေးကျသင့်ငွေပေးသွင်းရန်(အထိုးဇယား/ငွေလွှဲ)ခလုတ်ကိုနှိပ်ပါ။",
        )


    elif text == "💰 အထိုးဇယား / ငွေလွှဲ" or text == "💰 အထူးဇယား / ငွေလွှဲ":
        await update.message.reply_text(
            text="💰 မိမိ Ngweသွင်းလိုသော 2Dအမျိုးအစား ခလုတ်ကို အောက်တွင် ရွေးချယ်ပေးပါရန်။",
            reply_markup=main_keyboard
        )


    # 🎯 ၁။ Crypto2d Ngweသွင်းရန် ခလုတ် နှိပ်ခဲ့လျှင်
    elif text == "💰 Crypto2d Ngweသွင်းရန်":
        context.user_data["receipt_type"] = "crypto"
        money_text = f"""💰 **Crypto2d Ngweသွင်းရန် လမ်းညွှန်ချက်** 💰

📱 *KPay Account*
 ➡ နံပါတ် - 09428176370
 ➡ အမည် - Ko Kyawthura

📱 *WaveMoney Account*
 ➡ နံပါတ် - 09428176370
 ➡ အမည် - Ko Kyawthura

⚠️ Ngweလွှဲပြီးပါက ဤနေရာတွင် 'Ngweလွှဲပြေစာ (Screenshot)' ဓာတ်ပုံကို တိုက်ရိုက် ပေးပို့ပေးပါရန်။"""
        await update.message.reply_text(money_text, parse_mode="Markdown")

    # ⭐ ၂။ Shinehope2d Ngweသွင်းရန် ခလုတ် နှိပ်ခဲ့လျှင်
    elif text == "💰 Shinehope2d Ngweသွင်းရန်":
        context.user_data["receipt_type"] = "shine"
        money_text = f"""💰 **Shinehope2d Ngweသွင်းရန် လမ်းညွှန်ချက်** 💰

📱 *KPay Account*
 ➡ နံပါတ် - 09428176370
 ➡ အမည် - Ko Kyawthura

📱 *WaveMoney Account*
 ➡ နံပါတ် - 09428176370
 ➡ အမည် - Ko Kyawthura

⚠️ Ngweလွှဲပြီးပါက ဤနေရာတွင် 'Ngweလွှဲပြေစာ (Screenshot)' ဓာတ်ပုံကို တိုက်ရိုက် ပေးပို့ပေးပါရန်။"""
        await update.message.reply_text(money_text, parse_mode="Markdown")


    elif text == "🔮 VIP အခန်း":
        user_id = update.effective_user.id
        from datetime import datetime
        
        conn = sqlite3.connect("bot.db")
        cur = conn.cursor()
        cur.execute("SELECT joined_date, view_count FROM vip WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        
        if row:
            joined_date_str, view_count = row
            joined_date = datetime.strptime(joined_date_str, "%Y-%m-%d")
            days_passed = (datetime.now() - joined_date).days
            
            # 🔴 စစ်ဆေးချက် - ၅ ရက်ကျော်သွားလျှင် သို့မဟုတ် ၁၀ ကြိမ်ပြည့်သွားလျှင် သက်တမ်းဖြတ်မည်
            if days_passed >= 5 or view_count >= 10:
                cur.execute("DELETE FROM vip WHERE user_id = ?", (user_id,))
                conn.commit()
                conn.close()
                
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🆗 OK", callback_data="vip_request")]])
                await update.message.reply_text(
                    "❌ **သင်၏ VIP သက်တမ်း ကုန်ဆုံးသွားပါပြီ။**\n\n"
                    "သက်တမ်း (၅) ရက် သို့မဟုတ် (၁၀) ကြိမ် ကြည့်ရှုခြင်း ပြည့်မြောက်သွားပြီ ဖြစ်သဖြင့် VIP အခန်းသို့ ဝင်ရောက်ခွင့် မရှိတော့ပါ။ ဆက်လက်ကြည့်ရှုလိုပါက အောက်ပါ OK ကိုနှိပ်၍ သက်တမ်းတိုးနိုင်ပါသည်။",
                    reply_markup=keyboard
                )
                return
            
            # 🟢 သက်တမ်းရှိသေးပါက ကြည့်ရှုကြိမ်ရေ ၁ ကြိမ် တိုးပေးမည်
            new_count = view_count + 1
            cur.execute("UPDATE vip SET view_count = ? WHERE user_id = ?", (new_count, user_id))
            
            # Admin တင်ထားသော နောက်ဆုံး VIP ဂဏန်းဒေတာကို ဆွဲထုတ်ခြင်း
            cur.execute("SELECT date_text, main_numbers, hot_numbers FROM vip_data ORDER BY id DESC LIMIT 1")
            data_row = cur.fetchone()
            conn.commit()
            conn.close()
            
            if data_row:
                date_txt, main_num, hot_num = data_row
            else:
                date_txt, main_num, hot_num = "မရှိသေးပါ", "**-**", "**-**"
                
            vip_data_text = (
                f"💎 **VIP သီးသန့် အထူးအချက်အလက်များ** 💎\n\n"
                f"📅 နေ့စွဲ : {date_txt}\n"
                f"🎯 VIP ထိပ်စီး / ပတ်သီး : {main_num}\n"
                f"🔥 VIP အပိုင်ကွက်များ : {hot_num}\n\n"
                f"📊 မိမိကြည့်ရှုမှုအကြိမ်ရေ : ({new_count}/10) ကြိမ်\n"
                f"⏱️ သက်တမ်းကျန် : ({5 - days_passed}) ရက်\n\n"
                f"⚠️ *ဤအချက်အလက်ကို မိမိတစ်ဦးတည်းသာ ကြည့်ရှုရန်ဖြစ်ပြီး ပြင်ပသို့ မမျှဝေပါရန်။*"
            )
            await update.message.reply_text(vip_data_text, parse_mode="Markdown")
        else:
            conn.close()
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🆗 OK", callback_data="vip_request")]])
            await update.message.reply_text(
                "🔒 **VIP အခန်းဝင်ခွင့် မရှိသေးပါ။**\n\n"
                "VIP အခန်းသို့ ဝင်ရောက်လိုပါက အောက်ပါ OK ကို နှိပ်ပါ။",
                reply_markup=keyboard
            )


    elif text == "💳 Member ကြေးလွှဲရန်":

        await update.message.reply_text(
            "💳 Member Fee\n\n"
            "Kpay / Wave ဖြင့် လွှဲပြီး Admin သို့ ပို့ပါ။"
        )

    elif text == "📚 အခြား 2D":
        # 🔗 မိမိ၏ Telegram Group / Channel Link အမှန်များကို ဤနေရာတွင် အစားထိုးထည့်ပါ
        laos_link = "https://t.me/specialonelaos2d"
        shinehope_link = "https://t.me/specialoneshinehope2d"
        dubai_link = "https://t.me/speciaondu2d"
        mega_link = "https://t.me/mega2dsp"
        crypto_link = "https://t.me/Crypto2dSp"
        other_link = "https://t.me/otherdatasp"

        # Markdown သုံး၍ စာသားကို အပြာရောင်လင့်ခ်အဖြစ် ပြောင်းလဲခြင်း
        group_text = (
            "📚 **အခြား 2D Group များ**\n\n"
            f"🇱🇦 [LA Laos 2D]({laos_link})\n\n"
            f"⭐ [ShineHope]({shinehope_link})\n\n"
            f"🇦🇪 [DU2D]({dubai_link})\n\n"
            f"🎰 [Mega]({mega_link})\n\n"
            f"🪙 [Crypto]({crypto_link})\n\n"
            f"➕ [အခြား]({other_link})"
        )

        await update.message.reply_text(
            text=group_text,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

    elif text == "👨‍💻 Admin သို့":
        # 🔗 မိမိ၏ Admin အကောင့် Telegram Username Link ကို ဤနေရာတွင် အစားထိုးထည့်ပါ 
        # (ဥပမာ - YourAdmin နေရာတွင် မိမိ Username ကို ပြောင်းပါ)
        admin_username_link = "https://t.me/Apaperkite75"

        admin_contact_text = (
            "👨‍💻 **Admin နှင့် တိုက်ရိုက် ဆက်သွယ်ရန်**\n\n"
            "တစ်စုံတစ်ရာ အခက်အခဲရှိပါကသော်လည်းကောင်း၊ မေးမြန်းလိုသည်များရှိပါကသော်လည်းကောင်း "
            f"အောက်ပါ အပြာရောင်စာသားကို နှိပ်၍ Admin ထံ တိုက်ရိုက် ဆက်သွယ်နိုင်ပါသည်။\n\n"
            f"💬 [ဆက်သွယ်ရန် : @YourAdmin]({admin_username_link})"
        )

        await update.message.reply_text(
            text=admin_contact_text,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

async def admin_callback(update, context):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    current_text = query.message.text if query.message.text else query.message.caption
    if not current_text:
        current_text = ""

    # =========================================================================
    # 📸 (၁) ငွေလွှဲပြေစာ (Screenshot) အတွက် အတည်ပြု/ပယ်ဖျက် စနစ် (သင်တောင်းဆိုသော စာသားများ အတိအကျ)
    # =========================================================================

    # === 🎯 Crypto2d ပြေစာ မှန်/မှား စစ်ဆေးခြင်း အပိုင်း ===
    if data.startswith("cryptopayok_"):
        user_id = data.replace("cryptopayok_", "")
        await context.bot.send_message(
            chat_id=int(user_id), 
            text="သင့်ရဲ့ Crypto2d ထိုးကွက်များအတွက် Ngweလွှဲပြေစာ မှန်ကန်ပါသည်။သင့်ဘောင်ချာအား အတည်ပြု့ခြင်းမက်ဆေ့ ကို မကြာမီ ရရှိပါမည်။chatboxတွင် /start စာသားရိုက်​ြပီးokနှိပ်ကာ​ြပန်ထွက်ပါ"
        )
        await query.edit_message_caption(caption=f"{current_text}\n\n🟢 အခြေအနေ: Crypto2d ငွေလွှဲပြေစာ အတည်ပြုပြီး။")
       
    elif data.startswith("cryptopayno_"):
        user_id = data.replace("cryptopayno_", "")
        await context.bot.send_message(
            chat_id=int(user_id), 
            text="⚠️ Crypto 2d အတွက်သင့်ငွေလွှဲပြေစာ မှားယွင်းနေပါသည်။ပြန်လည်စစ်ဆေးပြီး ထပ်မံပို့ဆောင်ပေးပါရန်​​။"
        )
        await query.edit_message_caption(caption=f"{current_text}\n\n🔴 အခြေအနေ: Crypto2d ငွေလွှဲပြေစာ မှားယွင်းကြောင်း အကြောင်းပြန်ပြီး။")

    # === ⭐ Shinehope2d ပြေစာ မှန်/မှား စစ်ဆေးခြင်း အပိုင်း ===
    elif data.startswith("shinepayok_"):
        user_id = data.replace("shinepayok_", "")
        await context.bot.send_message(
            chat_id=int(user_id), 
            text="သင့်ရဲ့ Shinehope2d ထိုးကွက်များအတွက် Ngweလွှဲပြေစာ မှန်ကန်ပါသည်။သင့်ဘောင်ချာအား အတည်ပြု့ခြင်းမက်ဆေ့ ကို မကြာမီ ရရှိပါမည်​​။chatbox တွင် /start စာသားရိုက်နှိပ်​ြပီး ok နှိပ်ကာ​ြပန်ထွက်ပါ"
        )
        await query.edit_message_caption(caption=f"{current_text}\n\n🟢 အခြေအနေ: Shinehope2d ငွေလွှဲပြေစာ အတည်ပြုပြီး။")
        
    elif data.startswith("shinepayno_"):
        user_id = data.replace("shinepayno_", "")
        await context.bot.send_message(
            chat_id=int(user_id), 
            text="⚠️ Shinehope 2d အတွက်သင့်ငွေလွှဲပြေစာ မှားယွင်းနေပါသည်။ပြန်လည်စစ်ဆေးပြီး ထပ်မံပို့ဆောင်ပေးပါရန်​​။"
        )
        await query.edit_message_caption(caption=f"{current_text}\n\n🔴 အခြေအနေ: Shinehope2d ငွေလွှဲပြေစာ မှားယွင်းကြောင်း အကြောင်းပြန်ပြီး။")

    # =========================================================================
    # 📸 (၂) ထိုးသားဘက်မှ 'ပြေစာတင်ရန်' ခလုတ်များ နှိပ်သည့်အပိုင်း
    # =========================================================================
    elif data == "send_receipt_crypto":
        context.user_data["receipt_type"] = "crypto"
        await context.bot.send_message(chat_id=query.message.chat_id, text="📸 Crypto2d အတွက် ငွေလွှဲပြေစာ (Screenshot) ဓာတ်ပုံကို ပေးပို့ပေးပါရန်​​။")
    elif data == "send_receipt_shine":
        context.user_data["receipt_type"] = "shine"
        await context.bot.send_message(chat_id=query.message.chat_id, text="📸 Shinehope2d အတွက် ငွေလွှဲပြေစာ (Screenshot) ဓာတ်ပုံကို ပေးပို့ပေးပါရန်​​။")

    # =========================================================================
    # 🎯 (၃) Crypto 2D ထိုးကွက်ဇယားအစစ်အမှန်များ အတည်ပြု/ပယ်ဖျက်ခြင်း (နောက်ဆုံးမှ နှိပ်ရမည့် ခလုတ်စာသား)
    # =========================================================================
    elif data.startswith("ok_"):
        user_id = data.replace("ok_", "")
        await context.bot.send_message(
            chat_id=int(user_id), 
            text="သင်၏ Crypto 2d ထိုးကွက်များ အတည်ပြု့လိုက်ပါပြီ။"
        )
        await query.edit_message_text(text=f"{current_text}\n\n🟢 အခြေအနေ: ထိုးကွက်ဇယား အတည်ပြုပြီး")
        
    elif data.startswith("no_"):
        user_id = data.replace("no_", "")
        await context.bot.send_message(
            chat_id=int(user_id), 
            text="❌ သင်၏ Crypto 2D ထိုးကွက်ကို ပယ်ဖျက်လိုက်ပါပြီ။"
        )
        await query.edit_message_text(text=f"{current_text}\n\n🔴 အခြေအနေ: ထိုးကွက်ဇယား ပယ်ဖျက်ပြီး")

    # =========================================================================
    # ⭐ (၄) ShineHope 2D ထိုးကွက်ဇယားအစစ်အမှန်များ အတည်ပြု/ပယ်ဖျက်ခြင်း
    # =========================================================================
    elif data.startswith("shineok_"):
        user_id = data.replace("shineok_", "")
        await context.bot.send_message(
            chat_id=int(user_id), 
            text="သင်၏ Shinehope 2d ထိုးကွက်များ အတည်ပြု့လိုက်ပါပြီ​​။"
        )
        await query.edit_message_text(text=f"{current_text}\n\n🟢 အခြေအနေ: ထိုးကွက်ဇယား အတည်ပြုပြီး")
        
    elif data.startswith("shineno_"):
        user_id = data.replace("shineno_", "")
        await context.bot.send_message(
            chat_id=int(user_id), 
            text="❌ သင်၏ Shinehope 2D ထိုးကွက်ကို ပယ်ဖျက်လိုက်ပါပြီ။"
        )
        await query.edit_message_text(text=f"{current_text}\n\n🔴 အခြေအနေ: ထိုးကွက်ဇယား ပယ်ဖျက်ပြီး")



    # 1. ပြေစာမှန်ကန်ကြောင်း အတည်ပြုခြင်း စနစ်
    elif data.startswith("payok_"):
        user_id = data.replace("payok_", "")
        await context.bot.send_message(
            chat_id=int(user_id), 
            text="🎉 မန်နေဂျာမှ စစ်ဆေးပြီးပါပြီ။ သင်၏ **ငွေလွှဲမှု မှန်ကန်ပါသည်**။ အကောင့်ထဲသို့ ငွေဖြည့်သွင်းပေးလိုက်ပါပြီ။",
            parse_mode="Markdown"
        )
        await query.edit_message_caption(
            caption=f"{current_text}\n\n🟢 **အခြေအနေ: ငွေလွှဲမှန်ကန်ကြောင်း အတည်ပြုပြီး။**",
            parse_mode="Markdown"
        )

    # 2. ပြေစာမှားယွင်းကြောင်း အကြောင်းပြန်ခြင်း စနစ်
    elif data.startswith("payno_"):
        user_id = data.replace("payno_", "")
        await context.bot.send_message(
            chat_id=int(user_id), 
            text="⚠️ စစ်ဆေးချက်အရ သင်၏ **ငွေလွှဲမှု (ပြေစာ) မှားယွင်းနေပါသည်**။ အချက်အလက်များ ပြန်လည်စစ်ဆေးပြီး မန်နေဂျာထံ ပြန်လည် ဆက်သွယ်ပေးပါရန်။",
            parse_mode="Markdown"
        )
        await query.edit_message_caption(
            caption=f"{current_text}\n\n🔴 **အခြေအနေ: ငွေလွှဲမှားယွင်းကြောင်း အကြောင်းပြန်ပြီး။**",
            parse_mode="Markdown"
        )

    elif data.startswith("vipok_"):
        await query.answer()
        user_id = int(data.replace("vipok_", ""))
        
        # --- ယနေ့ရက်စွဲဖြင့် ၅ ရက် သက်တမ်း စတင်သတ်မှတ်ခြင်း ---
        from datetime import datetime
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect("bot.db")
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO vip (user_id, joined_date, view_count) 
            VALUES (?, ?, 0)
            ON CONFLICT(user_id) DO UPDATE SET joined_date=?, view_count=0
        """, (user_id, today_str, today_str))
        conn.commit()
        conn.close()
        # --------------------------------------------------
        
        vip_approved_text = (
            "🎉 **မင်္ဂလာပါ ခင်ဗျာ။**\n\n"
            "လူကြီးမင်း ပို့ပေးထားသော VIP မန်ဘာကြေးသွင်း ပြေစာကို "
            "Admin မှ သေချာစွာ စစ်ဆေးပြီး အတည်ပြုပေးလိုက်ပါပြီ။\n\n"
            "ယခုမှစ၍ လူကြီးမင်းသည် ကျွန်ုပ်တို့၏ **VIP Member** ဖြစ်သွားပါပြီ။\n"
            "⏱️ သက်တမ်းမှာ (၅) ရက် သို့မဟုတ် (၁၀) ကြိမ် ကြည့်ရှုခွင့် ရရှိမည် ဖြစ်ပါသည်။ ✨"
        )
        try:
            await context.bot.send_message(chat_id=user_id, text=vip_approved_text, parse_mode="Markdown")
            await query.edit_message_caption(
                caption=f"{query.message.caption}\n\n🟢 [Admin မှ အတည်ပြုပြီးပါပြီ]",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Error: {e}")


    elif data.startswith("vipno_"):
        await query.answer()
        user_id = data.replace("vipno_", "")
        vip_rejected_text = (
            "⚠️ **အကြောင်းကြားစာ**\n\n"
            "လူကြီးမင်း ပို့ပေးထားသော VIP မန်ဘာကြေးသွင်း ပြေစာသည် "
            "မှန်ကန်မှုမရှိခြင်း (သို့မဟုတ်) ငွေဝင်ရောက်ခြင်းမရှိသေးသောကြောင့် Admin မှ ပယ်ဖျက်လိုက်ပါသည်။\n\n"
            "အကယ်၍ တစ်စုံတစ်ရာ မှားယွင်းမှုရှိပါက Admin ထံသို့ တိုက်ရိုက် ဆက်သွယ်မေးမြန်းနိုင်ပါသည်။"
        )
        try:
            await context.bot.send_message(chat_id=int(user_id), text=vip_rejected_text, parse_mode="Markdown")
            await query.edit_message_caption(
                caption=f"{query.message.caption}\n\n🔴 [Admin မှ ပယ်ဖျက်လိုက်ပါပြီ]",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Error: {e}")


    elif data == "vip_request":
        await query.answer()
        vip_message = (
            "💎 **သင့်ရဲ့တောင်းဆိုမှုကို လက်ခံရရှိပါသည်။**\n\n"
            "ဆက်လက်လုပ်ဆောင်ရန် အောက်ပါ ဖုန်းနံပါတ်များသို့\n"
            "VIP အခန်းအတွက် ကျသင့်ငွေ **10,000 Ks** ကို လွှဲပေးပါ။\n\n"
            "📱 **KPay:** 09428176370\n"
            "📱 **WaveMoney:** 09428176370\n\n"
            "ပြီးလျှင် ငွေလွှဲပြီးကြောင်းပြေစာ (Screenshot) ကို "
            "ယခု **CHAT BOX** ကနေ ထပ်မံပို့ပေးရပါမည်။"
        )
        context.user_data["vip_mode"] = True
        await query.edit_message_text(text=vip_message)


         # <- ဤနေရာတွင် ကွင်းပိတ်ရန် ကျန်ခဲ့ခြင်း ဖြစ်ပါသည်

async def handle_screenshot(update, context):
    if context.user_data.get("vip_mode"):
        context.user_data["vip_mode"] = False
        await handle_vip_screenshot(update, context)
        return

    user = update.message.from_user
    photo_file = update.message.photo[-1]
    
    # 💥 ရောထွေးမှုမရှိစေရန် User နှိပ်ခဲ့သော ခလုတ်အမျိုးအစားကို သေချာစွာ စစ်ဆေးခြင်း 💥
    receipt_type = context.user_data.get("receipt_type", "crypto")
    
    admin_text = f"""💰 **ထိုးသားထံမှ ငွေလွှဲပြေစာ ရောက်ရှိလာပါသည်** 💰

🎮 အမျိုးအစား : {receipt_type.upper()} 2D ပြေစာ
👤 အမည် : {user.first_name}
🆔 User ID : {user.id}

ငွေလွှဲဝင်၊ မဝင် သေချာစစ်ဆေးပြီး အောက်ပါခလုတ်တစ်ခုခုကို နှိပ်၍ အကြောင်းပြန်ပေးပါရန်။"""

    # callback_data များကို အောက်ပါအတိုင်း တိုက်ရိုက် အသစ် ပြောင်းလဲသတ်မှတ်လိုက်ပါသည်
    if receipt_type == "crypto":
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ မှန်ကန်ပါသည်", callback_data=f"cryptopayok_{user.id}"),
                InlineKeyboardButton("❌ မှားယွင်းနေပါသည်", callback_data=f"cryptopayno_{user.id}")
            ]
        ])
    else:
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ မှန်ကန်ပါသည်", callback_data=f"shinepayok_{user.id}"),
                InlineKeyboardButton("❌ မှားယွင်းနေပါသည်", callback_data=f"shinepayno_{user.id}")
            ]
        ])
    
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_file.file_id,
        caption=admin_text,
        reply_markup=keyboard
    )
    
    await update.message.reply_text(
        "✅ သင်၏ ငွေလွှဲပြေစာကို လက်ခံရရှိပါပြီ။ မန်နေဂျာမှ စစ်ဆေးနေပါသဖြင့် ခေတ္တစောင့်ဆိုင်းပေးပါ။"
    )


async def handle_vip_screenshot(update, context):
    user = update.message.from_user
    photo_file = update.message.photo[-1]

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ VIP အတည်ပြု",
                callback_data=f"vipok_{user.id}"
            ),
            InlineKeyboardButton(
                "❌ VIP ပယ်ဖျက်",
                callback_data=f"vipno_{user.id}"
            )
        ]
    ])

    admin_text = (
        "💎 **VIP MEMBER ပြေစာ ရရှိပါသည်**\n\n"
        f"👤 အမည် : {user.first_name}\n"
        f"📛 Username : @{user.username if user.username else 'မရှိပါ'}\n"
        f"🆔 User ID : {user.id}\n\n"
        "VIP ကြေး ဝင်၊ မဝင် သေချာစစ်ဆေးပြီးမှ အပေါ်က ခလုတ်တစ်ခုခုကို နှိပ်၍ အတည်ပြုပေးပါ။"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_file.file_id,
        caption=admin_text,
        reply_markup=keyboard
    )

    await update.message.reply_text(
        "✅ သင်၏ VIP မန်ဘာကြေးသွင်း ပြေစာကို လက်ခံရရှိပါပြီ။\n"
        "Admin မှ အမြန်ဆုံး စစ်ဆေးပြီး အကြောင်းပြန်ပေးပါမည်။"
    )

async def set_vip_data(update, context):
    user_id = update.effective_user.id
    
    # လူကြီးမင်း၏ ADMIN_ID ဖြစ်မှသာ ပြင်ခွင့်ပေးမည်
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ သင်သည် Admin မဟုတ်သဖြင့် ဤ Command ကို သုံးခွင့်မရှိပါ။")
        return
        
    try:
        command_text = " ".join(context.args)
        if not command_text or "|" not in command_text:
            await update.message.reply_text(
                "💡 **ဂဏန်းတင်နည်း အသုံးပြုပုံ**\n\n"
                "`/setvip နေ့စွဲ | ထိပ်စီး | အပိုင်ကွက်များ`\n\n"
                "ဥပမာ -\n"
                "`/setvip 19-07-2026 | 5 - 9 | 54, 59, 92, 97`",
                parse_mode="Markdown"
            )
            return
            
        parts = command_text.split("|")
        date_txt = parts[0].strip()
        main_num = parts[1].strip()
        hot_num = parts[2].strip()
        
        conn = sqlite3.connect("bot.db")
        cur = conn.cursor()
        cur.execute("INSERT INTO vip_data (date_text, main_numbers, hot_numbers) VALUES (?, ?, ?)", 
                    (date_txt, main_num, hot_num))
        conn.commit()
        conn.close()
        
        await update.message.reply_text(
            f"✅ **VIP ဂဏန်းများကို အောင်မြင်စွာ Update လုပ်ပြီးပါပြီ။**\n\n"
            f"📅 နေ့စွဲ : {date_txt}\n"
            f"🎯 ထိပ်စီး/ပတ်သီး : {main_num}\n"
            f"🔥 အပိုင်ကွက်များ : {hot_num}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ အမှားဖြစ်သွားပါသည်- {e}")


# ===== Run Bot =====

def main():

    app = Application.builder().token(TOKEN).build()


    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(CommandHandler("setvip", set_vip_data))


    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            reply
        )
    )

    app.add_handler(CallbackQueryHandler(admin_callback))

    # 💥 ဤစာကြောင်းကို မဖြစ်မနေ ထည့်ပေးရပါမည် 💥
    app.add_handler(MessageHandler(filters.PHOTO, handle_screenshot))


    print("Bot is running...")


    app.run_polling()



if __name__ == "__main__":
    main()
