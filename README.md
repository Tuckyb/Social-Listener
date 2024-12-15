# Social Media Marketing Insights Tool

A comprehensive web application that analyzes social media comments to generate actionable marketing intelligence.

## Features

- YouTube comments extraction and analysis
- Think/Feel/Act categorization
- Pain points analysis
- Future content topics discovery
- Language alignment tracking
- Sentiment analysis

## Tech Stack

- Backend: FastAPI (Python)
- Frontend: HTML, CSS, JavaScript
- Database: Firebase
- Authentication: Firebase Auth

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Start the backend server:
```bash
cd backend
uvicorn main:app --reload
```

3. Start the frontend server:
```bash
cd frontend
python -m http.server 8080
```

4. Visit http://localhost:8080 in your browser

## Environment Variables

Create a `.env` file in the backend directory with:
```
YOUTUBE_API_KEY=your_api_key_here
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
