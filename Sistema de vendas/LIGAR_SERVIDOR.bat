@echo off
setlocal
cd /d "%~dp0"

REM Grand Parfum - atalho de primeira configuracao e uso diario
REM
REM Fluxo de primeira instalacao:
REM   1. Arraste o serviceAccountKey.json do Firebase sobre este .bat
REM   2. O launcher valida, copia para %%APPDATA%%\GrandParfum\serviceAccountKey.json
REM   3. O launcher salva a configuracao local fora do repositorio
REM   4. O servidor sobe em GRAND_PARFUM_MODE=production por padrao
REM
REM Fluxo de inicializacao diaria:
REM   1. Dê duplo clique neste .bat, sem arrastar nada
REM   2. Se a credencial persistida existir, o servidor sobe usando ela
REM
REM Para usar o executavel PyInstaller:
REM   - coloque GrandParfumServer.exe nesta pasta
REM   - troque "python launcher.py" por "GrandParfumServer.exe"
REM   - o executavel tambem depende de configuracao externa; nao embuta credenciais reais

if "%~1"=="" (
  echo Grand Parfum - inicializacao diaria
  echo.
  echo Nenhum arquivo foi arrastado.
  echo Tentando iniciar com a configuracao persistida em %%APPDATA%%\GrandParfum...
  echo.
  python launcher.py
  pause
  exit /b %errorlevel%
)

echo Grand Parfum - primeira configuracao / atualizacao
echo.
echo Arquivo recebido: %~1
echo.
python launcher.py "%~1"
pause
