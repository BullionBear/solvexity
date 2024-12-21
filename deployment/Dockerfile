# Use the official Python 3.12 image as the base
FROM python:3.12

# Set the working directory in the container
WORKDIR /solvexity

# Add the working directory to the PYTHONPATH
ENV PYTHONPATH=/solvexity

# Copy the Python code and dependency files into the container
COPY . /solvexity

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Specify the command to run your Python script
CMD ["python", "zsrv/main.py", "-s", "FEED"]
