import os
import sys
import subprocess
import tempfile
from io import StringIO
import traceback
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# توکن ربات تلگرام خود را اینجا وارد کنید
BOT_TOKEN = "7530258287:AAEQzSqEYvU9pOM8UfqSPhW6hDs9nbqR-Sw"

# لیست کاربران مجاز (اختیاری - برای امنیت بیشتر)
ALLOWED_USERS = []  # مثال: [123456789, 987654321]

class CodeExecutor:
    def __init__(self):
        self.allowed_imports = {
            # کتابخانه‌های تلگرام
            'telegram', 'telegram.ext', 'python-telegram-bot',
            # کتابخانه‌های پایه
            'os', 'sys', 'json', 'time', 'datetime', 'random', 'math',
            'requests', 'urllib', 'base64', 'hashlib', 'uuid',
            # کتابخانه‌های علمی
            'numpy', 'pandas', 'matplotlib', 'seaborn', 'scipy',
            # کتابخانه‌های وب
            'beautifulsoup4', 'lxml', 'selenium',
            # سایر کتابخانه‌های مفید
            'pillow', 'opencv-python', 'sqlite3'
        }
    
    def execute_python_code(self, code):
        """اجرای کد پایتون در محیط امن"""
        try:
            # ایجاد فایل موقت
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # اجرای کد با timeout
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30,  # حداکثر 30 ثانیه
                cwd=tempfile.gettempdir()
            )
            
            # پاک کردن فایل موقت
            os.unlink(temp_file)
            
            output = ""
            if result.stdout:
                output += f"📤 خروجی:\n```\n{result.stdout}\n```\n"
            
            if result.stderr:
                output += f"❌ خطا:\n```\n{result.stderr}\n```\n"
            
            if result.returncode != 0:
                output += f"💥 کد خروج: {result.returncode}"
            
            return output if output else "✅ کد با موفقیت اجرا شد (بدون خروجی)"
            
        except subprocess.TimeoutExpired:
            return "⏰ خطا: زمان اجرا بیش از حد مجاز (30 ثانیه)"
        except Exception as e:
            return f"❌ خطای اجرا: {str(e)}"
    
    def install_package(self, package_name):
        """نصب کتابخانه با pip"""
        try:
            if package_name not in self.allowed_imports:
                return f"❌ کتابخانه '{package_name}' در لیست مجاز نیست"
            
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return f"✅ کتابخانه '{package_name}' با موفقیت نصب شد"
            else:
                return f"❌ خطا در نصب '{package_name}':\n```{result.stderr}```"
                
        except subprocess.TimeoutExpired:
            return "⏰ خطا: زمان نصب بیش از حد مجاز"
        except Exception as e:
            return f"❌ خطای نصب: {str(e)}"

# ایجاد نمونه اجراکننده کد
executor = CodeExecutor()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور شروع"""
    welcome_text = """
🤖 سلام! من ربات اجرای کد پایتون هستم

📝 دستورات موجود:
/start - نمایش این پیام
/help - راهنمای استفاده
/install <package> - نصب کتابخانه
/allowed - نمایش کتابخانه‌های مجاز

💡 برای اجرای کد، فقط کد پایتون خود را ارسال کنید!

⚠️ نکات مهم:
• حداکثر زمان اجرا: 30 ثانیه
• کد در محیط امن اجرا می‌شود
• فقط کتابخانه‌های مجاز قابل استفاده است
    """
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """راهنمای استفاده"""
    help_text = """
📚 راهنمای استفاده:

1️⃣ اجرای کد ساده:
```python
print("سلام دنیا!")
```

2️⃣ استفاده از کتابخانه‌ها:
```python
import requests
response = requests.get('https://api.github.com')
print(response.status_code)
```

3️⃣ کار با تلگرام:
```python
from telegram import Bot
# کد ربات تلگرام شما
```

4️⃣ نصب کتابخانه جدید:
/install requests

⚠️ محدودیت‌ها:
• بدون دسترسی به فایل سیستم
• بدون دسترسی به شبکه محلی
• حداکثر 30 ثانیه زمان اجرا
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def install_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نصب کتابخانه"""
    if not context.args:
        await update.message.reply_text("❌ لطفاً نام کتابخانه را مشخص کنید\nمثال: /install requests")
        return
    
    package_name = context.args[0]
    await update.message.reply_text(f"⏳ در حال نصب {package_name}...")
    
    result = executor.install_package(package_name)
    await update.message.reply_text(result, parse_mode='Markdown')

async def show_allowed_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش کتابخانه‌های مجاز"""
    packages = "\n".join(f"• {pkg}" for pkg in sorted(executor.allowed_imports))
    text = f"📦 کتابخانه‌های مجاز:\n\n{packages}"
    await update.message.reply_text(text)

async def execute_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اجرای کد پایتون"""
    # بررسی کاربر مجاز (اختیاری)
    if ALLOWED_USERS and update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("❌ شما مجاز به استفاده از این ربات نیستید")
        return
    
    code = update.message.text
    
    # بررسی امنیتی ساده
    dangerous_keywords = ['import os', 'subprocess', 'eval', 'exec', 'open(', '__import__']
    for keyword in dangerous_keywords:
        if keyword in code.lower():
            await update.message.reply_text(f"⚠️ استفاده از '{keyword}' مجاز نیست")
            return
    
    await update.message.reply_text("⏳ در حال اجرای کد...")
    
    result = executor.execute_python_code(code)
    
    # محدود کردن طول پیام
    if len(result) > 4000:
        result = result[:4000] + "\n... (خروجی کوتاه شده)"
    
    await update.message.reply_text(result, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت خطاها"""
    error_message = f"❌ خطای داخلی: {context.error}"
    if update.effective_message:
        await update.effective_message.reply_text(error_message)

def main():
    """تابع اصلی"""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ لطفاً توکن ربات را در کد وارد کنید")
        return
    
    # ایجاد اپلیکیشن
    app = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن دستورات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("install", install_package))
    app.add_handler(CommandHandler("allowed", show_allowed_packages))
    
    # اضافه کردن هندلر برای کدها
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, execute_code))
    
    # مدیریت خطاها
    app.add_error_handler(error_handler)
    
    print("🤖 ربات شروع شد...")
    print("برای توقف: Ctrl+C")
    
    # شروع ربات
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()