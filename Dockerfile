FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY board ./board
COPY project ./project
COPY .streamlit ./.streamlit
ENV PYTHONPATH=/app
ENV APP_ENV=production
ENV POST_SOURCE=local
ENV SEED_DEMO=1
EXPOSE 8501
CMD ["streamlit", "run", "project/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
