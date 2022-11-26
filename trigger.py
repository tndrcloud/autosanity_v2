#!/usr/bin/python3.6
import  requests, datetime, json, time, os, sys, subprocess
import random
from settings import url, chat_id, token, quickRemoveTrigger, Directory_triggersFile
from configurator import get_CallNumbersByMRF, get_TriggerFromFile, put_triggerInFile


# custom_sanity - должен передаться 4 аргумент в формате in:84951112223344 или out:84951112223344
def read_CallsFile(caller_domain=None, callee_number=None, allFromMRF=False):
    MRF = caller_domain.split('.')[1]
    callsFileData = get_CallNumbersByMRF(MRF)
    # for key in callsFileData: Если вызовы будут между МРФ
    if allFromMRF:
        result = callsFileData
    else:
        result = {'caller': None, 'callee': None}
        if caller_domain != None:
            for data in callsFileData:
                if data['domain'] == caller_domain:
                    result['caller'] = data
                    break
        if callee_number != None:
            for data in callsFileData:
                if data['callerNumber'] == callee_number:
                    result['callee'] = data
                    break
    return result


def sendMessage(triggerData, text, keyboard=None):
    metod = '/sendMessage'

    if keyboard == None:
        params = {'chat_id': chat_id,
                  'text': text}
    else:
        params = {'chat_id': chat_id,
                   'text': text, 'reply_markup': json.dumps(keyboard)}

    r = requests.post(url+token+metod, data=params)
    return json.loads(r.text)


def update_telegram(triggerData, text):
    metod = '/editMessageText'

    params = {'chat_id': chat_id,
              'message_id': triggerData['message_id'], 'text': text}

    r = requests.post(url+token+metod, data=params)
    return json.loads(r.text)


def update_keyboard(triggerData, keyboard):
    metod = '/editMessageReplyMarkup'

    params = {'chat_id': chat_id,
              'message_id': triggerData['message_id'], 'reply_markup': json.dumps(keyboard)}

    r = requests.post(url + token + metod, data=params)
    return json.loads(r.text)


def delete_telegram(triggerData):
    metod = '/deleteMessage'
    params = {'chat_id': chat_id,
              'message_id': triggerData['message_id']}
    r = requests.post(url + token + metod, data=params)
    return json.loads(r.text)


def parserText(triggerData, optional='', stepExtra=''):
    if triggerData['status'] == 'good':
        emoji = '✅'
        textOfStatus = 'вызов прошел успешно!'
    elif triggerData['status'] == 'unavailable':
        emoji = '🔕'
        textOfStatus = 'вызов не прошел!'
    elif triggerData['status'] == 'noaudibility':
        emoji = '🔇'
        textOfStatus = 'нет слышимости!'
    elif triggerData['status'] == 'noregistration':
        emoji = '📡'
        textOfStatus = ', отсутствует регистрация!\n'

    text_other = f"Первый триггер: {triggerData['date']}\n"

    text = f" {triggerData['step']}{stepExtra}{emoji} {triggerData['callsData']['caller']['callerNumber']} ({triggerData['callsData']['caller']['domain']}," \
           f" г. {triggerData['callsData']['caller']['city']}) "

    text2 = f"---> {triggerData['callsData']['callee']['callerNumber']} ({triggerData['callsData']['callee']['domain']}," \
           f" г. {triggerData['callsData']['callee']['city']})" \
           f", {textOfStatus}\n" \
           f"{text_other}" + f"{optional}"
    if triggerData['status'] == 'noregistration': result = text + textOfStatus + text_other
    else: result = text + text2

    return result


def parserKeyboard(triggerData):
    randData = randomaiser(triggerData)
    if randData == None: return None
    randNumberCallee = randData['randNumberCallee']
    randNumberCaller = randData['randNumberCaller']

    buttonOutCallback = [triggerData['callsData']['callee']['callerNumber'],
                            "out",randNumberCallee]

    buttonInCallback = [triggerData['callsData']['callee']['callerNumber'],
                            "in",randNumberCaller[1]]

    # Проверяем исходящую связь
    buttonRandOut = {'text':'Исходящий '+triggerData['callsData']['caller']['callerNumber']+' --> '+randNumberCallee,
                'callback_data': str(buttonOutCallback)}
    # Проверяем входящую связь
    buttonRandIn = {'text':'Входящий '+randNumberCaller[0]+' --> '+triggerData['callsData']['callee']['callerNumber'],
                'callback_data': str(buttonInCallback)}

    keyboard = {'inline_keyboard': [[buttonRandOut],[buttonRandIn]]}

    return keyboard


def randomaiser(triggerData):
    callsDataFromFile = read_CallsFile(caller_domain=triggerData['callsData']['caller']['domain'], allFromMRF=True)
    count = 0
    while count <= 20:
        if count == 20: return None
        count += 1
        randData = random.choice(callsDataFromFile)
        if randData['callerNumber'] != triggerData['callsData']['caller']['callerNumber'] \
                and randData['callerNumber'] != triggerData['callsData']['callee']['callerNumber'] \
                and randData['status'] == 'True':
            randNumberCaller = [randData['callerNumber'], randData['domain']]
            break
    count = 0
    while count <= 20:
        if count == 20: return None
        count += 1
        randData = random.choice(callsDataFromFile)
        if randData['callerNumber'] != triggerData['callsData']['caller']['callerNumber'] \
                and randData['callerNumber'] != triggerData['callsData']['callee']['callerNumber'] \
                and randData['status'] == 'True':
            randNumberCallee = randData['callerNumber']
            break

    result = {'randNumberCaller': randNumberCaller, 'randNumberCallee': randNumberCallee}
    return result


def triggerName(triggerData):
    return triggerData['callsData']['callee']['callerNumber']


def send_in_zabbix(triggerData):
    domain = triggerData['callsData']['caller']['domain']
    number = triggerData['callsData']['callee']['callerNumber']

    zabbix_command = f'zabbix_sender -c /etc/zabbix/zabbix_agentd.conf -k number_result[\\"{domain}\\"] -o {triggerData["status"]}:{number}'
    zabbix_answer = subprocess.run(zabbix_command,
                             shell=True, encoding='utf-8', stderr=subprocess.PIPE, stdout=subprocess.PIPE)


def register_triggerCheck(caller, status):
    domain = caller['domain']
    calleeNumber = caller['calleeNumber']
    triggerData = {'message_id': None, 'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   'step': 1, 'status': status, 'callsData': read_CallsFile(domain, calleeNumber)}

    if os.path.isfile(Directory_triggersFile + triggerName(triggerData)):
        triggerDataFile = get_TriggerFromFile(triggerName(triggerData))
        if status == 'good':
            if triggerDataFile['status'] == 'noregistration':
                os.remove(Directory_triggersFile + triggerName(triggerData))
                count = 0
                triggerDataFile['status'] = triggerData['status']

                if not quickRemoveTrigger:
                    for emoji in ['🏃🏻', '🏃🏻', '🏃🏻', '🚶🏻', '🚶🏻', '🚶🏻', '🧎🏻', '🧎🏻', '🧎🏻', '🤚🏻']:
                        text = parserText(triggerDataFile,
                                          optional=f'\n Триггер исчезнет через: {emoji} ' + str(10 - count))
                        update_telegram(triggerDataFile, text)
                        count += 1
                        time.sleep(1)

                delete_telegram(triggerDataFile)

        elif status == 'noregistration':
            triggerDataFile['step'] += 1
            text = parserText(triggerDataFile)

            delete_telegram(triggerDataFile)
            resultSendMessage = sendMessage(triggerDataFile, text)

            triggerDataFile['message_id'] = str(resultSendMessage['result']['message_id'])
            put_triggerInFile(triggerDataFile)

    else:
        if status == 'good': pass # Регистрация есть, всё хорошо
        elif status == 'noregistration':
            text = parserText(triggerData)
            resultSendMessage = sendMessage(triggerData, text)
            triggerData['message_id'] = str(resultSendMessage['result']['message_id'])

            put_triggerInFile(triggerData)


def triggerCheck(domain, calleeNumber, status, typeCall=None, quickRemove=False):
    if typeCall == None:
        customSanity = False
    else:
        customSanity = True
    triggerData = {'message_id': None, 'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   'step': 1, 'status': status, 'callsData': read_CallsFile(domain, calleeNumber)}

    if not customSanity:
        if os.path.isfile(Directory_triggersFile + triggerName(triggerData)):
            triggerDataFile = get_TriggerFromFile(triggerName(triggerData))

            if triggerData['status'] == 'good':
                # Триггер окнулся
                send_in_zabbix(triggerData)

                triggerDataFile['status'] = triggerData['status']
                count = 0
                # while count <10:
                os.remove(Directory_triggersFile + triggerName(triggerData))
                if not quickRemove:
                    for emoji in ['🏃🏻', '🏃🏻', '🏃🏻', '🚶🏻', '🚶🏻', '🚶🏻', '🧎🏻', '🧎🏻', '🧎🏻', '🤚🏻']:
                        text = parserText(triggerDataFile,
                                          optional=f'\n Триггер исчезнет через: {emoji} ' + str(10 - count))
                        update_telegram(triggerDataFile, text)
                        count += 1
                        time.sleep(1)
                else:
                    text = parserText(triggerDataFile)
                    update_telegram(triggerDataFile, text)
                    time.sleep(10)

                delete_telegram(triggerDataFile)

            elif triggerData['status'] == 'unavailable' or triggerData['status'] == 'noaudibility':
                send_in_zabbix(triggerData)

                oldStatus = triggerDataFile['status']
                triggerDataFile['status'] = triggerData['status']
                # Триггер снова не ок
                if oldStatus == triggerData['status']:
                    triggerDataFile['step'] += 1
                else:
                    triggerDataFile['step'] = 1

                text = parserText(triggerDataFile)
                checkCount = True
                for count in (6 * count for count in range(1, 100)):
                    if triggerDataFile['step'] > 0 and triggerDataFile['step'] < 3 \
                            or triggerDataFile['step'] > count and triggerDataFile['step'] < count + 3:
                        keyboard = parserKeyboard(triggerDataFile)
                        delete_telegram(triggerDataFile)
                        resultSendMessage = sendMessage(triggerDataFile, text, keyboard)
                        checkCount = False

                        triggerDataFile['keyboard'] = keyboard
                        break

                if checkCount:
                    delete_telegram(triggerDataFile)
                    resultSendMessage = sendMessage(triggerDataFile, text)

                triggerDataFile['message_id'] = str(resultSendMessage['result']['message_id'])

                put_triggerInFile(triggerDataFile)

        else:
            if triggerData['status'] == 'good':
                pass  # Ничего не надо делать, всё хорошо
            elif triggerData['status'] == 'unavailable' or triggerData['status'] == 'noaudibility':
                send_in_zabbix(triggerData)

                text = parserText(triggerData)
                keyboard = parserKeyboard(triggerData)

                resultSendMessage = sendMessage(triggerData, text, keyboard)
                triggerData['keyboard'] = keyboard

                triggerData['message_id'] = str(resultSendMessage['result']['message_id'])
                put_triggerInFile(triggerData)

    elif customSanity:
        if os.path.isfile(Directory_triggersFile + triggerName(triggerData)):
            triggerDataFile = get_TriggerFromFile(triggerName(triggerData))

            if triggerData['status'] == 'good':
                emoji = '✅'
            elif triggerData['status'] == 'unavailable':
                emoji = '🔕'
            elif triggerData['status'] == 'noaudibility':
                emoji = '🔇'

            if typeCall == 'out':
                buttonActive = 0
                buttonInactive = 1
            elif typeCall == 'in':
                buttonActive = 1
                buttonInactive = 0

            if triggerDataFile['keyboard']['inline_keyboard'][buttonInactive][0]['callback_data'] == 'calling':
                oldTextInactive = triggerDataFile['keyboard']['inline_keyboard'][buttonInactive][0]['text']
                triggerDataFile['keyboard']['inline_keyboard'][buttonInactive][0]['text'] = "Подожди, я звоню..."

            triggerDataFile['keyboard']['inline_keyboard'][buttonActive][0]['callback_data'] = 'None'
            triggerDataFile['keyboard']['inline_keyboard'][buttonActive][0]['text'] = f'{emoji} ' \
                                                                                      + triggerDataFile['keyboard'][
                                                                                          'inline_keyboard'][
                                                                                          buttonActive][0]['text']

            update_keyboard(triggerDataFile, triggerDataFile['keyboard'])
            if triggerDataFile['keyboard']['inline_keyboard'][buttonInactive][0]['callback_data'] == 'calling':
                triggerDataFile['keyboard']['inline_keyboard'][buttonInactive][0]['text'] = oldTextInactive
            put_triggerInFile(triggerDataFile)



if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Скрипт запускается с атрибутами, обязательные: "Домен", "Номер вызываемого", "Статус вызова (0,1 или 2)"'
              '\nнеобязательный четвертый атрибут: "Санити ручное? 0 - да, 1 - нет"')
        sys.exit()

    if len(sys.argv) == 5:
        typeCall = sys.argv[4].split(':')[0]
    else:
        typeCall = None

    if not os.path.isdir(Directory_triggersFile):
        import shutil
        from settings import User
        os.mkdir(Directory_triggersFile)
        shutil.chown(Directory_triggersFile, user=User, group=User)

    domain = sys.argv[1]
    calleeNumber = sys.argv[2]
    status = sys.argv[3]
    triggerCheck(domain, calleeNumber, status, typeCall, quickRemove=quickRemoveTrigger)
    