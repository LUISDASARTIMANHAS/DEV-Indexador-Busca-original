@echo off
ECHO RUN MODE
docker run -d -p 8080:8080 --name frontend_%computername% frontend
docker ps
exit /b 0