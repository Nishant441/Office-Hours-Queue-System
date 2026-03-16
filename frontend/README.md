# Office Hours Queue + Ticketing System - Frontend

A production-quality React + TypeScript frontend for managing office hours with ML-powered duplicate ticket detection.

## 🚀 Features

### Authentication & Authorization
- JWT-based authentication with secure token storage
- Role-based access control (STUDENT, TA, ADMIN)
- Protected routes with automatic redirect
- Automatic token refresh handling

### Role-Based Dashboards
- **Student Dashboard**: View courses, join office hours, create tickets
- **TA Dashboard**: View assigned courses, claim and resolve tickets
- **Admin Dashboard**: Create/manage courses, assign staff, manage sessions

### Office Hours Sessions
- Create sessions with start/end times
- Real-time session status and statistics
- View ticket queue with status indicators
- Close sessions when complete

### Intelligent Ticket System
- **Create Tickets** with title, description, and topic tags
- **ML-Powered Duplicate Detection**:
  - Automatic semantic similarity analysis using backend ML embeddings
  - Visual similarity scores (percentage match)
  - Color-coded ranking (red: >80%, amber: 60-80%, yellow: <60%)
  - Helps reduce duplicate questions
- **Ticket State Machine**:
  - OPEN → CLAIMED → IN_PROGRESS → RESOLVED
  - OPEN/CLAIMED → CANCELLED
- **Real-time Updates**: Refresh tickets to see current queue state

### UI/UX Excellence
- Clean, modern design with Tailwind CSS
- Loading states for all async operations
- Comprehensive error handling with retry options
- Empty states with helpful messaging
- Responsive layout for all screen sizes

## 📁 Project Structure

```
frontend/
├── src/
│   ├── api/                      # API client layer
│   │   ├── client.ts             # Axios instance with interceptors
│   │   ├── types.ts              # TypeScript interfaces
│   │   ├── auth.ts               # Authentication API
│   │   ├── courses.ts            # Courses API
│   │   ├── sessions.ts           # Sessions API
│   │   └── tickets.ts            # Tickets API
│   ├── components/               # Reusable components
│   │   ├── Auth/
│   │   │   └── ProtectedRoute.tsx
│   │   ├── Layout/
│   │   │   ├── Layout.tsx
│   │   │   └── Navbar.tsx
│   │   └── UI/
│   │       ├── LoadingSpinner.tsx
│   │       ├── ErrorMessage.tsx
│   │       └── EmptyState.tsx
│   ├── contexts/                 # React contexts
│   │   └── AuthContext.tsx       # Authentication state
│   ├── pages/                    # Page components
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── SessionsPage.tsx
│   │   └── TicketsPage.tsx
│   ├── App.tsx                   # Main app with routing
│   ├── main.tsx                  # Entry point
│   └── index.css                 # Global styles
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## 🛠️ Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite (fast HMR, optimized builds)
- **Styling**: Tailwind CSS (utility-first, responsive)
- **Routing**: React Router v6
- **HTTP Client**: Axios (interceptors, error handling)
- **State Management**: React Context API

## 🏁 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Backend server running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000` with automatic reload.

### Production Build

```bash
npm run build
npm run preview  # Preview production build
```

## 🔑 Environment Configuration

The frontend is configured to connect to the backend at `http://localhost:8000`. This is set in:
- `vite.config.ts` - Proxy configuration for development
- `src/api/client.ts` - API base URL

To change the backend URL for production, update `API_BASE_URL` in `src/api/client.ts`.

## 📖 Usage Guide

### Demo Flow

1. **Register** an account at `/register`
   - Choose role: STUDENT, TA, or ADMIN
   - Password must be 8+ characters

2. **Login** at `/login`
   - Redirects to dashboard on success

3. **Admin Workflow**:
   - Create a course (e.g., CS-101)
   - Navigate to course → Create office hours session
   - Monitor tickets and statistics

4. **TA Workflow**:
   - View assigned courses
   - Join active sessions
   - Claim tickets from queue
   - Start → Work → Resolve tickets

5. **Student Workflow**:
   - Browse available courses
   - Join active office hours
   - **Create ticket** with ML duplicate detection:
     - Fill in title, description, topic
     - View similar tickets (if any)
     - See similarity scores and rankings
   - Track ticket status

### Key Pages

#### Login & Register
- Clean forms with validation
- Error handling for duplicates, wrong credentials
- Auto-redirect when already authenticated

#### Dashboard
- Role-specific views
- Course management (Admin)
- Quick navigation to sessions

#### Sessions Page
- Create sessions (Admin/TA)
- View ticket queue
- Real-time statistics (open, in progress, resolved)
- Claim tickets (TA)
- Create tickets (Student)

#### Tickets Page
- **Create Mode**: Form with duplicate detection UI
  - Shows ML-powered similar tickets
  - Visual similarity scores with color coding
  - Explains how ML works (Sentence Transformers + pgvector)
- **View Mode**: Ticket details with state transitions
  - Students can cancel their open tickets
  - TAs can claim, start, resolve tickets

## 🎨 Design System

### Color Palette
- **Primary**: Blue shades for CTAs and branding
- **Status Colors**:
  - Open: Blue
  - Claimed: Yellow
  - In Progress: Purple
  - Resolved: Green
  - Cancelled: Red

### Component Classes (Tailwind)
- `btn-primary` - Primary action button
- `btn-secondary` - Secondary/cancel button
- `btn-danger` - Destructive action
- `input-field` - Form input styling
- `card` - Content card container
- `badge-*` - Status badges

## 🔒 Security

- JWT tokens stored in localStorage
- Automatic token attachment to all API requests
- 401 handling with auto-logout
- Protected routes require authentication
- CORS configured in Vite proxy

## 🧪 Testing Recommendations

```bash
# Install testing dependencies (not included)
npm install -D @testing-library/react @testing-library/jest-dom vitest

# Key areas to test:
# - AuthContext: login, logout, token management
# - API client: error handling, retries
# - Protected routes: redirect behavior
# - Form validation: registration, ticket creation
# - Duplicate detection UI: similarity visualization
```

## 🚀 Deployment

### Option 1: Static Hosting (Vercel, Netlify)
```bash
npm run build
# Deploy /dist folder
```

### Option 2: Docker
```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 🐛 Troubleshooting

### Backend Connection Issues
- Verify backend is running: `curl http://localhost:8000/api/v1/auth/login`
- Check CORS settings in backend
- Ensure proxy config in `vite.config.ts`

### Authentication Loop
- Clear localStorage: `localStorage.clear()`
- Check JWT token expiry in Auth context
- Verify backend JWT settings

### Duplicate Detection Not Showing
- Ensure backend ML service is running
- Check pgvector extension is enabled
- Verify embeddings are being generated

## 📊 Performance Optimizations

- Vite for fast HMR and optimized builds
- Code splitting with React.lazy (not yet implemented)
- Memoization opportunities: ticket lists, stats
- Lazy load heavy components

## 🎯 Future Enhancements

- [ ] Real-time updates with WebSockets
- [ ] Notifications for ticket state changes
- [ ] Ticket comments/chat
- [ ] File attachments
- [ ] Advanced filtering and search
- [ ] Analytics dashboard
- [ ] Dark mode toggle
- [ ] Internationalization (i18n)

## 📝 Resume Bullet Points

- Built production-quality React+TypeScript SPA with role-based authentication, JWT management, and protected routing
- Integrated ML-powered duplicate detection UI visualizing semantic similarity scores from backend embeddings
- Implemented comprehensive state management with Context API and type-safe Axios client with error interceptors
- Designed responsive UI with Tailwind CSS featuring loading states, error handling, and empty state patterns
- Created ticket lifecycle management with state machine transitions (OPEN → CLAIMED → IN_PROGRESS → RESOLVED)

## 📄 License

MIT License - see LICENSE file for details

## 👥 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

---

**Built with ❤️ for efficient office hours management**
