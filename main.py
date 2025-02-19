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
    "01.04.03_04" : {},
    "01.04.03_06" : {},
    "09.04.04_04" : {"1_course" : "5140904/40401", "2_course" : "5140904/30401"},
    "10.04.01_04" : {},
    "38.04.01_30" : {},
}
DISCIPLINES = {1 : ['Ин.яз. в проф. коммуникации', 'Цифровые ресурсы в НИ', 'Управление проектами', 'Верификация алгоритмов и систем', 'Построение ИТ инфраструктуры', 'ИТ инфраструктура предприятия', 'Внедрение и сопровождение ПП', 'Ознакомительная практика'],
               2 : [], 
               3 : [], 
               4 : []}
QUESTIONS = {}

def read_file(file_name):
    with open(file_name, 'r') as file:
        return file.read()

bot = telebot.TeleBot(read_file('token.ini'))

@bot.message_handler(commands=['start'])
def main(message):
    connect = sqlite3.connect('feedback.sql')
    cur = connect.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS student (chatid integer primary key, username varchar(50), fio varchar(80), specialization varchar(50), ciphergroup varchar(50))')
    cur.execute('CREATE TABLE IF NOT EXISTS education (id integer primary key, chatid integer, semester text, discipline text, question1 text, question2 text, question3 text, question4 text, question5 text, FOREIGN KEY(chatid) REFERENCES student(chatid))')
    cur.execute('CREATE TABLE IF NOT EXISTS practice (id integer primary key, chatid integer, semester text, question1 text, question2 text, question3 text, question4 text, question5 text, FOREIGN KEY(chatid) REFERENCES student(chatid))')
    cur.execute('INSERT OR IGNORE INTO student (chatid, username) VALUES (%d, "%s")' % (message.chat.id, message.chat.username))
    connect.commit()
    check_user = cur.execute('SELECT fio, specialization, ciphergroup FROM student WHERE chatid= %d' % message.chat.id).fetchone()
    cur.close()
    connect.close()
    
    if check_user[0] is None and check_user[1] is None and check_user[2] is None:
        btn = types.InlineKeyboardButton('Зарегистрироваться', callback_data='registration')
        first_message = f'Привет! \n\nТы здесь впервые, для того чтобы начать нужно пройти регистрацию.'
    # elif None in check_user:
    #     btn = types.InlineKeyboardButton('Продолжить регистрацию', callback_data='registration1')
    #     first_message = f'Ты не прошёл регистрацию до конца, для того чтобы продолжить нужно закончить регистрацию.'
    else:
        btn = types.InlineKeyboardButton('Пройти опрос', callback_data='complete_the_survey')
        first_message = f'Ты уже зарегестрирован и  можешь пройти опрос о качестве предоставляемого обучения на корпоративной магистратуре.'
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(btn)
    bot.send_message(message.chat.id, first_message, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda callback: True)
def survey(callback):
    if callback.data == 'complete_the_survey':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        semester_choice(callback)
    elif callback.data == 'registration':
        registration(callback)
    elif callback.data == '09.04.04_04':
        connect = sqlite3.connect('feedback.sql')
        cur = connect.cursor()
        cur.execute('UPDATE student SET specialization = "%s" WHERE chatid = %d ' % (callback.data, callback.message.chat.id))
        connect.commit()
        cur.close()
        connect.close()
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        keyboard = group_code_buttons(callback.data)
        bot.send_message(callback.message.chat.id, 'Ты выбрал направление "ИТ – инфраструктура предприятия".\nТеперь выбери свою группу:', reply_markup=keyboard)
    elif callback.data == '01.04.03_04' or callback.data == '01.04.03_06' or callback.data == '10.04.01_04' or callback.data == '38.04.01_30':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        # временно, пока не внесены данные о других направлениях
        keyboard = specializations_buttons()
        bot.send_message(callback.message.chat.id, 'Опрос для этого направления находится в разработке.\nСейчас доступно направление ИТ-инфраструктура предприятия', reply_markup=keyboard)
    elif callback.data == '1_course':
        connect = sqlite3.connect('feedback.sql')
        cur = connect.cursor()
        specialization = cur.execute('SELECT specialization FROM student WHERE chatid = %d' % callback.message.chat.id).fetchone()
        cur.execute('UPDATE student SET ciphergroup = "%s" WHERE chatid = %d ' % (GROUPS[specialization[0]][callback.data], callback.message.chat.id))
        connect.commit()
        cur.close()
        connect.close()
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        semester_choice(callback)
    elif callback.data == '2_course':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        # временно, пока не внесены данные о других группах
        keyboard = group_code_buttons('09.04.04_04') 
        bot.send_message(callback.message.chat.id, 'Опрос для этой группы находится в разработке.\nСейчас доступен опрос для группы 5140904/40401', reply_markup=keyboard)
    elif callback.data == '1_semester':
        bot.delete_message(callback.message.chat.id, callback.message.message_id) 
        discplines_choice(callback) 
    # elif callback.data == '2_semester' or callback.data == '3_semester' or callback.data == '4_semester':
    #     bot.delete_message(callback.message.chat.id, callback.message.message_id)
    #     keyboard = semester_choice('1_course') 
    #     bot.send_message(callback.message.chat.id, 'Опрос для этого семестра находится в разработке.\nСейчас доступен опрос для 1-го семетра', reply_markup=keyboard)
        
        
def register_fio(callback):
    connect = sqlite3.connect('feedback.sql')
    cur = connect.cursor()
    cur.execute('UPDATE student SET fio = "%s" WHERE chatid = %d ' % (callback.text, callback.chat.id))
    connect.commit()
    cur.close()
    connect.close()
    specialization_choice(callback)
    


def registration(callback):
    bot.edit_message_text('Отправь мне своё ФИО', callback.message.chat.id, callback.message.message_id)
    bot.register_next_step_handler(callback.message, register_fio)

  
        
def specialization_choice(callback):
    keyboard = specializations_buttons()
    bot.send_message(callback.chat.id, "Выберите ваше направление:", reply_markup=keyboard)       
    

def semester_choice(callback):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for key in DISCIPLINES.keys():
        callback_message = str(key) + '_semester'
        keyboard.add(types.InlineKeyboardButton(key, callback_data=callback_message))
    bot.send_message(callback.message.chat.id, 'О каком семестре ты хочешь оставить отзыв?', reply_markup=keyboard)
    
               
def discplines_choice(callback):
    callback_to_str = str(callback.data)
    semester = callback_to_str[:callback_to_str.find('_')]
    semester_to_int = int(semester)
    keyboard = discplines_button(semester_to_int)
    bot.send_message(callback.message.chat.id, f'Ты выбрал {semester} семестр.\n\nВыбери дисциплину на которую хочешь оставить отзыв.', reply_markup=keyboard)


def specializations_buttons():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for key, value in SPECIALIZATIONS.items():
        callback_message = key
        keyboard.add(types.InlineKeyboardButton(value, callback_data = callback_message))
    return keyboard
    
    
def group_code_buttons(group_code):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for key, value in GROUPS[group_code].items():
        callback_message = key
        keyboard.add(types.InlineKeyboardButton(value, callback_data = callback_message))
    return keyboard


def discplines_button(semester):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for discipline in DISCIPLINES[semester]:
        keyboard.add(types.InlineKeyboardButton(discipline, callback_data = discipline))
    return keyboard

bot.infinity_polling(timeout=10, long_polling_timeout = 5)