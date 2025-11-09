@echo off
echo ====================================
echo Installing dependencies for all MC folders
echo ====================================
echo.

echo [1/4] Installing dependencies for MC1...
cd MC1
call npm install
cd ..
echo.

echo [2/4] Installing dependencies for MC2...
cd MC2
call npm install
cd ..
echo.

echo [3/4] Installing dependencies for MC3...
cd MC3
call npm install
cd ..
echo.

echo [4/4] Installing dependencies for MC4...
cd MC4
call npm install
cd ..
echo.

echo ====================================
echo All installations completed!
echo ====================================
pause
