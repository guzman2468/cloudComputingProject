@echo off
set "PROJECT_ROOT=%~dp0.."
set "SOURCE_DIR=%PROJECT_ROOT%\frontend"
set "TARGET_DIR=%PROJECT_ROOT%\app\static"
set "TEMPLATE_DIR=%PROJECT_ROOT%\app\templates"

if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

mkdir "%TARGET_DIR%\pages" 2> nul
mkdir "%TARGET_DIR%\images" 2> nul
mkdir "%TARGET_DIR%\resources" 2> nul
mkdir "%TEMPLATE_DIR%" 2> nul

xcopy "%SOURCE_DIR%\pages\*.css" "%TARGET_DIR%\pages\" /I /Y > nul
xcopy "%SOURCE_DIR%\pages\*.js" "%TARGET_DIR%\pages\" /I /Y > nul
xcopy "%SOURCE_DIR%\images\*" "%TARGET_DIR%\images\" /E /I /Y > nul
xcopy "%SOURCE_DIR%\resources\*" "%TARGET_DIR%\resources\" /E /I /Y > nul
xcopy "%SOURCE_DIR%\pages\*.html" "%TEMPLATE_DIR%\" /I /Y > nul

echo Frontend prepared in app\static and app\templates.
