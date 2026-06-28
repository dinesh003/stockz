@echo off
set PORT=8080
set ACTION=%1

if "%ACTION%"=="" goto usage
if "%ACTION%"=="start" goto start
if "%ACTION%"=="stop" goto stop
if "%ACTION%"=="test" goto test
if "%ACTION%"=="build" goto build

:usage
echo Usage: manage-app.bat [start ^| stop ^| test ^| build]
echo.
echo start - Starts the Spring Boot application
echo stop  - Kills any process running on port %PORT%
echo test  - Executes the unit tests
echo build - Builds the application executable JAR file
goto end

:start
echo Starting application...
call .\gradlew bootRun
goto end

:stop
echo Finding process on port %PORT%...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%PORT% ^| findstr LISTENING') do (
    echo Killing process with PID %%a...
    taskkill /F /PID %%a
    goto end
)
echo No process found on port %PORT%.
goto end

:test
echo Running unit tests...
call .\gradlew test
goto end

:build
echo Building the application executable JAR file...
call .\gradlew clean build -x test
echo Build complete. Executable JAR file is in build/libs/
goto end

:end
pause
