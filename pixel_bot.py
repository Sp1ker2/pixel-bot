# -*- coding: utf-8 -*-
from io import BytesIO
import random
import copy
import os

import telebot
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# 🔑 Читаем токен из переменной окружения (для Koyeb) или используем дефолтный
BOT_TOKEN = os.getenv("BOT_TOKEN", "8447761359:AAEXdTEUX7mMnQkYUPme5DkMllSlBa1sufQ")

bot = telebot.TeleBot(BOT_TOKEN)


def image_to_pixel_array(img):
    """Преобразует изображение в массив пикселей (цветов)."""
    # Конвертируем в RGB
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    # Получаем размеры
    width, height = img.size
    
    # Создаем массив пикселей: [height][width][R, G, B]
    pixels = []
    pixel_data = img.load()
    
    for y in range(height):
        row = []
        for x in range(width):
            r, g, b = pixel_data[x, y]
            row.append([r, g, b])
        pixels.append(row)
    
    return pixels, width, height


def pixel_array_to_image(pixels, width, height):
    """Преобразует массив пикселей обратно в изображение."""
    img = Image.new("RGB", (width, height))
    pixel_data = img.load()
    
    for y in range(height):
        for x in range(width):
            if y < len(pixels) and x < len(pixels[y]):
                r, g, b = pixels[y][x]
                pixel_data[x, y] = (int(r), int(g), int(b))
    
    return img


def create_colored_letter_pattern_on_pixels(pixels, width, height, letter_size=8, alpha=255):
    """Создает паттерн из случайных символов (буквы, цифры, спец. знаки) цветом под цвет массива пикселей."""
    # Создаем изображение с прозрачностью
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Пытаемся загрузить маленький шрифт
    try:
        font = ImageFont.truetype("arial.ttf", letter_size)
    except:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", letter_size)
        except:
            font = ImageFont.load_default()
            letter_size = 8
    
    # Весь алфавит (строчные и заглавные)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    # Цифры
    digits = "0123456789"
    
    # Спец. знаки
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"
    
    # Объединяем все символы
    all_symbols = alphabet + digits + special_chars
    
    # Получаем размеры одного символа (используем "a" как эталон)
    bbox = draw.textbbox((0, 0), "a", font=font)
    letter_w = bbox[2] - bbox[0]
    letter_h = bbox[3] - bbox[1]
    
    # Создаем паттерн - случайные символы по всему изображению
    spacing_x = letter_w + 2
    spacing_y = letter_h + 2
    
    # Сохраняем информацию о символах
    used_symbols = []
    
    for y in range(0, height, spacing_y):
        for x in range(0, width, spacing_x):
            # Берем цвет из массива пикселей в этой позиции
            pixel_y = min(y + letter_h // 2, height - 1)
            pixel_x = min(x + letter_w // 2, width - 1)
            
            # Получаем цвет пикселя из массива
            r, g, b = pixels[pixel_y][pixel_x]
            
            # Выбираем случайный символ (буква, цифра или спец. знак)
            random_symbol = random.choice(all_symbols)
            used_symbols.append(random_symbol)
            
            # Рисуем символ с заданной прозрачностью
            draw.text((x, y), random_symbol, font=font, fill=(r, g, b, alpha))
    
    # Получаем уникальные символы и их количество
    unique_symbols = list(set(used_symbols))
    symbol_info = ", ".join(sorted(unique_symbols))
    
    return img, symbol_info, len(used_symbols)


def blend_pattern_on_pixels(pixels, width, height, pattern_img):
    """Накладывает паттерн из маленьких букв на массив пикселей."""
    # Конвертируем паттерн в RGBA
    if pattern_img.mode != "RGBA":
        pattern_img = pattern_img.convert("RGBA")
    
    pattern_w, pattern_h = pattern_img.size
    pattern_data = pattern_img.load()
    
    # Накладываем паттерн на все пиксели
    for py in range(min(pattern_h, height)):
        for px in range(min(pattern_w, width)):
            # Получаем пиксель паттерна
            pattern_r, pattern_g, pattern_b, pattern_a = pattern_data[px, py]
            
            # Если пиксель паттерна не прозрачный (это буква "а")
            if pattern_a > 0:
                # Получаем пиксель фона
                bg_r, bg_g, bg_b = pixels[py][px]
                
                # Альфа-блендинг
                alpha = pattern_a / 255.0
                inv_alpha = 1.0 - alpha
                
                new_r = int(pattern_r * alpha + bg_r * inv_alpha)
                new_g = int(pattern_g * alpha + bg_g * inv_alpha)
                new_b = int(pattern_b * alpha + bg_b * inv_alpha)
                
                pixels[py][px] = [new_r, new_g, new_b]
    
    return pixels


def make_row_black(pixels, width, height, row_number=None):
    """Делает одну строку черной."""
    import random
    if row_number is None:
        row_number = random.randint(0, height - 1)
    
    # Делаем указанную строку черной
    for x in range(width):
        pixels[row_number][x] = [0, 0, 0]
    
    return pixels, row_number


@bot.message_handler(commands=["start"])
def send_welcome(message):
    text = (
        "👋 Привет! Я бот для обработки изображений через массив пикселей!\n\n"
        
        "📷 Просто пришли мне фото!"
    )
    bot.send_message(message.chat.id, text)


@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    # Берем самое большое фото
    photo = message.photo[-1]
    
    # Скачиваем файл
    file_info = bot.get_file(photo.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    try:
        # Загружаем изображение
        img = Image.open(BytesIO(downloaded_file))
        
        # Отправляем сообщение о начале обработки
        processing_msg = bot.send_message(
            message.chat.id,
            "⏳ Раскладываю изображение в массив цветов..."
        )
        
        # Преобразуем в массив пикселей
        pixels, width, height = image_to_pixel_array(img)
        
        # Подсчитываем общее количество пикселей
        total_pixels = width * height
        
        # Создаем паттерн с прозрачностью 10
        letter_size = max(6, int(min(width, height) / 50))  # Маленький размер буквы
        pattern_img_10, symbol_info, total_symbols = create_colored_letter_pattern_on_pixels(pixels, width, height, letter_size, alpha=10)
        
        # Накладываем паттерн на пиксели (прозрачность 10)
        pixels_10 = blend_pattern_on_pixels(copy.deepcopy(pixels), width, height, pattern_img_10)
        
        # Преобразуем обратно в изображение (прозрачность 10)
        result_img_10 = pixel_array_to_image(pixels_10, width, height)
        
        # Применяем фильтры для четкости (убираем размытие) - версия 10
        enhancer_10 = ImageEnhance.Sharpness(result_img_10)
        result_img_10 = enhancer_10.enhance(1.5)  # Увеличиваем резкость на 50%
        result_img_10 = result_img_10.filter(ImageFilter.SHARPEN)
        
        # Создаем паттерн с прозрачностью 255
        pattern_img_255, _, _ = create_colored_letter_pattern_on_pixels(pixels, width, height, letter_size, alpha=255)
        
        # Накладываем паттерн на пиксели (прозрачность 255)
        pixels_255 = blend_pattern_on_pixels(copy.deepcopy(pixels), width, height, pattern_img_255)
        
        # Преобразуем обратно в изображение (прозрачность 255)
        result_img_255 = pixel_array_to_image(pixels_255, width, height)
        
        # Применяем фильтры для четкости (убираем размытие) - версия 255
        enhancer_255 = ImageEnhance.Sharpness(result_img_255)
        result_img_255 = enhancer_255.enhance(1.5)  # Увеличиваем резкость на 50%
        result_img_255 = result_img_255.filter(ImageFilter.SHARPEN)
        
        # Удаляем сообщение о обработке
        try:
            bot.delete_message(message.chat.id, processing_msg.message_id)
        except:
            pass
        
        # Отправляем информацию
        info_text = (
            f"✅ Обработка завершена!\n\n"
            f"📐 Размеры: {width} x {height} пикселей\n"
            f"🎨 Всего пикселей: {total_pixels}\n"
            f"🔤 Использовано символов: {total_symbols}\n\n"
            f"🔧 Что сделано:\n"
            f"1️⃣ Разложено в массив пикселей\n"
            f"2️⃣ Создан паттерн из случайных символов (буквы, цифры, спец. знаки)\n"
            f"3️⃣ Создано 2 версии: с прозрачностью 10 и 255\n"
            f"4️⃣ Применены фильтры четкости\n"
            f"5️⃣ Преобразовано обратно в изображение"
        )
        
        bot.send_message(message.chat.id, info_text)
        
        # Сохраняем результат с прозрачностью 10
        output_10 = BytesIO()
        output_10.name = "result_alpha10.png"
        result_img_10.save(output_10, format="PNG")
        output_10.seek(0)
        
        bot.send_photo(
            message.chat.id,
            output_10,
            caption=f"✅ Версия 1: Прозрачность 10 (едва заметные символы)"
        )
        
        # Сохраняем результат с прозрачностью 255
        output_255 = BytesIO()
        output_255.name = "result_alpha255.png"
        result_img_255.save(output_255, format="PNG")
        output_255.seek(0)
        
        bot.send_photo(
            message.chat.id,
            output_255,
            caption=f"✅ Версия 2: Прозрачность 255 (полностью видимые символы)"
        )
        
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Ошибка при обработке: {str(e)}"
        )


@bot.message_handler(content_types=["text"])
def handle_text(message):
    text = (
        "🎨 Обработка изображений через массив пикселей!\n\n"
        "📷 Пришли фото как *изображение*\n\n"
        "Я:\n"
        "1. Раскладываю в массив пикселей\n"
        "2. Создаю паттерн из случайных символов (буквы, цифры, спец. знаки) по всему изображению\n"
        "3. Накладываю паттерн на пиксели (буквы полностью прозрачные, невидимы)\n"
        "4. Применяю фильтры четкости\n"
        "5. Возвращаю результат\n\n"
        "Изображение становится четким, случайные символы (буквы, цифры, спец. знаки) полностью прозрачные (невидимы)!"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


if __name__ == "__main__":
    import sys
    
    print("=" * 50)
    print("Pixel Bot is starting...")
    print("=" * 50)
    
    # Проверяем наличие токена
    if not BOT_TOKEN or BOT_TOKEN == "":
        print("❌ ОШИБКА: BOT_TOKEN не установлен!")
        print("Установите переменную окружения BOT_TOKEN")
        sys.exit(1)
    
    print(f"✅ Токен загружен (длина: {len(BOT_TOKEN)} символов)")
    print("🔄 Подключаюсь к Telegram...")
    
    try:
        # Удаляем старые webhook'и и обновления
        bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook удален, старые обновления очищены")
        
        print("🚀 Бот запущен и готов к работе!")
        print("Для остановки нажмите Ctrl+C")
        print("=" * 50)
        
        # Запускаем polling
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
        
    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("⏹️  Бот остановлен пользователем")
        print("=" * 50)
        sys.exit(0)
    except Exception as e:
        print("\n" + "=" * 50)
        print("❌ ОШИБКА при запуске бота:")
        print(f"   {str(e)}")
        print("=" * 50)
        
        if "409" in str(e) or "Conflict" in str(e):
            print("\n⚠️  Другой экземпляр бота уже запущен!")
            print("Остановите все другие экземпляры и попробуйте снова.")
        elif "401" in str(e) or "Unauthorized" in str(e):
            print("\n⚠️  Неверный токен бота!")
            print("Проверьте переменную окружения BOT_TOKEN")
        
        sys.exit(1)