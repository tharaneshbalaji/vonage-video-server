# Vonage Video Server

A professional video conferencing application built with **FastAPI** and **Streamlit**, powered by the **Vonage Video API** (formerly OpenTok/TokBox). This project provides a complete solution for creating and joining video meetings with real-time communication capabilities.

## 🎥 Features

- **Create New Video Sessions**: Generate new meeting rooms with unique session IDs
- **Join Existing Sessions**: Connect to meetings using session IDs
- **Real-time Video & Audio**: HD video calling with audio support
- **Screen Sharing**: Share your screen during meetings
- **Multi-user Support**: Multiple participants can join the same session
- **Cross-platform**: Works on desktop and mobile browsers
- **RESTful API**: FastAPI backend with comprehensive endpoints
- **Interactive Web UI**: Streamlit-powered frontend for easy usage
- **Health Monitoring**: Built-in health checks and logging

## 🏗️ Architecture

### Backend (FastAPI)

- **`server.py`**: Main FastAPI application serving the video API
- RESTful endpoints for session management and token generation
- Vonage Video API integration
- CORS middleware for cross-origin requests
- Comprehensive logging and error handling

### Frontend (Streamlit)

- **`app.py`**: Interactive web interface for video meetings
- Create or join meeting functionality
- Real-time video embedding with HTML5/JavaScript
- User-friendly controls and session management

## 📋 Prerequisites

- Python 3.8+
- Vonage Video API Account
- Modern web browser with WebRTC support

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd vonage-video-server
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Setup

Create a `.env` file in the project root with your Vonage credentials:

```env
VONAGE_API_KEY=your_api_key
VONAGE_API_SECRET=your_api_secret
VONAGE_APPLICATION_ID=your_application_id
VONAGE_PRIVATE_KEY_PATH=/path/to/your/private.key
```

### 4. Start the Backend Server

```bash
python server.py
```

The FastAPI server will start on `http://127.0.0.1:5000`

### 5. Launch the Frontend

In a new terminal:

```bash
streamlit run app.py
```

The Streamlit app will open in your browser (typically `http://localhost:8501`)

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `VONAGE_API_KEY` | Your Vonage API key | Yes |
| `VONAGE_API_SECRET` | Your Vonage API secret | Yes |
| `VONAGE_APPLICATION_ID` | Your Vonage application ID | Yes |
| `VONAGE_PRIVATE_KEY_PATH` | Path to your private key file | Yes |
| `SERVER_HOST` | Backend server host (default: 127.0.0.1) | No |
| `SERVER_PORT` | Backend server port (default: 5000) | No |

### Vonage Video API Setup

1. Sign up at [Vonage Developer Dashboard](https://dashboard.nexmo.com/)
2. Create a new Video API application
3. Generate and download your private key
4. Copy your API credentials to the `.env` file

## 📚 API Documentation

### Base URL

```text
http://127.0.0.1:5000/api
```

### Endpoints

#### Create New Session

```http
POST /api/sessions/create
```

Creates a new video session and returns session details.

**Response:**

```json
{
  "session_id": "string",
  "api_key": "string",
  "application_id": "string",
  "created_at": "2024-01-01T00:00:00"
}
```

#### Get Session Info

```http
GET /api/sessions/{session_id}
```

Validates and returns information about an existing session.

#### Generate User Token

```http
GET /api/tokens/generate?username={username}&session_id={session_id}&role={role}
```

Generates an access token for a user to join a video session.

**Parameters:**

- `username` (optional): User's display name
- `session_id` (optional): Target session ID
- `role` (optional): User role (publisher/subscriber)

#### Health Check

```http
GET /api/health
```

Returns application health status and environment information.

### Interactive API Documentation

- Swagger UI: `http://127.0.0.1:5000/api/docs`
- ReDoc: `http://127.0.0.1:5000/api/redoc`

## 🎮 Usage

### Creating a Meeting

1. Open the Streamlit app
2. Select "Create New Meeting"
3. Enter your name
4. Click "🚀 Start Meeting"
5. Share the generated Session ID with participants

### Joining a Meeting

1. Get the Session ID from the meeting creator
2. Select "Join Existing Meeting"
3. Enter the Session ID and your name
4. Click "🔗 Join Meeting"

### During the Meeting

- **Camera**: Toggle video on/off
- **Microphone**: Mute/unmute audio
- **Screen Share**: Share your screen
- **Leave**: Exit the meeting

## 🔍 Testing

### Backend Health Check

Test if the FastAPI server is running:

```bash
curl http://127.0.0.1:5000/api/health
```

### Multi-user Testing

1. Open multiple browser tabs/windows
2. Join the same session with different usernames
3. Test video, audio, and screen sharing features

## 📁 Project Structure

```text
vonage-video-server/
│
├── app.py                 # Streamlit frontend application
├── server.py             # FastAPI backend server
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables (create this)
├── private.key          # Vonage private key file
├── README.md            # This file
└── vonage_video.log     # Application logs (generated)
```

## 🛠️ Development

### Running in Development Mode

```bash
# Backend with auto-reload
uvicorn server:video_api_app --host 127.0.0.1 --port 5000 --reload

# Frontend with auto-reload (Streamlit runs with auto-reload by default)
streamlit run app.py
```

### Adding New Features

1. Backend changes: Modify `server.py` and add new endpoints
2. Frontend changes: Update `app.py` for UI modifications
3. Dependencies: Add new packages to `requirements.txt`

## 📊 Logging

The application includes comprehensive logging:

- Console output for real-time monitoring
- File logging to `vonage_video.log`
- Structured log format with timestamps and levels

## 🐛 Troubleshooting

### Common Issues

#### Backend Connection Failed

- Ensure FastAPI server is running on the correct port
- Check firewall settings
- Verify the backend URL in Streamlit sidebar

#### Session Creation Failed

- Verify Vonage API credentials in `.env`
- Check internet connection
- Ensure private key file exists and is accessible

#### Video Not Loading

- Check browser WebRTC support
- Allow camera and microphone permissions
- Try a different browser (Chrome/Firefox recommended)

#### Token Generation Failed

- Validate session ID exists
- Check Vonage application configuration
- Review server logs for detailed error messages

### Getting Help

1. Check the application logs (`vonage_video.log`)
2. Test the health endpoint (`/api/health`)
3. Verify environment configuration
4. Check Vonage Developer Dashboard for API status

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🔗 Links

- [Vonage Video API Documentation](https://developer.vonage.com/en/video/overview)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)

---