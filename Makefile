# Variables
IMAGE_NAME = ghcr.io/bullionbear/solvexity
TAG = latest
DOCKERFILE = deployment/Dockerfile
CONTEXT = .

# Build the Docker image
build:
	docker build -t $(IMAGE_NAME):$(TAG) -f $(DOCKERFILE) $(CONTEXT)

# Run the Docker container
push:
	docker push $(IMAGE_NAME):$(TAG)

# Clean up Docker artifacts
clean:
	rm -rf log/*
	rm -rf verbose/*