@echo off
REM KuralIt Python SDK Publishing Script for Windows
REM This script automates the process of publishing the kuralit package to PyPI

setlocal enabledelayedexpansion

set PACKAGE_NAME=kuralit
set VERSION_FILE=kuralit\version.py
set PYPROJECT_FILE=pyproject.toml
set TEST_PYPI_REPO=testpypi
set PYPI_REPO=pypi

:menu
cls
echo.
echo KuralIt Publishing Script
echo ========================
echo.

REM Get current version
for /f "tokens=2 delims==" %%a in ('findstr "__version__" %VERSION_FILE%') do set CURRENT_VERSION=%%a
set CURRENT_VERSION=!CURRENT_VERSION:"=!
set CURRENT_VERSION=!CURRENT_VERSION: =!

echo Current version: !CURRENT_VERSION!
echo.
echo Options:
echo   1) Bump version
echo   2) Build package
echo   3) Test on TestPyPI
echo   4) Publish to PyPI
echo   5) Full workflow (bump -^> build -^> test -^> publish)
echo   6) Exit
echo.
set /p choice="Select option [1-6]: "

if "%choice%"=="1" goto bump_version
if "%choice%"=="2" goto build_package
if "%choice%"=="3" goto test_pypi
if "%choice%"=="4" goto publish_pypi
if "%choice%"=="5" goto full_workflow
if "%choice%"=="6" goto end
goto menu

:bump_version
cls
echo.
echo ========================================
echo Bump Version
echo ========================================
echo.
echo Current version: !CURRENT_VERSION!
set /p NEW_VERSION="Enter new version (e.g., 0.2.0): "

if "!NEW_VERSION!"=="" (
    echo Error: Version cannot be empty
    pause
    goto menu
)

echo.
echo Updating version to !NEW_VERSION!...

REM Update version.py (Windows PowerShell approach)
powershell -Command "(Get-Content %VERSION_FILE%) -replace '__version__ = \".*\"', '__version__ = \"!NEW_VERSION!\"' | Set-Content %VERSION_FILE%"

REM Update pyproject.toml
powershell -Command "(Get-Content %PYPROJECT_FILE%) -replace '^version = \".*\"', 'version = \"!NEW_VERSION!\"' | Set-Content %PYPROJECT_FILE%"

echo.
echo Version updated to !NEW_VERSION!
echo.
echo Next steps (optional):
echo   git add %VERSION_FILE% %PYPROJECT_FILE%
echo   git commit -m "Bump version to !NEW_VERSION!"
echo   git tag v!NEW_VERSION!
echo   git push origin main --tags
echo.
pause
goto menu

:build_package
cls
echo.
echo ========================================
echo Build Package
echo ========================================
echo.

echo Cleaning build artifacts...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.egg-info rmdir /s /q *.egg-info
if exist kuralit.egg-info rmdir /s /q kuralit.egg-info
echo Build artifacts cleaned
echo.

echo Building package...
python -m pip install --upgrade build wheel
python -m build --sdist --wheel

if errorlevel 1 (
    echo.
    echo Error: Build failed
    pause
    goto menu
)

echo.
echo Build complete! Files in dist\:
dir dist
echo.
pause
goto menu

:test_pypi
cls
echo.
echo ========================================
echo Test on TestPyPI
echo ========================================
echo.

if not exist dist\*.whl (
    echo Warning: No build files found. Building now...
    call :build_package
)

if "%TWINE_USERNAME%"=="" (
    echo Error: TWINE_USERNAME environment variable not set
    echo Set it with: set TWINE_USERNAME=__token__
    pause
    goto menu
)

if "%TWINE_PASSWORD%"=="" (
    echo Error: TWINE_PASSWORD environment variable not set
    echo Set it with: set TWINE_PASSWORD=pypi-your-token-here
    pause
    goto menu
)

echo Uploading to TestPyPI...
python -m pip install --upgrade twine
twine upload --repository %TEST_PYPI_REPO% dist\*

if errorlevel 1 (
    echo.
    echo Error: Upload failed
    pause
    goto menu
)

echo.
echo Uploaded to TestPyPI
echo View package at: https://test.pypi.org/project/%PACKAGE_NAME%/
echo.
pause
goto menu

:publish_pypi
cls
echo.
echo ========================================
echo Publish to PyPI
echo ========================================
echo.

for /f "tokens=2 delims==" %%a in ('findstr "__version__" %VERSION_FILE%') do set CURRENT_VERSION=%%a
set CURRENT_VERSION=!CURRENT_VERSION:"=!
set CURRENT_VERSION=!CURRENT_VERSION: =!

echo Warning: You are about to publish version !CURRENT_VERSION! to PyPI
echo This action cannot be undone!
set /p confirm="Are you sure? [y/N]: "

if /i not "!confirm!"=="y" (
    echo Publishing cancelled
    pause
    goto menu
)

if not exist dist\*.whl (
    echo Warning: No build files found. Building now...
    call :build_package
)

if "%TWINE_USERNAME%"=="" (
    echo Error: TWINE_USERNAME environment variable not set
    echo Set it with: set TWINE_USERNAME=__token__
    pause
    goto menu
)

if "%TWINE_PASSWORD%"=="" (
    echo Error: TWINE_PASSWORD environment variable not set
    echo Set it with: set TWINE_PASSWORD=pypi-your-token-here
    pause
    goto menu
)

echo Uploading to PyPI...
python -m pip install --upgrade twine
twine upload dist\*

if errorlevel 1 (
    echo.
    echo Error: Upload failed
    pause
    goto menu
)

echo.
echo Published to PyPI!
echo View package at: https://pypi.org/project/%PACKAGE_NAME%/
echo.
pause
goto menu

:full_workflow
cls
echo.
echo ========================================
echo Full Publishing Workflow
echo ========================================
echo.

REM Step 1: Bump version
call :bump_version
echo.

REM Step 2: Build
set /p confirm="Build package now? [Y/n]: "
if /i not "!confirm!"=="n" (
    call :build_package
    echo.
)

REM Step 3: Test on TestPyPI
set /p confirm="Test on TestPyPI first? [Y/n]: "
if /i not "!confirm!"=="n" (
    call :test_pypi
    echo.
    set /p confirm="TestPyPI test passed. Publish to production PyPI? [y/N]: "
    if /i not "!confirm!"=="y" (
        echo Stopping here. You can publish later with option 4.
        pause
        goto menu
    )
)

REM Step 4: Publish to PyPI
call :publish_pypi
goto menu

:end
echo.
echo Exiting...
exit /b 0

