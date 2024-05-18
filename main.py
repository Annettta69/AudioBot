# Импорт необходимых модулей
import os
import telebot
import requests
import speech_recognition as sr
from telebot import types
from pydub import AudioSegment
from collections import Counter
from nltk.corpus import stopwords

# Установка токена бота
token = '6616517747:AAGT10sGkVKKqUAgnfLYV3UTQpnIl0UjCF4'
bot = telebot.TeleBot(token)

count = 0
full_text = []
last_processed_message_id = None

# Обработчики сообщений
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    digital = types.KeyboardButton('Число сообщений')
    markup.add(digital)
    bot.send_message(message.chat.id, 'Привет! Здесь ты можешь обрабатывать свои сообщения! Введи количество сообщений, которое ты хочешь обработать!', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Число сообщений')
def handle_number_button(message):
    bot.send_message(message.chat.id, 'Хорошо, введите новое число.')

@bot.message_handler(func=lambda message: message.text.isdigit())
def handle_number(message):
    global count, full_text
    count = int(message.text)
    full_text = []  # Очищаем список full_text
    bot.send_message(message.chat.id, f'Число сообщений установлено на: {count}. Теперь можешь отправлять голосовые сообщения!')

@bot.message_handler(content_types=['voice'])
def handle_voice_messages(message):
    get_audio_messages(message)

# Обработка голосовых сообщений
def get_audio_messages(message):
    global fname  # Глобальная переменная для имени файла
    print("Started recognition...")  # Вывод сообщения о начале распознавания
    file_info = bot.get_file(message.voice.file_id)  # Получение информации о файле аудиосообщения
    path = file_info.file_path  # Получение пути к файлу
    fname = os.path.basename(path)  # Извлечение имени файла из пути
    download_audio_file(fname, path)  # Загрузка аудиофайла
    text = splitting_audio(fname)  # Разделение аудио на текст
    bot.send_message(message.from_user.id, text)  # Отправка текстового сообщения пользователю
    frequency = word_frequency(message, text)  # Вычисление частоты слов
    display_word_frequency(message, frequency)  # Отображение частоты слов
    delete_audio_file(fname)  # Удаление аудиофайла

# Скачивание аудиофайла
def download_audio_file(fname, path):
    doc = requests.get(f'https://api.telegram.org/file/bot{token}/{path}')  # загрузка аудиофайла по указанному пути
    with open(fname, 'wb') as file:
        file.write(doc.content)

# Разделение аудиофайла на сегменты
def splitting_audio(fname):
    recognizer = sr.Recognizer()  # Создаем экземпляр Recognizer
    ogg_audio = AudioSegment.from_ogg(fname)  # Загружаем аудиофайл формата OGG
    segment_duration = 60 * 1000  # Устанавливаем длительность сегмента в 60 секунд
    recognized_text = ""  # Инициализируем переменную для распознанного текста
    for i in range(0, len(ogg_audio), segment_duration): # Разбиваем аудио на сегменты длительностью 60 секунд
        segment = ogg_audio[i:i + segment_duration]
        segment.export(f"audio_segment_{i // segment_duration}.wav", format="wav")   # Экспортируем сегмент в формате WAV
        text = recognize_audio_segment(f"audio_segment_{i // segment_duration}.wav", recognizer)   # Распознаем текст в аудиосегменте
        recognized_text += text + " "  # Добавляем распознанный текст к общему результату
    return recognized_text.strip()  # Возвращаем распознанный текст без лишних пробелов

# Pаспознавание речи
def recognize_audio_segment(file_path, recognizer):
    with sr.AudioFile(file_path) as source:  # Открытие аудиофайла для чтения
        audio = recognizer.record(source)  # Запись аудио из файла
        text = recognizer.recognize_google(audio, language='ru-RU')  # Распознавание речи с помощью Google Speech Recognition
        print('You said:', text)  # Вывод распознанного текста в консоли
        return text

# Подсчет частоты слов
def word_frequency(message, text):
    global full_text, last_processed_message_id  # Глобальные переменные для хранения текста и последнего обработанного идентификатора сообщения
    if message.voice.file_id == last_processed_message_id:  # Проверка на совпадение идентификаторов файлов
        return  # Возврат, если идентификаторы совпадают
    last_processed_message_id = message.voice.file_id  # Обновление последнего обработанного идентификатора
    full_text.append("")  # Добавление пустой строки в список текста
    full_text[-1] += text  # Добавление текста к последней строке в списке
    if len(full_text) == count:  # Проверка на достижение заданного количества текстов
        word_counts = Counter()  # Создание счетчика слов
        russian_stopwords = stopwords.words('russian')  # Получение списка стоп-слов на русском языке
        for text in full_text:  # Перебор текстов
            words = text.split()  # Разделение текста на слова
            word_counts.update(word.lower() for word in words if word.lower() not in russian_stopwords)  # Обновление счетчика слов
        most_common_words = word_counts.most_common(10)  # Получение 10 наиболее часто встречающихся слов
        full_text = []  # Очистка списка текста
        return most_common_words  # Возврат наиболее часто встречающихся слов

# Oтображение результатов
def display_word_frequency(message, frequency):
    if frequency:  # Проверяем, есть ли частота слов
        message_text = "Топ 10 наиболее частых слов:\n"
        for word, count in frequency:
            message_text += f"{word}: {count}\n"  # Добавляем слово и его частоту к тексту сообщения
        bot.send_message(message.chat.id, message_text)

# Удаление аудиофайла
def delete_audio_file(fname):
    os.remove(fname)

# Запуск бота
bot.polling(none_stop=True, interval=0)
