import telebot
from PIL import Image, ImageOps
import io
from telebot import types
from dotenv import load_dotenv
import os
import cv2
import numpy as np
import random

# Загружаем токен бота Telegram из окружения
load_dotenv()
TOKEN = ''
bot = telebot.TeleBot(TOKEN)

# Словарь для хранения состояний пользователей
user_states = {}

# Набор ASCII-символов для создания ASCII-арта
ASCII_CHARS = '@%#*+=-:. '

# Список шуток
JOKES = [
    "Почему программисты всегда путают Хеллоуин и Рождество? Потому что 31 октября равно 25 декабря.",
    "Как назвать программиста, который использует и Java, и C#? Полиглот.",
    "Почему Java-разработчики всегда носят солнцезащитные очки? Потому что JAVA не знает оператора switch, а только if-else.",
    "Как называется группа программистов, которые всё время спорят о языках программирования? Флейм.",
    "Что общего между программистом и пиратом? Они оба работают с кодами."
]

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """
    Обрабатывает команды /start и /help.

    Args:
        message (telebot.types.Message): Объект сообщения.
    """
    bot.reply_to(message,
                 "Отправьте мне изображение, и я предоставлю вам варианты обработки! Или введите /random_joke, чтобы получить случайную шутку.")


@bot.message_handler(commands=['random_joke'])
def send_random_joke(message):
    """
    Обрабатывает команду /random_joke и отправляет случайную шутку пользователю.

    Args:
        message (telebot.types.Message): Объект сообщения.
    """
    # Выбираем случайную шутку из списка
    random_joke = random.choice(JOKES)

    # Отправляем шутку пользователю
    bot.reply_to(message, random_joke)


def resize_for_sticker(image, max_size=512):
    """
    Изменяет размер изображения, сохраняя пропорции, чтобы его максимальное измерение не превышало заданного максимума.

    Args:
        image (PIL.Image): Изображение, которое нужно изменить.
        max_size (int): Максимальный размер изображения (по одной из сторон).

    Returns:
        PIL.Image: Измененное изображение.
    """
    width, height = image.size

    # Определяем, какая сторона является максимальной
    max_dimension = max(width, height)

    # Если изображение и так меньше или равно заданному максимуму, возвращаем его без изменений
    if max_dimension <= max_size:
        return image

    # Вычисляем новые размеры, сохраняя пропорции
    if width >= height:
        new_width = max_size
        new_height = int(height * (max_size / width))
    else:
        new_height = max_size
        new_width = int(width * (max_size / height))

    # Изменяем размер изображения
    resized_image = image.resize((new_width, new_height), resample=Image.BICUBIC)

    return resized_image


def resize_image(image, new_width=100):
    """
    Изменяет размер изображения, сохраняя пропорции.

    Args:
        image (PIL.Image): Изображение, которое нужно изменить.
        new_width (int): Новая ширина изображения.

    Returns:
        PIL.Image: Измененное изображение.
    """
    width, height = image.size
    ratio = height / width
    new_height = int(new_width * ratio)
    return image.resize((new_width, new_height))


def grayify(image):
    """
    Преобразует изображение в оттенки серого.

    Args:
        image (PIL.Image): Изображение, которое нужно преобразовать.

    Returns:
        PIL.Image: Изображение в оттенках серого.
    """
    return image.convert("L")


def invert_colors(image):
    """
    Инвертирует цвета изображения.

    Args:
        image (PIL.Image): Изображение, цвета которого нужно инвертировать.

    Returns:
        PIL.Image: Изображение с инвертированными цветами.
    """
    return ImageOps.invert(image)


def image_to_ascii(image_stream, new_width=40, ascii_chars=ASCII_CHARS):
    """
    Преобразует изображение в ASCII-арт.

    Args:
        image_stream (io.BytesIO): Поток изображения, которое нужно преобразовать.
        new_width (int): Новая ширина ASCII-арта.
        ascii_chars (str): Набор символов, используемых для создания ASCII-арта.

    Returns:
        str: ASCII-арт, представляющий изображение.
    """
    image = Image.open(image_stream).convert('L')

    width, height = image.size
    aspect_ratio = height / float(width)
    new_height = int(aspect_ratio * new_width * 0.55)
    img_resized = image.resize((new_width, new_height))

    img_str = pixels_to_ascii(img_resized, ascii_chars)
    img_width = img_resized.width

    max_characters = 4000 - (new_width + 1)
    max_rows = max_characters // (new_width + 1)

    ascii_art = ""
    for i in range(0, min(max_rows * img_width, len(img_str)), img_width):
        ascii_art += img_str[i:i + img_width] + "\n"

    return ascii_art


def pixels_to_ascii(image, ascii_chars=ASCII_CHARS):
    """
    Преобразует пиксели изображения в ASCII-символы.

    Args:
        image (PIL.Image): Изображение, которое нужно преобразовать.
        ascii_chars (str): Набор символов, используемых для преобразования.

    Returns:
        str: ASCII-символьное представление изображения.
    """
    pixels = image.getdata()
    characters = ""
    for pixel in pixels:
        characters += ascii_chars[pixel * len(ascii_chars) // 256]
    return characters


def pixelate_image(image, pixel_size):
    """
    Пикселизует изображение.

    Args:
        image (PIL.Image): Изображение, которое нужно пикселизовать.
        pixel_size (int): Размер пикселей в пикселизованном изображении.

    Returns:
        PIL.Image: Пикселизованное изображение.
    """
    image = image.resize(
        (image.size[0] // pixel_size, image.size[1] // pixel_size),
        Image.NEAREST
    )
    image = image.resize(
        (image.size[0] * pixel_size, image.size[1] * pixel_size),
        Image.NEAREST
    )
    return image


def convert_to_heatmap(image_stream):
    """
    Преобразует изображение в тепловую карту.

    Args:
        image_stream (io.BytesIO): Поток изображения, которое нужно преобразовать.

    Returns:
        io.BytesIO: Поток изображения с тепловой картой.
    """
    # Загрузить изображение
    image = cv2.imdecode(np.frombuffer(image_stream.read(), np.uint8), cv2.IMREAD_COLOR)

    # Преобразовать в оттенки серого
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Применить тепловую карту
    heatmap = cv2.applyColorMap(gray_image, cv2.COLORMAP_JET)

    # Объединить исходное изображение и тепловую карту
    result = cv2.addWeighted(image, 0.5, heatmap, 0.5, 0)

    # Конвертировать в формат изображения для отправки
    output_stream = io.BytesIO()
    result_pil = Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
    result_pil.save(output_stream, format='JPEG')
    output_stream.seek(0)

    return output_stream


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """
    Обрабатывает команды /start и /help.

    Args:
        message (telebot.types.Message): Объект сообщения.
    """
    bot.reply_to(message, "Отправьте мне изображение, и я предоставлю вам варианты обработки!")


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """
    Обрабатывает изображение, полученное от пользователя.

    Args:
        message (telebot.types.Message): Объект сообщения, содержащий изображение.
    """
    bot.reply_to(message,
                 "Я получил ваше изображение! Пожалуйста, отправьте мне набор символов, которые вы хотите использовать для ASCII-арта.")
    user_states[message.chat.id] = {'photo': message.photo[-1].file_id, 'state': 'waiting_for_ascii_chars'}


@bot.message_handler(
    func=lambda message: user_states.get(message.chat.id, {}).get('state') == 'waiting_for_ascii_chars')
def handle_ascii_chars(message):
    """
    Обрабатывает ввод пользователя для символов ASCII-арта.

    Args:
        message (telebot.types.Message): Объект сообщения, содержащий ввод пользователя.
    """
    ascii_chars = message.text.strip()
    user_states[message.chat.id]['ascii_chars'] = ascii_chars
    bot.reply_to(message, "Понял! Выберите, что вы хотите сделать с изображением.",
                 reply_markup=get_options_keyboard())
    user_states[message.chat.id]['state'] = 'ready'


def get_options_keyboard():
    """
    Создает инлайн-клавиатуру с доступными вариантами обработки изображения.

    Returns:
        telebot.types.InlineKeyboardMarkup: Инлайн-клавиатура.
    """
    keyboard = types.InlineKeyboardMarkup()
    negative_btn = types.InlineKeyboardButton("Негатив", callback_data="negative")
    pixelate_btn = types.InlineKeyboardButton("Пикселизация", callback_data="pixelate")
    ascii_btn = types.InlineKeyboardButton("ASCII-арт", callback_data="ascii")
    heatmap_btn = types.InlineKeyboardButton("Тепловая карта", callback_data="heatmap")
    keyboard.add(negative_btn, pixelate_btn, ascii_btn, heatmap_btn)
    return keyboard


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """
    Обрабатывает нажатия на кнопки инлайн-клавиатуры.

    Args:
        call (telebot.types.CallbackQuery): Объект запроса обратного вызова.
    """
    if call.data == "negative":
        bot.answer_callback_query(call.id, "Применяю негатив к вашему изображению...")
        negative_and_send(call.message)
    elif call.data == "pixelate":
        bot.answer_callback_query(call.id, "Пикселизую ваше изображение...")
        pixelate_and_send(call.message)
    elif call.data == "ascii":
        bot.answer_callback_query(call.id, "Преобразую ваше изображение в ASCII-арт...")
        ascii_and_send(call.message)
    elif call.data == "heatmap":
        bot.answer_callback_query(call.id, "Применяю тепловую карту к вашему изображению...")
        heatmap_and_send(call.message)


def negative_and_send(message):
    """
    Применяет эффект негатива к изображению и отправляет его пользователю.

    Args:
        message (telebot.types.Message): Объект сообщения.
    """
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    inverted = invert_colors(image)

    output_stream = io.BytesIO()
    inverted.save(output_stream, format="JPEG")
    output_stream.seek(0)
    bot.send_photo(message.chat.id, output_stream)


def pixelate_and_send(message):
    """
    Применяет эффект пикселизации к изображению и отправляет его пользователю.

    Args:
        message (telebot.types.Message): Объект сообщения.
    """
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    image = invert_colors(image)
    pixelated = pixelate_image(image, 20)

    output_stream = io.BytesIO()
    pixelated.save(output_stream, format="JPEG")
    output_stream.seek(0)
    bot.send_photo(message.chat.id, output_stream)


def ascii_and_send(message):
    """
    Преобразует изображение в ASCII-арт и отправляет его пользователю.

    Args:
        message (telebot.types.Message): Объект сообщения.
    """
    photo_id = user_states[message.chat.id]['photo']
    ascii_chars = user_states[message.chat.id]['ascii_chars']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_stream = io.BytesIO(downloaded_file)
    image = Image.open(image_stream)
    image = invert_colors(image)
    ascii_art = image_to_ascii(image_stream, ascii_chars=ascii_chars)
    bot.send_message(message.chat.id, f"```\n{ascii_art}\n```", parse_mode="MarkdownV2")


def heatmap_and_send(message):
    """
    Применяет эффект тепловой карты к изображению и отправляет его пользователю.

    Args:
        message (telebot.types.Message): Объект сообщения.
    """
    photo_id = user_states[message.chat.id]['photo']
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_stream = io.BytesIO(downloaded_file)
    heatmap_stream = convert_to_heatmap(image_stream)
    bot.send_photo(message.chat.id, heatmap_stream)


bot.polling(none_stop=True)