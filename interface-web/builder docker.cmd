@echo off
echo.
echo ==========================
echo LDA BUILDER DOCKER
echo %computername%
echo %username%
echo %cd%
echo ==========================
echo.

docker build -f Dockerfile.windows -t frontend .
cmd /c "run-docker.cmd"
timeout 10