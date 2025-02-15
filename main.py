import telebot
import sqlite3
from telebot import types



SPECIALIZATIONS = {
    "01.04.03_04" : "Математическое моделирование процессов нефтегазодобычи",
    "01.04.03_06" : "Моделирование физико-механических свойств и технологии производства полимеров и композитов",
    "09.04.04_04" : "ИТ – инфраструктура предприятия",
    "10.04.01_04" : "Кибербезопасность нефтегазовой отрасли",
    "38.04.01_30" : "Экономика ИТ и бизнес-анализ"
}
GROUPS = {
    "01.04.03_04" : [],
    "01.04.03_06" : [],
    "09.04.04_04" : ['5140904/40401', '5140904/30401'],
    "10.04.01_04" : [],
    "38.04.01_30" : [],
}
DISCIPLINES = {1 : {}, 2 : {}, 3 : {}, 4 : {}}
QUESTIONS = {}

def read_file(file_name):
    with open(file_name, 'r') as file:
        return file.read()

bot = telebot.TeleBot(read_file('token.ini'))

@bot.message_handler(commands=['start'])
def main(message):
    connect = sqlite3.connect('feedback.sql')
    cur = connect.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS data (id integer primary key, username varchar(50), fio varchar(50), specialization varchar(50), semester varchar(50), survey text)')
    cur.execute('INSERT OR IGNORE INTO data (id, username) VALUES (%d, "%s")' % (message.chat.id, message.chat.username))
    connect.commit()
    check_user = cur.execute('SELECT fio FROM data WHERE id= %d' % message.chat.id).fetchone()
    cur.close()
    connect.close()
    if check_user[0] is None:
        btn = types.InlineKeyboardButton('Ввести ФИО', callback_data='enter_fio')
        first_message = f'Привет! \n\nЗдесь ты можешь пройти опрос о качестве предоставляемого обучения на корпоративных магистратурах и оставить отзыв о преподаваемых дисциплинах. \n\nДля того чтобы начать нажми на кнопку ниже и введи свои данные'
    else:
        btn = types.InlineKeyboardButton('Пройти опрос', callback_data='complete_the_survey')
        first_message = f'Привет! \n\nЗдесь ты можешь пройти опрос о качестве предоставляемого обучения на корпоративных магистратурах и оставить отзыв о преподаваемых дисциплинах.'
    keyboard= types.InlineKeyboardMarkup()
    keyboard.row(btn)
    bot.send_message(message.chat.id, first_message, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: True)
def survey(callback):
    if callback.data == 'complete_the_survey':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        keyboard = specializations_buttons()
        bot.send_message(callback.message.chat.id, "Выберите ваше направление:", reply_markup=keyboard)
    elif callback.data == 'enter_fio':
        bot.edit_message_text('Отправь мне своё ФИО', callback.message.chat.id, callback.message.message_id)
        bot.register_next_step_handler(callback.message, register_fio)
    elif callback.data == '09.04.04_04':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        keyboard = group_code_buttons(callback.data)
        bot.send_message(callback.message.chat.id, 'Ты выбрал направление "ИТ – инфраструктура предприятия".\nТеперь выбери свою группу:', reply_markup=keyboard)
    elif callback.data == '01.04.03_04' or callback.data == '01.04.03_06' or callback.data == '10.04.01_04' or callback.data == '38.04.01_30':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        # временно, пока не внесены данные о других направлениях
        keyboard = specializations_buttons()
        bot.send_message(callback.message.chat.id, 'Опрос для этого направления находится в разработка.\nСейчас доступно направление ИТ-инфраструктура предприятия', reply_markup=keyboard)
    elif callback.data == '1_course':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        bot.send_message(callback.message.chat.id, 'Ты выбрал группу 5140904/40401')
    elif callback.data == '2_course':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        # временно, пока не внесены данные о других группах
        keyboard = group_code_buttons('09.04.04_04') 
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
    for key, value in SPECIALIZATIONS.items():
        callback_message = key
        keyboard.add(types.InlineKeyboardButton(value, callback_data = callback_message))
    return keyboard
    
        
def group_code_buttons(group_code):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for group in GROUPS[group_code]:
        callback_message = str(GROUPS[group_code].index(group)+1) + '_course'
        print(callback_message)
        keyboard.add(types.InlineKeyboardButton(group, callback_data = callback_message))
    return keyboard

bot.infinity_polling(timeout=10, long_polling_timeout = 5)