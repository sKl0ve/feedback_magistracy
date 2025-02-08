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
    cur.execute('CREATE TABLE IF NOT EXISTS data (id integer primary key, username varchar(50), fio varchar(50), specialization varchar(50), semester varchar(50), survey text)')
    connect.commit()
    
    check_user = cur.execute('SELECT fio FROM data WHERE id= %d' % message.chat.id)
    user = check_user.fetchall()
    print(type(user))
    
    if len(user) == 0:
        btn = types.InlineKeyboardButton('Ввести ФИО', callback_data='enter_fio')
        first_message = f'Привет! \n\nЗдесь ты можешь пройти опрос о качестве предоставляемого обучения на корпоративных магистратурах и оставить отзыв о преподаваемых дисциплинах. \n\nДля того чтобы начать нажми на кнопку ниже и введи свои данные'
    else:
        btn = types.InlineKeyboardButton('Пройти опрос', callback_data='complete_the_survey')
        first_message = f'Привет! \n\nЗдесь ты можешь пройти опрос о качестве предоставляемого обучения на корпоративных магистратурах и оставить отзыв о преподаваемых дисциплинах.'
    keyboard= types.InlineKeyboardMarkup()
    keyboard.row(btn)
    bot.send_message(message.chat.id, first_message, reply_markup=keyboard)
    # if len(user) == 0:
    #     btn_registration = types.InlineKeyboardButton('Ввести ФИО', callback_data='enter_fio', )
    # btn_complete_the_survey = types.InlineKeyboardButton('Пройти опрос', callback_data='complete_the_survey')
    # inline_keyboard.row(btn_complete_the_survey)
    # bot.send_message(message.chat.id, f'Привет! \nЗдесь ты можешь пройти опрос о качестве по качеству предоставляемого обучения на корпоративных магистратурах и оставить отзыв о преподаваемых дисциплинах.', parse_mode='html', reply_markup=inline_keyboard)
    # bot.register_next_step_handler(message, wish_url_add)

    # connect = sqlite3.connect('feedback.sql')
    # cur = connect.cursor()
    # cur.execute('REPLACE INTO data (id, username, fio) VALUES (%d, "%s", "%s")' % (message.chat.id, message.chat.username))
    # connect.commit()
    cur.close()
    connect.close()


@bot.callback_query_handler(func=lambda callback: True)
def survey(callback):
    if callback.data == 'complete_the_survey':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for values in SPECIALIZATIONS.values():
            keyboard.add(types.InlineKeyboardButton(values, callback_data = "callback"))
        bot.send_message(callback.message.chat.id, "Выберите ваше направление:", reply_markup=keyboard )
    #elif callback.data == 'enter_fio':
        
        
        
        
        
    
    
bot.infinity_polling(timeout=10, long_polling_timeout = 5)