FROM python:3.11-slim

WORKDIR /code

# Copy requirements first to leverage Docker caching
COPY ./requirements.txt /code/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the rest of the application files
COPY . .

# Hugging Face Spaces strictly requires traffic on port 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
