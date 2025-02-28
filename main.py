from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException, status, Cookie
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import json
import logging
from pydantic import BaseModel

from auth import (
    get_current_user,
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    oauth2_scheme,
    get_token_from_cookie,
    get_password_hash,
)
from database import get_db_connection

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount static files and initialize templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Add CORS middleware if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# WebSocket Connection Manager
# ---------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[dict] = []

    async def connect(self, websocket: WebSocket, client_id: int, name: str):
        await websocket.accept()
        self.active_connections.append({"websocket": websocket, "client_id": client_id, "name": name})

    def disconnect(self, websocket: WebSocket):
        self.active_connections = [conn for conn in self.active_connections if conn["websocket"] != websocket]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, sender: str = "system"):
        for conn in self.active_connections:
            await conn["websocket"].send_text(json.dumps({"message": message, "sender": sender}))

    async def send_user_list(self, websocket: WebSocket):
        users = [{"id": conn["client_id"], "name": conn["name"]} for conn in self.active_connections]
        await websocket.send_text(json.dumps({"type": "user_list", "users": users}))

    async def send_private_message(self, sender_id: int, recipient_id: int, message: str):
        sender_name = None
        for conn in self.active_connections:
            if conn["client_id"] == sender_id:
                sender_name = conn["name"]
                break
        if sender_name is None:
            sender_name = "unknown"
        for conn in self.active_connections:
            if conn["client_id"] == recipient_id:
                await conn["websocket"].send_text(json.dumps({
                    "type": "private_message",
                    "sender": sender_name,
                    "message": message
                }))
                break

manager = ConnectionManager()

# ---------------------------
# Authentication Endpoints
# ---------------------------
@app.post("/token", response_model=dict)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    logger.debug(f"Access token created: {access_token}")
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get("/", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def get_chat(request: Request, token: str = Depends(get_token_from_cookie)):
    logger.debug(f"Token received in /chat endpoint: {token}")
    current_user = await get_current_user(token)
    logger.debug(f"Current user: {current_user}")
    return templates.TemplateResponse("chat.html", {"request": request, "user": current_user})

@app.get("/register", response_class=HTMLResponse)
async def get_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: str

@app.post("/register", response_model=dict)
async def register_user(user: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = get_password_hash(user.password)
    try:
        cursor.execute("""
            INSERT INTO users (username, hashed_password, full_name, email)
            VALUES (?, ?, ?, ?)
        """, (user.username, hashed_password, user.full_name, user.email))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already registered")
    finally:
        conn.close()
    return {"message": "User registered successfully"}

@app.get("/profile", response_class=HTMLResponse)
async def get_profile(request: Request, token: str = Depends(get_token_from_cookie)):
    current_user = await get_current_user(token)
    return templates.TemplateResponse("profile.html", {"request": request, "user": current_user})

class UserUpdate(BaseModel):
    full_name: str
    email: str

@app.post("/profile", response_model=dict)
async def update_profile(user_update: UserUpdate, token: str = Depends(get_token_from_cookie)):
    current_user = await get_current_user(token)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET full_name = ?, email = ?
        WHERE id = ?
    """, (user_update.full_name, user_update.email, current_user["id"]))
    conn.commit()
    conn.close()
    return {"message": "Profile updated successfully"}

@app.get("/messages", response_model=list)
async def get_messages(token: str = Depends(get_token_from_cookie)):
    current_user = await get_current_user(token)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, sender_id, message, timestamp, NULL AS recipient_id FROM public_messages
        UNION
        SELECT id, sender_id, message, timestamp, recipient_id FROM private_messages WHERE sender_id = ? OR recipient_id = ?
        ORDER BY timestamp DESC
    """, (current_user["id"], current_user["id"]))
    messages = cursor.fetchall()
    conn.close()
    
    # Convertir les objets sqlite3.Row en dictionnaires
    messages_dict = [dict(message) for message in messages]
    
    return messages_dict


# ---------------------------
# WebSocket Endpoint
# ---------------------------
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    token = websocket.cookies.get("access_token")
    if not token:
        await websocket.close(code=1008)
        return
    try:
        user = await get_current_user(token)
    except HTTPException:
        await websocket.close(code=1008)
        return

    query_params = websocket.query_params
    name = query_params.get("name", f"Client #{client_id}")

    await manager.connect(websocket, client_id, name)
    await manager.broadcast(f"{name} joined the chat")
    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)
            if data["type"] == "public_message":
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO public_messages (sender_id, message) VALUES (?, ?)",
                    (user["id"], data["message"])
                )
                conn.commit()
                conn.close()

                await manager.send_personal_message(
                    json.dumps({"message": f"You wrote: {data['message']}", "sender": "you"}),
                    websocket,
                )
                await manager.broadcast(f"{name} says: {data['message']}", sender=name)
            elif data["type"] == "get_user_list":
                await manager.send_user_list(websocket)
            elif data["type"] == "typing":
                for conn in manager.active_connections:
                    if conn["websocket"] != websocket:
                        await conn["websocket"].send_text(json.dumps({"type": "typing", "sender": name}))
            elif data["type"] == "stop_typing":
                for conn in manager.active_connections:
                    if conn["websocket"] != websocket:
                        await conn["websocket"].send_text(json.dumps({"type": "stop_typing", "sender": name}))
            elif data["type"] == "read_receipt":
                original_sender = data.get("original_sender")
                for conn in manager.active_connections:
                    if conn["name"] == original_sender:
                        await conn["websocket"].send_text(json.dumps({
                            "type": "read_receipt",
                            "reader": name,
                            "message": data.get("message", "")
                        }))
                        break
            elif data["type"] == "private_message":
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO private_messages (sender_id, recipient_id, message) VALUES (?, ?, ?)",
                    (user["id"], data["recipient_id"], data["message"])
                )
                conn.commit()
                conn.close()

                await manager.send_private_message(client_id, data["recipient_id"], data["message"])
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"{name} left the chat")
