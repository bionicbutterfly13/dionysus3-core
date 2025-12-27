# Quickstart: Neuronal Packet Mental Models

## Verification Scenarios

### 1. Energy-Well Stability
Check boundary energy in Neo4j:
```bash
# Query a cluster's energy barrier
cypher "MATCH (c:MemoryCluster) RETURN c.name, c.boundary_energy"
```

### 2. EFE Competition
Verify that the `EFEEngine` correctly ranks an epistemic action (Recall) over a pragmatic one (Execute) when context is missing:
```bash
docker exec dionysus-api pytest tests/unit/test_efe_engine.py
```

### 3. Metaplasticity
Observe learning rate adjustments during OODA:
```bash
# Monitor logs for surprise-driven adjustments
docker exec dionysus-api tail -f logs/api.log | grep "metaplasticity"
```

## Parallel Testing [P]
You can run the mathematical unit tests in parallel to speed up verification:
```bash
pytest tests/unit/test_efe_engine.py & 
pytest tests/unit/test_metaplasticity.py &
```
