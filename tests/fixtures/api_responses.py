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

OPENAPI_SPEC_RESPONSE = {
    "openapi": "3.0.0",
    "info": {
        "title": "Netcup Server Control Panel API",
        "version": "1.2.3",
        "description": "REST API for netcup vServer management",
    },
    "servers": [
        {"url": "https://servercontrolpanel.de/scp-core/api/v1"}
    ],
    "paths": {
        "/servers": {
            "get": {
                "summary": "List servers",
                "operationId": "listServers",
                "responses": {
                    "200": {
                        "description": "List of servers",
                        "content": {
                            "application/json": {
                                "schema": {"type": "array"}
                            }
                        },
                    }
                },
            }
        }
    },
}

OPENAPI_SPEC_INVALID_RESPONSE = '{"openapi": "3.0.0", "info": {"title": "Test" INVALID JSON'

DEVICE_AUTH_ERROR_AUTHORIZATION_PENDING = {
    "error": "authorization_pending",
    "error_description": "User has not yet authorized device",
}

DEVICE_AUTH_ERROR_SLOW_DOWN = {
    "error": "slow_down",
    "error_description": "Polling too frequently",
}

DEVICE_AUTH_ERROR_ACCESS_DENIED = {
    "error": "access_denied",
    "error_description": "User denied authorization",
}

DEVICE_AUTH_ERROR_EXPIRED_TOKEN = {
    "error": "expired_token",
    "error_description": "Device code has expired",
}

CUSTOM_IMAGE_LIST_RESPONSE = [
    {
        "key": "my-ubuntu-2204",
        "name": "Ubuntu 22.04 Custom",
        "size": 2147483648,
        "created_at": "2024-01-15T10:00:00Z",
        "status": "available",
    },
    {
        "key": "my-debian-12",
        "name": "Debian 12 Custom",
        "size": 1073741824,
        "created_at": "2024-01-10T09:00:00Z",
        "status": "available",
    },
]

CUSTOM_IMAGE_DETAIL_RESPONSE = {
    "key": "my-ubuntu-2204",
    "name": "Ubuntu 22.04 Custom",
    "size": 2147483648,
    "created_at": "2024-01-15T10:00:00Z",
    "status": "available",
    "description": "Custom Ubuntu 22.04 with pre-configured software",
}

UPLOAD_INIT_RESPONSE = {
    "uploadId": "upload-abc123def456",
    "key": "my-new-image",
}

UPLOAD_PART_RESPONSE = {
    "etag": "etag-part-12345",
    "partNumber": 1,
}

UPLOAD_COMPLETE_RESPONSE = {
    "key": "my-new-image",
    "status": "processing",
    "message": "Upload completed successfully",
}

CUSTOM_ISO_LIST_RESPONSE = [
    {
        "key": "my-rescue-iso",
        "name": "Custom Rescue ISO",
        "size": 524288000,
        "created_at": "2024-01-12T14:00:00Z",
        "status": "available",
    },
]

CUSTOM_ISO_DETAIL_RESPONSE = {
    "key": "my-rescue-iso",
    "name": "Custom Rescue ISO",
    "size": 524288000,
    "created_at": "2024-01-12T14:00:00Z",
    "status": "available",
    "description": "Custom rescue system",
}

FIREWALL_POLICY_LIST_RESPONSE = [
    {
        "id": "policy-001",
        "name": "web-server-policy",
        "description": "Allow HTTP/HTTPS traffic",
        "rules": [
            {
                "direction": "inbound",
                "protocol": "tcp",
                "port": "80",
                "source": "0.0.0.0/0",
                "action": "allow",
            },
            {
                "direction": "inbound",
                "protocol": "tcp",
                "port": "443",
                "source": "0.0.0.0/0",
                "action": "allow",
            },
        ],
        "created_at": "2024-01-10T00:00:00Z",
    },
    {
        "id": "policy-002",
        "name": "ssh-only-policy",
        "description": "Allow SSH from specific IPs",
        "rules": [
            {
                "direction": "inbound",
                "protocol": "tcp",
                "port": "22",
                "source": "203.0.113.0/24",
                "action": "allow",
            },
        ],
        "created_at": "2024-01-08T00:00:00Z",
    },
]

FIREWALL_POLICY_DETAIL_RESPONSE = {
    "id": "policy-001",
    "name": "web-server-policy",
    "description": "Allow HTTP/HTTPS traffic",
    "rules": [
        {
            "direction": "inbound",
            "protocol": "tcp",
            "port": "80",
            "source": "0.0.0.0/0",
            "action": "allow",
        },
        {
            "direction": "inbound",
            "protocol": "tcp",
            "port": "443",
            "source": "0.0.0.0/0",
            "action": "allow",
        },
    ],
    "created_at": "2024-01-10T00:00:00Z",
    "updated_at": "2024-01-10T00:00:00Z",
    "server_count": 5,
}

SSH_KEY_DETAIL_RESPONSE = {
    "id": "key-001",
    "name": "my-laptop",
    "fingerprint": "SHA256:abcdef123456",
    "public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC...",
    "created_at": "2024-01-01T00:00:00Z",
}

USER_UPDATE_RESPONSE = {
    "sub": "user_123",
    "id": "user_123",
    "preferred_username": "testuser",
    "email": "updated@example.com",
    "email_verified": True,
}

SNAPSHOT_DETAIL_RESPONSE = {
    "id": "snap-001",
    "name": "backup-2024-01-15",
    "created_at": "2024-01-15T00:00:00Z",
    "size": 52428800,
    "server_id": "srv-12345",
    "status": "available",
    "description": "Daily backup",
}

SNAPSHOT_EXPORT_RESPONSE = {
    "id": "snap-001",
    "export_url": "https://example.com/exports/snap-001.tar.gz",
    "expires_at": "2024-01-16T00:00:00Z",
}

SNAPSHOT_CREATE_RESPONSE = {
    "id": "snap-002",
    "name": "new-backup",
    "server_id": "srv-12345",
    "status": "creating",
}

SNAPSHOT_DRYRUN_RESPONSE = {
    "estimated_size": 52428800,
    "estimated_duration": 300,
    "warnings": [],
}

FAILOVER_IP_LIST_RESPONSE = [
    {
        "id": "fip-001",
        "ip": "203.0.113.100",
        "server_id": "srv-12345",
        "status": "active",
        "created_at": "2024-01-10T00:00:00Z",
    },
    {
        "id": "fip-002",
        "ip": "203.0.113.101",
        "server_id": None,
        "status": "unassigned",
        "created_at": "2024-01-12T00:00:00Z",
    },
]

FAILOVER_IP_DETAIL_RESPONSE = {
    "id": "fip-001",
    "ip": "203.0.113.100",
    "server_id": "srv-12345",
    "status": "active",
    "created_at": "2024-01-10T00:00:00Z",
    "netmask": "255.255.255.255",
    "gateway": "203.0.113.1",
}

FIREWALL_RULES_RESPONSE = {
    "rules": [
        {
            "direction": "inbound",
            "protocol": "tcp",
            "port": "22",
            "source": "0.0.0.0/0",
            "action": "allow",
        },
        {
            "direction": "inbound",
            "protocol": "tcp",
            "port": "80",
            "source": "0.0.0.0/0",
            "action": "allow",
        },
    ],
    "default_policy": "drop",
}

FIREWALL_STATUS_RESPONSE = {
    "enabled": True,
    "rules_count": 5,
    "last_applied": "2024-01-15T10:00:00Z",
}

IMAGE_LIST_RESPONSE = [
    {
        "id": "img-001",
        "name": "Ubuntu 22.04 LTS",
        "version": "22.04",
        "os": "ubuntu",
        "type": "base",
        "size": 2147483648,
    },
    {
        "id": "img-002",
        "name": "Debian 12",
        "version": "12",
        "os": "debian",
        "type": "base",
        "size": 1073741824,
    },
]

IMAGE_DETAIL_RESPONSE = {
    "id": "img-001",
    "name": "Ubuntu 22.04 LTS",
    "version": "22.04",
    "os": "ubuntu",
    "type": "base",
    "size": 2147483648,
    "description": "Ubuntu 22.04 LTS base image",
    "min_disk": 10,
    "min_ram": 1024,
    "created_at": "2024-01-01T00:00:00Z",
}

IMAGE_REQUIREMENTS_RESPONSE = {
    "min_disk": 10,
    "min_ram": 1024,
    "min_cpu": 1,
    "supported_server_types": ["vps-1", "vps-2", "vps-3"],
}

ISO_LIST_RESPONSE = [
    {
        "id": "iso-001",
        "name": "Ubuntu 22.04 Server",
        "version": "22.04",
        "size": 1468006400,
        "type": "linux",
    },
    {
        "id": "iso-002",
        "name": "Debian 12 NetInstall",
        "version": "12.0",
        "size": 629145600,
        "type": "linux",
    },
]

ISO_DETAIL_RESPONSE = {
    "id": "iso-001",
    "name": "Ubuntu 22.04 Server",
    "version": "22.04",
    "size": 1468006400,
    "type": "linux",
    "description": "Ubuntu 22.04 LTS Server installation ISO",
    "created_at": "2024-01-01T00:00:00Z",
}

ISO_MOUNT_RESPONSE = {
    "server_id": "srv-12345",
    "iso_id": "iso-001",
    "status": "mounted",
    "mounted_at": "2024-01-15T10:00:00Z",
}
