import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
import yt_dlp
import re
import time
from typing import Optional
import aiohttp

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token from environment variable
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8239659811:AAHYl1kdaoxI9efocf2tCVf7lKY_QJ0YAWA')

# Channel usernames to check
CHANNELS = ['@ProTech43', '@Pro43Zone', '@SQ_BOTZ']

# Language dictionaries with full descriptions
LANG = {
    'ps': {
        'welcome': "🌟 **د یوټیوب/فیسبوک/ټیکټاک ډاونلوډر بوټ ته ښه راغلاست!**\n\n"
                   "دا بوټ کولی شي له لاندې پلیټ فارمونو څخه ویدیوګانې ډاونلوډ کړي:\n"
                   "• **یوټیوب** - ویډیوګانې، شارټس، پلی لیستونه\n"
                   "• **فیسبوک** - عامه ویډیوګانې، ریلس\n"
                   "• **ټیکټاک** - ویډیوګانې پرته له واټرمارک\n\n"
                   "**څنګه کارول کیږي:**\n"
                   "1. لاندې چینلونو کې شامل شئ\n"
                   "2. د ویډیو لینک رالیږئ\n"
                   "3. بوټ به په اتوماتيک ډول ډاونلوډ کړي\n\n"
                   "**محدودیتونه:**\n"
                   "• اعظمي اندازه: 50MB\n"
                   "• ملاتړ شوي فارمېټونه: MP4، WEBM\n\n"
                   "مهرباني وکړئ خپله ژبه وټاکئ:",
        'select_lang': "📋 **ژبه وټاکئ:**",
        'send_link': "📩 **مهرباني وکړئ د ویډیو لینک رالیږئ**\n\n"
                     "지원되는 플랫폼:\n"
                     "• یوټیوب: https://youtube.com/watch?v=...\n"
                     "• فیسبوک: https://facebook.com/...\n"
                     "• ټیکټاک: https://tiktok.com/...",
        'processing': "⚙️ **پروسس کول...**\n\nمهرباني وکړئ انتظار وکړئ",
        'downloading': "📥 **ډاونلوډ کول...**\n\n⏳ دا یو څه وخت نیسي",
        'uploading': "📤 **اپلوډ کول...**\n\n⏳ مهرباني وکړئ صبر وکړئ",
        'success': "✅ **ویډیو په بریالیتوب سره ډاونلوډ شوه!**\n\n"
                   "📊 **د ویډیو معلومات:**\n"
                   "• عنوان: {title}\n"
                   "• اوږدوالی: {duration}\n"
                   "• اندازه: {size}\n\n"
                   "د بیا کارونې لپاره نوی لینک رالیږئ",
        'error': "❌ **تېروتنه!**\n\n{error}\n\nمهرباني وکړئ بیا هڅه وکړئ یا بل لینک وکاروئ",
        'invalid_link': "❌ **ناسم لینک**\n\nمهرباني وکړئ د یوټیوب، فیسبوک یا ټیکټاک معتبر لینک رالیږئ",
        'join_channels': "🚫 **لاسرسی نه دی اجازه!**\n\n"
                        "د دې بوټ کارولو لپاره، مهرباني وکړئ لومړی لاندې چینلونو کې شامل شئ:\n\n"
                        "{channels}\n\n"
                        "⚠️ **یادونه:**\n"
                        "• د شاملیدو وروسته، /start کېږئ\n"
                        "• که لا تر اوسه تېروتنه وي، چینلونه تازه کړئ",
        'joined': "✅ **مننه!**\n\n"
                 "تاسو په ټولو چینلونو کې شامل یاست.\n"
                 "اوس کولی شئ د ویډیو لینک رالیږئ",
        'not_joined': "❌ **تاسو لا تر اوسه په ټولو چینلونو کې نه یاست شامل شوي!**\n\n"
                     "مهرباني وکړئ لومړی ټولو چینلونو کې شامل شئ",
        'checking': "🔍 **چیک کول...**\n\nستاسو د غړیتوب تایید کیږي",
        'language_set': "✅ **ژبه په بریالیتوب سره وټاکل شوه!**\n\n"
                       "اوس مهرباني وکړئ د ویډیو لینک رالیږئ",
        'stats': "📊 **د بوټ احصایه:**\n\n"
                "• ټول ډاونلوډونه: {total_downloads}\n"
                "• نن ډاونلوډونه: {today_downloads}\n"
                "• فعال کارونکي: {active_users}\n"
                "• وروستی فعالیت: {last_activity}"
    },
    'fa': {
        'welcome': "🌟 **به ربات دانلود یوتیوب/فیسبوک/تیک تاک خوش آمدید!**\n\n"
                   "این ربات می‌تواند ویدیوها را از پلتفرم‌های زیر دانلود کند:\n"
                   "• **یوتیوب** - ویدیوها، شورتز، پلی لیست‌ها\n"
                   "• **فیسبوک** - ویدیوهای عمومی، ریلز\n"
                   "• **تیک تاک** - ویدیوها بدون واترمارک\n\n"
                   "**نحوه استفاده:**\n"
                   "1. در کانال‌های زیر عضو شوید\n"
                   "2. لینک ویدیو را ارسال کنید\n"
                   "3. ربات به صورت خودکار دانلود می‌کند\n\n"
                   "**محدودیت‌ها:**\n"
                   "• حداکثر اندازه: 50MB\n"
                   "• فرمت‌های پشتیبانی شده: MP4، WEBM\n\n"
                   "لطفاً زبان خود را انتخاب کنید:",
        'select_lang': "📋 **زبان خود را انتخاب کنید:**",
        'send_link': "📩 **لطفاً لینک ویدیو را ارسال کنید**\n\n"
                     "پلتفرم‌های پشتیبانی شده:\n"
                     "• یوتیوب: https://youtube.com/watch?v=...\n"
                     "• فیسبوک: https://facebook.com/...\n"
                     "• تیک تاک: https://tiktok.com/...",
        'processing': "⚙️ **در حال پردازش...**\n\nلطفاً صبر کنید",
        'downloading': "📥 **در حال دانلود...**\n\n⏳ این ممکن است چند لحظه طول بکشد",
        'uploading': "📤 **در حال آپلود...**\n\n⏳ لطفاً صبر کنید",
        'success': "✅ **ویدیو با موفقیت دانلود شد!**\n\n"
                   "📊 **اطلاعات ویدیو:**\n"
                   "• عنوان: {title}\n"
                   "• مدت زمان: {duration}\n"
                   "• اندازه: {size}\n\n"
                   "برای استفاده مجدد، لینک جدید ارسال کنید",
        'error': "❌ **خطا!**\n\n{error}\n\nلطفاً دوباره تلاش کنید یا از لینک دیگری استفاده کنید",
        'invalid_link': "❌ **لینک نامعتبر**\n\nلطفاً یک لینک معتبر از یوتیوب، فیسبوک یا تیک تاک ارسال کنید",
        'join_channels': "🚫 **دسترسی مجاز نیست!**\n\n"
                        "برای استفاده از این ربات، لطفاً ابتدا در کانال‌های زیر عضو شوید:\n\n"
                        "{channels}\n\n"
                        "⚠️ **توجه:**\n"
                        "• پس از عضویت، /start را بزنید\n"
                        "• اگر همچنان خطا دارید، کانال‌ها را رفرش کنید",
        'joined': "✅ **متشکرم!**\n\n"
                 "شما در تمام کانال‌ها عضو هستید.\n"
                 "اکنون می‌توانید لینک ویدیو را ارسال کنید",
        'not_joined': "❌ **شما هنوز در تمام کانال‌ها عضو نشده‌اید!**\n\n"
                     "لطفاً ابتدا در تمام کانال‌ها عضو شوید",
        'checking': "🔍 **در حال بررسی...**\n\nعضویت شما بررسی می‌شود",
        'language_set': "✅ **زبان با موفقیت انتخاب شد!**\n\n"
                       "اکنون لطفاً لینک ویدیو را ارسال کنید",
        'stats': "📊 **آمار ربات:**\n\n"
                "• کل دانلودها: {total_downloads}\n"
                "• دانلودهای امروز: {today_downloads}\n"
                "• کاربران فعال: {active_users}\n"
                "• آخرین فعالیت: {last_activity}"
    },
    'en': {
        'welcome': "🌟 **Welcome to YouTube/Facebook/TikTok Downloader Bot!**\n\n"
                   "This bot can download videos from the following platforms:\n"
                   "• **YouTube** - Videos, Shorts, Playlists\n"
                   "• **Facebook** - Public videos, Reels\n"
                   "• **TikTok** - Videos without watermark\n\n"
                   "**How to use:**\n"
                   "1. Join the channels below\n"
                   "2. Send the video link\n"
                   "3. Bot will automatically download\n\n"
                   "**Limitations:**\n"
                   "• Maximum size: 50MB\n"
                   "• Supported formats: MP4, WEBM\n\n"
                   "Please select your language:",
        'select_lang': "📋 **Select your language:**",
        'send_link': "📩 **Please send the video link**\n\n"
                     "Supported platforms:\n"
                     "• YouTube: https://youtube.com/watch?v=...\n"
                     "• Facebook: https://facebook.com/...\n"
                     "• TikTok: https://tiktok.com/...",
        'processing': "⚙️ **Processing...**\n\nPlease wait",
        'downloading': "📥 **Downloading...**\n\n⏳ This may take a moment",
        'uploading': "📤 **Uploading...**\n\n⏳ Please wait",
        'success': "✅ **Video downloaded successfully!**\n\n"
                   "📊 **Video Information:**\n"
                   "• Title: {title}\n"
                   "• Duration: {duration}\n"
                   "• Size: {size}\n\n"
                   "Send a new link to use again",
        'error': "❌ **Error!**\n\n{error}\n\nPlease try again or use another link",
        'invalid_link': "❌ **Invalid link**\n\nPlease send a valid YouTube, Facebook, or TikTok link",
        'join_channels': "🚫 **Access Denied!**\n\n"
                        "To use this bot, please join the following channels first:\n\n"
                        "{channels}\n\n"
                        "⚠️ **Note:**\n"
                        "• After joining, press /start\n"
                        "• If still error, refresh channels",
        'joined': "✅ **Thank you!**\n\n"
                 "You have joined all channels.\n"
                 "You can now send the video link",
        'not_joined': "❌ **You haven't joined all channels yet!**\n\n"
                     "Please join all channels first",
        'checking': "🔍 **Checking...**\n\nVerifying your membership",
        'language_set': "✅ **Language set successfully!**\n\n"
                       "Now please send the video link",
        'stats': "📊 **Bot Statistics:**\n\n"
                "• Total downloads: {total_downloads}\n"
                "• Today downloads: {today_downloads}\n"
                "• Active users: {active_users}\n"
                "• Last activity: {last_activity}"
    }
}

# User data storage (in production, use a database)
user_languages = {}
user_stats = {
    'total_downloads': 0,
    'today_downloads': 0,
    'active_users': set(),
    'last_activity': time.strftime('%Y-%m-%d %H:%M:%S')
}

class VideoDownloader:
    def __init__(self):
        self.ydl_opts = {
            'format': 'best[filesize<50M][ext=mp4]/best[filesize<50M]/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'force_generic_extractor': False,
        }
    
    async def download_video(self, url: str) -> Optional[dict]:
        """Download video and return info"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Extract info
                info = ydl.extract_info(url, download=False)
                
                if info.get('filesize', 0) > 50 * 1024 * 1024:
                    return {'error': 'File too large (>50MB)'}
                
                # Download
                filename = ydl.prepare_filename(info)
                ydl.download([url])
                
                return {
                    'success': True,
                    'filename': filename,
                    'title': info.get('title', 'Unknown'),
                    'duration': self.format_duration(info.get('duration', 0)),
                    'size': self.format_size(info.get('filesize', 0)),
                    'ext': info.get('ext', 'mp4')
                }
        except Exception as e:
            logger.error(f"Download error: {e}")
            return {'error': str(e)}
    
    def format_duration(self, seconds: int) -> str:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    def format_size(self, bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024
        return f"{bytes:.1f} GB"

# Initialize downloader
downloader = VideoDownloader()

async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is member of all channels"""
    try:
        for channel in CHANNELS:
            chat_member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if chat_member.status in ['left', 'kicked']:
                return False
        return True
    except Exception as e:
        logger.error(f"Membership check error: {e}")
        return False

def get_language_keyboard():
    """Create language selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("پښتو 🇦🇫", callback_data='lang_ps'),
            InlineKeyboardButton("فارسی 🇮🇷", callback_data='lang_fa'),
            InlineKeyboardButton("English 🇬🇧", callback_data='lang_en')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_channels_keyboard():
    """Create channels keyboard"""
    keyboard = []
    for channel in CHANNELS:
        keyboard.append([InlineKeyboardButton(f"📢 {channel}", url=f"https://t.me/{channel[1:]}")])
    keyboard.append([InlineKeyboardButton("✅ تایید عضویت", callback_data='check_membership')])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user_id = update.effective_user.id
    
    # Show language selection first
    await update.message.reply_text(
        LANG['en']['welcome'],
        reply_markup=get_language_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith('lang_'):
        # Set language
        lang = data.split('_')[1]
        user_languages[user_id] = lang
        
        # Check membership
        if await check_membership(user_id, context):
            await query.edit_message_text(
                LANG[lang]['joined'],
                parse_mode=ParseMode.MARKDOWN
            )
            await query.message.reply_text(
                LANG[lang]['send_link'],
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            channels_text = "\n".join([f"• {ch}" for ch in CHANNELS])
            await query.edit_message_text(
                LANG[lang]['join_channels'].format(channels=channels_text),
                reply_markup=get_channels_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
    
    elif data == 'check_membership':
        lang = user_languages.get(user_id, 'en')
        
        if await check_membership(user_id, context):
            await query.edit_message_text(
                LANG[lang]['joined'],
                parse_mode=ParseMode.MARKDOWN
            )
            await query.message.reply_text(
                LANG[lang]['send_link'],
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            channels_text = "\n".join([f"• {ch}" for ch in CHANNELS])
            await query.edit_message_text(
                LANG[lang]['not_joined'],
                reply_markup=get_channels_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video links"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Get user language
    lang = user_languages.get(user_id, 'en')
    
    # Check membership
    if not await check_membership(user_id, context):
        channels_text = "\n".join([f"• {ch}" for ch in CHANNELS])
        await update.message.reply_text(
            LANG[lang]['join_channels'].format(channels=channels_text),
            reply_markup=get_channels_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Validate URL
    url_pattern = re.compile(r'https?://(?:www\.)?(youtube\.com|youtu\.be|facebook\.com|fb\.watch|tiktok\.com)/\S+')
    if not url_pattern.match(text):
        await update.message.reply_text(
            LANG[lang]['invalid_link'],
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        LANG[lang]['processing'],
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Update stats
    user_stats['active_users'].add(user_id)
    user_stats['total_downloads'] += 1
    user_stats['today_downloads'] += 1
    user_stats['last_activity'] = time.strftime('%Y-%m-%d %H:%M:%S')
    
    # Download video
    result = await downloader.download_video(text)
    
    if 'error' in result:
        await processing_msg.edit_text(
            LANG[lang]['error'].format(error=result['error']),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    if result.get('success'):
        await processing_msg.edit_text(
            LANG[lang]['uploading'],
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Upload video
        try:
            with open(result['filename'], 'rb') as video:
                await update.message.reply_video(
                    video=video,
                    caption=LANG[lang]['success'].format(
                        title=result['title'],
                        duration=result['duration'],
                        size=result['size']
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                    supports_streaming=True
                )
            
            # Clean up
            os.remove(result['filename'])
            await processing_msg.delete()
            
        except Exception as e:
            logger.error(f"Upload error: {e}")
            await processing_msg.edit_text(
                LANG[lang]['error'].format(error="Upload failed"),
                parse_mode=ParseMode.MARKDOWN
            )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics"""
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, 'en')
    
    # Check if user is admin (you can add admin IDs)
    admin_ids = [123456789]  # Replace with your admin IDs
    
    if user_id not in admin_ids:
        await update.message.reply_text("⛔ Access denied!")
        return
    
    stats_text = LANG[lang]['stats'].format(
        total_downloads=user_stats['total_downloads'],
        today_downloads=user_stats['today_downloads'],
        active_users=len(user_stats['active_users']),
        last_activity=user_stats['last_activity']
    )
    
    await update.message.reply_text(
        stats_text,
        parse_mode=ParseMode.MARKDOWN
    )

def main():
    """Main function"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start bot
    logger.info("Bot started!")
    application.run_polling()

if __name__ == '__main__':
    main()
