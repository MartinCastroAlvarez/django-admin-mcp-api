"""MCP server layer.

This package owns the wire protocol (MCP JSON-RPC over HTTP) and nothing
else. All admin business logic — permissions, querysets, forms,
serialization, validation — lives in **django-admin-rest-api**. Code here
must never:

- query the database directly
- call ``user.has_perm`` or any other permission check
- serialize or deserialize a model
- mutate any data

Every MCP tool call is reshaped into the equivalent django-admin-rest-api
HTTP request and forwarded through the dispatcher (see ``dispatch.py``).
The response is reshaped back into an MCP JSON-RPC payload. That is all
this package does.
"""
