# YAML Configuration Parser with Environment Variable Substitution

A powerful YAML configuration parser that supports environment variable substitution, similar to docker-compose.yml.

## Features

- **Environment Variable Substitution**: Dynamically inject values from environment variables
- **Default Values**: Provide fallback values when variables are not set
- **Required Variables**: Enforce that certain variables must be set
- **Recursive Processing**: Works with nested dictionaries and lists
- **Docker-Compose Compatible**: Uses the same syntax as docker-compose.yml

## Quick Start

```python
from solvexity.strategy.config.config_parser import yml_to_dict

# Load config with environment variable substitution (default)
config = yml_to_dict('config/my_config.yml')

# Load without substitution
config = yml_to_dict('config/my_config.yml', substitute_env=False)
```

## Supported Syntax

### 1. Simple Substitution: `${VAR}`

Replaces with the value of `VAR` from environment. Returns empty string if not set.

```yaml
app_name: ${APP_NAME}
host: ${HOST}
```

### 2. Simple Format: `$VAR`

Alternative syntax for simple word characters (alphanumeric and underscore).

```yaml
user: $DB_USER
password: $DB_PASSWORD
```

### 3. Default Value: `${VAR:-default}`

Uses the default value if `VAR` is unset or empty.

```yaml
# If DB_HOST is not set, uses 'localhost'
database:
  host: ${DB_HOST:-localhost}
  port: ${DB_PORT:-5432}

# Constructing URLs
nats_url: nats://${NATS_HOST:-localhost}:${NATS_PORT:-4222}
```

### 4. Default If Unset: `${VAR-default}`

Uses the default value only if `VAR` is unset (but keeps empty string if `VAR` is set to empty).

```yaml
# Only use default if VAR is completely unset
path: ${DATA_PATH-./default/path}
```

### 5. Required Variable: `${VAR:?error message}`

Raises an error if `VAR` is not set. Use this for mandatory configuration.

```yaml
database:
  username: ${DB_USER:?Database username is required}
  password: ${DB_PASS:?Database password must be set}
  
api:
  key: ${API_KEY:?API key not found in environment}
```

## Usage Examples

### Example 1: Basic Configuration

**config.yml:**
```yaml
app:
  name: ${APP_NAME:-MyApp}
  environment: ${ENV:-development}
  debug: ${DEBUG:-false}

database:
  host: ${DB_HOST:-localhost}
  port: ${DB_PORT:-5432}
  name: ${DB_NAME:-mydb}
```

**Python:**
```python
import os
from solvexity.strategy.config.config_parser import yml_to_dict

# Set environment variables
os.environ['APP_NAME'] = 'SolvexityTrader'
os.environ['ENV'] = 'production'

# Load config
config = yml_to_dict('config.yml')

print(config['app']['name'])  # Output: SolvexityTrader
print(config['app']['environment'])  # Output: production
print(config['database']['host'])  # Output: localhost (default)
```

### Example 2: Docker-Compose Style

**docker-compose.yml:**
```yaml
services:
  nats:
    image: nats:latest
    command: "--user ${NATS_USER} --pass ${NATS_PASS} -js"
    ports:
      - "${NATS_PORT:-4222}:4222"
    environment:
      - NATS_USER=${NATS_USER:?NATS user required}
      - NATS_PASS=${NATS_PASS:?NATS password required}
```

**Python:**
```python
config = yml_to_dict('docker-compose.yml')
# All environment variables will be substituted
```

### Example 3: Multiple Variables in One String

```yaml
# Construct URLs dynamically
api:
  endpoint: ${PROTOCOL:-https}://${API_HOST}:${API_PORT}/api/${API_VERSION:-v1}

# Construct connection strings
database:
  connection_string: postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}
```

### Example 4: Lists and Nested Structures

```yaml
nats:
  servers:
    - nats://${NATS_HOST1:-localhost}:4222
    - nats://${NATS_HOST2:-localhost}:4223
    - nats://${NATS_HOST3:-localhost}:4224
  
  credentials:
    user: ${NATS_USER:-admin}
    password: ${NATS_PASS}
```

## Best Practices

### 1. Use Descriptive Variable Names

```yaml
# Good
database_host: ${DATABASE_HOST:-localhost}

# Less clear
host: ${HOST:-localhost}
```

### 2. Provide Sensible Defaults

```yaml
# Good - provides safe defaults for development
log_level: ${LOG_LEVEL:-INFO}
timeout: ${REQUEST_TIMEOUT:-30}

# Risky - no default for critical config
api_key: ${API_KEY}
```

### 3. Use Required Variables for Secrets

```yaml
# Good - enforces that secrets are provided
database:
  password: ${DB_PASSWORD:?Database password is required}
  api_key: ${API_KEY:?API key must be set}

# Bad - empty string fallback for sensitive data
password: ${DB_PASSWORD:-}
```

### 4. Document Your Configuration

```yaml
# Environment variables required:
# - NATS_HOST: NATS server hostname
# - NATS_USER: NATS authentication username
# - NATS_PASS: NATS authentication password (required)

nats:
  host: ${NATS_HOST:-localhost}
  user: ${NATS_USER:-admin}
  password: ${NATS_PASS:?NATS password is required}
```

## Environment Variable Management

### Using .env Files

```bash
# .env
APP_NAME=SolvexityTrader
ENV=production
DB_HOST=db.example.com
DB_PORT=5432
NATS_HOST=nats.example.com
```

Load with python-dotenv:

```python
from dotenv import load_dotenv
from solvexity.strategy.config.config_parser import yml_to_dict

# Load environment variables from .env file
load_dotenv()

# Parse config with substitution
config = yml_to_dict('config.yml')
```

### Using System Environment

```bash
# Set environment variables
export APP_NAME=MyApp
export DB_HOST=localhost
export NATS_USER=admin
export NATS_PASS=secret

# Run your application
python main.py
```

### Using Docker

```bash
# Pass environment variables to Docker container
docker run \
  -e APP_NAME=MyApp \
  -e DB_HOST=postgres \
  -e NATS_HOST=nats \
  myimage
```

## Error Handling

### Missing Required Variable

```python
# config.yml contains: ${API_KEY:?API key is required}
try:
    config = yml_to_dict('config.yml')
except ValueError as e:
    print(f"Configuration error: {e}")
    # Output: Configuration error: Required environment variable 'API_KEY' is not set: API key is required
```

## Integration with Pydantic

```python
from pydantic import BaseModel
from solvexity.strategy.config.config_parser import yml_to_dict

class DatabaseConfig(BaseModel):
    host: str
    port: int
    username: str
    password: str

class AppConfig(BaseModel):
    database: DatabaseConfig
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "AppConfig":
        """Load config from YAML with environment variable substitution."""
        config_dict = yml_to_dict(yaml_path)
        return cls(**config_dict)

# Usage
config = AppConfig.from_yaml('config.yml')
```

## Testing

Run tests with pytest:

```bash
pytest tests/test_config_parser.py -v
```

## Demo

Run the demo script to see all features in action:

```bash
python demo_config_parser.py
```

## See Also

- `config/example_config.yml` - Example configuration file
- `tests/test_config_parser.py` - Comprehensive test suite
- `demo_config_parser.py` - Interactive demo

