# Telegram Proxy Bot
# - Sends tutorial video first using the correct file_id
# - Then generates and sends 2 PDFs: 70 random HTTPS + 70 random SOCKS5 proxies
# - Includes /feedback → admin can reply to users
#
# Requirements: pip install pyTelegramBotAPI reportlab
# Recommended: Store BOT_TOKEN in GitHub Codespaces secrets (name: BOT_TOKEN)

import telebot
import random
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# ────────────────────────────────────────────────
#   CONFIGURATION
# ────────────────────────────────────────────────
BOT_TOKEN   = os.getenv('BOT_TOKEN')           # ← from Codespaces secret
ADMIN_ID    = 6241269407                        # ← CHANGE THIS to your Telegram user ID (number)
VIDEO_FILE_ID = "BAACAgQAAxkBAAEDZbVp6dXGW59IG9zAHcmOAAH6UvlB-6MAAlcaAAJFSrBQU0NMe7A8DMo7BA"

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN environment variable not set!")
    print("Please add it in GitHub → Settings → Secrets and variables → Codespaces")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

def generate_random_proxies(protocol, count=70):
    proxies = []
    for _ in range(count):
        ip   = '.'.join(str(random.randint(0, 255)) for _ in range(4))
        port = random.randint(1024, 65535)
        proxies.append(f"{protocol}://{ip}:{port}")
    return proxies

def generate_pdf(filename, servers):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y = height - 60
    c.setFont("Helvetica", 10)
    for server in servers:
        if y < 40:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 10)
        c.drawString(50, y, server)
        y -= 18
    c.save()

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id

    # 1. Send tutorial video first
    try:
        bot.send_video(
            chat_id,
            VIDEO_FILE_ID,
            caption="📱 How to use SOCKS proxies on Android devices\n\nWatch this tutorial first! (~2 min)",
            supports_streaming=True,
            timeout=60
        )
    except Exception as e:
        bot.send_message(
            chat_id,
            f"⚠️ Could not send tutorial video.\nError: {str(e)}\n\n"
            f"You can watch it here: https://youtu.be/0nozGPksGZM"
        )

    # 2. Generate fresh random proxies
    https_proxies  = generate_random_proxies('https')
    socks5_proxies = generate_random_proxies('socks5')

    generate_pdf('https_servers.pdf',  https_proxies)
    generate_pdf('socks5_servers.pdf', socks5_proxies)

    # 3. Send PDFs
    try:
        with open('https_servers.pdf', 'rb') as f:
            bot.send_document(
                chat_id,
                f,
                caption=f"70 Random HTTPS proxies\nGenerated: {len(https_proxies)}"
            )

        with open('socks5_servers.pdf', 'rb') as f:
            bot.send_document(
                chat_id,
                f,
                caption=f"70 Random SOCKS5 proxies\nGenerated: {len(socks5_proxies)}"
            )
    except Exception as e:
        bot.send_message(chat_id, f"Error sending PDF files: {str(e)}")

    # 4. Instructions
    bot.send_message(
        chat_id,
        "✅ All set!\n\n"
        "• Use /feedback <your message> to send feedback or report issues\n"
        "• Admin can reply directly to your messages"
    )

@bot.message_handler(commands=['feedback'])
def feedback(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if len(text.split()) <= 1:
        bot.reply_to(message, "Please add your message after /feedback\nExample:\n/feedback Proxies are working great but slow")
        return

    try:
        bot.forward_message(ADMIN_ID, chat_id, message.message_id)
        bot.reply_to(message, "✅ Feedback sent to admin. Thank you!")
    except Exception:
        bot.reply_to(message, "⚠️ Could not send feedback right now. Try again later.")

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.reply_to_message is not None)
def admin_reply(message):
    if not message.reply_to_message.forward_from:
        bot.reply_to(message, "This doesn't seem to be a reply to a forwarded feedback.")
        return

    user_id = message.reply_to_message.forward_from.id
    try:
        bot.send_message(
            user_id,
            f"📩 Admin reply:\n\n{message.text}"
        )
        bot.reply_to(message, f"Reply sent to user {user_id}")
    except Exception as e:
        bot.reply_to(message, f"Failed to send reply:\n{str(e)}")

if __name__ == '__main__':
    print("Proxy Bot starting...")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
