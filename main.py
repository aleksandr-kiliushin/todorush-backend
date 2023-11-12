import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from os.path import join, dirname
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import User

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


db_url = os.getenv('DB_URL')
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)

# Update the hello function to interact with the database
async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    session = Session()

    existing_user = session.query(User).filter_by(telegram_id=user_id).first()

    if existing_user:
        message = f'Welcome back. telegram_first_name: {update.effective_user.first_name}, DB id: {existing_user.id}, telegram_id: {existing_user.telegram_id}'
    else:
        new_user = User(telegram_id=user_id)
        session.add(new_user)
        session.commit()
        message = f'You just created an account. telegram_first_name: {update.effective_user.first_name}, DB id: {new_user.id}, telegram_id: {new_user.telegram_id}'

    await update.message.reply_text(message)

    session.close()

app = ApplicationBuilder().token(os.getenv('TELEGRAM_BOT_API_KEY')).build()
app.add_handler(CommandHandler("hello", hello))
app.run_polling()
