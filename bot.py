from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from database import init_db, add_phone, get_all_phones, delete_phone, get_expiring_phones
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Khởi tạo database
init_db()

def start(update: Update, context: CallbackContext):
    menu = [['/add', '/list'], ['/delete', '/expiring']]
    reply_markup = ReplyKeyboardMarkup(menu, resize_keyboard=True)
    update.message.reply_text(
        "📱 Bot quản lý số điện thoại\n\n"
        "Các lệnh có sẵn:\n"
        "/add - Thêm số mới\n"
        "/list - Xem tất cả số\n"
        "/delete - Xóa số\n"
        "/expiring - Xem số sắp hết hạn",
        reply_markup=reply_markup
    )

def add_phone_handler(update: Update, context: CallbackContext):
    update.message.reply_text("Nhập thông tin theo định dạng:\n"
                            "<Số điện thoại>|<Tên chủ sở hữu>|<Ngày hết hạn (YYYY-MM-DD)>|<Ghi chú (tùy chọn)>\n"
                            "Ví dụ: 0912345678|Nguyễn Văn A|2023-12-31|Gói cước 1GB/tháng")

def process_add(update: Update, context: CallbackContext):
    try:
        parts = update.message.text.split('|')
        phone = parts[0].strip()
        owner = parts[1].strip()
        expire_date = parts[2].strip()
        notes = parts[3].strip() if len(parts) > 3 else ""
        
        if add_phone(phone, owner, expire_date, notes):
            update.message.reply_text(f"✅ Đã thêm số {phone} thành công!")
        else:
            update.message.reply_text(f"❌ Số {phone} đã tồn tại!")
    except Exception as e:
        update.message.reply_text("⚠️ Định dạng không hợp lệ! Vui lòng nhập lại.")

def list_phones(update: Update, context: CallbackContext):
    phones = get_all_phones()
    if not phones:
        update.message.reply_text("📭 Danh sách trống!")
        return
    
    response = "📋 Danh sách số điện thoại:\n\n"
    for phone in phones:
        response += (f"📱 Số: {phone[1]}\n"
                   f"👤 Chủ sở hữu: {phone[2]}\n"
                   f"📅 Hết hạn: {phone[3]}\n"
                   f"📝 Ghi chú: {phone[4]}\n\n")
    
    update.message.reply_text(response)

def delete_phone_handler(update: Update, context: CallbackContext):
    update.message.reply_text("Nhập số điện thoại cần xóa:")

def process_delete(update: Update, context: CallbackContext):
    phone = update.message.text.strip()
    delete_phone(phone)
    update.message.reply_text(f"✅ Đã xóa số {phone} thành công!")

def check_expiring(update: Update, context: CallbackContext):
    phones = get_expiring_phones(7)  # Kiểm tra số hết hạn trong 7 ngày tới
    if not phones:
        update.message.reply_text("🎉 Không có số nào sắp hết hạn trong 7 ngày tới!")
        return
    
    response = "⚠️ Các số sắp hết hạn:\n\n"
    for phone in phones:
        response += (f"📱 Số: {phone[1]}\n"
                   f"👤 Chủ sở hữu: {phone[2]}\n"
                   f"⏳ Hết hạn: {phone[3]} (còn {days_remaining(phone[3])} ngày)\n\n")
    
    update.message.reply_text(response)

def days_remaining(expire_date):
    from datetime import datetime
    expire = datetime.strptime(expire_date, '%Y-%m-%d')
    return (expire - datetime.now()).days

def setup_scheduler(context):
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_notify, 'interval', hours=24, args=[context])
    scheduler.start()

def check_and_notify(context: CallbackContext):
    phones = get_expiring_phones(3)  # Kiểm tra số hết hạn trong 3 ngày tới
    for phone in phones:
        message = (f"🔔 Thông báo gia hạn:\n\n"
                 f"📱 Số: {phone[1]}\n"
                 f"👤 Chủ sở hữu: {phone[2]}\n"
                 f"⏳ Hết hạn vào: {phone[3]}\n"
                 f"⏳ Còn lại: {days_remaining(phone[3])} ngày")
        
        # Gửi cho tất cả admin (cần thêm logic lấy chat_id admin)
        context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add", add_phone_handler))
    dp.add_handler(CommandHandler("list", list_phones))
    dp.add_handler(CommandHandler("delete", delete_phone_handler))
    dp.add_handler(CommandHandler("expiring", check_expiring))

    # Message handlers
    dp.add_handler(MessageHandler(Filters.regex(r'^\d+\|.+\|\d{4}-\d{2}-\d{2}'), process_add))
    dp.add_handler(MessageHandler(Filters.regex(r'^\d+$') & Filters.reply, process_delete))

    # Thiết lập scheduler
    setup_scheduler(updater.job_queue)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()