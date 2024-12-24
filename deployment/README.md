# Push and Pull Docker Images with GitHub Container Registry (ghcr.io)

This guide explains how to authenticate with GitHub Container Registry (ghcr.io), push Docker images to it, and pull images from it.

## Prerequisites
1. Docker installed on your system.
2. A GitHub account.
3. GitHub CLI or a personal access token (PAT) with the `write:packages` and `read:packages` scopes enabled.

---

## Steps to Push an Image to ghcr.io

### 1. Log in to GitHub Container Registry

Log in using your GitHub username and a personal access token (PAT):

```bash
docker login ghcr.io
```

You will be prompted to enter:
- **Username**: Your GitHub username.
- **Password**: Your PAT (Personal Access Token).

If the login is successful, Docker will save the credentials for `ghcr.io`.

---

### 2. Build Your Docker Container

Before pushing, ensure your Docker image is built. Use the following command:

Example:
```bash
docker build -t ghcr.io/bullionbear/solvexity:latest .
```


### 3. Tag Your Docker Image

Ensure your Docker image is tagged correctly. The format should be:

```bash
docker tag solvexity ghcr.io/BullionBear/solvexity:latest
```

---

### 4. Push the Image to ghcr.io

Use the `docker push` command:

Example:
```bash
docker push ghcr.io/BullionBear/solvexity:latest
```

---

## Steps to Pull an Image from ghcr.io

1. Authenticate with `ghcr.io` if not already logged in:

```bash
docker login ghcr.io
```

2. Pull the image using the `docker pull` command:

```bash
docker pull ghcr.io/BullionBear/solvexity:latest
```

