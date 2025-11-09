@echo off
echo ====================================
echo Starting all MC bots...
echo ====================================
echo.

echo Starting MC1...
start "MC1 Bot" cmd /k "cd MC1 && npm start"

echo Starting MC2...
start "MC2 Bot" cmd /k "cd MC2 && npm start"

echo Starting MC3...
start "MC3 Bot" cmd /k "cd MC3 && npm start"

echo Starting MC4...
start "MC4 Bot" cmd /k "cd MC4 && npm start"

echo.
echo ====================================
echo All bots started in separate windows!
echo ====================================
pause
