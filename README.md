```
docker build --file ./Dockerfile.dev --tag todorush_backend .
docker run -it --name todorush_backend -v .:/app todorush_backend
docker start -i todorush_backend

docker stop todorush_backend && docker rm todorush_backend && docker rmi todorush_backend
```
