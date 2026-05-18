@echo off
ECHO RUN MODE
docker run -d -p 8000:8000 ^
--name backend_%computername% ^
-e DATABASE_URL=postgresql://%DATABASE_USER%:%DATABASE_PASSWORD%@%DATABASE_HOST%:%DATABASE_PORT%/ifesdoc ^
backend
docker ps
exit /b 0