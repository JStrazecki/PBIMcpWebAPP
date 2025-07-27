# AZURE STARTUP COMMAND EMERGENCY FIX

## The Problem
Azure is completely ignoring your startup command and falling back to .NET Core mode.

## Solution: Try these startup commands IN ORDER:

### Option 1: Direct bash script
```
bash run.sh
```

### Option 2: Force chmod and run
```
chmod +x run.sh && bash run.sh
```

### Option 3: Direct gunicorn with absolute path
```
/home/site/wwwroot/antenv/bin/gunicorn --bind=0.0.0.0:8000 --workers 1 --timeout 600 --access-logfile - --error-logfile - --log-level info app:APP
```

### Option 4: Activate venv first
```
source /home/site/wwwroot/antenv/bin/activate && gunicorn --bind=0.0.0.0:8000 --workers 1 --timeout 600 --access-logfile - --error-logfile - --log-level info app:APP
```

## In Azure Portal:
1. Go to Configuration → General Settings
2. **CLEAR the Startup Command field completely**
3. Save and restart
4. If still fails, try Option 1 above
5. Test each option until Python app starts

## Expected Success Log:
You should see:
```
[2025-07-27] Starting gunicorn 23.0.0
[2025-07-27] Listening at: http://0.0.0.0:8000
[2025-07-27] Using worker: sync
[2025-07-27] Booting worker with pid: 123
```

Instead of: "Sun Jul 27 running .net core"