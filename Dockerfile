# Use an official Python runtime as a parent image
FROM python:3.12.7-slim

# Set the working directory in the container
WORKDIR /code

# Copy the requirements.txt and install dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the application code
COPY ./src /code/src

EXPOSE 8501

CMD ["streamlit", "run", "src/chatbot.py", "--server.port=8501", "--server.address=0.0.0.0"]