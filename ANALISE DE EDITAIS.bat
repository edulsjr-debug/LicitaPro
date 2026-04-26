@echo off
title Análise de Editais
echo Iniciando o sistema de análise de editais...
echo.

:: encerra qualquer instância anterior do Python
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

echo Aguarde o navegador abrir automaticamente.
echo Para encerrar, feche esta janela.
echo.

:: abre o navegador após 4 segundos
start /min "" cmd /c "timeout /t 4 /nobreak >nul && start http://localhost:8000"

:: inicia o servidor
cd /d C:\projetos\proxy-licitacao
venv\Scripts\python main.py
