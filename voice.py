import os
import json
import asyncio
import subprocess
import uuid
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = "8922085167:AAHxXFvms5gporJOhSUbvWJg02nwOrW-X2A"

ADMIN_ID = 8889726455

CHANNEL_1 = "@ModderSanto_Official"
CHANNEL_2 = "@CHS_TEAM_OFFICIAL"

# Admin inbox
ADMIN_LINK = f"tg://user?id={ADMIN_ID}"

# Normal user limits
NORMAL_MAX_SECONDS = 20
NORMAL_DAILY_LIMIT = 5

# Default VIP limits
DEFAULT_VIP_DAYS = 30
DEFAULT_VIP_MAX_SECONDS = 120
DEFAULT_VIP_DAILY_LIMIT = 50

# =========================================================
# FILES
# =========================================================

DATA_FILE = "users.json"

os.makedirs("downloads", exist_ok=True)
os.makedirs("converted", exist_ok=True)


# =========================================================
# DATABASE
# =========================================================

def load_data():

    if not os.path.exists(DATA_FILE):
        return {
            "users": {},
            "blocked": []
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except:
        return {
            "users": {},
            "blocked": []
        }


def save_data(data):

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


db = load_data()


def get_user(user_id):

    uid = str(user_id)

    if uid not in db["users"]:

        db["users"][uid] = {
            "voice_count": 0,
            "count_date": datetime.now().strftime("%Y-%m-%d"),

            "vip": False,
            "vip_until": None,

            "vip_max_seconds": DEFAULT_VIP_MAX_SECONDS,
            "vip_daily_limit": DEFAULT_VIP_DAILY_LIMIT,
        }

        save_data(db)

    user = db["users"][uid]

    # Reset daily counter
    today = datetime.now().strftime("%Y-%m-%d")

    if user.get("count_date") != today:

        user["voice_count"] = 0
        user["count_date"] = today

        save_data(db)

    return user


# =========================================================
# VIP CHECK
# =========================================================

def is_vip(user):

    if not user.get("vip"):
        return False

    until = user.get("vip_until")

    if not until:
        return False

    try:

        expiry = datetime.fromisoformat(until)

        if datetime.now() >= expiry:

            user["vip"] = False
            user["vip_until"] = None

            save_data(db)

            return False

        return True

    except:

        return False


# =========================================================
# BLOCK CHECK
# =========================================================

def is_blocked(user_id):

    return str(user_id) in db.get("blocked", [])


# =========================================================
# CHANNEL VERIFY
# =========================================================

async def check_channel_membership(
    context,
    user_id,
    channel
):

    try:

        member = await context.bot.get_chat_member(
            chat_id=channel,
            user_id=user_id
        )

        return member.status in [
            "member",
            "administrator",
            "creator"
        ]

    except Exception as e:

        print(
            f"Channel check error {channel}:",
            e
        )

        return False


async def verify_user(
    update,
    context
):

    user_id = update.effective_user.id

    one = await check_channel_membership(
        context,
        user_id,
        CHANNEL_1
    )

    two = await check_channel_membership(
        context,
        user_id,
        CHANNEL_2
    )

    return one and two


# =========================================================
# JOIN MESSAGE
# =========================================================

def join_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📢 Join Channel 1",
                url="https://t.me/ModderSanto_Official"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 Join Channel 2",
                url="https://t.me/CHS_TEAM_OFFICIAL"
            )
        ],
        [
            InlineKeyboardButton(
                "✅ Verify Join",
                callback_data="verify_join"
            )
        ]
    ])


async def send_join_message(message):

    await message.reply_text(
        "🔐 <b>Channel Verification Required</b>\n\n"
        "Bot ব্যবহার করার আগে নিচের ২টি Channel-এ Join করুন।\n\n"
        "1️⃣ @ModderSanto_Official\n"
        "2️⃣ @CHS_TEAM_OFFICIAL\n\n"
        "Join করার পরে নিচের <b>Verify Join</b> button চাপুন।",
        parse_mode="HTML",
        reply_markup=join_keyboard()
    )


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    if is_blocked(user_id):

        await update.message.reply_text(
            "🚫 <b>You are blocked.</b>\n\n"
            "Admin-এর সাথে যোগাযোগ করুন।",
            parse_mode="HTML"
        )

        return

    if not await verify_user(update, context):

        await send_join_message(
            update.message
        )

        return

    keyboard = [
        [
            InlineKeyboardButton(
                "🎙️ Send Voice",
                callback_data="send_voice"
            )
        ],
        [
            InlineKeyboardButton(
                "👤 My Status",
                callback_data="my_status"
            )
        ]
    ]

    if user_id == ADMIN_ID:

        keyboard.append([
            InlineKeyboardButton(
                "👑 Admin Panel",
                callback_data="admin_panel"
            )
        ])

    await update.message.reply_text(
        "🎙️ <b>VOICE CHANGER BOT</b>\n\n"
        "👋 Welcome!\n\n"
        "আমাকে একটি Telegram Voice Message পাঠাও।\n\n"
        "🤖 Robot\n"
        "👽 Alien\n"
        "⚡ Hacker\n"
        "🧟 Deep Voice\n"
        "💻 Chipmunk\n"
        "🌌 Echo",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# VERIFY BUTTON
# =========================================================

async def verify_join(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    if await verify_user(update, context):

        await query.message.edit_text(
            "✅ <b>Verification Successful!</b>\n\n"
            "🎙️ এখন Voice Message পাঠাতে পারো।",
            parse_mode="HTML"
        )

    else:

        await query.answer(
            "❌ আপনি এখনো দুইটি Channel-এ Join করেননি!",
            show_alert=True
        )


# =========================================================
# SEND VOICE BUTTON
# =========================================================

async def send_voice_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if is_blocked(query.from_user.id):

        await query.message.reply_text(
            "🚫 You are blocked."
        )

        return

    if not await verify_user(update, context):

        await query.message.reply_text(
            "🔐 আগে দুইটি Channel-এ Join করুন।",
            reply_markup=join_keyboard()
        )

        return

    await query.message.reply_text(
        "🎙️ <b>এখন তোমার Voice Message পাঠাও</b>\n\n"
        "⏱️ Normal User: সর্বোচ্চ 20 seconds\n"
        "🎁 Daily Limit: 5 Voice\n\n"
        "👑 VIP হলে বেশি সুবিধা পাওয়া যাবে।",
        parse_mode="HTML"
    )


# =========================================================
# STATUS
# =========================================================

async def my_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user = get_user(
        query.from_user.id
    )

    vip = is_vip(user)

    if vip:

        expiry = user["vip_until"]

        try:
            expiry_text = datetime.fromisoformat(
                expiry
            ).strftime("%d-%m-%Y %H:%M")

        except:
            expiry_text = "Unknown"

        text = (
            "👑 <b>VIP STATUS</b>\n\n"
            "✅ VIP: Active\n"
            f"📅 Expire: {expiry_text}\n"
            f"⏱️ Voice Time: {user['vip_max_seconds']} sec\n"
            f"🎙️ Daily Voice: {user['vip_daily_limit']}\n"
            f"📊 Today Used: {user['voice_count']}"
        )

    else:

        text = (
            "👤 <b>NORMAL USER</b>\n\n"
            "❌ VIP: Not Active\n"
            f"⏱️ Voice Time: {NORMAL_MAX_SECONDS} sec\n"
            f"🎙️ Daily Voice: {NORMAL_DAILY_LIMIT}\n"
            f"📊 Today Used: {user['voice_count']}\n\n"
            "👑 VIP নিতে Admin-এর সাথে যোগাযোগ করুন।"
        )

    await query.message.reply_text(
        text,
        parse_mode="HTML"
    )


# =========================================================
# RECEIVE VOICE
# =========================================================

async def receive_voice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    if is_blocked(user_id):

        await update.message.reply_text(
            "🚫 আপনি এই Bot থেকে Blocked."
        )

        return

    # Channel check
    if not await verify_user(update, context):

        await send_join_message(
            update.message
        )

        return

    user = get_user(user_id)

    vip = is_vip(user)

    # Limits
    if vip:

        max_seconds = user.get(
            "vip_max_seconds",
            DEFAULT_VIP_MAX_SECONDS
        )

        daily_limit = user.get(
            "vip_daily_limit",
            DEFAULT_VIP_DAILY_LIMIT
        )

    else:

        max_seconds = NORMAL_MAX_SECONDS
        daily_limit = NORMAL_DAILY_LIMIT

    # =====================================================
    # DAILY LIMIT
    # =====================================================

    if user["voice_count"] >= daily_limit:

        keyboard = [
            [
                InlineKeyboardButton(
                    "👑 VIP কিনতে Admin-কে SMS দিন",
                    url=ADMIN_LINK
                )
            ]
        ]

        await update.message.reply_text(
            "⚠️ <b>Daily Voice Limit Finished!</b>\n\n"
            f"আজ আপনি {daily_limit}টি Voice Generate করেছেন।\n\n"
            "👑 আরো Voice Generate করতে VIP কিনুন।",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =====================================================
    # VOICE LENGTH
    # =====================================================

    voice = update.message.voice

    duration = voice.duration

    if duration > max_seconds:

        keyboard = [
            [
                InlineKeyboardButton(
                    "👑 VIP কিনতে Admin-কে SMS দিন",
                    url=ADMIN_LINK
                )
            ]
        ]

        await update.message.reply_text(
            "❌ <b>Voice Too Long!</b>\n\n"
            f"তোমার Voice: {duration} seconds\n"
            f"তোমার Limit: {max_seconds} seconds\n\n"
            "👑 বেশি সময়ের Voice Convert করতে VIP কিনুন।",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =====================================================
    # DOWNLOAD
    # =====================================================

    processing = await update.message.reply_text(
        "📥 Voice received...\n\n"
        "⏳ Processing..."
    )

    unique_id = uuid.uuid4().hex

    input_file = (
        f"downloads/{unique_id}.ogg"
    )

    try:

        telegram_file = await context.bot.get_file(
            voice.file_id
        )

        await telegram_file.download_to_drive(
            input_file
        )

        context.user_data["voice_file"] = input_file

        keyboard = [
            [
                InlineKeyboardButton(
                    "🤖 Robot",
                    callback_data="effect_robot"
                ),
                InlineKeyboardButton(
                    "👽 Alien",
                    callback_data="effect_alien"
                )
            ],
            [
                InlineKeyboardButton(
                    "⚡ Hacker",
                    callback_data="effect_chipmunk"
                ),
                InlineKeyboardButton(
                    "🧟 Deep Voice",
                    callback_data="effect_deep"
                )
            ],
            [
                InlineKeyboardButton(
                    "💻 Chipmunk",
                    callback_data="effect_hacker"
                ),
                InlineKeyboardButton(
                    "🌌 Echo",
                    callback_data="effect_echo"
                )
            ]
        ]

        await processing.edit_text(
            "✅ <b>Voice Received!</b>\n\n"
            "🎛️ কোন Voice Style চান?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            )
        )

    except Exception as e:

        await processing.edit_text(
            "❌ Error:\n\n"
            f"<code>{str(e)}</code>",
            parse_mode="HTML"
        )


# =========================================================
# EFFECTS
# =========================================================

EFFECTS = {

    "robot": (
        "aresample=44100,"
        "aecho=0.8:0.88:60:0.4,"
        "aphaser=in_gain=0.4:out_gain=0.6:delay=3:decay=0.4,"
        "acompressor=threshold=-18dB:ratio=4:attack=5:release=80"
    ),

    "alien": (
        "asetrate=44100*1.35,"
        "aresample=44100,"
        "aecho=0.8:0.88:90:0.35"
    ),

    # Hacker
    "hacker": (
        "asetrate=44100*0.82,"
        "aresample=44100,"
        "aecho=0.8:0.88:70:0.35,"
        "highpass=f=180,"
        "lowpass=f=5000"
    ),

    # Chipmunk
    "chipmunk": (
        "asetrate=44100*1.65,"
        "aresample=44100"
    ),

    "deep": (
        "asetrate=44100*0.72,"
        "aresample=44100,"
        "bass=g=7:f=120,"
        "acompressor=threshold=-18dB:ratio=3"
    ),

    "echo": (
        "aecho=0.8:0.88:500:0.35,"
        "aecho=0.8:0.88:1000:0.25"
    )
}


# =========================================================
# APPLY EFFECT
# =========================================================

async def apply_effect(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    if is_blocked(user_id):

        await query.message.reply_text(
            "🚫 You are blocked."
        )

        return

    # Verify again
    if not await verify_user(update, context):

        await query.message.reply_text(
            "🔐 Channel verification required.",
            reply_markup=join_keyboard()
        )

        return

    input_file = context.user_data.get(
        "voice_file"
    )

    if not input_file or not os.path.exists(
        input_file
    ):

        await query.message.reply_text(
            "❌ Voice file পাওয়া যায়নি।\n\n"
            "আবার Voice পাঠাও।"
        )

        return

    effect_name = query.data.replace(
        "effect_",
        ""
    )

    effect = EFFECTS.get(effect_name)

    if not effect:

        await query.message.reply_text(
            "❌ Unknown effect."
        )

        return

    # Count voice only when conversion starts
    user = get_user(user_id)

    vip = is_vip(user)

    if vip:
        daily_limit = user.get(
            "vip_daily_limit",
            DEFAULT_VIP_DAILY_LIMIT
        )
    else:
        daily_limit = NORMAL_DAILY_LIMIT

    if user["voice_count"] >= daily_limit:

        await query.message.reply_text(
            "⚠️ Daily limit reached."
        )

        return

    user["voice_count"] += 1

    save_data(db)

    output_id = uuid.uuid4().hex

    output_file = (
        f"converted/{output_id}.ogg"
    )

    status = await query.message.reply_text(
        f"🎛️ <b>{effect_name.upper()}</b>\n\n"
        "⏳ Voice তৈরি হচ্ছে...",
        parse_mode="HTML"
    )

    try:

        command = [
            "ffmpeg",
            "-y",
            "-i",
            input_file,
            "-af",
            effect,
            "-c:a",
            "libopus",
            "-b:a",
            "64k",
            output_file
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:

            # Conversion failed → restore count
            user["voice_count"] = max(
                0,
                user["voice_count"] - 1
            )

            save_data(db)

            error = stderr.decode(
                errors="ignore"
            )

            await status.edit_text(
                "❌ FFmpeg Error:\n\n"
                f"<code>{error[-1500:]}</code>",
                parse_mode="HTML"
            )

            return

        with open(
            output_file,
            "rb"
        ) as audio:

            await query.message.reply_voice(
                voice=audio,
                caption=(
                    f"🎙️ <b>Voice Style:</b> "
                    f"{effect_name.upper()}\n\n"
                    "⚡ Converted Successfully"
                ),
                parse_mode="HTML"
            )

        try:
            os.remove(output_file)
        except:
            pass

        try:
            os.remove(input_file)
        except:
            pass

        await status.delete()

    except Exception as e:

        user["voice_count"] = max(
            0,
            user["voice_count"] - 1
        )

        save_data(db)

        await status.edit_text(
            "❌ Error:\n\n"
            f"<code>{str(e)}</code>",
            parse_mode="HTML"
        )


# =========================================================
# ADMIN PANEL
# =========================================================

def admin_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📢 Broadcast",
                callback_data="admin_broadcast"
            )
        ],
        [
            InlineKeyboardButton(
                "🚫 Block User",
                callback_data="admin_block"
            ),
            InlineKeyboardButton(
                "✅ Unblock User",
                callback_data="admin_unblock"
            )
        ],
        [
            InlineKeyboardButton(
                "👑 Add VIP",
                callback_data="admin_addvip"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 Statistics",
                callback_data="admin_stats"
            ),
        ],
        [
            InlineKeyboardButton(
                "⚡ Bot Speed",
                callback_data="admin_speed"
            )
        ],
        [
            InlineKeyboardButton(
                "🔧 VIP Settings",
                callback_data="admin_vipsettings"
            )
        ]
    ])


async def open_admin_panel(
    update,
    context
):

    query = update.callback_query

    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    await query.message.reply_text(
        "👑 <b>ADMIN PANEL</b>\n\n"
        "নিচের option নির্বাচন করুন:",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )


# =========================================================
# ADMIN MENU
# =========================================================

async def admin_menu(
    update,
    context
):

    query = update.callback_query

    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    action = query.data

    if action == "admin_stats":

        total_users = len(
            db["users"]
        )

        blocked = len(
            db.get("blocked", [])
        )

        vip_users = 0

        for uid, user in db["users"].items():

            if is_vip(user):
                vip_users += 1

        await query.message.reply_text(
            "📊 <b>BOT STATISTICS</b>\n\n"
            f"👥 Total Users: {total_users}\n"
            f"👑 VIP Users: {vip_users}\n"
            f"🚫 Blocked: {blocked}",
            parse_mode="HTML"
        )

        return

    if action == "admin_speed":

        start = asyncio.get_event_loop().time()

        msg = await query.message.reply_text(
            "⚡ Checking bot speed..."
        )

        end = asyncio.get_event_loop().time()

        ms = round(
            (end - start) * 1000,
            2
        )

        await msg.edit_text(
            f"⚡ <b>BOT SPEED</b>\n\n"
            f"🚀 Response: {ms} ms",
            parse_mode="HTML"
        )

        return

    if action == "admin_broadcast":

        context.user_data[
            "admin_action"
        ] = "broadcast"

        await query.message.reply_text(
            "📢 <b>Broadcast Mode</b>\n\n"
            "এখন যে message সবাইকে পাঠাতে চাও "
            "সেটা send করো।",
            parse_mode="HTML"
        )

        return

    if action == "admin_block":

        context.user_data[
            "admin_action"
        ] = "block"

        await query.message.reply_text(
            "🚫 যে User ID block করতে চাও সেটা পাঠাও।"
        )

        return

    if action == "admin_unblock":

        context.user_data[
            "admin_action"
        ] = "unblock"

        await query.message.reply_text(
            "✅ যে User ID unblock করতে চাও সেটা পাঠাও।"
        )

        return

    if action == "admin_addvip":

        context.user_data[
            "admin_action"
        ] = "addvip"

        await query.message.reply_text(
            "👑 <b>Add VIP</b>\n\n"
            "এই format-এ পাঠাও:\n\n"
            "<code>USER_ID DAYS MAX_SECONDS DAILY_LIMIT</code>\n\n"
            "Example:\n"
            "<code>123456789 30 120 50</code>",
            parse_mode="HTML"
        )

        return

    if action == "admin_vipsettings":

        context.user_data[
            "admin_action"
        ] = "vipsettings"

        await query.message.reply_text(
            "🔧 <b>VIP Settings</b>\n\n"
            "এই format-এ পাঠাও:\n\n"
            "<code>DAYS MAX_SECONDS DAILY_LIMIT</code>\n\n"
            "Example:\n"
            "<code>30 120 50</code>\n\n"
            "এটি default VIP settings update করবে।",
            parse_mode="HTML"
        )

        return


# =========================================================
# ADMIN TEXT HANDLER
# =========================================================

async def admin_text_handler(
    update,
    context
):

    if update.effective_user.id != ADMIN_ID:
        return

    action = context.user_data.get(
        "admin_action"
    )

    if not action:
        return

    text = update.message.text.strip()

    # =====================================================
    # BLOCK
    # =====================================================

    if action == "block":

        uid = text

        if not uid.isdigit():

            await update.message.reply_text(
                "❌ Valid User ID দিন।"
            )

            return

        if uid not in db["blocked"]:

            db["blocked"].append(uid)

        save_data(db)

        context.user_data.pop(
            "admin_action",
            None
        )

        await update.message.reply_text(
            f"🚫 User <code>{uid}</code> blocked.",
            parse_mode="HTML"
        )

        return

    # =====================================================
    # UNBLOCK
    # =====================================================

    if action == "unblock":

        uid = text

        if uid in db["blocked"]:

            db["blocked"].remove(uid)

            save_data(db)

            message = (
                f"✅ User <code>{uid}</code> "
                "unblocked."
            )

        else:

            message = (
                "⚠️ এই User blocked list-এ নেই।"
            )

        context.user_data.pop(
            "admin_action",
            None
        )

        await update.message.reply_text(
            message,
            parse_mode="HTML"
        )

        return

    # =====================================================
    # ADD VIP
    # =====================================================

    if action == "addvip":

        try:

            parts = text.split()

            uid = parts[0]
            days = int(parts[1])
            max_seconds = int(parts[2])
            daily_limit = int(parts[3])

            user = get_user(
                int(uid)
            )

            user["vip"] = True

            user["vip_until"] = (
                datetime.now()
                + timedelta(days=days)
            ).isoformat()

            user["vip_max_seconds"] = max_seconds
            user["vip_daily_limit"] = daily_limit

            save_data(db)

            context.user_data.pop(
                "admin_action",
                None
            )

            await update.message.reply_text(
                "👑 <b>VIP Added Successfully!</b>\n\n"
                f"👤 User: <code>{uid}</code>\n"
                f"📅 Days: {days}\n"
                f"⏱️ Voice Time: {max_seconds}s\n"
                f"🎙️ Daily Limit: {daily_limit}",
                parse_mode="HTML"
            )

        except:

            await update.message.reply_text(
                "❌ Format ভুল।\n\n"
                "<code>USER_ID DAYS MAX_SECONDS DAILY_LIMIT</code>",
                parse_mode="HTML"
            )

        return

    # =====================================================
    # VIP SETTINGS
    # =====================================================

    if action == "vipsettings":

        try:

            parts = text.split()

            days = int(parts[0])
            max_seconds = int(parts[1])
            daily_limit = int(parts[2])

            # Store global settings
            global DEFAULT_VIP_DAYS
            global DEFAULT_VIP_MAX_SECONDS
            global DEFAULT_VIP_DAILY_LIMIT

            DEFAULT_VIP_DAYS = days
            DEFAULT_VIP_MAX_SECONDS = max_seconds
            DEFAULT_VIP_DAILY_LIMIT = daily_limit

            context.user_data.pop(
                "admin_action",
                None
            )

            await update.message.reply_text(
                "🔧 <b>VIP Settings Updated!</b>\n\n"
                f"📅 Default Days: {days}\n"
                f"⏱️ Max Voice: {max_seconds}s\n"
                f"🎙️ Daily Voice: {daily_limit}",
                parse_mode="HTML"
            )

        except:

            await update.message.reply_text(
                "❌ Format:\n\n"
                "<code>DAYS MAX_SECONDS DAILY_LIMIT</code>",
                parse_mode="HTML"
            )

        return

    # =====================================================
    # BROADCAST
    # =====================================================

    if action == "broadcast":

        success = 0
        failed = 0

        await update.message.reply_text(
            "📢 Broadcast শুরু হয়েছে..."
        )

        for uid in list(db["users"].keys()):

            try:

                await context.bot.send_message(
                    chat_id=int(uid),
                    text=text
                )

                success += 1

                await asyncio.sleep(
                    0.05
                )

            except:

                failed += 1

        context.user_data.pop(
            "admin_action",
            None
        )

        await update.message.reply_text(
            "✅ <b>Broadcast Complete</b>\n\n"
            f"📨 Sent: {success}\n"
            f"❌ Failed: {failed}",
            parse_mode="HTML"
        )

        return


# =========================================================
# ADMIN COMMAND
# =========================================================

async def admin_command(
    update,
    context
):

    if update.effective_user.id != ADMIN_ID:

        await update.message.reply_text(
            "🚫 Admin only."
        )

        return

    await update.message.reply_text(
        "👑 <b>ADMIN PANEL</b>",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )


# =========================================================
# ERROR
# =========================================================

async def error_handler(
    update,
    context
):

    print(
        "ERROR:",
        context.error
    )


# =========================================================
# MAIN
# =========================================================

def main():

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "admin",
            admin_command
        )
    )

    # Voice
    app.add_handler(
        MessageHandler(
            filters.VOICE,
            receive_voice
        )
    )

    # Admin text
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            admin_text_handler
        )
    )

    # Verify
    app.add_handler(
        CallbackQueryHandler(
            verify_join,
            pattern="^verify_join$"
        )
    )

    # Send voice
    app.add_handler(
        CallbackQueryHandler(
            send_voice_button,
            pattern="^send_voice$"
        )
    )

    # Status
    app.add_handler(
        CallbackQueryHandler(
            my_status,
            pattern="^my_status$"
        )
    )

    # Admin panel
    app.add_handler(
        CallbackQueryHandler(
            open_admin_panel,
            pattern="^admin_panel$"
        )
    )

    # Admin actions
    app.add_handler(
        CallbackQueryHandler(
            admin_menu,
            pattern="^admin_"
        )
    )

    # Voice effects
    app.add_handler(
        CallbackQueryHandler(
            apply_effect,
            pattern="^effect_"
        )
    )

    app.add_error_handler(
        error_handler
    )

    print(
        "===================================="
    )
    print(
        "🎙️ VOICE CHANGER BOT STARTED"
    )
    print(
        "===================================="
    )

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
