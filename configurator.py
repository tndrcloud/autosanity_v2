from settings import CallsFile, Directory_triggersFile, Directory_asterisk_CallFiles
import os, subprocess, threading, time, csv, json


lock_CallsFile = threading.RLock()
lock_TriggerFile = threading.RLock()


def check_reg(domain):
    regFull = subprocess.run(f'asterisk -rx "pjsip show registration {domain}_reg"',
                             shell=True, encoding='utf-8', stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    if regFull.returncode == 1:
        return 'error', regFull.stderr
    else:
        if regFull.stdout == f'Unable to find object {domain}_reg.\n\n':
            return 'error', regFull.stdout
        else:

            regStatus = regFull.stdout.split('\n')[4].split()[2]
            if regStatus == 'Registered':
                return True
            else:
                return False


def get_TriggerFromFile(nameTrigger):
    with lock_TriggerFile:
        file_path = Directory_triggersFile + nameTrigger
        if os.path.exists(file_path):
            with open(file_path, 'r') as triggerFile:
                reader = triggerFile.read()
                return json.loads(reader)
        else: False


def get_AllTriggerFromFile():
    triggersDir = os.listdir(Directory_triggersFile)
    triggers = []
    for triggerName in triggersDir:
        with lock_TriggerFile:
            with open(Directory_triggersFile + triggerName, 'r') as triggerFile:
                reader = triggerFile.read()
                triggers.append(json.loads(reader))

    triggersRegion = {'14': [], '15': [], '16': [], '17': [], '18': [], '34': [], '19': [], '29': [], '20': [],
                      '21': []}
    for triggerData in triggers:
        zone = triggerData["callsData"]["caller"]["domain"].split('.')[1]
        triggersRegion[zone].append(triggerData)

    triggersRegion['18'].extend(triggersRegion['34'])
    del triggersRegion['34']
    triggersRegion['19'].extend(triggersRegion['29'])
    del triggersRegion['29']

    for MRF in ['14','15','16','17','18','19','20','21']:
        if len(triggersRegion[MRF]) == 0:
            del triggersRegion[MRF]

    return triggersRegion


def put_triggerInFile(triggerData):
    with lock_TriggerFile:
        with open(Directory_triggersFile + triggerData['callsData']['caller']['calleeNumber'], 'w') as triggerFile:
            triggerFile.write(json.dumps(triggerData))
        return True


def get_CallsFileCSVFull():
    file = []
    with lock_CallsFile:
        with open(CallsFile) as callsFile:
            reader = csv.reader(callsFile, delimiter=';')
            #next(reader, None)
            for row in reader:
                if len(row) > 0:
                    file.append(row)
    return file


def get_CallsFileRead():
    with lock_CallsFile:
        with open(CallsFile, 'r') as sourceFile:
            reader = sourceFile.read()
    return reader


def put_callsFileCSVFull(data_list):
    with lock_CallsFile:
        with open(CallsFile, 'w') as callsFile:
            writer = csv.writer(callsFile, delimiter=';')
            writer.writerows(data_list)
        return True


def get_CallNumbersByMRF(MRF='all'):
    with lock_CallsFile:
        with open(CallsFile) as callsFile:
            data = {'14':[], '15':[], '16':[], '17':[], '18':[], '34':[], '19':[], '29':[], '20':[], '21':[]}
            reader = csv.reader(callsFile, delimiter=';')
            next(reader, None)
            for row in reader:
                if len(row) > 0:
                    zone = row[1].split('.')[1]
                    row_in_dict = {'city':row[0],'domain':row[1],'callerNumber':row[2], 'calleeNumber':row[3],'status':row[4]}
                    data[zone].append(row_in_dict)

    data['18'].extend(data['34'])
    del data['34']
    data['19'].extend(data['29'])
    del data['29']

    if MRF == 'all':
        return data
    else:
        if MRF == '34':
            return data['18']
        elif MRF == '29':
            return data['19']
        else:
            return data[MRF]


def restart_asterisk():
    call_files_from_asterisk = os.listdir(Directory_asterisk_CallFiles)

    if call_files_from_asterisk:
        for call_file in call_files_from_asterisk:
            os.remove(Directory_asterisk_CallFiles + call_file)

    result = subprocess.run(f'systemctl restart asterisk',
                             shell=True, encoding='utf-8', stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    time.sleep(10)
    if result.returncode == 1:
        return 'error', result.stderr
    else:
        return True


def parser_pjsip(domainList):
    def parser_config_pjsip_text(domain):
        text = f'''
    [{domain}]
    type=endpoint
    transport=transport-udp
    context=sanity-in
    disallow=all
    allow=alaw
    allow=ulaw
    outbound_auth={domain}_auth
    aors={domain}_aor
    from_user=asterisk_sanity
    from_domain={domain}
    direct_media=no
    force_rport=yes
    contact_user=asterisk_sanity

    [{domain}_auth]
    type=auth
    auth_type=userpass
    password=*****
    username=*****

    [{domain}_aor]
    type=aor
    contact=sip:{domain}
    qualify_frequency=15

    [{domain}_reg]
    type=registration
    transport=transport-udp
    outbound_auth={domain}_auth
    server_uri=sip:{domain}
    client_uri=sip:asterisk_sanity@{domain}
    retry_interval=60
    expiration=600
    contact_user=asterisk_sanity
    endpoint={domain}
    line=yes
    '''
        return text

    name_list = []

    # Создаем папку с конфигами
    if not os.path.isdir('/etc/asterisk/pjsip_custom'):
        os.mkdir('/etc/asterisk/pjsip_custom')

    confNewPJSIP_List = []

    for domain in domainList:
        if not os.path.isfile(f'/etc/asterisk/pjsip_custom/{domain}'): # Проверка есть ли файл
            confNewPJSIP_List.append(domain)
            name_list.append(f'#include "/etc/asterisk/pjsip_custom/{domain}"')
            with open(f'/etc/asterisk/pjsip_custom/{domain}', 'w') as file_end:
                file_end.write(parser_config_pjsip_text(domain))

        def removePJSIPfile():
            for file in confNewPJSIP_List:
                os.remove('/etc/asterisk/pjsip_custom/'+file)
            with open('/etc/asterisk/pjsip.conf', 'w') as include:
                include.write(readerPJSIPconf)
            restart_asterisk()

        with open('/etc/asterisk/pjsip.conf', 'r') as include:
            readerPJSIPconf = include.read()

        with open('/etc/asterisk/pjsip.conf', 'a') as include:
            include.write('\n'.join(name_list))

        def check_reg_performer():
            for domain in confNewPJSIP_List:
                checkReg = check_reg(domain)
                if checkReg != True:
                    return checkReg
            return True

        if restart_asterisk() != True:
            result_restart_asterisk = restart_asterisk()
            if result_restart_asterisk != True: return result_restart_asterisk

        for step in range(0,3):
            checkReg = check_reg_performer()
            if checkReg:
                return True
            if step == 2:
                # Hегистрация не прошла
                if checkReg[0] == False:
                    removePJSIPfile()
                    return checkReg

                # Rакая то ошибка при проверке
                else:
                    removePJSIPfile()
                    return checkReg

            else: time.sleep(5)
    else: return True
