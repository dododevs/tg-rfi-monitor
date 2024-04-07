from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler

import os
from dotenv import load_dotenv
load_dotenv()

import rfi
from persistence import Session, get_session

async def departures(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  session: Session = get_session(update.effective_user.id)
  session.request_departures()
  return await update.message.reply_text(
    "Cerca il nome della stazione di cui vuoi visualizzare il tabellone orario. Digita almeno 3 caratteri."
  )

async def arrivals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  session: Session = get_session(update.effective_user.id)
  session.request_arrivals()
  return await update.message.reply_text(
    "Cerca il nome della stazione di cui vuoi visualizzare il tabellone orario. Digita almeno 3 caratteri."
  )

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  query = update.message.text.lower()
  if len(query) < 3:
    return
  session: Session = get_session(update.effective_user.id)
  if session.requested_departures or session.request_arrivals:
    stations = await rfi.get_stations()
    results = [station for station in stations if query in station.name.lower()]
    if not results:
      return await update.message.reply_text("Nessuna stazione trovata.")
    session.reset_selections()
    session.save()

    return await update.message.reply_text(
      "Scegli una stazione per visualizzare il tabellone orario.",
      reply_markup=InlineKeyboardMarkup(
        [[
          InlineKeyboardButton(
            text=station.name,
            web_app=WebAppInfo(f"https://rfi-monitor-webapp.web.app/monitor.html?station={station._id}&direction={'departures' if session.request_departures else 'arrivals'}")
          )
        ] for station in results]
      )
    )

app = Application.builder().token(os.environ["TELEGRAM_BOT_API_KEY"]).build()
app.add_handler(CommandHandler("departures", departures))
app.add_handler(CommandHandler("arrivals", arrivals))
app.add_handler(MessageHandler(None, message))
app.run_polling(allowed_updates=Update.ALL_TYPES)