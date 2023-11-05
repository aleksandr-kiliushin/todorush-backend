```
docker build --file ./backend/Dockerfile.dev --tag todorush_backend .
docker run -it --name todorush_backend --publish 8000:8000 --volume ./backend:/app todorush_backend
docker start -i todorush_backend

docker stop todorush_backend && docker rm todorush_backend && docker rmi todorush_backend
```
