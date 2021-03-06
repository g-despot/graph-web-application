FROM python:3.9

# Install CMake
RUN apt-get update && \
  apt-get --yes install cmake && \
  rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt ./
RUN pip3 install -r requirements.txt

# Copy the source code
COPY public /app/public
COPY app.py /app/app.py
WORKDIR /app

# Set the environment variables
ENV FLASK_ENV=development
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Start the web application
ENTRYPOINT ["python3", "app.py"]
