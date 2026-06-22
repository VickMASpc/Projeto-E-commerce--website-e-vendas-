@echo off
setlocal
cd /d "%~dp0"

REM Para usar o executavel gerado com PyInstaller, coloque GrandParfumServer.exe nesta pasta
REM e troque a linha "python launcher.py "%%~1"" por "GrandParfumServer.exe "%%~1"".
REM O executavel tambem espera configuracao externa; nao embuta serviceAccountKey.json nem .env real.

if "%~1"=="" (
  echo Grand Parfum - servidor headless
  echo.
  echo Arraste um arquivo server_config.json ou serviceAccountKey.json sobre este .bat.
  echo.
  echo Exemplo server_config.json:
  echo {"host":"0.0.0.0","port":5000,"credentialsPath":"C:\\seguro\\serviceAccountKey.json","apiToken":"troque-este-token","allowedOrigins":["http://localhost:5173"]}
  echo.
  pause
  exit /b 0
)

python launcher.py "%~1"
pause
