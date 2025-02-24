import telebot
import sqlite3
import whisper
import requests
import os
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
DISCIPLINES = {"1" : ['Ин.яз. в проф. коммуникации', 'Цифровые ресурсы в НИ', 'Управление проектами', 'Верификация алгоритмов и систем', 'Построение ИТ инфраструктуры', 'ИТ инфраструктура предприятия', 'Внедрение и сопровождение ПП', 'Ознакомительная практика'],
               "2" : [], 
               "3" : [], 
               "4" : []
}
QUESTIONS_EDUCATION = {
    "question1" : {"Оцените сложность курса" : 
        {"answer1" : "1", 
         "answer2" : "2", 
         "answer3" : "3", 
         "answer4" : "4", 
         "answer5" : "5"}},
    "question2" : {"Оцените полезность и применимость данного курса для вашей дальнейшей деятельности" : {"answer1" : "1", "answer2" : "2", "answer3" : "3", "answer4" : "4", "answer5" : "5"}},
    "question3" : {"Оцените качество преподавания данной дисциплины" : {"answer1" : "1", "answer2" : "2", "answer3" :  "3","answer4" :  "4","answer5" :  "5"}},
    "question4" : {"Оцените время проведения занятий по данной дисциплине" : {"answer1" : "Cлишком поздно", "answer2" : "Меня устраивает", "answer3" : "Cлишком рано"}},
    "question5" : {"Оцените местоположение проведения занятий" : {"answer1" : "Устраивает", "answer2" : "Не устраивает", "answer3" : "Не имеет значения"}}
}
QUESTIONS_PRACTICE = {
    "question1" : {"Оцените поддержку куратора вашего направления магистратуры со стороны университета" : {"ans1" : "1", "ans2" : "2", "ans3" : "3", "ans4" : "4", "ans5" : "5"}},
    "question2" : {"Оцените поддержку куратора вашего направления магистратуры со стороны компании" : {"ans1" : "1", "ans2" : "2", "ans3" : "3", "ans4" : "4", "ans5" : "5"}},
    "question3" : {"Оцените заинтересованность наставника от компании" : {"ans1" : "1", "ans2" : "2", "ans3" : "3", "ans4" : "4", "ans5" : "5"}},
    "question4" : {"Совпадают ли ваши ожидания о практике с действительностью" : {"ans1" : "Ожидал большего", "ans2" : "Совпадают", "ans3" : "Превосходит ожидания"}},
    "question5" : {"Какое количество часов вы тратите на практику в неделю" : {"ans1" : "Меньше 5", "ans2" : "От 5 до 10", "ans3" : "От 10 до 15", "ans4" : "От 15 до 20", "ans5" : "Больше 20"}},
    
}

def read_file(file_name):
    with open(file_name, 'r') as file:
        return file.read()

bot = telebot.TeleBot(read_file('token.ini'))

@bot.message_handler(commands=['start'])
def main(message):
    connect = sqlite3.connect('feedback.sql')
    cur = connect.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS student (chatid integer primary key, username varchar(50), fio varchar(80), specialization varchar(50), ciphergroup varchar(50))')
    cur.execute('CREATE TABLE IF NOT EXISTS education (id integer primary key, chatid integer, semester text, discipline text, question1 text, question2 text, question3 text, question4 text, question5 text, summary text, FOREIGN KEY(chatid) REFERENCES student(chatid))')
    cur.execute('CREATE TABLE IF NOT EXISTS practice (id integer primary key, chatid integer, semester text, question1 text, question2 text, question3 text, question4 text, question5 text, summary text, FOREIGN KEY(chatid) REFERENCES student(chatid))')
    cur.execute('INSERT OR IGNORE INTO student (chatid, username) VALUES (%d, "%s")' % (message.chat.id, message.chat.username))
       
    connect.commit()
    check_user = cur.execute('SELECT fio, specialization, ciphergroup FROM student WHERE chatid= %d' % message.chat.id).fetchone()
    cur.close()
    connect.close()
    
    if check_user[0] is None and check_user[1] is None and check_user[2] is None:
        btn = types.InlineKeyboardButton('Зарегистрироваться', callback_data='registration')
        first_message = f'👋🏻 Привет! \n\nТы здесь впервые, для того чтобы начать нужно пройти регистрацию.'
    else:
        btn = types.InlineKeyboardButton('Пройти опрос', callback_data='complete_the_survey')
        first_message = f'Ты уже зарегестрирован и можешь пройти опрос о качестве предоставляемого обучения на корпоративной магистратуре.'
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
        semester = callback.data[:callback.data.find('_')]
        connect = sqlite3.connect('feedback.sql')
        cur = connect.cursor()
        check = cur.execute('SELECT id FROM education WHERE chatid = %d AND semester = "%s" AND discipline IS NULL' % (callback.message.chat.id, semester)).fetchone()
        check_practice = cur.execute('SELECT id FROM practice WHERE chatid = %d AND semester = "%s"' % (callback.message.chat.id, semester)).fetchone()
        print(semester)
        print(check)
        
        print('-------------------------------------')
        
        print(check_practice)
        if check ==  None:
            cur.execute('INSERT OR IGNORE INTO education (id, chatid, semester) VALUES (NULL, %d, %s)' % (callback.message.chat.id, semester))
        if check_practice == None:
            cur.execute('INSERT OR IGNORE INTO practice (chatid, semester) VALUES (%d, "%s")' % (callback.message.chat.id, semester))
        connect.commit()
        cur.close()
        connect.close()
        bot.delete_message(callback.message.chat.id, callback.message.message_id) 
        discplines_choice(callback, semester) 
    elif callback.data == '2_semester' or callback.data == '3_semester' or callback.data == '4_semester':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for key in DISCIPLINES.keys():
            callback_message = key + '_semester'
            keyboard.add(types.InlineKeyboardButton(key, callback_data=callback_message))
        bot.send_message(callback.message.chat.id, 'Опрос для этого семестра находится в разработке.\nСейчас доступен опрос для 1-го семетра', reply_markup=keyboard)
    elif [key for key, val in DISCIPLINES.items() if callback.data in val]: 
        bot.edit_message_text(f'Ты выбрал предмет <b>{callback.data}</b>', callback.message.chat.id, callback.message.message_id, parse_mode="html")
        print(callback.data)
        if callback.data != 'Ознакомительная практика':
            connect = sqlite3.connect('feedback.sql')
            cur = connect.cursor()
            semester = cur.execute('SELECT semester FROM education WHERE chatid = %d AND discipline IS NULL' % (callback.message.chat.id)).fetchone()
            check = cur.execute('SELECT * FROM education WHERE chatid = %d AND semester = "%s" AND discipline = "%s"' % (callback.message.chat.id, semester[0], callback.data))
            if len(check.fetchall()) == 0:
                cur.execute('UPDATE education SET discipline = "%s" WHERE chatid = %d AND semester = "%s" AND discipline IS NULL' % (callback.data, callback.message.chat.id, semester[0]))
            connect.commit()
            cur.close()
            connect.close()
            global discipline 
            discipline = callback.data
            education_survey(callback, discipline)
        else:
            connect = sqlite3.connect('feedback.sql')
            cur = connect.cursor()
            semester = cur.execute('SELECT semester FROM practice WHERE chatid = %d' % (callback.message.chat.id)).fetchone()
            cur.close()
            connect.close()
            practice_survey(callback, semester[0])
    elif callback.data == 'answer1' or callback.data == 'answer2' or callback.data == 'answer3' or callback.data == 'answer4' or callback.data == 'answer5':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        for key, values in QUESTIONS_EDUCATION.items():
            if list(QUESTIONS_EDUCATION[key].keys())[0] == callback.message.text:
                question_n = key 
                break
        answer = QUESTIONS_EDUCATION[question_n][callback.message.text][callback.data]
        connect = sqlite3.connect('feedback.sql')
        cur = connect.cursor()
        cur.execute('UPDATE education SET "%s" = "%s" WHERE chatid = %d and "%s" IS NULL and discipline = "%s"' % (question_n, answer, callback.message.chat.id, question_n, discipline))
        connect.commit()
        cur.close()
        connect.close()
        education_survey(callback, discipline)
    elif callback.data == 'ans1' or callback.data == 'ans2' or callback.data == 'ans3' or callback.data == 'ans4' or callback.data == 'ans5':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        for key, values in QUESTIONS_PRACTICE.items():
            if list(QUESTIONS_PRACTICE[key].keys())[0] == callback.message.text:
                question_n = key 
                break
        answer = QUESTIONS_PRACTICE[question_n][callback.message.text][callback.data]
        semester = semester_info(callback.message.chat.id)
        connect = sqlite3.connect('feedback.sql')
        cur = connect.cursor()
        cur.execute('UPDATE practice SET "%s" = "%s" WHERE chatid = %d and "%s" IS NULL and semester = "%s"' % (question_n, answer, callback.message.chat.id, question_n, semester))
        connect.commit()
        cur.close()
        connect.close()
        practice_survey(callback, semester)
        
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
        callback_message = key + '_semester'
        keyboard.add(types.InlineKeyboardButton(key, callback_data=callback_message))
    bot.send_message(callback.message.chat.id, 'О каком семестре ты хочешь оставить отзыв?', reply_markup=keyboard)
    
               
def discplines_choice(callback, semester):
    keyboard = discplines_button(semester)
    bot.send_message(callback.message.chat.id, f'Ты выбрал <b>{semester}</b> семестр.\n\nВыбери дисциплину на которую хочешь оставить отзыв.', parse_mode="html", reply_markup=keyboard)


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
        

def education_survey(callback, discipline):
    connect = sqlite3.connect('feedback.sql')
    cur = connect.cursor()
    question_list = cur.execute('SELECT question1, question2, question3, question4, question5 FROM education WHERE discipline = "%s" AND chatid = %d' % (discipline, callback.message.chat.id)).fetchone()
    summary = cur.execute('SELECT summary FROM education WHERE discipline = "%s" AND chatid = %d' % (discipline, callback.message.chat.id)).fetchone()
    cur.close()
    connect.close()
    if None in question_list:
        for el in question_list:
            if el == None:
                question = "question" + str(question_list.index(el)+1)
                break
        questions = QUESTIONS_EDUCATION[question].keys()
        que = list(questions)[0]
        answers = QUESTIONS_EDUCATION[question][que]
        keyboard = answer_buttons(answers)
        bot.send_message(callback.message.chat.id, que, reply_markup=keyboard)
    elif None in summary:
        bot.send_message(callback.message.chat.id, f"Оставь развёрнутый отзыв о дисциплине - <b>{discipline}</b>.\nРасскажи о своих ожиданиях, что тебе понравилось и не понравилось.\nМожешь написать текстом 📄 \nили записать голосовое сообщение 🎤", parse_mode="html")
        bot.register_next_step_handler(callback.message, education_summary_register)
    else:   
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(types.InlineKeyboardButton("Вернуться к другим дисциплинам", callback_data = "1_course"))
        bot.send_message(callback.message.chat.id, f"✅ Ты прошёл опрос по дисциплине - <b>{discipline}</b>", parse_mode="html", reply_markup=keyboard)
        
    
def practice_survey(callback, semester):
    connect = sqlite3.connect('feedback.sql')
    cur = connect.cursor()
    question_list = cur.execute('SELECT question1, question2, question3, question4, question5 FROM practice WHERE chatid = %d AND semester = "%s"' % (callback.message.chat.id, semester)).fetchone()
    summary = cur.execute('SELECT summary FROM practice WHERE semester = "%s" AND chatid = %d' % (semester, callback.message.chat.id)).fetchone()
    cur.close()
    connect.close()
    print(question_list)
    if None in question_list:
        for el in question_list:
            if el == None:
                question = "question" + str(question_list.index(el)+1)
                break
        questions = QUESTIONS_PRACTICE[question].keys()
        que = list(questions)[0]
        answers = QUESTIONS_PRACTICE[question][que]
        keyboard = answer_buttons(answers)
        bot.send_message(callback.message.chat.id, que, reply_markup=keyboard)
    elif None in summary:
        bot.send_message(callback.message.chat.id, f"Оставь развёрнутый отзыв о <b>практике</b>.\nРасскажи о своих ожиданиях, что тебе понравилось и не понравилось.\nМожешь написать текстом 📄 \nили записать голосовое сообщение 🎤", parse_mode="html")
        bot.register_next_step_handler(callback.message, practice_summary_register)
    else:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(types.InlineKeyboardButton("Вернуться к другим дисциплинам", callback_data = "1_course"))
        bot.send_message(callback.message.chat.id, f"✅ Ты прошёл опрос о <b>практике</b>", parse_mode="html", reply_markup=keyboard)
    
    
def answer_buttons(answers):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for key, value in answers.items():
        keyboard.add(types.InlineKeyboardButton(value, callback_data = key))
    return keyboard


def mp3_to_text_with_punctuation(mp3_file):
    model = whisper.load_model("./whisper/medium.pt") 
    result = model.transcribe(mp3_file, language="ru")
    return result["text"]


def education_summary_register(message):
    if message.content_type == "voice":
        SAVE_DIR = "voice_msg" 
        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)
        file_info = bot.get_file(message.voice.file_id) 
        file_url = f"https://api.telegram.org/file/bot{read_file('token.ini')}/{file_info.file_path}"
        
        file_path_voice = f"voice_msg/voice_{message.message_id}.ogg"
        file_path = os.path.join(SAVE_DIR, f"voice_{message.message_id}.ogg")
        
        response = requests.get(file_url)
        
        with open(file_path, "wb") as f:
            f.write(response.content)
        
        text_result = mp3_to_text_with_punctuation(file_path_voice)
        os.remove(file_path)
        connect = sqlite3.connect('feedback.sql')
        cur = connect.cursor()
        cur.execute('UPDATE education SET summary = "%s" WHERE chatid = %d and summary IS NULL and discipline = "%s"' % (text_result, message.chat.id, discipline))
        connect.commit()
        cur.close()
        connect.close()
    elif message.content_type == "text":
        connect = sqlite3.connect('feedback.sql')
        cur = connect.cursor()
        cur.execute('UPDATE education SET summary = "%s" WHERE chatid = %d and summary IS NULL and discipline = "%s"' % (message.text, message.chat.id, discipline))
        connect.commit()
        cur.close()
        connect.close()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("Вернуться к другим дисциплинам", callback_data = "1_course"))
    bot.send_message(message.chat.id, f"✅ Ты прошёл опрос по дисциплине - <b>{discipline}</b>", parse_mode="html", reply_markup=keyboard)


def practice_summary_register(message):
    semester = semester_info(message.chat.id)
    if message.content_type == "voice":
        SAVE_DIR = "voice_msg" 
        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)
        file_info = bot.get_file(message.voice.file_id) 
        file_url = f"https://api.telegram.org/file/bot{read_file('token.ini')}/{file_info.file_path}"
        
        file_path_voice = f"voice_msg/voice_{message.message_id}.ogg"
        file_path = os.path.join(SAVE_DIR, f"voice_{message.message_id}.ogg")
        
        response = requests.get(file_url)
        
        with open(file_path, "wb") as f:
            f.write(response.content)
        
        text_result = mp3_to_text_with_punctuation(file_path_voice)
        os.remove(file_path)
        connect = sqlite3.connect('feedback.sql')
        cur = connect.cursor()
        cur.execute('UPDATE practice SET summary = "%s" WHERE chatid = %d and summary IS NULL and semester = "%s"' % (text_result, message.chat.id, semester))
        connect.commit()
        cur.close()
        connect.close()
    elif message.content_type == "text":
        connect = sqlite3.connect('feedback.sql')
        cur = connect.cursor()
        cur.execute('UPDATE practice SET summary = "%s" WHERE chatid = %d and summary IS NULL and semester = "%s"' % (message.text, message.chat.id, semester))
        connect.commit()
        cur.close()
        connect.close()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("Вернуться к другим дисциплинам", callback_data = "1_course"))
    bot.send_message(message.chat.id, f"✅ Ты прошёл опрос о <b>практике</b>", parse_mode="html", reply_markup=keyboard)

def semester_info(chat_id):
    connect = sqlite3.connect('feedback.sql')
    cur = connect.cursor()
    semester = cur.execute('SELECT semester FROM practice WHERE chatid = %d AND semester NOT NULL' % (chat_id)).fetchone()
    cur.close()
    connect.close()
    return semester[0]
    

bot.infinity_polling(timeout=10, long_polling_timeout = 5)