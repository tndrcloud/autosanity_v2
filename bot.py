from bot_extension import *


updater = Updater(token=False, use_context=True)
dispatcher = updater.dispatcher

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

autosanity_handler = CommandHandler('menu', menuStart)
dispatcher.add_handler(autosanity_handler)

#file_handler = MessageHandler(Filters.document, setConfigPutCallsFile_performer)
#dispatcher.add_handler(file_handler)

# {'setConfig': 'putFile'}

offNumberEnterDialog_handler = ConversationHandler(
                        entry_points=[CallbackQueryHandler(dialog_setConfigPutCallsFile_sendKeyboard, pattern='{"setConfig": "putFile"}')],
                        states={dialog_putfile: [MessageHandler(Filters.document, dialog_setConfigPutCallsFile_performer)]},
                        fallbacks=[CallbackQueryHandler(dialog_setConfigPutCallsFile_Cancel, pattern='{"menu": "setConfig"}')],
                                      )
dispatcher.add_handler(offNumberEnterDialog_handler)

offNumberEnterDialog_handler = ConversationHandler(
                        entry_points=[CallbackQueryHandler(dialogOffNumberEnterStart, pattern='{"offNumberMenu": "offNumberEnter"}')],
                        states={step: [MessageHandler(Filters.text, dialogOffNumberEnterFile)]},
                        fallbacks=[CallbackQueryHandler(dialogOffNumberEnterCancel, pattern='offNumberEnterBack')],
                                      )
dispatcher.add_handler(offNumberEnterDialog_handler)

spam_handler = MessageHandler(Filters.text, spam_performer)
dispatcher.add_handler(spam_handler)

autosanity_callback_handler = CallbackQueryHandler(general_callbackHandler)
dispatcher.add_handler(autosanity_callback_handler)

updater.start_polling()