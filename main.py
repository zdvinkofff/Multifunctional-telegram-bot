import telebot
from PIL import Image
import io
from telebot import types
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = ''
bot = telebot.TeleBot(TOKEN)

user_states = {}  # Здесь будем хранить информацию о действиях пользователя

def mirror_image(image, orientation):
    if orientation == "horizontal":
        return image.transpose(Image.FLIP_LEFT_RIGHT)
    elif orientation == "vertical":
        return image.transpose(Image.FLIP_TOP_BOTTOM)
    else:
        return image

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Send me an image, and I'll provide options for you!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "I got your photo! Please choose the orientation for the mirrored image.",
                 reply_markup=get_orientation_keyboard())
    user_states[message.chat.id] = {'photo': message.photo[-1].file_id, 'state': 'waiting_for_orientation'}

def get_orientation_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    horizontal_btn = types.InlineKeyboardButton("Горизонтально", callback_data="horizontal")
    vertical_btn = types.InlineKeyboardButton("Вертикально", callback_data="vertical")
    keyboard.add(horizontal_btn, vertical_btn)
    return keyboard

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data in ["horizontal", "vertical"]:
        bot.answer_callback_query(call.id, f"Applying {call.data} mirroring to your image...")
        mirror_and_send(call.message, call.data)

def mirror_and_send(message, orientation):
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    mirrored_image = mirror_image(image, orientation)

    output_stream = io.BytesIO()
    mirrored_image.save(output_stream, format="JPEG")
    output_stream.seek(0)
    bot.send_photo(message.chat.id, output_stream)

bot.polling(none_stop=True)
