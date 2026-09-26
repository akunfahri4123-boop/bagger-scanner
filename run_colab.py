# Google Colab launcher
!pip -q install -r requirements.txt
!streamlit run app.py &>/content/bagger_log.txt & npx localtunnel --port 8501
