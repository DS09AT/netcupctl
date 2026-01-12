"""netcup SCP CLI Client."""

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    from importlib_metadata import version, PackageNotFoundError

try:
    __version__ = version("netcupctl")
except PackageNotFoundError:
    # Package not installed, fallback for development
    __version__ = "0.0.0.dev"
