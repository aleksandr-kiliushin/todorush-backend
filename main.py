import random
from datetime import datetime, timedelta
import configparser
import string
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, ConversationHandler, filters
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import User, Task, VerificationCode

env_config = configparser.ConfigParser()
env_config.read("./.env")

db_url = env_config.get("DEFAULT", "DB_URL", fallback=None)
telegram_bot_api_key = env_config.get("DEFAULT", "TELEGRAM_BOT_API_KEY", fallback=None)
frontend_authorization_url = env_config.get("DEFAULT", "FRONTEND_URL_ORIGIN", fallback=None)


engine = create_engine(db_url)
Session = sessionmaker(bind=engine)


def generate_random_string(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    random_string = "".join(random.choice(characters) for _ in range(length))
    return random_string


async def verification_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_user_id = update.effective_user.id  # TODO: Rename to telegram_user_id
    session = Session()

    telegram_user = session.query(User).filter_by(telegram_id=telegram_user_id).first()

    if not telegram_user:
        await update.message.reply_text("You are not registered")
        session.close()
        return

    random_string = generate_random_string(50)
    verification_code = VerificationCode(
        user=telegram_user, value=str(random_string), expires_at=datetime.now() + timedelta(minutes=2)
    )

    session.add(verification_code)
    session.commit()

    await update.message.reply_text(f"Your code will be expired in 2 minutes")
    await update.message.reply_text(verification_code.value)

    session.close()


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_user_id = update.effective_user.id
    session = Session()

    telegram_user = session.query(User).filter_by(telegram_id=telegram_user_id).first()

    if telegram_user:
        message = f"Welcome back. telegram_first_name: {update.effective_user.first_name}, DB id: {telegram_user.id}, telegram_id: {telegram_user.telegram_id}"
    else:
        new_user = User(telegram_id=telegram_user_id)
        session.add(new_user)
        session.commit()
        message = f"You just created an account. telegram_first_name: {update.effective_user.first_name}, DB id: {new_user.id}, telegram_id: {new_user.telegram_id}"

    await update.message.reply_text(message)

    session.close()


async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    session = Session()

    telegram_user = session.query(User).filter_by(telegram_id=user_id).first()

    if not telegram_user:
        await update.message.reply_text("You are not registered")
        session.close()
        return

    message = ""
    for task in telegram_user.tasks:
        message += f"\n#{task.id}: {task.title}"
    await update.message.reply_text(message or "You don't have tasks")

    session.close()


# Define states for the conversation
TASK_TITLE = 0


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Check if the user is registered
    user_id = update.effective_user.id
    session = Session()
    telegram_user = session.query(User).filter_by(telegram_id=user_id).first()

    if not telegram_user:
        await update.message.reply_text("You are not registered")
        session.close()
        return

    # Start the conversation
    await update.message.reply_text("Task title:")
    context.user_data["user_id"] = user_id
    return TASK_TITLE


async def get_task_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Retrieve the task title from user input
    task_title = update.message.text

    # Save the task title in the context for later use
    context.user_data["task_title"] = task_title

    # You can prompt the user for more information if needed, or proceed to the next step

    # Example: Prompt for task description
    # await update.message.reply_text("Please enter the description of the task:")
    # return TASK_DESCRIPTION

    # If no further information is needed, you can proceed to save the task
    return await save_task(update, context)


async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Retrieve user data from context
    user_id = context.user_data["user_id"]
    task_title = context.user_data["task_title"]

    # Create a new task in the database
    session = Session()
    existing_user = session.query(User).filter_by(telegram_id=user_id).first()
    new_task = Task(user=existing_user, title=task_title)
    session.add(new_task)
    session.commit()

    # Provide feedback to the user
    await update.message.reply_text(f'Task "{task_title}" added successfully!')

    # Cleanup and close the session
    session.close()

    # End the conversation
    return ConversationHandler.END


# Add the conversation handler to your application
conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("add", add)],
    states={
        TASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_task_title)],
        # Add more states if needed for additional information
    },
    fallbacks=[],
)


DELETE_TASK_ID = 1


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Check if the user is registered
    telegram_user_id = update.effective_user.id
    session = Session()
    telegram_user = session.query(User).filter_by(telegram_id=telegram_user_id).first()

    if not telegram_user:
        await update.message.reply_text("You are not registered")
        session.close()
        return

    # Fetch and display the user's tasks for deletion
    message = "Select a task to delete:"
    for task in telegram_user.tasks:
        message += f"\n#{task.id}: {task.title}"
    await update.message.reply_text(message)

    # Set the user ID in the context for later use
    context.user_data["user_id"] = telegram_user_id

    # Move to the next state for deleting a task
    return DELETE_TASK_ID


async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Retrieve user data from context
    telegram_user_id = context.user_data["user_id"]

    # Retrieve the task ID to delete from user input
    task_id = update.message.text

    # Retrieve the task from the database
    session = Session()
    existing_user = session.query(User).filter_by(telegram_id=telegram_user_id).first()
    task_to_delete = session.query(Task).filter_by(id=task_id, user=existing_user).first()

    if task_to_delete:
        # Delete the task from the database
        session.delete(task_to_delete)
        session.commit()
        await update.message.reply_text(f"Task #{task_id} deleted successfully!")
    else:
        await update.message.reply_text(f"Task #{task_id} not found or does not belong to you.")

    # Cleanup and close the session
    session.close()

    # End the conversation
    return ConversationHandler.END


# Add the conversation handler for deleting tasks
delete_task_handler = ConversationHandler(
    entry_points=[CommandHandler("delete", delete)],
    states={
        DELETE_TASK_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_task)],
    },
    fallbacks=[],
)


app = ApplicationBuilder().token(telegram_bot_api_key).build()
app.add_handler(CommandHandler("verification_code", verification_code))
app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("tasks", tasks))
app.add_handler(conversation_handler)
app.add_handler(delete_task_handler)
app.run_polling()
