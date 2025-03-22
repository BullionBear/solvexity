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
### Integration test

Start local resource
```
docker compose up -d 
```

Run integration test
```
pytest -m integration
```