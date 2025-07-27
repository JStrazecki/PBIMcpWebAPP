# Flask Secret Key Generation Guide

The `FLASK_SECRET_KEY` is a critical security component required for your Power BI MCP Finance Server. This guide explains what it is, why you need it, and how to generate it securely.

## 🔒 What is a Flask Secret Key?

The Flask secret key is used for:
- **Session Security**: Encrypting user session data
- **CSRF Protection**: Preventing cross-site request forgery attacks
- **Secure Cookies**: Signing cookies to prevent tampering
- **Authentication State**: Maintaining secure login sessions

## 🚨 Why is it Critical?

Your application **will not start** without a Flask secret key because:
- Flask requires it for session management
- Security features depend on it
- Both simplified and full modes need it
- Azure Web App deployment requires it

## 🛠️ How to Generate a Flask Secret Key

### Method 1: Python Command (Recommended)
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Example output:**
```
vK7x9mN2pQ8rL4sB6tY1uA3zC5wE7dF9
```

### Method 2: Python Script
Create a file `generate_secret.py`:
```python
import secrets

# Generate a secure random secret key
secret_key = secrets.token_urlsafe(32)
print(f"Your Flask secret key: {secret_key}")
print(f"Add this to your .env file:")
print(f"FLASK_SECRET_KEY={secret_key}")
```

Run it:
```bash
python generate_secret.py
```

### Method 3: Online Generator (Use with Caution)
⚠️ **Security Warning**: Only use trusted generators and never share the key

You can use online tools like:
- Password generators (set to 32+ characters)
- Random string generators
- UUID generators

### Method 4: Manual Generation (Advanced)
```python
import os
import base64

# Generate 32 random bytes and encode as URL-safe base64
secret_bytes = os.urandom(32)
secret_key = base64.urlsafe_b64encode(secret_bytes).decode('utf-8')
print(secret_key)
```

## 📋 Step-by-Step Setup

### For Local Development (.env file)

1. **Generate the key**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Copy the output** (example):
   ```
   vK7x9mN2pQ8rL4sB6tY1uA3zC5wE7dF9
   ```

3. **Add to your .env file**:
   ```bash
   FLASK_SECRET_KEY=vK7x9mN2pQ8rL4sB6tY1uA3zC5wE7dF9
   ```

### For Azure Web App Deployment

1. **Generate the key** using any method above

2. **Add to Azure Portal**:
   - Go to: Azure Portal → Your Web App → Configuration → Application settings
   - Click: "New application setting"
   - Name: `FLASK_SECRET_KEY`
   - Value: `vK7x9mN2pQ8rL4sB6tY1uA3zC5wE7dF9`
   - Click: "OK" → "Save"

3. **Restart your web app** for changes to take effect

## 🔐 Security Best Practices

### ✅ Do's
- **Generate a new key** for each environment (dev, staging, production)
- **Use at least 32 characters** for strong security
- **Keep it secret** - never commit to version control
- **Use cryptographically secure** random generation
- **Rotate periodically** in production environments

### ❌ Don'ts
- **Don't use simple passwords** like "password123"
- **Don't reuse keys** across different applications
- **Don't share keys** in emails, chat, or documentation
- **Don't commit to Git** - use .env files that are gitignored
- **Don't use predictable values** like dates or names

## 🧪 Testing Your Secret Key

### Verify it's Working
```bash
# Test with your environment
python test_env_simple.py
```

**Expected output:**
```
FLASK_SECRET_KEY         SET
```

### Test Locally
```bash
# Start your application
python main_simple.py

# Check for errors - should start without Flask secret key errors
```

## 🔄 Key Rotation (Production)

When you need to change the secret key:

1. **Generate a new key**
2. **Update Azure App Settings**
3. **Restart the web app**
4. **Note**: All existing sessions will be invalidated

## 🚨 Troubleshooting

### Common Issues

**Error: "SECRET_KEY not found"**
- Solution: Generate and set `FLASK_SECRET_KEY`

**Error: "ValueError: FLASK_SECRET_KEY environment variable must be set"**
- Solution: Check spelling and ensure the variable is set

**Error: Sessions not working**
- Solution: Ensure the key is consistent across app restarts

**Error: "RuntimeError: The session is unavailable"**
- Solution: Verify the secret key is properly configured

### Validation Commands

**Check if key is set:**
```bash
# Windows
echo %FLASK_SECRET_KEY%

# Linux/Mac
echo $FLASK_SECRET_KEY
```

**Python validation:**
```python
import os
secret = os.environ.get('FLASK_SECRET_KEY')
if secret:
    print(f"Secret key is set (length: {len(secret)})")
else:
    print("Secret key is NOT set")
```

## 📝 Example Configurations

### Development (.env file)
```bash
# Generated with: python -c "import secrets; print(secrets.token_urlsafe(32))"
FLASK_SECRET_KEY=kJ8mN5pQ2wE7rT9yU1iO3sD6fG0hL4xV
```

### Azure Production (App Settings)
```
Name: FLASK_SECRET_KEY
Value: aB3cD7eF2gH6iJ9kL1mN4oP8qR5sT0uV
```

### Environment Variable (Command Line)
```bash
# Windows
set FLASK_SECRET_KEY=xY2zA5bC8dE1fG4hI7jK0lM3nO6pQ9rS

# Linux/Mac
export FLASK_SECRET_KEY=xY2zA5bC8dE1fG4hI7jK0lM3nO6pQ9rS
```

## 🎯 Quick Reference

**Generate Command:**
```bash
python -c "import secrets; print('FLASK_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

**Minimum Requirements:**
- ✅ At least 16 characters (32+ recommended)
- ✅ Cryptographically random
- ✅ URL-safe characters
- ✅ Unique per environment

**Security Level:**
- 🔴 **Weak**: "mysecretkey123" (predictable)
- 🟡 **Medium**: "kJ8mN5pQ2wE7rT9y" (16 chars)
- 🟢 **Strong**: "kJ8mN5pQ2wE7rT9yU1iO3sD6fG0hL4xV" (32 chars)

---

## 🆘 Need Help?

If you're still having issues:

1. **Check the main README.md** for troubleshooting
2. **Run the environment test**: `python test_env_simple.py`
3. **Verify your .env file** is in the correct location
4. **Check Azure App Settings** are properly saved

**Remember**: The Flask secret key is just one of the 4 critical variables needed for deployment. Make sure you also have your Power BI credentials configured!