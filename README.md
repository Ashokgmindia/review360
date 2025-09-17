# Review360 - Multi-Tenant Academic Management System

A comprehensive Django-based multi-tenant SaaS application for academic institutions, featuring role-based access control, student management, teacher administration, and academic workflow management.

## 🚀 Features

### Core Functionality
- **Multi-Tenant Architecture**: Complete data isolation between colleges
- **Role-Based Access Control**: SuperAdmin, CollegeAdmin, Teacher, and Student roles
- **Student Management**: Complete student lifecycle management
- **Teacher Administration**: Faculty management and academic assignments
- **Academic Workflows**: Class management, subject handling, and academic year tracking
- **Activity Sheets**: Student project and assignment management
- **Follow-up Sessions**: Teacher-student academic sessions
- **Validation System**: Teacher validation of student work
- **Import/Export**: Bulk data management capabilities

### Security Features
- **JWT Authentication**: Secure token-based authentication
- **OTP Verification**: Two-factor authentication via email
- **Field-Level Permissions**: Granular control over data modification
- **Tenant Isolation**: Complete data separation between institutions
- **Rate Limiting**: API protection against abuse
- **CORS Configuration**: Secure cross-origin resource sharing

### Production Ready
- **Docker Support**: Complete containerization with Docker Compose
- **Nginx Configuration**: Production-ready reverse proxy setup
- **Database Optimization**: Comprehensive indexing for performance
- **Monitoring**: Health checks and logging
- **Backup System**: Automated database backups
- **SSL/TLS Support**: Secure communication

## 📋 Requirements

- Python 3.9+
- Django 5.2+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (for containerized deployment)
- Nginx (for production)

## 🛠️ Installation

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd review360
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Set up permissions**
   ```bash
   python manage.py setup_permissions
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Start development server**
   ```bash
   python manage.py runserver
   ```

### Production Deployment

1. **Prepare environment**
   ```bash
   cp .env.example .env.production
   # Edit .env.production with production values
   ```

2. **Deploy using Docker**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh deploy
   ```

3. **Or use Docker Compose directly**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## 🏗️ Architecture

### Multi-Tenant Design
- **Shared Schema**: All tenants share the same database schema
- **Data Isolation**: Automatic filtering by college/tenant
- **Tenant Middleware**: Automatic query scoping
- **College-Based Scoping**: Each college is a separate tenant

### Permission System
- **Role-Based Access Control (RBAC)**: Four distinct user roles
- **Field-Level Security**: Granular control over data modification
- **Permission Matrix**: Comprehensive permission mapping
- **Django Groups**: Integration with Django's permission system

### API Design
- **RESTful API**: Complete REST API with DRF
- **JWT Authentication**: Secure token-based authentication
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Rate Limiting**: Protection against API abuse

## 👥 User Roles & Permissions

### Super Admin
- Full system access across all tenants
- College and user management
- System administration

### College Admin
- Full access within their college
- Student, teacher, and class management
- Academic program oversight

### Teacher
- Limited access to assigned classes
- Student management for their classes
- Activity sheet and validation management
- Follow-up session management

### Student
- Read-only access to academic information
- Personal profile management (limited fields)
- Activity sheet submission
- View validation results

## 🔧 Configuration

### Environment Variables

```bash
# Django Settings
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=your-domain.com

# Database
POSTGRES_DB=review360
POSTGRES_USER=review360
POSTGRES_PASSWORD=your-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# JWT
JWT_ACCESS_MIN=30
JWT_REFRESH_DAYS=7
```

### Database Configuration

The application uses PostgreSQL with comprehensive indexing for optimal performance:

- **Class Model**: Indexed by college, academic year, teacher
- **Student Model**: Indexed by college, class, department, email
- **Teacher Model**: Indexed by college, department, employee ID
- **Activity Sheets**: Indexed by college, student, status
- **Follow-up Sessions**: Indexed by college, student, teacher

## 📚 API Documentation

### Authentication Endpoints
- `POST /api/v1/iam/auth/login/` - Login with email/password
- `POST /api/v1/iam/auth/otp-verify/` - Verify OTP
- `POST /api/v1/iam/auth/password-reset-request/` - Request password reset
- `POST /api/v1/iam/auth/password-reset-confirm/` - Confirm password reset

### Academic Endpoints
- `GET /api/v1/academics/classes/` - List classes
- `POST /api/v1/academics/classes/` - Create class
- `GET /api/v1/academics/students/` - List students
- `POST /api/v1/academics/students/` - Create student
- `GET /api/v1/academics/teachers/` - List teachers
- `POST /api/v1/academics/teachers/` - Create teacher

### Learning Endpoints
- `GET /api/v1/learning/activity-sheets/` - List activity sheets
- `POST /api/v1/learning/activity-sheets/` - Create activity sheet
- `GET /api/v1/learning/validations/` - List validations
- `POST /api/v1/learning/validations/` - Create validation

### Follow-up Endpoints
- `GET /api/v1/followup/follow-up-sessions/` - List sessions
- `POST /api/v1/followup/follow-up-sessions/` - Create session

### API Documentation
- Swagger UI: `https://your-domain.com/api/docs/`
- ReDoc: `https://your-domain.com/api/redoc/`
- OpenAPI Schema: `https://your-domain.com/api/schema/`

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python manage.py test

# Run specific test module
python manage.py test iam.tests

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Test Coverage
The test suite includes:
- Permission system tests
- Role-based access control tests
- Field-level permission tests
- Tenant isolation tests
- API endpoint tests

## 🚀 Deployment

### Docker Deployment
```bash
# Deploy to production
./deploy.sh deploy

# Update application
./deploy.sh update

# Rollback changes
./deploy.sh rollback

# Check status
./deploy.sh status
```

### Manual Deployment
1. Set up PostgreSQL database
2. Configure Redis
3. Install Python dependencies
4. Run migrations
5. Set up permissions
6. Configure Nginx
7. Set up SSL certificates
8. Start services

## 📊 Monitoring

### Health Checks
- Application health: `GET /health/`
- Database connectivity
- Redis connectivity
- Service status monitoring

### Logging
- Application logs: `/var/log/review360/django.log`
- Security logs: `/var/log/review360/security.log`
- Nginx logs: `/var/log/nginx/`

### Metrics
- API response times
- Database query performance
- Memory usage
- CPU utilization

## 🔒 Security

### Authentication
- JWT tokens with configurable expiration
- OTP-based two-factor authentication
- Password reset with OTP verification

### Authorization
- Role-based access control
- Field-level permissions
- Tenant isolation
- API rate limiting

### Data Protection
- HTTPS enforcement
- Secure headers
- Input validation
- SQL injection protection

## 🛠️ Development

### Code Structure
```
review360/
├── academics/          # Academic management
├── iam/               # Identity and access management
├── learning/          # Learning management
├── followup/          # Follow-up sessions
├── compliance/        # Audit and compliance
├── review360/         # Django project settings
└── tests/            # Test suite
```

### Adding New Features
1. Create model in appropriate app
2. Add permissions to permission matrix
3. Create serializers with field-level validation
4. Implement viewsets with proper permissions
5. Add API documentation
6. Write tests
7. Update migrations

### Database Migrations
```bash
# Create migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create custom migration
python manage.py makemigrations --empty app_name
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the documentation
- Review the test cases
- Examine the permission system
- Contact the development team

## 🔄 Changelog

### Version 1.0.0
- Initial release
- Multi-tenant architecture
- Role-based access control
- Complete academic management system
- Production-ready deployment
- Comprehensive test suite
- API documentation

---

**Review360** - Empowering educational institutions with modern, secure, and scalable academic management solutions.