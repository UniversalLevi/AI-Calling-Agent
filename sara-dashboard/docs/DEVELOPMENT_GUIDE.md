# 🧭 SARA DASHBOARD - MERN Stack Admin Panel

## 📋 Project Overview

The Sara Dashboard is a comprehensive web-based admin panel built with the MERN stack (MongoDB, Express.js, React, Node.js) for monitoring and managing the Sara AI Calling Bot. It provides real-time call monitoring, analytics, user management, and system configuration capabilities.

## 🏗️ Project Structure

```
sara-dashboard/
├── backend/                    # Node.js + Express API
│   ├── config/
│   │   └── db.js              # Database configuration
│   ├── controllers/
│   │   ├── callController.js   # Call management logic
│   │   ├── userController.js   # User management logic
│   │   └── systemController.js # System configuration logic
│   ├── middleware/
│   │   ├── authMiddleware.js   # JWT authentication
│   │   └── errorHandler.js     # Error handling
│   ├── models/
│   │   ├── CallLog.js         # Call logs schema
│   │   ├── User.js            # User schema
│   │   └── SystemConfig.js    # System config schema
│   ├── routes/
│   │   ├── callRoutes.js       # Call API routes
│   │   ├── userRoutes.js       # User API routes
│   │   └── systemRoutes.js     # System API routes
│   ├── socket/
│   │   └── socketHandler.js    # Socket.io real-time events
│   ├── package.json
│   └── server.js              # Main server file
├── frontend/                   # React application
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   ├── contexts/          # React contexts
│   │   ├── pages/             # Page components
│   │   ├── App.js             # Main app component
│   │   ├── index.js           # Entry point
│   │   └── index.css          # Global styles
│   ├── package.json
│   ├── tailwind.config.js     # Tailwind configuration
│   └── postcss.config.js      # PostCSS configuration
├── docs/                       # Documentation
├── package.json               # Root package.json
├── env.example                # Environment variables template
└── README.md                  # Project documentation
```

## 🚀 Features Implemented

### ✅ Backend Features

#### 🔐 Authentication & Authorization
- JWT-based authentication
- Role-based access control (Admin, Operator, Viewer)
- Permission-based authorization
- Account lockout after failed attempts
- Password hashing with bcrypt

#### 📊 Database Models
- **CallLog**: Complete call tracking with analytics
- **User**: User management with roles and permissions
- **SystemConfig**: Dynamic system configuration

#### 🔌 Real-time Communication
- Socket.io integration for live updates
- Real-time call monitoring
- System health monitoring
- User activity tracking

#### 🛡️ Security Features
- Helmet.js for security headers
- Rate limiting
- CORS configuration
- Input validation
- Error handling middleware

### ✅ Frontend Features

#### 🎨 Modern UI/UX
- Responsive design with Tailwind CSS
- Dark mode support
- Clean, professional interface
- Loading states and animations

#### 🔄 Real-time Updates
- Live call monitoring
- Real-time notifications
- System health indicators
- Socket.io integration

#### 📱 Responsive Design
- Mobile-first approach
- Tablet and desktop optimized
- Touch-friendly interface

## 🛠️ Technology Stack

### Backend
- **Node.js** - Runtime environment
- **Express.js** - Web framework
- **MongoDB** - Database
- **Mongoose** - ODM
- **Socket.io** - Real-time communication
- **JWT** - Authentication
- **bcrypt** - Password hashing
- **Helmet** - Security
- **CORS** - Cross-origin requests

### Frontend
- **React 18** - UI library
- **React Router** - Routing
- **Tailwind CSS** - Styling
- **Socket.io Client** - Real-time communication
- **Axios** - HTTP client
- **React Hot Toast** - Notifications
- **Recharts** - Data visualization
- **React Hook Form** - Form handling

## 📡 API Endpoints

### Authentication
- `POST /api/users/login` - User login
- `GET /api/users/profile` - Get user profile
- `PUT /api/users/profile` - Update profile
- `PUT /api/users/change-password` - Change password

### Call Management
- `GET /api/calls` - Get all call logs
- `GET /api/calls/stats` - Get call statistics
- `GET /api/calls/analytics` - Get detailed analytics
- `GET /api/calls/active` - Get active calls
- `POST /api/calls/:id/terminate` - Terminate call

### System Configuration
- `GET /api/system/config` - Get configurations
- `PUT /api/system/config/:name` - Update configuration
- `GET /api/system/analytics` - Get system analytics
- `GET /api/system/health` - Get system health

### User Management (Admin only)
- `POST /api/users/register` - Register user
- `GET /api/users` - Get all users
- `PUT /api/users/:id` - Update user
- `DELETE /api/users/:id` - Delete user

## 🔧 Installation & Setup

### Prerequisites
- Node.js (v16 or higher)
- MongoDB (local or Atlas)
- npm or yarn

### Backend Setup
```bash
cd backend
npm install
cp ../env.example .env
# Edit .env with your configuration
npm run dev
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Root Setup (Run both)
```bash
npm install
npm run dev
```

## 🌐 Environment Variables

### Backend (.env)
```env
MONGO_URI=mongodb://localhost:27017/sara-dashboard
PORT=5000
NODE_ENV=development
JWT_SECRET=your-super-secret-jwt-key
JWT_EXPIRE=7d
FRONTEND_URL=http://localhost:3000
SOCKET_CORS_ORIGIN=http://localhost:3000
SARA_BOT_URL=http://localhost:8000
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### Frontend (.env)
```env
REACT_APP_SOCKET_URL=http://localhost:5000
REACT_APP_API_URL=http://localhost:5000/api
```

## 📊 Database Schema

### CallLog Model
```javascript
{
  callId: String,           // Unique call identifier
  type: String,             // 'inbound' | 'outbound'
  caller: String,           // Caller phone number
  receiver: String,         // Receiver phone number
  startTime: Date,          // Call start time
  endTime: Date,            // Call end time
  duration: Number,         // Duration in seconds
  status: String,           // 'success' | 'failed' | 'missed' | 'in-progress'
  transcript: String,       // Call transcript
  audioFile: String,        // Audio file path
  language: String,         // 'en' | 'hi' | 'mixed'
  interruptionCount: Number, // Number of interruptions
  satisfaction: String,     // 'positive' | 'negative' | 'neutral' | 'unknown'
  metadata: Object,         // Additional metadata
  createdAt: Date,          // Creation timestamp
  updatedAt: Date           // Last update timestamp
}
```

### User Model
```javascript
{
  username: String,         // Unique username
  email: String,            // Unique email
  password: String,         // Hashed password
  role: String,             // 'admin' | 'operator' | 'viewer'
  firstName: String,        // First name
  lastName: String,         // Last name
  isActive: Boolean,        // Account status
  permissions: Object,      // Permission settings
  preferences: Object,      // User preferences
  lastLogin: Date,          // Last login time
  loginAttempts: Number,     // Failed login attempts
  lockUntil: Date,          // Account lock expiry
  createdAt: Date,          // Creation timestamp
  updatedAt: Date           // Last update timestamp
}
```

### SystemConfig Model
```javascript
{
  name: String,             // Configuration name
  category: String,         // Configuration category
  value: Mixed,            // Configuration value
  dataType: String,        // 'string' | 'number' | 'boolean' | 'array' | 'object'
  description: String,      // Configuration description
  isActive: Boolean,       // Configuration status
  isEditable: Boolean,     // Whether config can be edited
  validation: Object,      // Validation rules
  lastModifiedBy: ObjectId, // User who last modified
  createdAt: Date,         // Creation timestamp
  updatedAt: Date         // Last update timestamp
}
```

## 🔌 Socket.io Events

### Client to Server
- `join-room` - Join role-based room
- `call-started` - Emit call start event
- `call-ended` - Emit call end event
- `call-updated` - Emit call update event
- `call-interrupted` - Emit interruption event
- `system-status` - Emit system status
- `user-activity` - Emit user activity

### Server to Client
- `call-started` - New call started
- `call-ended` - Call ended
- `call-updated` - Call updated
- `call-interrupted` - Call interrupted
- `call-terminated` - Call terminated
- `system-health` - System health update
- `system-status-update` - System status change
- `user-activity` - User activity notification

## 🎯 Key Features

### 📞 Real-time Call Monitoring
- Live call tracking
- Call status updates
- Interruption monitoring
- Call termination capability

### 📊 Analytics & Reporting
- Call statistics and trends
- Success/failure rates
- Language distribution
- Performance metrics
- Daily/weekly/monthly reports

### 👥 User Management
- Role-based access control
- User registration and management
- Permission management
- Activity tracking

### ⚙️ System Configuration
- Dynamic configuration management
- Voice settings
- Language preferences
- Call limits and timeouts
- Security settings

### 🔒 Security Features
- JWT authentication
- Role-based authorization
- Account lockout protection
- Rate limiting
- Input validation

## 🚀 Deployment

### Backend Deployment
1. Set up MongoDB Atlas or local MongoDB
2. Configure environment variables
3. Deploy to Heroku, Railway, or similar platform
4. Set up SSL certificate

### Frontend Deployment
1. Build the React application
2. Deploy to Vercel, Netlify, or similar platform
3. Configure environment variables
4. Set up custom domain

### Database Setup
1. Create MongoDB database
2. Run initialization scripts
3. Set up indexes for performance
4. Configure backup strategy

## 📈 Performance Optimizations

### Backend
- Database indexing
- Query optimization
- Caching strategies
- Rate limiting
- Error handling

### Frontend
- Code splitting
- Lazy loading
- Image optimization
- Bundle optimization
- Caching strategies

## 🔧 Development Guidelines

### Code Structure
- Modular architecture
- Separation of concerns
- Clean code principles
- Error handling
- Documentation

### Testing
- Unit tests for controllers
- Integration tests for APIs
- Frontend component tests
- End-to-end tests

### Security
- Input validation
- SQL injection prevention
- XSS protection
- CSRF protection
- Secure headers

## 📝 Next Steps

### Phase 1: Core Features ✅
- [x] Project structure setup
- [x] Backend API development
- [x] Database models
- [x] Authentication system
- [x] Basic frontend components

### Phase 2: Advanced Features 🚧
- [ ] Complete frontend pages
- [ ] Real-time dashboard
- [ ] Advanced analytics
- [ ] User management interface
- [ ] System configuration UI

### Phase 3: Integration & Testing 🔄
- [ ] Sara Bot integration
- [ ] Webhook implementation
- [ ] Testing suite
- [ ] Performance optimization
- [ ] Documentation completion

### Phase 4: Deployment & Production 🎯
- [ ] Production deployment
- [ ] SSL configuration
- [ ] Monitoring setup
- [ ] Backup strategy
- [ ] User training

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

---

**Built with ❤️ for Sara AI Calling Bot**
