# Office Hours Queue + Ticketing System

> A production-quality full-stack system for managing university office hours with **ML-powered duplicate ticket detection**

![OfficeHours_V1](https://github.com/user-attachments/assets/4aba2380-6b59-4f9c-953a-a1a14e4ed170)


## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** and `pip`
- **Node.js 18+** and `npm`
- **Docker** and **Docker Compose** (for database)

### 1. Start Backend

```bash
# Terminal 1: Start Backend Services
cd backend

# Verify services
docker compose config --services

# Start Database
docker compose up -d postgres

# Check container status
docker compose ps

# Start Backend API
docker compose up -d backend

# Run migrations (crucial for first run!)
docker compose exec backend alembic upgrade head

# Backend runs on http://localhost:8000
```

### 2. Start Frontend

```bash
# Terminal 2: Start React frontend
cd frontend
npm install
npm run dev
# Frontend runs on http://localhost:3000
```

### 3. Open Application

Visit **http://localhost:3000** and create an account!

## ✨ Key Features

### 🔐 Authentication & Authorization
- JWT-based authentication with secure token management
- Role-based access control: **STUDENT**, **TA**, **ADMIN**
- Protected routes and API endpoints

### ⚡ Real-time Queue Updates
- **Instant Status Sync**: When a TA claims or starts a ticket, the student's dashboard updates in real-time.
- **WebSocket-Powered**: Uses persistent WebSocket connections to push updates from server to clients.
- **Auto-Reconnection**: Frontend hook handles network drops and automatic reconnection.

### 🎓 Role-Based Workflows

#### Students
- Browse available courses
- Join active office hours sessions
- **Create support tickets** with duplicate detection
- **Track ticket status in real-time** (WebSockets)
- Track ticket status in real-time

#### Teaching Assistants (TAs)
- View assigned courses
- Claim tickets from the queue
- Manage ticket lifecycle: Claim → Start → Resolve
- Monitor session statistics

#### Admins
- Create and manage courses
- Assign staff (TAs) to courses
- Open/close office hours sessions
- View analytics and metrics

### 🤖 ML-Powered Duplicate Detection

**The Star Feature**: When students create tickets, the backend:
1. Generates semantic embeddings using an ultra-optimized **ONNX Runtime** version of the *all-MiniLM-L6-v2* model (shrinks deployment memory by 85% to fit inside strict 512MB limits)
2. Stores embeddings in PostgreSQL with **pgvector** extension
3. Performs **ANN similarity search** using cosine distance
4. Returns ranked list of similar tickets

**Frontend Visualization**:
- Color-coded similarity scores (Red: >80%, Amber: 60-80%, Yellow: <60%)
- Visual percentage bars showing match strength
- Ranked display with status badges
- Educational tooltips explaining ML technology

This reduces duplicate questions and helps students find existing solutions faster!

### 📊 Analytics Dashboard
- Real-time session statistics
- Wait time metrics (average, median)
- Time-to-resolution tracking
- Ticket status breakdown

### 🎯 Ticket State Machine
- **OPEN** → TA claims → **CLAIMED**
- **CLAIMED** → TA starts work → **IN_PROGRESS**
- **IN_PROGRESS** → TA resolves → **RESOLVED**
- **OPEN/CLAIMED** → Student cancels → **CANCELLED**
- Full audit trail with `ticket_events` logging

## 🏗️ Architecture

### Backend (FastAPI + PostgreSQL + ML)
```
backend/
├── app/
│   ├── api/v1/           # REST API endpoints
│   ├── core/             # Config, security, dependencies
│   ├── db/               # Database session management
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   │   ├── embedding/    # ML embeddings (Sentence Transformers)
│   │   └── tickets/      # Ticket service with state machine
│   ├── tests/            # Pytest test suite
│   ├── main.py           # FastAPI application
│   └── core/websocket.py # Connection manager for push notifications
├── alembic/              # Database migrations
├── Dockerfile
└── docker-compose.yml    # PostgreSQL + pgvector
```

**Tech Stack**:
- **FastAPI** - Modern async Python web framework
- **SQLAlchemy 2.0** - ORM with async support
- **PostgreSQL** - Relational database
- **pgvector** - Vector similarity search
- **ONNX Runtime** - Hyper-optimized ML vector inference
- **Alembic** - Database migrations
- **Pytest** - Testing framework

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── api/              # Type-safe API client
│   ├── components/       # Reusable UI components
│   ├── contexts/         # React Context (Auth)
│   ├── hooks/            # Custom hooks (useWebSocket)
│   ├── pages/            # Page components
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── SessionsPage.tsx
│   │   └── TicketsPage.tsx  # ⭐ Duplicate detection UI
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── vite.config.ts
```

**Tech Stack**:
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Tailwind CSS** - Styling

### 1. Register & Login
- Create account with role selection
- JWT token stored in localStorage
- Auto-redirect to role-based dashboard

### 2. Admin: Create Course & Session
- Create course: CS-101 "Intro to Computer Science"
- Open office hours session (2 PM - 4 PM)

### 3. Student: Create Ticket with Duplicate Detection
- Navigate to CS-101 office hours
- Create ticket: "Need help with binary search in homework 2"
- **ML system analyzes and shows similar tickets**:
  - "Binary search implementation issue" - 87% similar ⬛⬛⬛⬛⬛⬛⬛⬛⬛⬜
  - "Homework 2 question 3 problem" - 64% similar ⬛⬛⬛⬛⬛⬛⬜⬜⬜⬜
- Student can review duplicates or proceed with new ticket

### 4. TA: Manage Queue
- View ticket queue
- Claim ticket (status: OPEN → CLAIMED)
- Start working (status: CLAIMED → IN_PROGRESS)
- Resolve ticket (status: IN_PROGRESS → RESOLVED)

### 5. Analytics
- View session statistics
- Average wait time: 5 minutes
- Average resolution time: 12 minutes
- Tickets resolved: 15 / 20

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest -v --cov=app

# 15+ tests covering:
# - Authentication (register, login, token validation)
# - Ticket workflow (CRUD, state transitions)
# - Permissions and IDOR prevention
# - Duplicate detection
# - Analytics
```

### Frontend Tests (To Implement)
```bash
cd frontend
npm run test

# Recommended tests:
# - Auth flow (login, logout, protected routes)
# - Duplicate detection UI rendering
# - Form validation
# - API error handling
```

## 🚀 Deployment

### Backend Deployment (Render / Fly.io)

**Environment Variables**:
```env
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

**Steps**:
1. Deploy PostgreSQL with pgvector
2. Run migrations: `alembic upgrade head`
3. Deploy FastAPI app
4. The backend will automatically cache the lightweight ONNX ML model on first boot

### Frontend Deployment (Vercel / Netlify)

**Environment Variables**:
```env
VITE_API_URL=https://your-backend-url.com
```

**Build Command**:
```bash
npm run build
```

**Output Directory**: `dist`

## 📊 Database Schema

```sql
-- Core tables
users (id, name, email, password_hash, role, created_at)
courses (id, code, name, created_at)
course_staff (course_id, user_id)  -- Many-to-many
office_hours_sessions (id, course_id, starts_at, ends_at, is_active)

-- Ticket system
tickets (id, session_id, student_id, assigned_ta_id, title, description, 
         topic_tag, status, created_at, claimed_at, started_at, resolved_at)
ticket_events (id, ticket_id, event_type, actor_id, timestamp, notes)

-- ML embeddings
ticket_embeddings (ticket_id, embedding, created_at)
  -- embedding is vector(384) with IVFFlat index for ANN search
```

## 🔒 Security Features

- **Password hashing** with bcrypt
- **JWT tokens** with expiration
- **IDOR prevention** (users can only access their own resources)
- **Role-based authorization** on all endpoints

- **CORS** configured for frontend origin
- **SQL injection protection** via SQLAlchemy ORM
- **Input validation** with Pydantic schemas

## 📈 Performance Optimizations

### Backend
- **Async/await** throughout codebase
- **Database connection pooling** (SQLAlchemy)
- **Lazy loading** for ML model (loads once on startup)
- **IVFFlat index** for fast ANN search in pgvector
- **Efficient SQL queries** with joins

### Frontend
- **Vite** for fast builds and HMR
- **Code splitting** (can add React.lazy)
- **Tailwind CSS** tree-shaking
- **Local state management** (Context API)

## 🛠️ Development Workflow

### Backend Development
```bash
# Create migration
alembic revision --autogenerate -m "Add new feature"

# Run tests with coverage
pytest --cov=app --cov-report=html

# Format code
black app/
isort app/

# Type checking
mypy app/
```

### Frontend Development
```bash
# Start dev server with HMR
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

## 🐛 Troubleshooting

### Backend Issues

**pgvector extension not found**:
```bash
# Use pgvector/pgvector Docker image
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres pgvector/pgvector:pg16
```

**ML model download fails**:
```bash
# Models are downloaded dynamically from HuggingFace cache via backend logic
# Ensure your server environment can access huggingface.co without firewall blocks
```

**Migrations out of sync**:
```bash
# Reset database (DEV ONLY!)
alembic downgrade base
alembic upgrade head
```

### Frontend Issues

**CORS errors**:
- Ensure backend has correct `origins` in `CORSMiddleware`
- Check Vite proxy config in `vite.config.ts`

**Authentication loop**:
- Clear localStorage: `localStorage.clear()`
- Check JWT token expiry in backend settings

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

```
POST   /api/v1/auth/register        # Create account
POST   /api/v1/auth/login           # Get JWT token

GET    /api/v1/courses/             # List courses
POST   /api/v1/courses/             # Create course (Admin)

POST   /api/v1/sessions/            # Create session (Admin/TA)
GET    /api/v1/sessions/{id}/stats  # Get analytics

POST   /api/v1/tickets/             # Create ticket (returns duplicates!)
GET    /api/v1/tickets/sessions/{session_id}/tickets  # List tickets
POST   /api/v1/tickets/{id}/claim   # Claim ticket (TA)
POST   /api/v1/tickets/{id}/start   # Start work (TA)
POST   /api/v1/tickets/{id}/resolve # Resolve ticket (TA)
GET    /api/v1/tickets/{id}/duplicates  # Get similar tickets

WS     /api/v1/ws/{session_id}      # Real-time update stream
```


## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Built with ❤️  for efficient university office hours management**
