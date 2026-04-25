"""Entry point for netcupctl CLI."""

import ssl
import sys
import warnings

# Matches the conditional filter in cli.py; needed when the package is run as a module.
if "LibreSSL" in ssl.OPENSSL_VERSION:
    warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")

from netcupctl.cli import main

if __name__ == "__main__":
    sys.exit(main())
