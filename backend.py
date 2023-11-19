import configparser
from datetime import datetime, timedelta
import json
import jwt
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from schema import User, VerificationCode
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schema import Task

app = FastAPI()

env_config = configparser.ConfigParser()
env_config.read("./.env")

DB_URL = env_config.get("DEFAULT", "DB_URL", fallback=None)
AUTHORIZATION_TOKEN_SECRET = env_config.get("DEFAULT", "AUTHORIZATION_TOKEN_SECRET", fallback=None)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[env_config.get("DEFAULT", "FRONTEND_URL_ORIGIN", fallback="http://localhost:3400")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)


@app.post("/api/authorize")
async def authorize(request: Request):
	request_body = await request.body()
	body = json.loads(request_body.decode("utf-8"))

	session = Session()
	verification_code = session.query(VerificationCode).filter_by(value=body["verification_code"]).first()

	# TODO: if verification_code.expires_at < now(): throw error

	if verification_code:
		session.query(VerificationCode).filter(VerificationCode.user_id == verification_code.user_id).delete()

	session.commit()
	session.close()

	if verification_code:
		session.query(VerificationCode).filter(VerificationCode.user_id == verification_code.user_id).delete()
		authorization_token = jwt.encode(
			{
				"user_id": verification_code.user_id,
				"expires_at": str(datetime.now() + timedelta(days=10)) # TODO: Use ISO
			},
			AUTHORIZATION_TOKEN_SECRET,
			algorithm="HS256"
		)
		return {"authorization_token": authorization_token}
	else:
		return {"error": "Invalid verification code"}


@app.get("/api/me")
def me(request: Request):
	authorization_token = request.headers.get('Authorization')

	try:
		decoded_data = jwt.decode(authorization_token, AUTHORIZATION_TOKEN_SECRET, algorithms=["HS256"])
	except:
		return {"error": "Invalid authorization token"}

	expires_at = datetime.strptime(decoded_data['expires_at'], "%Y-%m-%d %H:%M:%S.%f")
	if expires_at < datetime.now():
		return {"error": "Authorization token expired"}

	session = Session()
	user = session.query(User).filter_by(id=decoded_data["user_id"]).first()

	response_body = {"user_id": user.id}

	session.commit()
	session.close()

	if not user:
		return {"error": f"User with id {decoded_data['user_id']} not found"}

	return response_body


@app.get("/api/tasks")
def tasks(request: Request):
	authorization_token = request.headers.get('Authorization')

	try:
		decoded_data = jwt.decode(authorization_token, AUTHORIZATION_TOKEN_SECRET, algorithms=["HS256"])
	except:
		return {"error": "Invalid authorization token"}

	expires_at = datetime.strptime(decoded_data['expires_at'], "%Y-%m-%d %H:%M:%S.%f")
	if expires_at < datetime.now():
		return {"error": "Authorization token expired"}

	session = Session()
	user = session.query(User).filter_by(id=decoded_data["user_id"]).first()
	
	if not user:
		session.commit()
		session.close()
		return {"error": f"User with id {decoded_data['user_id']} not found"}

	response_body = jsonable_encoder(user.tasks)

	session.commit()
	session.close()

	return response_body


@app.post("/api/tasks")
async def create_task(request: Request):
	authorization_token = request.headers.get('Authorization')

	try:
		decoded_data = jwt.decode(authorization_token, AUTHORIZATION_TOKEN_SECRET, algorithms=["HS256"])
	except:
		return {"error": "Invalid authorization token"}

	expires_at = datetime.strptime(decoded_data['expires_at'], "%Y-%m-%d %H:%M:%S.%f")
	if expires_at < datetime.now():
		return {"error": "Authorization token expired"}

	session = Session()
	user = session.query(User).filter_by(id=decoded_data["user_id"]).first()

	if not user:
		session.commit()
		session.close()
		return {"error": f"User with id {decoded_data['user_id']} not found"}

	request_body = await request.json()

	new_task = Task(user_id=user.id, title=request_body["title"])

	session.add(new_task)
	session.commit()
	session.flush()
	session.refresh(new_task)

	response_body = jsonable_encoder(new_task)

	session.close()

	return response_body


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int, request: Request):
	print("task_id")
	print(task_id)

	authorization_token = request.headers.get('Authorization')

	try:
		decoded_data = jwt.decode(authorization_token, AUTHORIZATION_TOKEN_SECRET, algorithms=["HS256"])
	except:
		return {"error": "Invalid authorization token"}

	expires_at = datetime.strptime(decoded_data['expires_at'], "%Y-%m-%d %H:%M:%S.%f")
	if expires_at < datetime.now():
		return {"error": "Authorization token expired"}

	session = Session()
	user = session.query(User).filter_by(id=decoded_data["user_id"]).first()

	if not user:
		session.commit()
		session.close()
		return {"error": f"User with id {decoded_data['user_id']} not found"}

	task = session.query(Task).filter_by(id=task_id).first()

	if not task:
		session.commit()
		session.close()
		return {"error": f"Task with ID {task_id} is not found"}

	if user.id != task.user_id:
		session.commit()
		session.close()
		return {"error": f"You don't have access to task with ID {task_id}"}

	response_body = jsonable_encoder(task)

	session.delete(task)
	session.commit()
	session.close()

	return response_body
