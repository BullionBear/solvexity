# Solvexity

## Generate proto
```
./scripts/grpc.sh codegen
```

## Run gRPC server
```
python -m solvexity.main
```

## Unittest & Integration Test
### Unittest
```
pytest -m "not integration"
```

### Integration test
For each test in integration test, developer need to add decorator like:
```
@pytest.mark.integration
def test_request_sql_klines(feed):
```

Start local resource
```
docker compose up -d 
```

Run integration test
```
pytest -m integration
```

### Run all tests
```
pytest 
```