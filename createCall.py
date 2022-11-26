#!/usr/bin/python3.6
import shutil, sys, time
from settings import *


def create_file_call_asterisk(call_dict, context='autosanity', typeRandCall='',randNumberOrDomain=None):
    text = ''
    if randNumberOrDomain != None:
        if typeRandCall == 'out':
            text += f"Channel: PJSIP/{randNumberOrDomain}@{call_dict['domain']}\n"
        elif typeRandCall == 'in':
            text += f"Channel: PJSIP/{call_dict['calleeNumber']}@{randNumberOrDomain}\n"
    else:
        text += f"Channel: PJSIP/{call_dict['calleeNumber']}@{call_dict['domain']}\n"

    text += f"Callerid: autosanity\n" \
    f"MaxRetries: 0\n" \
    f"Context: {context}\n" \
    f"Extension: s\n" \
    f"Priority: 1\n" \
    f"Set: callerDomain={call_dict['domain']}\n" \
    f"Set: calleeNumber={call_dict['calleeNumber']}\n"

    if randNumberOrDomain != None:
     text += f"Set: randData={typeRandCall}:{randNumberOrDomain}"

    with open(Directory_asterisk_temp_CallFiles + call_dict['calleeNumber'], 'w') as call_file:
        call_file.write(text)
    shutil.chown(Directory_asterisk_temp_CallFiles + call_dict['calleeNumber'], user=User, group=User)
    shutil.move(Directory_asterisk_temp_CallFiles + call_dict['calleeNumber'], Directory_asterisk_CallFiles + call_dict['calleeNumber'])


if __name__ == '__main__':
    if len(sys.argv) == 4:
        call_dict = {'domain': sys.argv[1], 'calleeNumber': sys.argv[2]}
        step = sys.argv[3]
        if step == '2':
            context = 'autosanity_step2'
        else:
            context = 'autosanity_step3'
        time.sleep(5)
        create_file_call_asterisk(call_dict, context=context)
