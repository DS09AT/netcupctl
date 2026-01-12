SERVER_LIST_RESPONSE = [
    {
        "id": "srv-12345",
        "name": "web-server-01",
        "status": "running",
        "ipv4": "203.0.113.10",
        "ipv6": "2001:db8::1",
        "cpu": 4,
        "memory": 8192,
        "disk": 100,
    },
    {
        "id": "srv-67890",
        "name": "db-server-01",
        "status": "stopped",
        "ipv4": "203.0.113.20",
        "ipv6": "2001:db8::2",
        "cpu": 8,
        "memory": 16384,
        "disk": 500,
    },
]

SERVER_DETAIL_RESPONSE = {
    "id": "srv-12345",
    "name": "web-server-01",
    "status": "running",
    "ipv4": "203.0.113.10",
    "ipv6": "2001:db8::1",
    "cpu": 4,
    "memory": 8192,
    "disk": 100,
    "created_at": "2024-01-15T10:30:00Z",
    "datacenter": "NBG1",
}

DISK_LIST_RESPONSE = [
    {
        "id": "disk-001",
        "name": "system-disk",
        "size": 100,
        "type": "ssd",
        "server_id": "srv-12345",
    },
    {
        "id": "disk-002",
        "name": "data-disk",
        "size": 500,
        "type": "hdd",
        "server_id": "srv-12345",
    },
]

SNAPSHOT_LIST_RESPONSE = [
    {
        "id": "snap-001",
        "name": "backup-2024-01-15",
        "created_at": "2024-01-15T00:00:00Z",
        "size": 50,
        "server_id": "srv-12345",
    },
]

SSH_KEY_LIST_RESPONSE = [
    {
        "id": "key-001",
        "name": "my-laptop",
        "fingerprint": "SHA256:abcdef123456",
        "created_at": "2024-01-01T00:00:00Z",
    },
]

FIREWALL_RULE_RESPONSE = {
    "id": "fw-001",
    "direction": "inbound",
    "protocol": "tcp",
    "port": "22",
    "source": "0.0.0.0/0",
    "action": "allow",
}

VLAN_LIST_RESPONSE = [
    {
        "id": "vlan-001",
        "name": "internal",
        "vlan_id": 100,
        "servers": ["srv-12345", "srv-67890"],
    },
]

INTERFACE_LIST_RESPONSE = [
    {
        "id": "iface-001",
        "name": "eth0",
        "mac": "00:11:22:33:44:55",
        "ipv4": "203.0.113.10",
        "ipv6": "2001:db8::1",
        "type": "public",
    },
]

TASK_RESPONSE = {
    "id": "task-001",
    "type": "server_start",
    "status": "completed",
    "progress": 100,
    "created_at": "2024-01-15T10:00:00Z",
    "completed_at": "2024-01-15T10:01:00Z",
}

METRICS_RESPONSE = {
    "cpu": {"current": 45.2, "average": 30.5, "peak": 95.0},
    "memory": {"current": 4096, "total": 8192, "percent": 50.0},
    "disk": {"read_iops": 150, "write_iops": 75, "latency_ms": 2.5},
    "network": {"rx_bytes": 1073741824, "tx_bytes": 536870912},
}

ERROR_RESPONSE_401 = {
    "error": "unauthorized",
    "message": "Invalid or expired token",
}

ERROR_RESPONSE_403 = {
    "error": "forbidden",
    "message": "Access denied",
}

ERROR_RESPONSE_404 = {
    "error": "not_found",
    "message": "Resource not found",
}

ERROR_RESPONSE_422 = {
    "errors": [
        {"field": "name", "message": "Name is required"},
        {"field": "size", "message": "Size must be positive"},
    ],
}

ERROR_RESPONSE_500 = {
    "error": "internal_server_error",
    "message": "An unexpected error occurred",
}

TOKEN_RESPONSE = {
    "access_token": "new_access_token_abc123",
    "refresh_token": "new_refresh_token_xyz789",
    "expires_in": 3600,
    "token_type": "Bearer",
}

DEVICE_AUTH_RESPONSE = {
    "device_code": "device_code_12345",
    "user_code": "ABCD-EFGH",
    "verification_uri": "https://auth.example.com/device",
    "verification_uri_complete": "https://auth.example.com/device?code=ABCD-EFGH",
    "expires_in": 600,
    "interval": 5,
}

USERINFO_RESPONSE = {
    "sub": "user_123",
    "id": "user_123",
    "preferred_username": "testuser",
    "email": "test@example.com",
}
