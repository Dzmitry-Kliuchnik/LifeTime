# 🗓️ Lifetime Calendar

A Python + Vue.js application that visualizes your entire life as a calendar of weeks. Each box represents one week of your life, helping you visualize time and make the most of it.

## Features

- **Visual Life Timeline**: See your entire life laid out as weeks in a grid format
- **Week Tracking**: Track which weeks you've lived, your current week, and future weeks
- **Personal Notes**: Add notes to any week to remember important events or milestones
- **Customizable Settings**: Set your birthdate and life expectancy
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Statistics**: View stats about weeks lived, remaining weeks, and life percentage

## Screenshots

The application displays:
- ✅ **Green boxes**: Weeks you've already lived
- 🟡 **Yellow box**: Your current week (animated)
- ⬜ **White boxes**: Future weeks
- 💜 **Purple border**: Weeks with notes

## Tech Stack

**Backend:**
- Python 3.8+
- FastAPI
- SQLite database
- SQLAlchemy

**Frontend:**
- Vue.js 3
- Axios for API calls
- CSS3 with responsive design

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn

### Quick Start

**For Linux/macOS:**
```bash
./start.sh
```

**For Windows:**
```bash
start.bat
```

The startup scripts will automatically:
- Check for required dependencies (Python, Node.js, npm)
- Create and activate a virtual environment for Python
- Install backend dependencies (if needed)
- Install frontend dependencies (if needed)
- Start both backend and frontend servers

### Manual Setup

If you prefer to set up and run the servers manually:

#### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the backend server
python main.py
```

The backend will be available at `http://localhost:8000`

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

1. **First Time Setup**: Enter your birthdate and life expectancy
2. **View Your Calendar**: See all your life weeks laid out in a grid
3. **Add Notes**: Click on any week to add notes or memories
4. **Track Progress**: Monitor your life statistics in the dashboard

## API Endpoints

- `GET /api/user` - Get user data (birthdate, life expectancy)
- `POST /api/user` - Save user data
- `GET /api/calendar` - Get calendar data with all weeks
- `POST /api/week-note` - Save or update a note for a specific week

## Database Schema

The application uses SQLite with two main tables:
- `user_data`: Stores birthdate and life expectancy
- `week_notes`: Stores notes and metadata for specific weeks

## Development

### Running Tests
```bash
# Backend tests (if available)
cd backend
pytest

# Frontend tests (if available)
cd frontend
npm run test
```

### Building for Production
```bash
# Build frontend
cd frontend
npm run build

# The built files will be in the dist/ directory
```

## Inspiration

This project is inspired by the "Your Life in Weeks" concept, which helps visualize the finite nature of time and encourages mindful living. Each week is precious, and seeing your life laid out this way can be both sobering and motivating.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.