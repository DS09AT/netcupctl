import pytest
import click

from netcupctl.commands.validators import (
    validate_server_id,
    validate_mac_address,
    validate_snapshot_name,
    validate_disk_name,
    validate_ipv4,
    validate_ipv6,
    validate_ip,
    validate_uuid,
)


@pytest.mark.unit
class TestValidateServerId:

    @pytest.mark.parametrize("server_id", [
        "srv-12345",
        "server_123",
        "SERVER-ABC",
        "a1b2c3",
    ])
    def test_valid_server_ids(self, server_id):
        result = validate_server_id(server_id)
        assert result == server_id

    @pytest.mark.parametrize("server_id", [
        "../../../etc/passwd",
        "server;rm -rf /",
        "server$(whoami)",
        "server`id`",
        "server|cat",
        "server<script>",
    ])
    def test_injection_attempts(self, server_id):
        with pytest.raises(click.BadParameter):
            validate_server_id(server_id)

    def test_too_long_server_id(self):
        with pytest.raises(click.BadParameter, match="too long"):
            validate_server_id("a" * 65)

    def test_max_length_server_id(self):
        result = validate_server_id("a" * 64)
        assert len(result) == 64


@pytest.mark.unit
class TestValidateMacAddress:

    @pytest.mark.parametrize("mac,expected", [
        ("00:11:22:33:44:55", "00:11:22:33:44:55"),
        ("AA:BB:CC:DD:EE:FF", "aa:bb:cc:dd:ee:ff"),
        ("aA:bB:cC:dD:eE:fF", "aa:bb:cc:dd:ee:ff"),
    ])
    def test_valid_mac_addresses(self, mac, expected):
        result = validate_mac_address(mac)
        assert result == expected

    @pytest.mark.parametrize("mac", [
        "invalid",
        "00-11-22-33-44-55",
        "00:11:22:33:44",
        "00:11:22:33:44:55:66",
        "GG:HH:II:JJ:KK:LL",
    ])
    def test_invalid_mac_addresses(self, mac):
        with pytest.raises(click.BadParameter):
            validate_mac_address(mac)


@pytest.mark.unit
class TestValidateSnapshotName:

    @pytest.mark.parametrize("name", [
        "snapshot-2024",
        "backup_daily",
        "snap.v1",
        "SNAPSHOT123",
    ])
    def test_valid_snapshot_names(self, name):
        result = validate_snapshot_name(name)
        assert result == name

    def test_empty_snapshot_name(self):
        with pytest.raises(click.BadParameter, match="empty"):
            validate_snapshot_name("")

    def test_whitespace_only_name(self):
        with pytest.raises(click.BadParameter, match="empty"):
            validate_snapshot_name("   ")

    def test_too_long_snapshot_name(self):
        with pytest.raises(click.BadParameter, match="too long"):
            validate_snapshot_name("a" * 129)

    @pytest.mark.parametrize("name", [
        "snap/path",
        "snap;cmd",
        "snap$(id)",
    ])
    def test_invalid_characters(self, name):
        with pytest.raises(click.BadParameter, match="invalid characters"):
            validate_snapshot_name(name)


@pytest.mark.unit
class TestValidateDiskName:

    @pytest.mark.parametrize("name", [
        "system-disk",
        "data_disk",
        "disk.backup",
        "DISK123",
    ])
    def test_valid_disk_names(self, name):
        result = validate_disk_name(name)
        assert result == name

    def test_empty_disk_name(self):
        with pytest.raises(click.BadParameter, match="empty"):
            validate_disk_name("")

    def test_too_long_disk_name(self):
        with pytest.raises(click.BadParameter, match="too long"):
            validate_disk_name("a" * 65)

    @pytest.mark.parametrize("name", [
        "disk/path",
        "disk;rm",
        "disk`cmd`",
    ])
    def test_invalid_characters(self, name):
        with pytest.raises(click.BadParameter, match="invalid characters"):
            validate_disk_name(name)


@pytest.mark.unit
class TestValidateIpv4:

    @pytest.mark.parametrize("ip", [
        "192.168.1.1",
        "10.0.0.1",
        "255.255.255.255",
        "0.0.0.0",
    ])
    def test_valid_ipv4(self, ip):
        result = validate_ipv4(ip)
        assert result == ip

    @pytest.mark.parametrize("ip", [
        "256.1.1.1",
        "192.168.1",
        "192.168.1.1.1",
        "invalid",
        "192.168.1.1/24",
    ])
    def test_invalid_ipv4(self, ip):
        with pytest.raises(click.BadParameter):
            validate_ipv4(ip)


@pytest.mark.unit
class TestValidateIpv6:

    @pytest.mark.parametrize("ip", [
        "2001:db8::1",
        "::1",
        "fe80::1",
        "2001:0db8:0000:0000:0000:0000:0000:0001",
    ])
    def test_valid_ipv6(self, ip):
        result = validate_ipv6(ip)
        assert result is not None

    @pytest.mark.parametrize("ip", [
        "invalid",
        "192.168.1.1",
        "2001:db8::1::2",
        "gggg::1",
    ])
    def test_invalid_ipv6(self, ip):
        with pytest.raises(click.BadParameter):
            validate_ipv6(ip)


@pytest.mark.unit
class TestValidateIp:

    def test_ipv4_detection(self):
        ip, version = validate_ip("192.168.1.1")
        assert version == "v4"

    def test_ipv6_detection(self):
        ip, version = validate_ip("2001:db8::1")
        assert version == "v6"

    def test_invalid_ip(self):
        with pytest.raises(click.BadParameter):
            validate_ip("invalid")


@pytest.mark.unit
class TestValidateUuid:

    @pytest.mark.parametrize("uuid", [
        "550e8400-e29b-41d4-a716-446655440000",
        "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    ])
    def test_valid_uuids(self, uuid):
        result = validate_uuid(uuid)
        assert result == uuid

    @pytest.mark.parametrize("uuid", [
        "invalid",
        "550e8400-e29b-41d4-a716",
        "not-a-uuid-format",
    ])
    def test_invalid_uuids(self, uuid):
        with pytest.raises(click.BadParameter):
            validate_uuid(uuid)
