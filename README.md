

This project consists of two main parts:

1. Backend: A FastAPI application handling Twilio webhooks, transcription, and data processing.
2. Frontend: A Gradio-based user interface for emergency response management.

## Setup

### Backend
1. Navigate to the backend directory: \`cd backend\`
2. Create a virtual environment: \`python -m venv venv\`
3. Activate the virtual environment: 
   - On Windows: \`venv\\Scripts\\activate\`
   - On Unix or MacOS: \`source venv/bin/activate\`
4. Install dependencies: \`pip install -r requirements.txt\`
5. Set up your \`.env\` file with necessary credentials

### Frontend
1. Navigate to the frontend directory: \`cd frontend\`
2. Install Gradio: \`pip install gradio\`

## Running the application

1. Start the backend server: \`cd backend && python run.py\`
2. In a new terminal, start the frontend: \`cd frontend && python app.py\`

" > README.md