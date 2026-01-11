# Use a slim Python image
FROM python:3.10-slim

# Set working directory to the root of your project
WORKDIR /code

# Copy requirements and install
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the entire project
COPY . /code/

# Run Uvicorn pointing to the app folder's main.py
# Assuming your FastAPI instance is named 'app' inside main.py
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]