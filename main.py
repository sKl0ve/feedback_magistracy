import telebot
import sqlite3
from telebot import types



QUESTIONS = {}
SPECIALIZATIONS = {
    1 : "01.04.03_04 Математическое моделирование процессов нефтегазодобычи",
    2 : "01.04.03_06 Моделирование физико-механических свойств и технологии производства полимеров и композитов",
    3 : "09.04.04_04 ИТ – инфраструктура предприятия",
    4 : "10.04.01_04 Кибербезопасность нефтегазовой отрасли",
    5 : "38.04.01_30 Экономика ИТ и бизнес-анализ"
}
DISCIPLINES = {1 : {}, 2 : {}, 3 : {}, 4 : {}}

def read_file(file_name):
    with open(file_name, 'r') as file:
        return file.read()

bot = telebot.TeleBot(read_file('token.ini'))

@bot.message_handler(commands=['start'])
def main(message):
    connect = sqlite3.connect('feedback.sql')
    cur = connect.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS data (id integer, username varchar(50), fio varchar(50), specialization varchar(50), semester varchar(50), survey text)')
    cur.execute('INSERT INTO data (id, username) VALUES (%d, "%s")' % (message.chat.id, message.chat.username))
    connect.commit()
    
    check_user = cur.execute('SELECT fio FROM data WHERE id= %d' % message.chat.id).fetchone()
    
    if check_user[0] is None:
        btn = types.InlineKeyboardButton('Ввести ФИО', callback_data='enter_fio')
        first_message = f'Привет! \n\nЗдесь ты можешь пройти опрос о качестве предоставляемого обучения на корпоративных магистратурах и оставить отзыв о преподаваемых дисциплинах. \n\nДля того чтобы начать нажми на кнопку ниже и введи свои данные'
    else:
        btn = types.InlineKeyboardButton('Пройти опрос', callback_data='complete_the_survey')
        first_message = f'Привет! \n\nЗдесь ты можешь пройти опрос о качестве предоставляемого обучения на корпоративных магистратурах и оставить отзыв о преподаваемых дисциплинах.'
    keyboard= types.InlineKeyboardMarkup()
    keyboard.row(btn)
    bot.send_message(message.chat.id, first_message, reply_markup=keyboard)
    cur.close()
    connect.close()


@bot.callback_query_handler(func=lambda callback: True)
def survey(callback):
    if callback.data == 'complete_the_survey':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        keyboard = specializations_buttons()
        bot.send_message(callback.message.chat.id, "Выберите ваше направление:", reply_markup=keyboard)
    elif callback.data == 'enter_fio':
        bot.edit_message_text('Отправь мне своё ФИО', callback.message.chat.id, callback.message.message_id)
        bot.register_next_step_handler(callback.message, register_fio)
    elif callback.data == 'specialization_09.04.04_04':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        keyboard = group_code_buttons()
        bot.send_message(callback.message.chat.id, 'Ты выбрал направление "ИТ – инфраструктура предприятия".\nТеперь выбери свою группу:', reply_markup=keyboard)
    elif callback.data == 'specialization_01.04.03_04' or callback.data == 'specialization_01.04.03_06' or callback.data == 'specialization_10.04.01_04' or callback.data == 'specialization_38.04.01_30':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        keyboard = specializations_buttons()
        bot.send_message(callback.message.chat.id, 'Опрос для этого направления находится в разработка.\nСейчас доступно направление ИТ-инфраструктура предприятия', reply_markup=keyboard)
    elif callback.data == 'first_course':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        bot.send_message(callback.message.chat.id, 'Ты выбрал группу 5140904/40401')
    elif callback.data == 'second_course':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        keyboard = group_code_buttons()
        bot.send_message(callback.message.chat.id, 'Опрос для этой группы находится в разработка.\nСейчас доступен опрос для группы 5140904/40401', reply_markup=keyboard)
        
        
def register_fio(message):
    connect = sqlite3.connect('feedback.sql')
    cur = connect.cursor()
    cur.execute('UPDATE data SET fio = "%s" WHERE id = %d ' % (message.text, message.chat.id))
    connect.commit()
    cur.close()
    connect.close()
    btn = types.InlineKeyboardButton('Пройти опрос', callback_data='complete_the_survey')
    keyboard= types.InlineKeyboardMarkup()
    keyboard.row(btn)
    bot.send_message(message.chat.id, 'Отлично! Теперь ты можешь пройти опрос о качестве обучения', reply_markup=keyboard)


def specializations_buttons():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for values in SPECIALIZATIONS.values():
        callback_message = "specialization_" + values[:11]
        keyboard.add(types.InlineKeyboardButton(values, callback_data = callback_message))
    return keyboard
    
        
def group_code_buttons():
    keyboard= types.InlineKeyboardMarkup(row_width=2)
    btn_group_1_course = types.InlineKeyboardButton('5140904/40401', callback_data = 'first_course')
    btn_group_2_course = types.InlineKeyboardButton('5140904/30401', callback_data = 'second_course')
    keyboard.row(btn_group_1_course, btn_group_2_course)
    return keyboard

bot.infinity_polling(timeout=10, long_polling_timeout = 5)