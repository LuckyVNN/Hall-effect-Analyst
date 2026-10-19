@echo off
title Hall Effect Measurement Analyzer
echo Starting Hall Effect Analyzer in your default web browser...
python -m streamlit run app.py --server.headless=false
pause
