import threading
from createCall import *
from configurator import check_reg, get_CallNumbersByMRF, os
from trigger import register_triggerCheck

lock = threading.Lock()


class Autosanity():
    def start_sanity(self, event, MRF):
        # Получаем данные по списку обзвона
        while True:
            if event.is_set(): return # Выход из потока
            # Не большее n вызовов одновременно
            if len(os.listdir(Directory_asterisk_CallFiles)) > int(Limit_calls):
                time.sleep(5)

            else:
                with lock:
                    calls_list = get_CallNumbersByMRF(MRF)
                    for call_dict in calls_list:
                        # Проверка регистрации, если ок вернет True
                        if event.is_set(): return  # Выход из потока
                        if call_dict['status'] == 'True':
                            if check_reg(call_dict['domain']):
                                register_triggerCheck(call_dict, 'good')
                                create_file_call_asterisk(call_dict)
                                # Создание файла раз в секунду
                                time.sleep(1)
                            else:
                                register_triggerCheck(call_dict, 'noregistration')

                time.sleep(int(Call_waiting_time))
