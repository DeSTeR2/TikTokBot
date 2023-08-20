import pickle
import random

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import os.path
from datetime import datetime

BOT_TOKEN = ""
bot = telebot.TeleBot(BOT_TOKEN)

user_dict = {}
registered_users = {}
registered_chat_id = []
SENDER = {}
GLOB_LINK = {}

link_to_add = ''

class User:
    def __init__(self, name):
        self.name = name
        self.friends = []
        self.friends_chat_id = []
        self.chat_id = None
        self.videos = dict(str=[])

    def add_new_friend(self, friend, chat_id):
        self.friends.append(friend)
        self.friends_chat_id.append(chat_id)

    def add_new_video(self, link, who):
        if who in self.videos:
            for i in range(len(self.videos[who])):
                if self.videos[who][i] == link:
                    return -1
        else:
            self.videos[who] = []
        self.videos[who].append(link)

    def print_friend(self):
        for i in range(len(self.friends)):
            print(self.friends[i])

@bot.message_handler(commands=['start'])
def send_welcome(message):
    msg = bot.reply_to(message, """\
Привіт для я тобі допоможу не втрачати відео з тік току від твоїх друзів. Тобі треба лише відправити мене своїм друзям та додати їх до списку "друзі" за допомогою команди /add_person 
""")
    process_name_step(message)


def process_name_step(message):
    chat_id = message.chat.id
    name = '@' + message.from_user.username
    if name[0] != '@':
        msg = bot.reply_to(message, 'Ваш тег повинен починатись на @, повторіть спробу')
        bot.register_next_step_handler(msg, process_name_step)
    else:
        if chat_id not in registered_chat_id:
            registered_users[name] = chat_id
            registered_chat_id.append(chat_id)
            user = User(name)
            user.chat_id = chat_id
            user_dict[chat_id] = user
            msg = bot.reply_to(message, 'Яким людям ти хочеш відправляти відео? \nВідправь тег людини (приклад: @men)')
            save()
            bot.register_next_step_handler(msg, process_friends_step)
        else:
            bot.reply_to(message, 'Ви вже зареєстровані')


@bot.message_handler(commands=['add_person'])
def add_friend_with_command(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, 'Яким людям ти хочеш відправляти відео? \nВідправь тег людини (приклад: @men)')
    bot.register_next_step_handler(msg, process_friends_step)


def process_friends_step(message):
    chat_id = message.chat.id
    friend = message.text
    if friend == '0':
        bot.reply_to(message, 'Всі люди додані!')
        return 0

    if friend[0] != '@':
        msg = bot.send_message(chat_id, 'Тег людини повинен починатись на @, повторіть спробу')
        bot.register_next_step_handler(msg, process_friends_step)
        return 0

    if friend not in registered_users.keys():
        msg = bot.reply_to(message, 'Ця людина не зареєстровона в боті.\nДодайте іншу людину\n'
                                    'Якщо ви не хочете нікого додавати, то відправте 0')
        bot.register_next_step_handler(msg, process_friends_step)
        return 0
    else:
        user = user_dict[chat_id]

        friend_chat_id = registered_users[friend]

        user.add_new_friend(friend, friend_chat_id)
        user_dict[chat_id] = user
        save()
        msg = bot.send_message(chat_id, 'Додано!\n\nЯкщо ви хочете додати ще одну людину, то відправте новий тег. \n'
                                        'Якщо ні, то відправте 0')
        bot.register_next_step_handler(msg, process_friends_step)
        return 0


@bot.message_handler(commands=['delete_person'])
def delete_friend(message):
    chat_id = message.chat.id
    msg = 'Кого ви хочете видалити?\nВаші друзі:\n'

    user = user_dict[chat_id]
    buttons = []
    delete_button = ReplyKeyboardMarkup()

    for i in range(len(user.friends)):
        buttons.append(KeyboardButton(user.friends[i]))
        delete_button.add(buttons[i])
        msg = msg + user.friends[i] + '\n'

    save()
    msg = bot.send_message(chat_id, msg, reply_markup=delete_button)
    bot.register_next_step_handler(msg, delete_friend_from_class)


def delete_friend_from_class(message):
    chat_id = message.chat.id
    text = message.text
    if text[0] != '@':
        bot.reply_to(message, 'Ви відправили тег не у вірному форматі.\nВиберіть тег, клацнувши на кнопку.')
        delete_friend(message)
        return 0

    user = user_dict[chat_id]

    if text not in user.friends:
        bot.reply_to(message, 'Ця людина не є вашим другом')
        return 0

    user.friends.remove(text)
    user.friends_chat_id.remove(registered_users[text])

    msg = 'Успішно видалено із друзів\nВаші друзі:\n'
    for i in range(len(user.friends)):
        msg = msg + user.friends[i] + '\n'
    save()
    bot.send_message(chat_id, msg)


@bot.message_handler(commands=['answer'])
def answer_the_tt(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]
    videos = user.videos
    keys = list(videos.keys())
    msg = 'Всі відправники та їх відео:\n'

    buttons = []
    answer_buttons = ReplyKeyboardMarkup()

    for i in range(len(keys)):
        if i > 0:
            buttons.append(KeyboardButton(keys[i]))
            answer_buttons.add(buttons[i-1])
            msg = msg + keys[i] + '\n'
            for j in range(len(videos[keys[i]])):
                msg = msg + str(j+1) + '. ' + videos[keys[i]][j] + '\n'

    bot.send_message(chat_id, msg)
    save()
    msg = bot.send_message(chat_id, 'Оберіть відправника', reply_markup=answer_buttons)
    bot.register_next_step_handler(msg, answer_the_tt_bufer)




def answer_the_tt_bufer(message):
    answer_the_tt_in_class(message, 1)

def answer_the_tt_in_class(message, flag):
    chat_id = message.chat.id
    user = user_dict[chat_id]
    videos = user.videos
    keys = list(videos.keys())
    text = message.text


    SENDER[chat_id] = text

    if flag == 1:
        if text == '0':
            return 0

        flag = True

        for i in range(len(keys)):
            if keys[i] == text:
                flag = False

        if flag:
            bot.reply_to(message, 'Ви обрали тег людини, який не відправляв вам відео.\nСпробуйте ще раз')
            answer_the_tt(message)
            return 0

        if text[0] != '@':
            bot.reply_to(message, 'Ви відправили інфомацію не у вірному форматі.\nСпробуйте ще раз')
            answer_the_tt(message)
            return 0

        bot.send_message(chat_id, 'Ви обрали відправника ' + text + '\nВ наступних повідомленнях буде поданно всі '
                                                                    'відео, які він вам відправляв.\n'
                                                                    'Після кожного відео, я буду '
                                                                    'чекати відповіді, в текстовому форматі, на відео')

    sz = len(videos[text])

    if sz > 0:
        msg = bot.send_message(chat_id, videos[text][0])
        GLOB_LINK[chat_id] = videos[text][0]
        SENDER[chat_id] = text
        bot.register_next_step_handler(msg, send_answer_to_sender)
    else:
        GLOB_LINK[chat_id] = ''
        SENDER[chat_id] = ''


def send_answer_to_sender(message):
    chat_id = message.chat.id
    sender = SENDER[chat_id]
    SENDER[chat_id] = ' '
    answer = message.text

    sender_chat_id = registered_users[sender]

    bot.send_message(sender_chat_id, 'Користувач ' + user_dict[message.chat.id].name + ' відповів вам на відео ' +
                     GLOB_LINK[chat_id] + '\n\nЙого відповідь:\n' + answer)

    user = user_dict[message.chat.id]

    user.videos[sender].remove(GLOB_LINK[chat_id])

    GLOB_LINK[chat_id] = ' '
    save()
    keys = list(user.videos.keys())
    if len(keys) > 0:
        message.text = sender
        answer_the_tt_in_class(message, 0)


def load():
    bot.send_message(735454251, 'Роботу розпочато о ' + datetime.now().strftime("%H:%M:%S"))
    global user_dict
    if os.path.getsize('user_dict.json') > 0:
        with open('user_dict.json', 'rb') as outp:
            user_dict = pickle.load(outp)

    global registered_users
    if os.path.getsize('registered_users.json') > 0:
        with open('registered_users.json', 'rb') as outp:
            registered_users = pickle.load(outp)

    global registered_chat_id
    if os.path.getsize('registered_char_id.json') > 0:
        with open('registered_char_id.json', 'rb') as outp:
            registered_chat_id = pickle.load(outp)


def save():
    del_the_file('user_dict.json')
    with open('user_dict.json', 'wb') as outp:
        pickle.dump(user_dict, outp)

    del_the_file('registered_users.json')
    with open('registered_users.json', 'wb') as outp:
        pickle.dump(registered_users, outp)

    del_the_file('registered_char_id.json')
    with open('registered_char_id.json', 'wb') as outp:
        pickle.dump(registered_chat_id, outp)


@bot.message_handler(commands=['i_want_attention'])
def want_attention(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, 'Виберіть користувача, увагу від якого ви хочете отримати')
    user = user_dict[chat_id]
    buttons = []
    attention_buttons = ReplyKeyboardMarkup()

    for i in range(len(user.friends)):
        buttons.append(KeyboardButton(user.friends[i]))
        attention_buttons.add(buttons[i])

    bot.register_next_step_handler(msg, send_attention_to_user)


def send_attention_to_user(message):
    chat_id = message.chat.id
    text = message.text
    user = user_dict[chat_id]
    if text[0] != '@':
        bot.reply_to(message, 'Ви відправили тег не у вірному форматі.\nВиберіть тег, клацнувши на кнопку.')
        delete_friend(message)
        return 0

    if text not in user.friends:
        bot.reply_to(message, 'Ця людина не є вашим другом')
        return 0

    reciver_chat_id = registered_users[text]
    bot.send_message(chat_id, 'Відправлено!')
    bot.send_message(reciver_chat_id, 'Користувач ' + '@' + message.from_user.username + ' хоче уваги від вас!!!')


@bot.message_handler(commands=['admin'])
def all_func(message):
    if message.chat.id == 735454251:
        bot.send_message(message.chat.id, 'Наявні функції адміністратора:\n/logs_all_users - '
                                          'інформація про всіх користувачів\n/send_love - відправити кохання Женеві)')


@bot.message_handler(commands=['logs_all_users'])
def logs(message):
    if message.chat.id == 735454251:
        msg = ''
        for i in range(len(registered_chat_id)):
            user = user_dict[registered_chat_id[i]]
            msg = msg + 'Username: ' + user.name + '\n'
            msg = msg + 'Chat id: ' + str(user.chat_id) + '\nFriends: '
            for j in range(len(user.friends)):
                msg = msg + str(user.friends[j]) + ', '
            msg = msg + '\nFriends chat ids: '
            for j in range(len(user.friends_chat_id)):
                msg = msg + str(user.friends_chat_id[j]) + ' '
            msg = msg + '\n'
            msg = msg + 'Videos from friends:\n'
            for j in range(len(user.friends)):
                msg = msg + '  From: ' + user.friends[j] + ' - '
                if user.friends[j] in user.videos:
                    for k in range(len(user.videos[user.friends[j]])):
                        msg = msg + user.videos[user.friends[j]][k] + ' '
            msg = msg + '\n\n'
        bot.send_message(735454251, msg)
    else:
        bot.reply_to(message, 'Ви знайшли пасхалку! Вітаю!')


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id,
                     '/start - початок роботи, регестрація\n/add_person - додати людину до списку "друзі", '
                     'які можна буде відправляти відео чи бажання уавги\n/delete_person '
                     '- видалити людину із списку "друзі"\n/answer - відповісти на відео вашого друга. Вам відправляється список всіх ваших друзів, а під ними всі відео, які вони відправляли. Обираєте людину, дивитесь відео та даєте відповідь на відео.\n'
                     '/i_want_attention - Обрати людину, від якої хочеш отримати увагу')
    if (message.chat.id == 735454251):
        all_func(message)
        bot.send_message(message.chat.id, '/kuni - сказати Женеві, що хочеш куні зробити їй\n/horny - скажзати Женеві, що ти хорні')
    if (message.chat.id == 743996927):
        bot.send_message(message.chat.id, '/horny - сказати Захару, що ти хорні')


@bot.message_handler(content_types=['text'])
def add_link_to_watch(message):
    link = message.text
    chat_id = message.chat.id
    global link_to_add
    link_to_add = link
    if chat_id not in registered_chat_id:
        bot.reply_to(message, 'Ви не зареєстровані, щоб зареєструватись введіть команду /start')
        return 0

    def_link = 'https://vm.tiktok.com/'

    for i in range(len(def_link)):
        if def_link[i] != link[i]:
            bot.reply_to(message, 'Якщо ви хотіли відправити посилання на відео, '
                                  'то воно має бути у форматі https://vm.tiktok.com/...')
            return 0

    msg = 'Кому ви хочете відправити відео?\nВаші друзі:\n'

    user = user_dict[chat_id]

    buttons = []
    tt_send_to = ReplyKeyboardMarkup()

    for i in range(len(user.friends)):
        buttons.append(KeyboardButton(user.friends[i]))
        tt_send_to.add(buttons[i])
        msg = msg + user.friends[i] + '\n'

    msg = bot.send_message(chat_id, msg, reply_markup=tt_send_to)
    save()
    bot.register_next_step_handler(msg, add_link_to_class)


def add_link_to_class(message):
    chat_id = message.chat.id
    text = message.text
    if text[0] != '@':
        msg = bot.send_message(chat_id, 'Тег людини повинен починатись на @, повторіть спробу')
        bot.register_next_step_handler(msg, add_link_to_class)
        return 0

    user = user_dict[chat_id]

    if text not in user.friends:
        bot.reply_to(message, 'Ця людина не є вашим другом')
        return 0

    global link_to_add
    link = link_to_add

    reciver_chat_id = registered_users[text]
    user = user_dict[reciver_chat_id]

    user.add_new_video(link, user_dict[chat_id].name)
    link_to_add = ''
    save()
    bot.send_message(reciver_chat_id, "Користувач на ім'я " + user_dict[chat_id].name + " відправив відео: " + link)



def del_the_file(name):
    open(name, "w").close()


load()
bot.infinity_polling()
