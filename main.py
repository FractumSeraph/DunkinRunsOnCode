# Python program to automatically complete dunkin donuts surveys.
# -FractumSeraph

import logging  # Used to make log messages
import os
from datetime import date
from time import sleep  # Used for sleep()
import gspread  # Used to interface with Google Sheets
from configparser import ConfigParser  # Used for settings

# Imports for web automation
import splinter
from selenium.webdriver.chrome.service import Service
from splinter.exceptions import DriverNotFoundError
from webdriver_manager.chrome import ChromeDriverManager

# python-telegram-bot
import telegram
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters

botfathercode = os.environ['BOTFATHERCODE']  # TODO Move to config
storecode = os.environ['STORECODE']  # TODO Move to config

updater = Updater(botfathercode, use_context=True)
dispatcher = updater.dispatcher
bot = telegram.Bot(botfathercode)

logging.basicConfig(
    level=logging.INFO,  # Debug, Info, Warning, Error, Critical
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)


def start():
    logging.info("Beginning of start function.")
    exampleCode = "839035018005092727"

    # Read configuration
    # Accept input
    # Sanitize
    # Extract info and save to DB
    readConfig()
    # submitSurvey(sanitize(exampleCode))

    gc = gspread.service_account()
    sh = gc.open("DunkinCodes")
    print(sh.worksheet("Scores").cell(1, 3).value)  # Cell(Number, Letter)


def readConfig():
    #  TODO Add google sheet key to config
    logging.info("Beginning of readConfig function.")
    # Create configuration file
    config = ConfigParser()
    config.read('config.ini')
    with open('config.ini', 'w') as f:
        config.write(f)

    # If a setting for sheet key does not exist, set it to 0000
    if not config.has_option('Google', "SheetKey"):
        config.set('Google', "SheetKey", "0000")

        # Save changes to config.
        with open('config.ini', 'w') as f:
            config.write(f)


def sanitize(unsanitizedCode):
    logging.info("Beginning of sanitize function.")
    unsanitizedCode = unsanitizedCode.strip()  # remove any spaces and newlines
    unsanitizedCode = unsanitizedCode.replace('-', '')  # remove "-"s
    if len(unsanitizedCode) != 18:
        logging.warning(
            "Survey code should be 18 numbers long, that one was " + str(len(unsanitizedCode)) + ". Ignoring")
        return ""
    if unsanitizedCode[5:10] != str(storecode):
        logging.warning("Survey code doesn't contain " + storecode +
                        " in the correct place, instead we found " +
                        unsanitizedCode[5:10] + " Ignoring.")
        return ""
    sanitizedCode = unsanitizedCode
    return sanitizedCode


service = Service(ChromeDriverManager().install())
browser = splinter.Browser('chrome', headless=True)


# browser = splinter.Browser('chrome')


def submitSurvey(codeToSubmit, user):
    logging.info("Beginning of submitSurvey function")
    try:
        logging.info("Running browser.visit")
        browser.visit('http://dunkinrunsonyou.com/')
        sleep(5)
        logging.info("Browser.get complete.")
        browser.fill('spl_q_inrest_rcpt_code_txt', codeToSubmit)
        browser.find_by_name('forward_main-pager').click()
        sleep(5)
        browser.find_by_id("onf_q_inrest_recommend_ltr_11").click()
        browser.find_by_id("onf_q_inrest_recent_experience_osat_5").click()
        browser.fill('spl_q_inrest_score_cmt', user)
        browser.find_by_id("buttonNext").click()
        sleep(2)
        browser.find_by_id("onf_q_inrest_speed_of_service_osat_5").click()
        browser.find_by_id("onf_q_inrest_appearence_of_the_restraunt_osat_5").click()
        browser.find_by_id("onf_q_inrest_taste_of_food_osat_5").click()
        browser.find_by_id("onf_q_inrest_friendliness_of_staff_osat_5").click()
        browser.find_by_id("onf_q_inrest_order_fulffiled_yn_1").click()
        browser.find_by_id("onf_q_inrest_visit_experience_yn_2").click()
        sleep(5)
        browser.find_by_id("buttonNext").click()
        sleep(5)
        browser.fill("spl_q_inrest_email_address_txt", """dunkincode@harakirimail.com""")
        sleep(1)
        browser.find_by_id("onf_q_inrest_rcpt_additional_questions_alt_2").click()
        sleep(1)
        browser.find_by_id("buttonNext").click()
    except DriverNotFoundError:
        logging.error("Webdriver not found exception!")
        pass
    except Exception as e:
        logging.error("submit_survey has encountered an exception! Passing." + "\n" + str(e))
        pass
    logging.info("Survey " + codeToSubmit + " is complete.")


def addCodes(update: Update, context: CallbackContext):
    logging.debug("add_to_list has been called by " + str(update.message.from_user.id))
    user = update.message.from_user
    logging.info("Conversation started with " + str(user.username) + " " + str(user.id))
    index: int
    for index, line in enumerate(context.args):
        line = line + " "
        sanitized_code = sanitize(line)
        if sanitized_code != "":
            submitSurvey(str(sanitized_code), str(user.first_name))
            update.message.reply_text(
                "Code " + sanitized_code + " was completed! " + "Waiting 20 minutes.")
            sleep(1200)
            # TODO Add code to sheets
        else:
            update.message.reply_text("Failed!")
            continue
        logging.info(str(user.id) + " has successfully completed code " + str(sanitized_code))
        update.message.reply_text(str(user.id) + " has successfully completed code " + str(sanitized_code))


def tgstart(update: Update):
    update.message.reply_text(
        "Welcome to the Dunkin Donuts Survey Completer bot! Send /help to get started.")
    logging.info("/start has been called by " + str(update.message.from_user.id))


def tghelp(update: Update):
    update.message.reply_text(
        "Use the /addcodes command to submit surveys. For example \n /addcodes 012345678901234567 \n Use the /score "
        "command to show the scoreboard.")
    logging.info("/help has been called by " + str(update.message.from_user.id))


def unknown_text(update: Update):
    update.message.reply_text("Sorry I can't recognize you , you said '%s'" % update.message.text)


def tgscore(update: Update):
    logging.info("/score has been called by " + str(update.message.from_user.id))
    user = update.message.from_user
    today = date.today()
    logging.info(str(user.id) + " " + str(user.username) + " has requested the scoreboard.")
    update.message.reply_text(
        "Sorry, the score system is currently down while I rebuild the bot from scratch." % update.message.text)


def tgunknown(update: Update):
    update.message.reply_text(
        "Sorry '%s' is not a valid command" % update.message.text)
    logging.info("An unknown command has been called by " + str(update.message.from_user.id))


updater.dispatcher.add_handler(CommandHandler('start', tgstart))
updater.dispatcher.add_handler(CommandHandler('help', tghelp))
updater.dispatcher.add_handler(CommandHandler('addcodes', addCodes, pass_args=True))
updater.dispatcher.add_handler(CommandHandler('score', tgscore))
updater.dispatcher.add_handler(MessageHandler(Filters.text, tgunknown))
updater.dispatcher.add_handler(MessageHandler(
    # Filters out unknown commands
    Filters.command, tgunknown))

logging.info("Updater is polling")
updater.start_polling()

if __name__ == '__main__':
    start()