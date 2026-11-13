# RACE collaborative document sidecar

This optional sidecar runs the Yjs/y-websocket document server on port 1234. It provides CRDT document synchronization primitives for a future multi-operator floor-plan editor. It is intentionally isolated from the simulation control channel: shared document edits must be validated and converted into a versioned environment configuration before a simulation reset/restart.

Start it with `docker compose --profile collaboration up --build collaboration`.

The current React application does not yet expose collaborative obstacle editing or connect a Yjs client. This sidecar is infrastructure groundwork, not a claim that collaborative editing is already available in the UI. Before production, add authentication, room authorization, persistence (y-leveldb or equivalent), and a frontend Yjs provider.
