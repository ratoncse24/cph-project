# Environment Setup Guide

This guide explains how to set up environment variables for the User Management API.

## Quick Setup

1. **Copy the example file:**
   ```bash
   cp env.example .env
   ```

2. **Edit the `.env` file with your actual values:**
   ```bash
   nano .env  # or use your preferred editor
   ```

3. **Verify your setup:**
   ```bash
   python -c "from app.core.config import settings; print('✅ Configuration loaded successfully')"
   ```

## Configuration Sections

### 🔧 **Essential Settings (Required)**

These must be configured for the application to work:

```bash
# Database (Required)
POSTGRES_DB=your_database_name
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_secure_password

# Security (Required - CHANGE THESE!)
JWT_SECRET_KEY=your-super-secret-jwt-key-here
SECRET_KEY=your-super-secret-application-key-here
```

### 🌍 **Environment-Specific Settings**

#### Development
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
```

#### Staging
```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
```

#### Production
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
```

### ☁️ **AWS Configuration (Optional)**

Only needed if using AWS services:
```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET_NAME=your_bucket_name
```

### 📧 **Email Configuration (Optional)**

For sending emails:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=noreply@yourapp.com
```

### 📱 **SMS Configuration (Optional)**

For Twilio SMS integration:
```bash
SMS_PROVIDER=twilio
SMS_ACCOUNT_SID=your_twilio_sid
SMS_AUTH_TOKEN=your_twilio_token
SMS_FROM_NUMBER=+1234567890
SMS_ENABLED=true
```

## Environment Variable Priority

The application loads configuration in this order:
1. Environment variables (highest priority)
2. `.env` file values
3. Default values in `config.py` (lowest priority)

## Security Best Practices

### 🔒 **For Production:**
- ✅ Change all default secret keys
- ✅ Set `DEBUG=false`
- ✅ Use strong, unique passwords
- ✅ Keep `.env` file out of version control
- ✅ Use environment-specific configurations
- ✅ Regularly rotate secrets

### ⚠️ **Never commit:**
- `.env` files
- Production credentials
- API keys or secrets

## Validation

The application automatically validates:
- Required secrets are changed in production
- DEBUG is false in production
- Database connectivity
- AWS credentials format (if provided)

## Common Issues

### **Configuration Error:**
```
ValueError: JWT_SECRET_KEY must be changed in production
```
**Solution:** Update your JWT_SECRET_KEY in the `.env` file.

### **Database Connection Error:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```
**Solution:** Check your database credentials and ensure PostgreSQL is running.

### **Import Error:**
```
ValidationError: [Environment variables not found]
```
**Solution:** Ensure your `.env` file exists and contains required variables.

## Testing Configuration

For running tests, set:
```bash
TESTING=true
```

This skips production validations during test runs.

## Docker Integration

The provided `docker-compose.yml` automatically loads your `.env` file:

```bash
# Build and run with environment variables
docker-compose up --build
```

Make sure your `.env` file exists before running Docker Compose. 