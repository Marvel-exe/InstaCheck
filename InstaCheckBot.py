# -*- coding: utf-8 -*-
# Made by @nesterovoa
#
# > FAQ:
# - Token should be placed in TOKEN_FILE!
# - If lib requests not installed run: pip.main(['install', 'requests'])
# - Pip install telegram-bot:
#   pip install python-telegram-bot --upgrade
# - Anaconda install telegram-bot:
#   conda install -c conda-forge python-telegram-bot
#   conda install -c conda-forge/label/gcc7 python-telegram-bot
#   conda install -c conda-forge/label/cf201901 python-telegram-bot
#
# TODO Git
# TODO Restricted access to a admin handler
# TODO Добавить все сообщения от пользователя в лог файл или print
# TODO Добавить возможность вводить имя после пустой команды
# TODO Python autoinstall Dependencies
# TODO Добавить фильтр Filter.text?
# TODO Вынести все повторения в переменные глобальные
# TODO data_list не создается сам
# TODO уведомление о смене статуса отправится только одному пользователю!!
# TODO расписание бэкапы
# TODO проверять по ID а не имени

import requests
from datetime import datetime
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters

DATA_FILE = 'data_list.txt'
USERS_FILE = 'users_list.txt'
LOG_FILE = 'log_list.txt'
TOKEN_FILE = 'token.txt'

# Read token from file
with open(TOKEN_FILE, 'r') as token_data: 
    API_TOKEN = token_data.read()

# Own logger to txt file and console
def logger(priority, message):
    users_list = open(LOG_FILE,"a")
    users_list.write('<' + priority + '> ' + str(datetime.now()) + ' ' + message + '\n')
    users_list.close()
    print ('<' + priority + '> ' + str(datetime.now()) + ' ' + message)

# Start and help message for telegram user
def do_help (bot, update):
    logger ('LOG', "Help for ChatID: " + str(update.message.chat_id) + ". Service Info (bot, update): " + str(bot) + str(update))
    
    bot.send_message(
        chat_id = update.message.chat_id,        
        text = "Use commands: \n\n/add <instagram profile name> to track account status \n/remove for removing from tracking list \nFor example: /add Instagram"
    )

# Add instagram username to tracking list   
def do_add (bot, update, args):
    # args from pass_args - name
    inst_name = ''.join(args).lower()
    logger ('LOG', "Add: " + inst_name + ". ChatID: " + str(update.message.chat_id))
    
    if len(args) == 0:
        update.message.reply_text("Enter correct instagram profile username after /add command")
    else: 
        # is user exist in check list?
        with open(USERS_FILE) as users_list:  
            if inst_name + " tracked by " + str(update.message.chat_id) in users_list.read():
                logger ('LOG', "  User exists in USERS_FILE: " + inst_name + ". ChatID: " + str(update.message.chat_id))
                update.message.reply_text("User " + inst_name + " is already added to your tracking list")
                users_list.close()
                return 
            
        # user not exists, check for valid account name
        checkresult = do_checkname(inst_name)
        
        if checkresult == 1:                        
            logger ('LOG', "    Writing to file user: " + inst_name + ". ChatID: " + str(update.message.chat_id))
            users_list = open(USERS_FILE,"a")
            users_list.write(inst_name + " tracked by " + str(update.message.chat_id))
            users_list.close()
            update.message.reply_text("User " + inst_name + " added to your tracking list")              
        elif checkresult == 0:                      
            update.message.reply_text("User " + inst_name + " not found")              
        else:                                       
            update.message.reply_text("Error, try later")             

# Remove instagram username from tracking list           
def do_remove (bot, update, args):
    inst_name = ''.join(args).lower()
    logger ('LOG', "Remove: " + inst_name + ". ChatID: " + str(update.message.chat_id))
    
    if len(args) == 0:
        update.message.reply_text("Enter correct instagram profile username after /remove command")
    else:
        # is user exist in check list?
        with open(USERS_FILE, 'r') as users_list:            
            if not (inst_name + " tracked by " + str(update.message.chat_id) in users_list.read()):
                logger ('LOG', "  User not exists in users_list: " + inst_name + ". ChatID: " + str(update.message.chat_id))
                users_list.close()
                update.message.reply_text("User " + inst_name + " not tracked")
            else:                
                # not exists, deleting
                logger ('LOG', "  Removing from USERS_FILE: " + inst_name + ". ChatID: " + str(update.message.chat_id))
                with open(USERS_FILE, 'r') as users_list:
                    lines = users_list.readlines()
                with open(USERS_FILE, 'w') as users_list:
                    for line in lines:
                        if line.strip('\n') != inst_name + " tracked by " + str(update.message.chat_id):
                            users_list.write(line)                            
                users_list.close()
                update.message.reply_text("User " + inst_name + " removed from tracking list")

# Check for valid account name            
def do_checkname (name):
    logger ('LOG', "  Checking: " + name)
    req = requests.get("https://www.instagram.com/" + name)
    
    if req.status_code == 404:
        logger ('LOG', "   User not found: " + name)
        return 0
    elif req.status_code == 200:
        logger ('LOG', "    User found: " + name)
        return 1
    else:
        logger ('ERROR', "    Is https://www.instagram.com/ available? ")
        return 2

# Check instagram accounts status    
def users_stat_checker (bot, job):
    logger ('LOG', "Heartbeat")
    
    with open(USERS_FILE, 'r') as users_list:        
        lines = users_list.readlines()
        
        # read every line, get instagram account name and tracking users ID
        for line in lines:
            inst_name = line.split(" tracked by ", 1)[0]
            chat_number = line.split(" tracked by ", 1)[1]
            #logger ('LOG', "Check privacy status of user " + inst_name + " for ChatID: " + chat_number)
            req = requests.get("https://instagram.com/" + inst_name)
            
            # find string in HTML page
            if '"is_private":true' in str(req.content):
                inst_status = "private"
                #logger ('LOG', "  User status is private: " + inst_name)
            elif '"is_private":false' in str(req.content):
                inst_status = "public"
                #logger ('LOG', "  User status is public: " + inst_name)
            else:
                logger ('ERROR', "  Failed status check for user " + inst_name)
            
            with open(DATA_FILE, 'r') as data_list:
                # make a copy of data_list in memory for faster work
                data_list_copy = data_list.read()
                
                # is that a new account name?
                if not (inst_name + " is " in data_list_copy):
                    logger ('LOG', "    Adding new user to data_list: " + inst_name + " is " + inst_status)
                    data_list = open("data_list.txt","a")
                    data_list.write(inst_name + " is " + inst_status)
                    data_list.close()                    
                else:                    
                    # it's not new, check for status change
                    if inst_status == "private":
                        if (inst_name + " is public" in data_list_copy):
                            logger ('LOG', "    Changed status of user: " + inst_name + ". Now is " + inst_status)
                            # removing this string with account name-status in 2 steps
                            with open(DATA_FILE, 'r') as data_list:
                                data_lines = data_list.readlines()
                            with open(DATA_FILE, 'w') as data_list:
                                for data_line in data_lines:
                                    if data_line.strip('\n') != inst_name + " is public":
                                        data_list.write(data_line)    
                            # add changed account name-status in the end                                                
                            data_list = open("data_list.txt","a")
                            data_list.write(inst_name + " is " + inst_status)
                            data_list.close()
                            bot.send_message(chat_id = chat_number, text = inst_name + " changed status to private!")  
                            
                    elif inst_status == "public":
                        if (inst_name + " is private" in data_list_copy):
                            logger ('LOG', "    Changed status of user: " + inst_name + ". Now is " + inst_status)
                            # removing this string with account name - status in 2 steps
                            with open(DATA_FILE, 'r') as data_list:
                                data_lines = data_list.readlines()
                            with open(DATA_FILE, 'w') as data_list:
                                for data_line in data_lines:
                                    if data_line.strip('\n') != inst_name + " is private":
                                        data_list.write(data_line) 
                            # add changed account name-status in the end                                                     
                            data_list = open("data_list.txt","a")
                            data_list.write(inst_name + " is " + inst_status)
                            data_list.close()
                            bot.send_message(chat_id = chat_number, text = inst_name + " changed status to public!")                                                                

def main():
    # token for API connection
    updater = Updater(token = API_TOKEN)  
    
    # sheduled jobs - 10 min (600 sec) accounts check interval 
    users_checker_job = updater.job_queue.run_repeating(users_stat_checker, interval = 600, first = 3)
    users_checker_job.enabled = True;
    
    # command handlers
    shitdispatcher = updater.dispatcher
    shitdispatcher.add_handler(CommandHandler('start', do_help))
    shitdispatcher.add_handler(CommandHandler('add', do_add, pass_args = True))
    shitdispatcher.add_handler(CommandHandler('remove', do_remove, pass_args = True))
   
    # start and idle for interuptions
    updater.start_polling()
    updater.idle()
    #updater.stop()
    
if __name__ == '__main__':
    main()