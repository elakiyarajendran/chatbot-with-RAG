@echo off
echo ============================================================
echo   MC Buddy - Mesderian Christ College Chatbot
echo   Starting Django backend + React frontend
echo ============================================================
echo.

:: Start Django Backend in background
echo [1/2] Starting Django backend on http://localhost:8000 ...
start "Django Backend" cmd /k "cd /d d:\expo 4 && python manage.py runserver 8000"

:: Wait a moment for Django to boot
timeout /t 3 /nobreak >nul

:: Start React Frontend
echo [2/2] Starting React frontend on http://localhost:5173 ...
start "React Frontend" cmd /k "cd /d d:\expo 4\frontend && npm run dev"

echo.
echo ✅ Both servers starting!
echo    Backend API:  http://localhost:8000/api/
echo    Frontend App: http://localhost:5173
echo.
pause
