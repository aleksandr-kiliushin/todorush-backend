```
docker build --file ./telegram_bot/Dockerfile.dev --tag todorush_telegram_bot .
docker create -it --name todorush_telegram_bot --volume ./telegram_bot:/app todorush_telegram_bot
docker start -i todorush_telegram_bot

docker stop todorush_telegram_bot && docker rm todorush_telegram_bot && docker rmi todorush_telegram_bot
```
