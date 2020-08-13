
import telegram
import logging
import json
import requests
import time
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater,MessageHandler,Filters,CommandHandler,ConversationHandler

import yfinance as yf
import matplotlib.pyplot as plt
import datetime as dt
from mplfinance.original_flavor import candlestick2_ohlc 
import numpy as np
import os

url = 'https://www.bitstamp.net/api/v2/ticker/{}{}/'
TOKEN = '1281436289:AAFEjqedc7456W1ij2h6gu2f40n37LLT1ks'
#SET-UP

bot = telegram.Bot(token=TOKEN)
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)


#START COMMAND
def start(update, context):
    start_text = '''Hi there, I'm the Crypto Alerts Bot.
    What can I help you with today?

    Here's a list of commands:
    /setalert - sets an alert when a cryptocurrency hits a certain 
                    price
    /graph - gives you a candlestick graph of your selected 
                    cryptocurrency
    '''
    context.bot.send_message(chat_id=update.effective_chat.id, text=start_text)

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)


#SET ALERT SET-UP
cryptocurrency=""
forex=""
up_lim=float()
low_lim=float()

CRYPTO, CURRENCY, UPPER, LOWER = range(4)


#SET ALERT 
def setalert(update,context): 
    reply_keyboard = [['BTC', 'ETH', 'XRP', 'LTC']]
    update.message.reply_text("Send /cancel to stop (before setting your lower limit).\n\n"
                              "What cryptocurrency would you like to track?\n Bitcoin(BTC)\n Ethereum(ETH)\n Ripple(XRP)\n Litecoin(LTC)\n\n Please select from the buttons, thanks!",
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return CRYPTO

def crypto(update,context):
    reply_keyboard = [['USD', 'EUR', 'GBP']]
    global cryptocurrency
    cryptocurrency = update.message.text.lower() 
    update.message.reply_text("In what FOREX currency would you like to track it in?\n US Dollars(USD)\n Euros(EUR)\n Great British Pound(GBP)",
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return CURRENCY

def currency(update,context):
    global forex
    forex = update.message.text.lower()
    update.message.reply_text("Set an upper limit.",
                              reply_markup=ReplyKeyboardRemove())

    return UPPER

def upper(update,context):
    global up_lim
    up_lim=float(update.message.text)
    update.message.reply_text("Set a lower limit.",
                              reply_markup=ReplyKeyboardRemove())
                   
    return LOWER

def lower(update,context):
    global low_lim
    low_lim=float(update.message.text)
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'll get right on that! I'll send a message if the prices cross those limits.")
    while True:
        data = requests.get(url.format(cryptocurrency,forex))
        price=json.loads(data.text)
        if float(price['last'])>up_lim:
            context.bot.send_message(chat_id=update.effective_chat.id, text="The price of 1 {0} is now {1} {2}, higher than your set price of {3} {4}".format(cryptocurrency.upper(), price['last'],forex.upper(),up_lim,forex.upper()))
            break
        elif float(price['last'])<low_lim:
            context.bot.send_message(chat_id=update.effective_chat.id, text="The price of 1 {0} is now {1} {2}, lower than your set price of {3} {4}".format(cryptocurrency.upper(), price['last'],forex.upper(),low_lim,forex.upper()))
            break

        time.sleep(5)
    
    return ConversationHandler.END

def cancel(update, context):
    update.message.reply_text('Alright, hope I can help you with something else.',
                              reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

#ADDING CONVERSATION HANDLER
alert_handler = ConversationHandler(
    entry_points=[CommandHandler('setalert', setalert)],    
    states={
        CRYPTO: [MessageHandler(Filters.regex('^(BTC|ETH|XRP|LTC)$'), crypto)],

        CURRENCY: [MessageHandler(Filters.regex('^(USD|EUR|GBP)$'), currency)],

        UPPER: [MessageHandler(Filters.text & ~Filters.command, upper)],

        LOWER: [MessageHandler(Filters.text & ~Filters.command, lower)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
dispatcher.add_handler(alert_handler)


# GRAPH SET-UP
CRYPTO_GRAPH, CURRENCY_GRAPH, DAYS_GRAPH = range(3)
days_=int()
# GRAPH FUNCTIONS
def graph(update,context):
    reply_keyboard = [['BTC', 'ETH', 'XRP', 'LTC']]
    update.message.reply_text("Send /cancel to stop making a graph.\n\n"
                              "What cryptocurrency would you like to graph?\n Bitcoin(BTC)\n Ethereum(ETH)\n Ripple(XRP)\n Litecoin(LTC)\n\n Please type the symbol, thanks!",
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return CRYPTO_GRAPH

def crypto_graph(update,context):
    reply_keyboard = [['USD', 'EUR', 'GBP']]
    global cryptocurrency
    cryptocurrency = update.message.text 
    update.message.reply_text("In what FOREX currency would you like compare it to?\n US Dollars(USD)\n Euros(EUR)\n Great British Pound(GBP)",
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return CURRENCY_GRAPH

def currency_graph(update,context):
    global forex
    forex = update.message.text
    update.message.reply_text("Set the number of days from today that you want displayed.",
                              reply_markup=ReplyKeyboardRemove())
    return DAYS_GRAPH

def days_graph(update,context):
    global days
    days = int(update.message.text)
    ticker = "{}-{}".format(cryptocurrency,forex)
    
    currpair = yf.Ticker(ticker)
    start_date=(dt.datetime.now() - dt.timedelta(days=days-2)).date() 
    
    df = currpair.history(period = "1d", start=start_date, end = (dt.datetime.now() + dt.timedelta(days=1)).date())
    df.reset_index(inplace=True)

    #change the percentages %m %d %y for the date format.
    df["Date"]= df["Date"].dt.strftime("%m/%d/%y")

    #Candlestick
    fg,ax1 = plt.subplots()

    candlestick2_ohlc(ax = ax1, opens=df['Open'],
                      highs = df['High'], lows = df['Low'], closes = df['Close'], width = 0.4, 
                      colorup = '#77d879', colordown ='#db3f3f')

    ax1.set_xticks(np.arange(len(df)))
    ax1.set_xticklabels(df['Date'], fontsize=7, rotation=-45, color='black') #the fontsize important if data too big, mag overlap yung date.
    ax1.tick_params(axis='y', colors='black')
    plt.title("{} Trend in the Past {} Days".format(cryptocurrency,days))
    plt.ylabel("Price in {}".format(forex))

    ax1.grid(True)
    ax1.set_axisbelow(True)
    
    #save, send, and delete
    plt.savefig("candlestick.png")
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("candlestick.png","rb"))
    os.remove("candlestick.png")

    return ConversationHandler.END

graph_handler = ConversationHandler(
    entry_points=[CommandHandler('graph',graph)],

    states={
        CRYPTO_GRAPH: [MessageHandler(Filters.regex('^(BTC|ETH|XRP|LTC)$'), crypto_graph)],

        CURRENCY_GRAPH: [MessageHandler(Filters.regex('^(USD|EUR|GBP)$'), currency_graph)],

        DAYS_GRAPH: [MessageHandler(Filters.text & ~Filters.command, days_graph)]
    },

    fallbacks=[CommandHandler('cancel', cancel)]
)
dispatcher.add_handler(graph_handler)


#UNKNOWN COMMAND FILTER
def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)

#UNKNOWN MESSAGE FILTER
def unknownmes(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hey, I can't really hold a conversation yet, and I likely never will, but I'm sure you said something nice, so thanks!")

unknownmes_handler = MessageHandler(Filters.text & ~Filters.command, unknownmes)
dispatcher.add_handler(unknownmes_handler)

updater.start_polling()

updater.idle()
