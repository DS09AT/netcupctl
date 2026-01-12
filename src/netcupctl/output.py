"""Output formatting for netcupctl."""

import json
import sys
from typing import Any

from rich.console import Console
from rich.table import Table


class OutputFormatter:
    """Handles output formatting."""

    def __init__(self, format: str = "json"):
        """Initialize output formatter.

        Args:
            format: Output format ('json' or 'table')
        """
        self.format = format
        self.console = Console()

    def output(self, data: Any) -> None:
        """Output data in specified format.

        Args:
            data: Data to output (dict, list, or other)
        """
        if self.format == "json":
            self._output_json(data)
        elif self.format == "table":
            self._output_table(data)
        else:
            self._output_json(data)

    def _output_json(self, data: Any) -> None:
        """Output data as JSON.

        Args:
            data: Data to output
        """
        try:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            print(json_str)
        except (TypeError, ValueError):
            print("Error: Could not format data as JSON", file=sys.stderr)

    def _output_table(self, data: Any) -> None:
        """Output data as table using rich.

        Args:
            data: Data to output (expects list of dicts or single dict)
        """
        if isinstance(data, dict):
            if not data:
                self.console.print("[yellow]No data[/yellow]")
                return
            data = [data]

        if isinstance(data, list):
            if not data:
                self.console.print("[yellow]No data[/yellow]")
                return

            all_keys = set()
            for item in data:
                if isinstance(item, dict):
                    all_keys.update(item.keys())

            if not all_keys:
                self.console.print("[yellow]No data[/yellow]")
                return

            table = Table(show_header=True, header_style="bold cyan")

            for key in sorted(all_keys):
                table.add_column(str(key))

            for item in data:
                if isinstance(item, dict):
                    row = [self._format_value(item.get(key, "")) for key in sorted(all_keys)]
                    table.add_row(*row)

            self.console.print(table)
        else:
            self.console.print(str(data))

    def _format_value(self, value: Any) -> str:
        """Format a value for table display.

        Args:
            value: Value to format

        Returns:
            Formatted string
        """
        if value is None:
            return ""
        elif isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        elif isinstance(value, bool):
            return "✓" if value else "✗"
        else:
            return str(value)
