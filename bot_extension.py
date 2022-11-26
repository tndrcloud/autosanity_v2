from telegram.ext import *
from telegram import *
import json, time, os
from settings import Directory_triggersFile, User
import threading #Нужен для lock
import configurator


AUTHORIZED_USERS = ["tndrcloud", "y_evsyukov", "DSOTT", "Stl36", "OTT_2"]

autosanityThreads = {'14':None, '15':None, '16':None, '17':None, '18':None, '19':None, '20':None, '21':None}


class SanityThread(threading.Thread):
    def __init__(self, MRF):
        threading.Thread.__init__(self)
        self.MRF = MRF
        self.event = threading.Event()

    def run(self):
        sanityStart(self.event, self.MRF)
        #autosanityThreads[self.MRF] = None


def sanityStart(event, MRF):
    import autosanity
    sanity = autosanity.Autosanity()
    sanity.start_sanity(event, MRF)


def authorized(func_to_decorate):
    def new_func(*original_args, **original_kwargs):
        update = original_args[0]
        if update.effective_user.username in AUTHORIZED_USERS:
            return func_to_decorate(*original_args, **original_kwargs)
        else:
            return send_unauthorized_message(*original_args, **original_kwargs)
    return new_func


def cancel(update, context):
    pass


def spam_performer(update, context, message_id=None, timeKill=120):
    def MesKill(update, context, message_id=None):
        time.sleep(timeKill)
        chat_id = update.effective_chat.id
        if  message_id == None:
            message_id = update.message.message_id
        context.bot.delete_message(chat_id=chat_id, message_id=message_id)

    kill = threading.Thread(target=MesKill, args=(update, context, message_id), daemon=True)
    kill.start()


def sendMesAndKill(update, context, text, timeKill=7):
    answerMes = context.bot.send_message(chat_id=update.effective_chat.id,
                                         text=text)

    def MesKill(update, context, message_id, timeKill):
        time.sleep(timeKill)
        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)

    sendAndKill = threading.Thread(target=MesKill, args=(update, context, answerMes['message_id'], timeKill), daemon=True)
    sendAndKill.start()


def send_unauthorized_message(update, context):
    sendMesAndKill(update, context, text='Вы не авторизованы!')


@authorized
def start(update, context):
    if not os.path.isdir(Directory_triggersFile):
        import shutil
        os.mkdir(Directory_triggersFile)
        shutil.chown(Directory_triggersFile, user=User, group=User)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Привет! Я бот autosanity!" \
                                  "\nОписание пока не придумано..!..",
                             reply_markup=ReplyKeyboardRemove())


@authorized
def general_callbackHandler(update, context):
    querryData = update.callback_query.data

    if querryData == 'None':
        context.bot.answer_callback_query(update.callback_query.id, text="Эта кнопка ничего не делает ;)")
    elif querryData == 'calling':
        context.bot.answer_callback_query(update.callback_query.id, text="Я звоню, подожди :)")

    elif querryData[0] == '[' and querryData[-1] == ']':
        customTrigger_performer(update, context)

    elif querryData[0] == '{' and querryData[-1] == '}':
        menu_callbackHandler(update, context)
        context.bot.answer_callback_query(update.callback_query.id, text="")

    elif querryData == 'offNumberEnterBack':
        offNumberMenu_sendKeyboard(update, context)
        context.bot.answer_callback_query(update.callback_query.id, text="")


@authorized
def menuStart(update, context):
    context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
    menu_sendKeyboard(update, context, newKeyboard=True)


mesMenuId = range(0)
@authorized
def menu_callbackHandler(update, context):
    querryData = update.callback_query.data
    querryData = eval(querryData)
    typeMenu = list(querryData)[0]
    global mesMenuId
    mesMenuId = update.callback_query.message.message_id
    # Обработка меню: Главное меню
    if typeMenu == 'menu':
        if querryData['menu'] == 'autosanity': autosanity_sendKeyboard(update, context)
        elif querryData['menu'] == 'close': update.callback_query.message.delete()
        elif querryData['menu'] == 'onNumber': onNumberMenu_sendKeyboard(update, context)
        elif querryData['menu'] == 'offNumber': offNumberMenu_sendKeyboard(update, context)
        elif querryData['menu'] == 'setConfig': setConfig_sendKeyboard(update, context)
        # Возврат в главное меню
        elif querryData['menu'] == 'generalMenu': menu_sendKeyboard(update, context)

    elif typeMenu == 'autosanity': autosanityKeyboard_performer(update, context)

    # Обработка меню: Включить номер
    elif typeMenu == 'onNumberMenu':
        MRF = querryData[typeMenu]
        if MRF == 'all': OnNumberMenuByNumbers_sendKeyboard(update, context, MRF)
        else: OnNumberMenuByNumbers_sendKeyboard(update, context, MRF)
    # Обработка меню: Включить номер/выбранный МРФ или показ всех номеров
    elif typeMenu == 'onNumber': changeNumber_performer(update, context)

    elif typeMenu == 'offNumberMenu':
        if querryData['offNumberMenu'] == 'offNumberTriggers': offNumberTriggersMenu_sendKeyboard(update, context)
    elif typeMenu == 'offNumberTriggers': offNumberMenuByTriggers_sendKeyboard(update, context, querryData['offNumberTriggers'])
    elif typeMenu == 'offNumberByTrigger': changeNumber_performer(update, context)

    elif typeMenu == 'setConfig':
        if querryData['setConfig'] == 'getFile':
            setConfigSendCallsFile_performer(update, context)
        if querryData['setConfig'] == 'restart_asterisk':
            setConfig_restart_asterisk(update, context)


@authorized
def menu_sendKeyboard(update, context, newKeyboard=False):
    buttons = [
            [InlineKeyboardButton('🚀 Sanity по регионам', callback_data=json.dumps({'menu': 'autosanity'}))],

                [
                 InlineKeyboardButton('✅ Включить номер', callback_data=json.dumps({'menu': 'onNumber'})),
                InlineKeyboardButton('❌ Выключить номер', callback_data=json.dumps({'menu': 'offNumber'}))
                ],

            [InlineKeyboardButton('⚙️ Изменить настройки', callback_data=json.dumps({'menu': 'setConfig'})),
             InlineKeyboardButton('🔚 Закрыть меню', callback_data=json.dumps({'menu': 'close'}))
             ]
            ]

    keyboard = InlineKeyboardMarkup(buttons)
    if newKeyboard:
        global mesMenuId
        mesMenuId = context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Меню",
                                 reply_markup=keyboard)['message_id']
    else:
        update.callback_query.message.edit_text(text='Меню', reply_markup=keyboard)


@authorized
def setConfig_sendKeyboard(update, context, returnKeyboard=False):
    buttons = [
        [InlineKeyboardButton('📤 Получить текущий файл обзвона', callback_data=json.dumps({'setConfig': 'getFile'}))],
        [InlineKeyboardButton('📥 Загрузить новый файл обзвона', callback_data=json.dumps({'setConfig': 'putFile'}))],
        [InlineKeyboardButton('🔄 Перезапустить asterisk', callback_data=json.dumps({'setConfig': 'restart_asterisk'}))],

        [InlineKeyboardButton('Вернуться назад 🔙', callback_data=json.dumps({'menu': 'generalMenu'}))]
                ]

    keyboard = InlineKeyboardMarkup(buttons)
    if returnKeyboard: return keyboard
    else: update.callback_query.message.edit_text(text='Меню', reply_markup=keyboard)


@authorized
def setConfigSendCallsFile_performer(update, context):
    import tempfile

    tempFile = configurator.get_CallsFileRead()
    tempFile = tempFile.encode('cp1251')
    with tempfile.NamedTemporaryFile() as targetFile:
        targetFile.write(tempFile)
        targetFile.seek(0)

        answerMes = context.bot.send_document(chat_id=update.effective_chat.id, document=targetFile, filename='calls_data.csv')

    def goodMesKill(update, context, message_id):
        time.sleep(7)
        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)

    kill = threading.Thread(target=goodMesKill, args=(update, context, answerMes['message_id']), daemon=True)
    kill.start()


dialog_putfile = range(0)
def dialog_setConfigPutCallsFile_sendKeyboard(update, context):
    buttons = [
        [InlineKeyboardButton('Вернуться назад 🔙', callback_data=json.dumps({'menu': 'setConfig'}))]
                ]

    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.message.edit_text(text='Жду файл в формате csv', reply_markup=keyboard)

    return dialog_putfile


def dialog_setConfigPutCallsFile_performer(update, context):
    import shutil
    spam_performer(update, context, timeKill=2)
    context.bot.edit_message_text(text='Работаю...', message_id=mesMenuId, chat_id=update.effective_chat.id)

    example_header = ['Город','Домен', 'Номер в домене (Caller)', 'Номер на который звонит (Callee)', 'Участие в обзвоне (True/False)']

    get_file = update.message.document.get_file()
    get_file.download('temp_calls_file.csv')

    with open('temp_calls_file.csv', 'r+b') as file:
        tempReader = file.read().decode('cp1251')
        file.seek(0)
        tempFile = tempReader.encode('utf-8')
        file.write(tempFile)

    tempReaderList = tempReader.replace('\r\n', '\n').split('\n')

    def validationFile():
        try:
            if len(tempReader) > 99: # Файл включает в себя не только заголовки

                if tempReaderList[len(tempReaderList) - 1] == '': tempReaderList.pop(len(tempReaderList) - 1)
                for step, row in enumerate(tempReaderList):
                    if row == '': continue
                    row = row.split(';')
                    if step == 0:
                        if str(row) == str(example_header): continue
                        else: return f'Заголовок файла неправильный\n{step+1}:{row}'

                    domain = row[1].split('.')
                    if domain[1] in ['14', '15', '16', '17', '18', '34', '19', '29', '20', '21']: pass
                    else: return f'Некорректный регион домена\n{step+1}:{row}'
                    if domain[2] != 'rt' or domain[3] != 'ru': return f'неправильный домен, должен быть rt.ru\n{step+1}:{row}'

                    if len(row[2]) != 11: return f'Неправильный номер caller (номер должен включать 11 символов)\n{step+1}:{row}'
                    if len(row[3]) != 11: return f'Неправильный номер callee (номер должен включать 11 символов)\n{step+1}:{row}'
                    if row[2] == row[3]: return f'Самому себе звонить не надо\n{step+1}:{row}'
                    for symbol in row[1]:
                        if symbol == " ": return f'В домене есть символ "пробел"\n{step + 1}:{row}'
                    for symbol in row[4]:
                        if symbol == " ": return f'В столбце "участие в обзвоне" есть символ "пробел"\n{step + 1}:{row}'
            return True
        except Exception as err:
            return 'Возникла ошибка при проверке файла: ' + str(err)

    resultValidation = validationFile()
    if resultValidation == True:
        for MRF in autosanityThreads:
            if autosanityThreads[MRF] != None:
                autosanityThreads[MRF].event.set()
                autosanityThreads[MRF] = None
        time.sleep(2)

        domainList = []
        for row in tempReaderList[1:]:
            domain = row.split(';')[1]
            domainList.append(domain)

        result = configurator.parser_pjsip(domainList)
        if result:
            shutil.move('calls_file.csv', 'calls_file.csv.backup')
            shutil.move('temp_calls_file.csv', 'calls_file.csv')
            sendMesAndKill(update, context, text='Файл проверен, конфигурация выполена.')
        else:
            os.remove('temp_calls_file.csv')
            sendMesAndKill(update, context, text=str(result))
    else:
        os.remove('temp_calls_file.csv')
        sendMesAndKill(update, context, text=resultValidation, timeKill=10)

    context.bot.edit_message_text(text='Меню', message_id=mesMenuId,
                                  chat_id=update.effective_chat.id, reply_markup=setConfig_sendKeyboard(update, context, returnKeyboard=True))
    return ConversationHandler.END


def dialog_setConfigPutCallsFile_Cancel(update, context):
    setConfig_sendKeyboard(update, context)
    return ConversationHandler.END


def setConfig_restart_asterisk(update, context):
    global autosanityThreads
    context.bot.edit_message_text(text='Рестарт займет около 11 секунд, после рестарта обзвон начнется сначала (с 14-ой зоны)', message_id=mesMenuId, chat_id=update.effective_chat.id)
    for MRF in autosanityThreads:
        if autosanityThreads[MRF] != None:
            autosanityThreads[MRF].event.set()
            autosanityThreads[MRF] = None
    time.sleep(1)
    result = configurator.restart_asterisk()

    if result == True:
        for MRF in autosanityThreads:
            if autosanityThreads[MRF] == None:
                autosanityThreads[MRF] = SanityThread(MRF)
                autosanityThreads[MRF].start()
                time.sleep(0.4)
        sendMesAndKill(update, context, text='✅ asterisk перезапущен' + str(result))
    else:
        sendMesAndKill(update, context, text='‼️asterisk не перезапущен: ' + str(result))

    setConfig_sendKeyboard(update, context)


@authorized
def offNumberMenu_sendKeyboard(update, context):

    checkTriggers = getSumTriggerFiles()
    buttons = []

    if checkTriggers > 0:
        buttons.append([InlineKeyboardButton('Выбрать из списка триггеров', callback_data=json.dumps({'offNumberMenu': 'offNumberTriggers'}))])
        text = f'Всего триггеров: {checkTriggers}'
    else:
        text = f'Всего триггеров: {checkTriggers} ⛔️'
        buttons.append([InlineKeyboardButton('⛔️ Cписок триггеров пуст',
                                             callback_data='None')])
    buttons.append([InlineKeyboardButton('⚠️ Ввести данные вручную', callback_data=json.dumps({'offNumberMenu': 'offNumberEnter'}))])
    buttons.append([InlineKeyboardButton('Вернуться назад 🔙', callback_data=json.dumps({'menu': 'generalMenu'}))])
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.message.edit_text(text=text, reply_markup=keyboard)


@authorized
def offNumberTriggersMenu_sendKeyboard(update, context):
    buttons = []
    triggers = configurator.get_AllTriggerFromFile()
    counter = 0

    if len(triggers) != 0:
        for MRF in triggers:
            counter += len(triggers[MRF])
            button = InlineKeyboardButton(MRF + f' ({len(triggers[MRF])})',
                                          callback_data=json.dumps({"offNumberTriggers": MRF}))
            buttons.append(button)
    keyboardList = parserKeyboardFromRow(buttons, row=2)
    if len(triggers) != 0:
        keyboardList.insert(0,[InlineKeyboardButton('Показать все триггеры',
                                                callback_data=json.dumps({"offNumberTriggers": 'all'}))])
    keyboardList.append([InlineKeyboardButton('Вернуться назад 🔙', callback_data=json.dumps({'menu': 'offNumber'}))])

    keyboard = InlineKeyboardMarkup(keyboardList)
    text = f'Всего триггеров: ' + str(counter)
    update.callback_query.message.edit_text(text=text, reply_markup=keyboard)


@authorized
def offNumberMenuByTriggers_sendKeyboard(update, context, MRF):
    triggers = configurator.get_AllTriggerFromFile()
    buttons = []
    MRFGlobal = MRF
    def parserButton(MRF):
        buttonsParser = []

        for triggerData in triggers[MRF]:
            if triggerData['status'] == 'unavailable':
                emoji = '🔕'
            elif triggerData['status'] == 'noaudibility':
                emoji = '🔇'
            elif triggerData['status'] == 'noregistration':
                emoji = '📡'
            text1 = f'{emoji} {triggerData["callsData"]["caller"]["domain"]} ({triggerData["callsData"]["caller"]["callerNumber"]}) '
            text2 = f'--> {triggerData["callsData"]["callee"]["domain"]} ({triggerData["callsData"]["callee"]["callerNumber"]}))'

            if triggerData['status'] != 'noregistration': text = text1 + text2
            else: text = text1

            button = [InlineKeyboardButton(text, callback_data=json.dumps(
                {"offNumberByTrigger": triggerData["callsData"]["caller"]["callerNumber"], 'histType': MRFGlobal}))]
            buttonsParser.append(button)
        return buttonsParser

    if len(triggers) != 0:
        if MRF == 'all':
            for MRF in triggers:
                buttons.extend(parserButton(MRF))
        else:
            if MRF in triggers:
                buttons = parserButton(MRF)
            else:
                offNumberTriggersMenu_sendKeyboard(update, context)
                return
    else:
        offNumberMenu_sendKeyboard(update, context)
        return
    buttons.append([InlineKeyboardButton('Вернуться назад 🔙', callback_data=json.dumps({'offNumberMenu': 'offNumberTriggers'}))])
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.message.edit_text(text='Нажмите на триггер чтобы выключить его и исключить номер из обзвона📌\n',
                                            reply_markup=keyboard)

    #TODO: Сделать динамическое меню с триггерами как у включения номеров


def getSumTriggerFiles():
    return len(os.listdir(Directory_triggersFile))


step = range(1)
@authorized
def dialogOffNumberEnterStart(update, context):

    buttons = []
    textOutMes = 'Напишите домен с которого происходит исходящий вызов. Можно выключить несколько доменов. ' \
                 '\nПравила: \n1. Одно сообщение боту должно содержать только один домен \n2. Указывать нужно именно домен инициатора вызова'
    buttons.append(
        [InlineKeyboardButton('Вернуться назад 🔙', callback_data='offNumberEnterBack')])
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.message.edit_text(text=textOutMes, reply_markup=keyboard)
    return step


@authorized
def dialogOffNumberEnterFile(update, context):
    import trigger
    domain = update.message.text
    allListFromFile = configurator.get_CallsFileCSVFull()

    def parserCallFile(changeParam):
        search = False
        for itr, row in enumerate(allListFromFile):
            if row[1].lower() == domain.lower():
                allListFromFile[itr][4] = changeParam
                search = True
                break
        return row, search

    resultParser = parserCallFile(changeParam='False')
    if resultParser[1]:
        configurator.put_callsFileCSVFull(allListFromFile)
        def triggerKill(domain, caleeNumber, status, typeCall):
            trigger.triggerCheck(domain, caleeNumber, status, typeCall)

        kill = threading.Thread(target=triggerKill, args=(resultParser[0][1], resultParser[0][3], 'good', None), daemon=True)
        kill.start()
        time.sleep(0.3)  # Что бы файл триггера в потоке убийце успел удалиться

        answerGoodMes = context.bot.send_message(chat_id=update.effective_chat.id, text=f"{domain} успешно выключен")
    else:
        answerGoodMes = context.bot.send_message(chat_id=update.effective_chat.id, text=f"{domain} не найден. Домен введен верно?")

    def goodMesKill(update, context, message_id):
        time.sleep(5)
        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)
    kill = threading.Thread(target=goodMesKill, args=(update, context, answerGoodMes['message_id']), daemon=True)
    kill.start()
    context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
    return step


@authorized
def dialogOffNumberEnterCancel(update, context):
    offNumberMenu_sendKeyboard(update, context)
    return ConversationHandler.END


@authorized
def autosanity_sendKeyboard(update, context):
    region = {'14': {'text': 'Москва'}, '15':{'text': 'Центр'},
              '16': {'text': 'Северо-запад'}, '17':{'text': 'Волга'},
            '18': {'text': 'Юг'}, '19':{'text': 'Урал'},
              '20':{'text': 'Сибирь'}, '21':{'text': 'Дальний восток'}}

    buttons = []
    count = 0
    for MRF in autosanityThreads:
        if autosanityThreads[MRF] == None:
            status = 'start'
            text = '🔴 Запустить: '
            count -= 1
        else:
            status = 'stop'
            text = '🟢 Остановить: '
            count += 1

        button = [InlineKeyboardButton(text + region[MRF]['text'],
                    callback_data=json.dumps({"autosanity": status, "region": MRF}))]
        buttons.append(button)
    if count == -8 or count == 8:
        buttons.insert(0,[InlineKeyboardButton(text + 'все ⚠',
                    callback_data=json.dumps({"autosanity": status, "region": 'all'}))])

    buttons.append([InlineKeyboardButton('Вернуться назад 🔙', callback_data=json.dumps({'menu': 'generalMenu'}))])
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.message.edit_reply_markup(reply_markup=keyboard)


@authorized
def autosanityKeyboard_performer(update, context):
    global autosanityThreads
    querryData = update.callback_query.data
    querryData = eval(querryData)
    status = querryData['autosanity']
    region = querryData['region']
    if status == 'start' and region == 'all':
        update.callback_query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('Запускаю все МРФ....', callback_data="None")]]
        ))

        for MRF in autosanityThreads:
            if autosanityThreads[MRF] == None:
                autosanityThreads[MRF] = SanityThread(MRF)
                autosanityThreads[MRF].start()
                time.sleep(0.4)
        autosanity_sendKeyboard(update, context)

    elif status == 'stop' and region == 'all':
        for MRF in autosanityThreads:
            if autosanityThreads[MRF] != None:
                autosanityThreads[MRF].event.set()
                autosanityThreads[MRF] = None
        autosanity_sendKeyboard(update, context)
    elif status == 'start':
        if autosanityThreads[region] == None:
            autosanityThreads[region] = SanityThread(region)
            autosanityThreads[region].start()
            autosanity_sendKeyboard(update, context)
    elif status == 'stop':
        if autosanityThreads[region] != None:
            autosanityThreads[region].event.set()
            autosanityThreads[region]=None
            autosanity_sendKeyboard(update, context)


@authorized
def onNumberMenu_sendKeyboard(update, context):
    buttons = []
    offNumberList = getOffNumberList()
    counter = 0

    if len(offNumberList) != 0:
        for MRF in offNumberList:
            counter += len(offNumberList[MRF])
            button = InlineKeyboardButton(MRF + f' ({len(offNumberList[MRF])})',
                                       callback_data=json.dumps({"onNumberMenu": MRF}))
            buttons.append(button)

    keyboardList = parserKeyboardFromRow(buttons, row=2)
    if len(offNumberList) != 0:
        keyboardList.insert(0,[InlineKeyboardButton('Показать все выключенные',
                                                callback_data=json.dumps({"onNumberMenu": 'all'}))])
    keyboardList.append([InlineKeyboardButton('Вернуться назад 🔙', callback_data=json.dumps({'menu': 'generalMenu'}))])
    keyboard = InlineKeyboardMarkup(keyboardList)

    if counter == 0:
        text = 'Выключенные номера отсутствуют'
    else:
        text = f'Всего выключенных номеров: {counter}\nВ скобках указано количество выключенных номеров\nВыбери регион:'
    update.callback_query.message.edit_text(text=text, reply_markup=keyboard)


@authorized
def OnNumberMenuByNumbers_sendKeyboard(update, context, MRF):
    buttons = []
    all = configurator.get_CallNumbersByMRF()
    offNumberList = getOffNumberList(allMRF=all)

    def search(MRF, callee_number):
        for data in all[MRF]:
            if data['callerNumber'] == callee_number:
                return data

    MRFGlobal = MRF
    def parserButton(MRF):
        buttonsParser = []
        for caller in offNumberList[MRF]:
            callee = search(MRF, caller['calleeNumber'])
            text = f'{caller["domain"]} ({caller["callerNumber"]}) --> {callee["domain"]} ({callee["callerNumber"]})'
            button = [InlineKeyboardButton(text, callback_data=json.dumps({"onNumber": caller["callerNumber"], 'histType': MRFGlobal}))]
            buttonsParser.append(button)
        return buttonsParser

    if len(offNumberList) != 0:
        if MRF == 'all':
            for MRF in offNumberList:
                buttons.extend(parserButton(MRF))
        elif MRF in offNumberList:
            buttons = parserButton(MRF)
        else:
            onNumberMenu_sendKeyboard(update, context)
            return
    else:
        onNumberMenu_sendKeyboard(update, context)
        return

    buttons.append([InlineKeyboardButton('Вернуться назад 🔙', callback_data=json.dumps({'menu': 'onNumber'}))])
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.message.edit_text(text='Нажмите на номер что бы включить его 📌\nВсе выключенные номера:', reply_markup=keyboard)


@authorized
def changeNumber_performer(update, context):
    import trigger
    querryData = update.callback_query.data
    querryData = eval(querryData)
    MRF = querryData['histType']
    allListFromFile = configurator.get_CallsFileCSVFull()

    def parserCallFile(changeParam):
        for itr, row in enumerate(allListFromFile):
            if row[2] == callerNumber:
                allListFromFile[itr][4] = changeParam
                break
        return row

    if list(querryData)[0] == 'onNumber':
        callerNumber = querryData['onNumber']
        parserCallFile(changeParam='True')
        configurator.put_callsFileCSVFull(allListFromFile)
        OnNumberMenuByNumbers_sendKeyboard(update, context, MRF)

    elif list(querryData)[0] == 'offNumberByTrigger':
        callerNumber = querryData['offNumberByTrigger']
        row = parserCallFile(changeParam='False')
        configurator.put_callsFileCSVFull(allListFromFile)

        def triggerKill(domain, caleeNumber, status, typeCall):
            trigger.triggerCheck(domain, caleeNumber, status, typeCall, quickRemove=True)
        kill = threading.Thread(target=triggerKill, args=(row[1], row[3], 'good', None), daemon=True)
        kill.start()
        time.sleep(0.5) # Что бы файл триггера в потоке убийце успел удалиться
        offNumberMenuByTriggers_sendKeyboard(update, context, MRF)


def getOffNumberList(allMRF=None):
    listOff = {'14':[], '15':[], '16':[], '17':[], '18':[], '19':[], '20':[], '21':[]}
    if allMRF == None:
        allMRF = configurator.get_CallNumbersByMRF()

    for MRF in allMRF:
        for row in allMRF[MRF]:
            if row['status'] == 'False':
                listOff[MRF].append(row)

    for MRF in allMRF:
        if len(listOff[MRF]) == 0:
            del listOff[MRF]
    return listOff


def parserKeyboardFromRow(buttons ,row):
    start = 0
    countAll = len(buttons)
    end = countAll // row
    step = countAll // row
    remainder = countAll % row
    keyboard = []
    if countAll >= row:
        for x in range(0,row):
            if remainder == 0:
                keyboard.append(buttons[start:end])
                start += step
                end += step
            elif remainder != 0:
                keyboard.append(buttons[start:end+1])
                remainder -= 1
                start += step + 1
                end += step + 1
    elif countAll == 0: pass
    else: keyboard.append(buttons)
    return keyboard


@authorized
def customTrigger_performer(update, context):
    import createCall
    querryData = update.callback_query.data
    querryData = eval(querryData)
    typeCall = querryData[1]
    randData = querryData[2]
    nameTriggerFile = querryData[0]
    trigger = configurator.get_TriggerFromFile(nameTriggerFile)
    keyboad = trigger['keyboard']

    if typeCall == 'out':
        buttonActive = 0
        buttonInactive = 1
    elif typeCall == 'in':
        buttonActive = 1
        buttonInactive = 0
    if keyboad['inline_keyboard'][buttonInactive][0]['callback_data'] == 'calling':
        oldTextInactive = keyboad['inline_keyboard'][buttonInactive][0]['text']
        keyboad['inline_keyboard'][buttonInactive][0]['text'] = "Подожди, я звоню..."

    oldText = keyboad['inline_keyboard'][buttonActive][0]['text']
    keyboad['inline_keyboard'][buttonActive][0]['text'] = "Подожди, я звоню..."
    keyboad['inline_keyboard'][buttonActive][0]['callback_data'] = 'calling'

    context.bot.answer_callback_query(update.callback_query.id, text="")
    update.callback_query.message.edit_reply_markup(reply_markup=json.dumps(keyboad))

    if keyboad['inline_keyboard'][buttonInactive][0]['callback_data'] == 'calling':
        keyboad['inline_keyboard'][buttonInactive][0]['text'] = oldTextInactive
    keyboad['inline_keyboard'][buttonActive][0]['text'] = oldText
    configurator.put_triggerInFile(trigger)

    call_dict = trigger['callsData']['caller']

    createCall.create_file_call_asterisk(call_dict, context='rand_call', typeRandCall=typeCall, randNumberOrDomain=randData)
