```
docker create --name todorush_database --publish 5432:5432 --volume .:/app --env POSTGRES_HOST_AUTH_METHOD=trust postgres:15.3
docker start -i todorush_database

docker stop todorush_database && docker rm todorush_database


docker build --file ./Dockerfile.telegram_bot.dev --tag todorush_telegram_bot .
docker create --name todorush_telegram_bot --volume .:/app todorush_telegram_bot
docker start -i todorush_telegram_bot

docker stop todorush_telegram_bot && docker rm todorush_telegram_bot && docker rmi todorush-server-telegram_bot

alembic revision --autogenerate -m "Added user table"
alembic upgrade head
```
