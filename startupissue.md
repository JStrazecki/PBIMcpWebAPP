# Azure Python startup failures decoded: From deployment success to running application

When Azure Web App deployments succeed but Python applications fail to start, the root cause typically involves **port binding mismatches**, **missing startup commands**, or **virtual environment path issues**. The most critical fix is ensuring your application binds to `0.0.0.0:$PORT` and setting `WEBSITES_PORT` to match your application's listening port. Azure expects containers to respond within 230 seconds on the configured port, and without proper logging flags (`--access-logfile '-' --error-logfile '-'`), troubleshooting becomes nearly impossible. This comprehensive guide covers the 10 most common startup failure patterns and provides battle-tested solutions for each scenario.

## Port binding and the container startup dance

Azure App Service performs HTTP health checks on deployed containers, expecting responses on port 80 by default. When applications bind to localhost or incorrect ports, the dreaded "Container didn't respond to HTTP pings" error appears after 230 seconds, causing startup failure despite successful deployment.

**The golden rule of Azure port configuration** requires three aligned components: your application must bind to `0.0.0.0:PORT`, the `WEBSITES_PORT` app setting must match this port, and your startup command must include proper logging flags. A working Gunicorn configuration looks like `gunicorn --bind=0.0.0.0:8000 --timeout 600 --access-logfile '-' --error-logfile '-' app:app` with `WEBSITES_PORT=8000` set in Application Settings.

Critical to understand is Azure's **warmup request behavior** - the platform sends HTTP requests to random paths expecting 404 responses for non-existent routes. Applications without proper 404 handlers may fail startup checks even when correctly configured. Flask applications need `@app.errorhandler(404)` implementations, while Django apps must ensure proper URL configuration handles unknown routes gracefully.

## Startup command hierarchy and execution mysteries

Azure App Service follows a strict precedence order for Python startup commands that often confuses developers. **Portal/CLI startup commands override everything**, including automatic framework detection and file-based configurations. This hierarchy means a startup command set in the Azure Portal will ignore your carefully crafted startup.sh file, leading to unexpected behavior.

The platform's automatic detection works remarkably well for standard Flask and Django applications. It searches for `app.py` or `application.py` with an `app` object for Flask, and `wsgi.py` files for Django. However, **FastAPI and custom frameworks require explicit startup commands** because they lack automatic detection patterns. The solution involves setting commands like `gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 main:app` for FastAPI applications.

File-based startup configurations offer version control benefits but require careful attention to line endings and paths. **Windows CRLF line endings silently break shell scripts**, causing commands to appear to run but fail mysteriously. Always use LF line endings and test scripts locally on Linux systems before deployment. Reference files with relative paths from the project root, never absolute paths.

## Gunicorn configuration pitfalls on Azure Linux containers

Gunicorn serves as the default WSGI server for Python applications on Azure App Service, but its configuration requirements differ from typical Linux deployments. **Missing logging flags represent the most common misconfiguration**, preventing any application output from appearing in Azure's log streams.

The required Gunicorn invocation pattern includes both access and error log redirection: `--access-logfile '-' --error-logfile '-'`. Without these flags, applications start successfully but provide no diagnostic information when issues occur. Azure's default configuration includes these flags, but custom startup commands often omit them, creating debugging nightmares.

**Worker timeout issues plague long-running requests** when developers override startup commands without specifying `--timeout`. Azure defaults to 600 seconds, but Gunicorn's default 30-second timeout causes worker processes to restart during normal operations. Setting explicit timeouts prevents mysterious request failures and worker cycling. For CPU-bound applications, configure workers based on available cores using `--workers $((($NUM_CORES*2)+1))`.

## Missing logs and the silent failure problem

When deployments succeed but no application logs appear, the issue typically stems from Python's output buffering or incorrect logging configuration. **Setting `PYTHONUNBUFFERED=1` solves most logging visibility problems** by forcing immediate output flushing.

Azure's logging architecture distinguishes between application logs (your Python output) and container logs (system-level information). Application logs require explicit enablement through the portal or CLI, and **Linux App Services can only store Python logs in the file system**, not Azure Storage blobs. This limitation means logs accumulate until manually cleared or the retention period expires.

The Kudu console provides crucial diagnostic access when normal logging fails. Navigate to `https://<app-name>.scm.azurewebsites.net` and check `/home/LogFiles/` for application output. The `docker.log` file in this directory often contains startup errors invisible through normal log streaming. SSH access via the Kudu console allows real-time debugging with commands like `tail -f /home/LogFiles/docker.log`.

## Python path mysteries and import failures  

Azure's virtual environment structure follows specific conventions that trip up many deployments. The platform expects virtual environments in `antenv/lib/python[version]/site-packages`, but **Windows-created environments use different capitalization** (`Lib` vs `lib`), causing import failures on case-sensitive Linux systems.

Module import errors despite successful pip installations usually indicate path configuration problems. Azure's Oryx build system creates virtual environments automatically when `SCM_DO_BUILD_DURING_DEPLOYMENT=true` is set, but the **resulting environment lives in `/tmp/<uid>/antenv`** rather than the expected `/home/site/wwwroot/antenv`. This temporary location works for Oryx-managed deployments but breaks custom startup scripts expecting traditional paths.

The solution involves understanding deployment methods and their path implications. Git deployments and `az webapp up` commands trigger Oryx builds with temporary paths, while ZIP deployments without build automation expect pre-built environments. **Always enable Oryx build automation** for new deployments to ensure consistent behavior: `az webapp config appsettings set --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true`.

## Environment variable timing and availability gaps

Environment variables in Azure App Service exist in two distinct contexts that confuse many developers. **Build-time variables differ from runtime variables**, and some critical variables like `APP_PATH` only exist during Oryx-managed builds. This temporal distinction explains why database connections work during development but fail in production.

Applications must handle both scenarios gracefully. The `APP_PATH` variable points to the actual application location when Oryx builds run, but remains undefined for external build deployments. Robust applications check multiple locations: `os.environ.get('APP_PATH', '/home/site/wwwroot')` provides appropriate fallbacks.

**Secret management requires special attention** because startup commands appear in logs and configuration interfaces. Never include sensitive data in startup commands; instead, use Azure App Settings or Key Vault references. Environment variables set through App Settings remain secure and available at runtime without exposure in build logs.

## Oryx build conflicts and override strategies

Azure's Oryx build system automates dependency installation but sometimes conflicts with custom build processes. **Platform detection failures occur when `requirements.txt` is missing** from the project root or when ZIP files have incorrect structure. Oryx expects Python projects to follow conventional layouts, and deviations trigger detection failures.

Build process hangs often indicate dependency resolution problems. Unpinned package versions force pip to solve complex dependency graphs, potentially timing out after 60 seconds. **Pin all package versions in requirements.txt** to ensure reproducible builds. For projects with many dependencies, scale up to higher App Service SKUs during deployment to provide adequate memory for package compilation.

When Oryx conflicts with custom build processes, disable it entirely with `ENABLE_ORYX_BUILD=false` and `SCM_DO_BUILD_DURING_DEPLOYMENT=false`. This approach requires external build systems to create properly structured deployments, including virtual environments that match Azure's Linux filesystem expectations.

## Container health checks and HTTP ping responses

Azure performs continuous health checks on running containers, expecting HTTP responses to validate application availability. **Applications must handle arbitrary URL requests with appropriate responses**, not just defined routes. The platform sends requests to random paths like `/LKNSLDNlkdns` expecting 404 responses, and applications that crash on unknown routes fail health checks.

The health check timeout of 230 seconds seems generous but proves insufficient for applications with complex initialization. Machine learning models, database migrations, or cache warming can exceed this limit. **Extend the timeout with `WEBSITES_CONTAINER_START_TIME_LIMIT=1800`** for applications needing up to 30 minutes for initialization.

Network binding represents another critical health check requirement. Applications binding only to localhost remain inaccessible to Azure's health check infrastructure. Always bind to `0.0.0.0` rather than `127.0.0.1` or `localhost`. Test binding with `netstat -tulnp` via SSH to verify correct network configuration.

## Framework-specific startup patterns that work

Different Python frameworks require distinct startup approaches on Azure App Service. **Django applications benefit from automatic detection** when following standard project structure, but custom configurations need explicit startup commands like `gunicorn --bind=0.0.0.0 --timeout 600 --chdir <module_path> <module>.wsgi`.

FastAPI applications always require custom startup commands because Azure lacks automatic ASGI detection. The working pattern uses Gunicorn with Uvicorn workers: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --timeout 600 main:app`. Direct Uvicorn usage works for development but lacks production robustness.

Flask applications with non-standard structures need careful path configuration. When the main application file isn't named `app.py` or the Flask instance isn't called `app`, specify both in the startup command: `gunicorn --bind=0.0.0.0 --timeout 600 hello:myapp`. For applications in subdirectories, add `--chdir` to set the working directory correctly.

## Emergency diagnostics when nothing else works

When applications refuse to start despite correct configuration, systematic diagnosis reveals hidden issues. **Start with the Kudu console** at `https://<app-name>.scm.azurewebsites.net` to access raw logs and system state. Check `/home/LogFiles/docker.log` for container startup errors that don't appear in application logs.

Manual startup testing via SSH provides immediate feedback about configuration problems. Navigate to `/home/site/wwwroot` and attempt to start your application directly with `python app.py`. Import errors, missing dependencies, or configuration problems become immediately visible. Test Gunicorn commands interactively to verify syntax and module resolution.

**Process inspection reveals running state** when logs provide insufficient information. Use `ps aux` to see running processes and `netstat -tulnp` to verify port bindings. These commands expose issues like multiple processes competing for ports or applications binding to wrong interfaces. The combination of process state and network configuration often reveals issues invisible through logs alone.

## Conclusion

Azure Web App Python startup failures typically stem from a handful of root causes that manifest in confusing ways. Port binding mismatches, missing logging configurations, and path issues account for most problems. Success requires understanding Azure's container architecture, health check requirements, and the critical difference between deployment success and application startup. 

The most important configuration elements remain consistent across all scenarios: bind to `0.0.0.0:PORT`, set `WEBSITES_PORT` correctly, include Gunicorn logging flags, handle 404 responses gracefully, and enable `PYTHONUNBUFFERED=1`. With these fundamentals in place, Python applications start reliably on Azure App Service, and when issues occur, comprehensive logging provides clear diagnostic paths.

Remember that Azure's default configurations work well for standard Flask and Django applications. Complexity increases with custom frameworks, non-standard project structures, or specialized requirements. When facing startup failures, systematic diagnosis using Kudu SSH access, process inspection, and manual testing reveals issues that logs alone cannot expose. The platform's flexibility supports virtually any Python application architecture when properly configured.