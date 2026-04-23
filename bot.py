import telebot
import random
import os
import time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# ────────────────────────────────────────────────
#   CONFIGURATION
# ────────────────────────────────────────────────
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 6241269407                     # ← CHANGE TO YOUR TELEGRAM USER ID

# ✅ Updated Video File ID (fresh one you provided)
VIDEO_FILE_ID = "BAACAgQAAxkBAAFH4etp6flCWbYOBZn7QaIgd-Yr4Lk7OgAC6hsAApA3UFPf1V5onit4LzsE"

if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN environment variable not set!")
    print("   Add it in GitHub → Settings → Secrets → Codespaces")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)


def generate_random_proxies(protocol: str, count: int = 70) -> list:
    """Generate random proxies"""
    proxies = []
    for _ in range(count):
        ip = '.'.join(str(random.randint(1, 255)) for _ in range(4))
        port = random.randint(1024, 65535)
        proxies.append(f"{protocol}://{ip}:{port}")
    return proxies


def generate_pdf(filename: str, proxies: list, title: str):
    """Generate nicely formatted PDF"""
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y = height - 1.5 * inch

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, title)
    y -= 40

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    y -= 50

    c.setFont("Courier", 10)

    for proxy in proxies:
        if y < 50:
            c.showPage()
            y = height - 1 * inch
            c.setFont("Courier", 10)
        
        c.drawString(50, y, proxy)
        y -= 14

    c.save()


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id

    # 1. Send tutorial video using the new file_id
    try:
        bot.send_video(
            chat_id,
            VIDEO_FILE_ID,
            caption="📹 **How to use SOCKS5/HTTPS proxies on Android**\n\n"
                    "Watch this short tutorial first (~2 minutes)",
            supports_streaming=True,
            timeout=60
        )
    except Exception as e:
        print(f"Video send error: {e}")
        bot.send_message(
            chat_id,
            "⚠️ Could not send the tutorial video right now.\n"
            "Please try /start again in a few moments."
        )

    # 2. Generate fresh random proxies
    https_proxies = generate_random_proxies('https', 70)
    socks5_proxies = generate_random_proxies('socks5', 70)

    # 3. Create PDFs
    generate_pdf('https_servers.pdf', https_proxies, "HTTPS Proxies List")
    generate_pdf('socks5_servers.pdf', socks5_proxies, "SOCKS5 Proxies List")

    # 4. Send PDFs
    try:
        with open('https_servers.pdf', 'rb') as f:
            bot.send_document(
                chat_id, f,
                caption=f"🔒 70 Random HTTPS Proxies\nGenerated: {len(https_proxies)}"
            )

        with open('socks5_servers.pdf', 'rb') as f:
            bot.send_document(
                chat_id, f,
                caption=f"🧦 70 Random SOCKS5 Proxies\nGenerated: {len(socks5_proxies)}"
            )
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error sending PDF files: {str(e)}")

    # 5. Final instructions
    bot.send_message(
        chat_id,
        "✅ **All set!**\n\n"
        "• Use the proxies at your own risk (they are randomly generated)\n"
        "• Send feedback anytime:\n"
        "`/feedback Your message here`",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=['feedback'])
def feedback(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if len(text.split()) <= 1:
        bot.reply_to(message, "❗ Please write your message after `/feedback`\n"
                              "Example: `/feedback The proxies are working great!`")
        return

    try:
        bot.forward_message(ADMIN_ID, chat_id, message.message_id)
        bot.reply_to(message, "✅ Your feedback has been sent to the admin. Thank you!")
    except Exception:
        bot.reply_to(message, "⚠️ Failed to send feedback. Please try again later.")


@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.reply_to_message is not None)
def admin_reply(message):
    replied = message.reply_to_message

    if not replied.forward_from:
        bot.reply_to(message, "❌ This message is not a forwarded feedback.")
        return

    user_id = replied.forward_from.id

    try:
        bot.send_message(
            user_id,
            f"📨 **Admin Reply**:\n\n{message.text}",
            parse_mode="Markdown"
        )
        bot.reply_to(message, f"✅ Reply sent to user {user_id}")
    except Exception as e:
        bot.reply_to(message, f"❌ Failed to send reply:\n{str(e)}")


if __name__ == '__main__':
    print("🚀 Proxy Bot is running...")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
