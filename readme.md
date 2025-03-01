# FastAPI Dockerized Chat Application

This project is a **Dockerized FastAPI application** that provides a real-time chat system with WebSocket support. It includes a SQLite database for storing user data and chat messages, designed for easy deployment and development using Docker.

## Features

- **Real-time Chat**: WebSocket connections enable instant messaging.
- **User Authentication**: JWT-based authentication for registration, login, and logout.
- **Private Messaging**: Direct messaging between users.
- **Typing Indicators**: Displays when a user is typing.
- **Message History**: Load past messages from the database.
- **User List**: Shows currently connected users.
- **Dockerized**: Simplified setup with Docker.
- **Scalable & Extensible**: Easily deployable with additional features.

---

## Prerequisites

Ensure you have the following installed before running the project:

- **[Docker](https://docs.docker.com/get-docker/)**
- **[Docker Compose](https://docs.docker.com/compose/install/)**

---

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Build and Run the Application with Docker Compose

Run the following command:

```bash
docker-compose up --build
```

This will:

- Build the Docker image for the FastAPI application.
- Run the `entrypoint.sh` script to:
  - Activate the virtual environment.
  - Initialize the SQLite database.
  - Seed the database with initial data.
  - Start the FastAPI application using Uvicorn.

### 3. Access the Application

- **FastAPI Application**: [http://localhost:8000](http://localhost:8000)
- **Swagger UI (API Docs)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc (Alternative API Docs)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Usage

### Sample Users

```json
[
  {
    "username": "user1",
    "password": "password1",
    "full_name": "User One",
    "email": "user1@example.com"
  },
  {
    "username": "user2",
    "password": "password2",
    "full_name": "User Two",
    "email": "user2@example.com"
  },
  {
    "username": "user3",
    "password": "password3",
    "full_name": "User Three",
    "email": "user3@example.com"
  },
  {
    "username": "user4",
    "password": "password4",
    "full_name": "User Four",
    "email": "user4@example.com"
  }
]
```

### Register a New User

1. Go to [http://localhost:8000/register](http://localhost:8000/register).
2. Fill in the registration form (username, password, full name, and email).
3. Click **Register** to create an account.

### Log In

1. Navigate to [http://localhost:8000](http://localhost:8000).
2. Enter your username and password.
3. Click **Login** to authenticate and access the chat.

### Chat Interface

- **Send Messages**: Type a message and press **Send**.
- **Private Messages**: Click a user's name in the user list to send a private message.
- **Typing Indicators**: Displays when another user is typing.
- **Load Message History**: Click **Load Message History** to view past messages.

### Log Out

Click the **Logout** button in the navigation bar to sign out.

---

## API Endpoints

### Authentication

- `POST /token` - Log in and receive a JWT token.
- `POST /logout` - Log out and invalidate the JWT token.
- `POST /register` - Register a new user.

### Chat

- `GET /chat` - Render the chat interface.
- `GET /messages` - Retrieve message history.
- `WS /ws/{client_id}` - WebSocket endpoint for real-time chat.

### Profile

- `GET /profile` - View user profile.
- `POST /profile` - Update user profile information.

---

## Database Schema

The SQLite database consists of the following tables:

### `users`

- `id` - Unique user ID.
- `username` - User's username.
- `hashed_password` - Encrypted password.
- `full_name` - User's full name.
- `email` - User's email address.

### `public_messages`

- `id` - Unique message ID.
- `sender_id` - User ID of the sender.
- `message` - Content of the message.
- `timestamp` - Time when the message was sent.

### `private_messages`

- `id` - Unique message ID.
- `sender_id` - User ID of the sender.
- `recipient_id` - User ID of the recipient.
- `message` - Content of the message.
- `timestamp` - Time when the message was sent.

---

## Customization

### Environment Variables

Modify the following environment variables in `docker-compose.yml` as needed:

- `DATABASE_URL` - Database connection URL (default: `sqlite:///./chat.db`).
- `SECRET_KEY` - Secret key for JWT token generation.
- `ACCESS_TOKEN_EXPIRE_MINUTES` - JWT token expiration time (default: 30 minutes).

---

## Troubleshooting

### Common Issues

#### 1. Docker Compose Fails to Start

- Ensure Docker and Docker Compose are installed.
- Check for port conflicts (e.g., port 8000 in use).

#### 2. Database Not Initialized

- Ensure `entrypoint.sh` has execute permissions:
  ```bash
  chmod +x entrypoint.sh
  ```
- Check Docker logs for database initialization errors.

#### 3. WebSocket Connection Issues

- Verify that the WebSocket URL in the frontend matches the backend (`ws://localhost:8000/ws/{client_id}`).

---

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.

## Acknowledgments

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern, high-performance web framework.
- **[Docker](https://www.docker.com/)** - Simplified containerization.
- **[Uvicorn](https://www.uvicorn.org/)** - ASGI server for FastAPI.

---

**Contributions are welcome!** Feel free to open issues or submit pull requests. 🚀
