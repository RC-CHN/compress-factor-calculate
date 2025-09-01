FROM python:3.10-slim
WORKDIR /app
COPY api.py calculator.py calculator_optimized.py calculator_pure.py constants.py ./
RUN pip install fastapi uvicorn numpy
EXPOSE 8003
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8003"]