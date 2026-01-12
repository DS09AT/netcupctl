"""Output formatting for netcupctl."""

import json
import sys
from typing import Any

from rich.console import Console
from rich.table import Table

if sys.platform == "win32":
    import codecs
    if sys.stdout.encoding != "utf-8":
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")


class OutputFormatter:
    """Handles output formatting."""

    def __init__(self, format: str = "list"):
        """Initialize output formatter.

        Args:
            format: Output format ('json', 'table', or 'list')
        """
        self.format = format
        self.console = Console(legacy_windows=False, safe_box=True)

    def output(self, data: Any) -> None:
        """Output data in specified format.

        Args:
            data: Data to output (dict, list, or other)
        """
        if self.format == "json":
            self._output_json(data)
        elif self.format == "table":
            self._output_table(data)
        elif self.format == "list":
            self._output_list(data)
        else:
            self._output_list(data)

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

    def _output_list(self, data: Any) -> None:
        """Output data in list view format (human-readable key-value).

        Args:
            data: Data to output (expects list of dicts or single dict)
        """
        if isinstance(data, dict):
            if not data:
                self.console.print("[yellow]No data[/yellow]")
                return
            self._output_list_item(data)
            return

        if isinstance(data, list):
            if not data:
                self.console.print("[yellow]No data[/yellow]")
                return

            for i, item in enumerate(data):
                if i > 0:
                    self.console.print()
                    self.console.print("─" * 80, style="dim")
                    self.console.print()

                if isinstance(item, dict):
                    self._output_list_item(item)
                else:
                    self.console.print(str(item))
        else:
            self.console.print(str(data))

    def _output_list_item(self, data: dict) -> None:
        """Output a single dict item in list format.

        Args:
            data: Dictionary to output
        """
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="bold cyan", no_wrap=True)
        table.add_column("Value", no_wrap=False)

        for key in sorted(data.keys()):
            value = self._format_value(data[key])
            table.add_row(str(key), value)

        self.console.print(table)

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

    def _format_value(self, value: Any, depth: int = 0, max_depth: int = 4) -> str:
        """Format a value for table display.

        Args:
            value: Value to format
            depth: Current recursion depth
            max_depth: Maximum recursion depth for nested structures

        Returns:
            Formatted string
        """
        if value is None:
            return ""
        elif isinstance(value, bool):
            return "Yes" if value else "No"
        elif isinstance(value, dict):
            return self._format_dict(value, depth, max_depth)
        elif isinstance(value, list):
            return self._format_list(value, depth, max_depth)
        else:
            return str(value)

    def _format_dict(self, value: dict, depth: int, max_depth: int) -> str:
        """Format a dictionary for table display.

        Args:
            value: Dictionary to format
            depth: Current recursion depth
            max_depth: Maximum recursion depth

        Returns:
            Formatted string with key-value pairs
        """
        if not value:
            return "{}"

        if depth >= max_depth:
            return json.dumps(value, ensure_ascii=False)

        items = []
        for k, v in value.items():
            formatted_val = self._format_value(v, depth + 1, max_depth)
            if depth > 0:
                formatted_val = formatted_val.replace("\n", " ")
            items.append(f"{k}: {formatted_val}")

        return "\n".join(items)

    def _format_list(self, value: list, depth: int, max_depth: int) -> str:
        """Format a list for table display.

        Args:
            value: List to format
            depth: Current recursion depth
            max_depth: Maximum recursion depth

        Returns:
            Formatted string
        """
        if not value:
            return "[]"

        if depth >= max_depth:
            return json.dumps(value, ensure_ascii=False)

        all_primitives = all(
            not isinstance(item, (dict, list)) for item in value
        )

        if all_primitives:
            formatted_items = [self._format_value(item, depth + 1, max_depth) for item in value]
            return ", ".join(formatted_items)
        else:
            formatted_items = []
            for item in value:
                formatted = self._format_value(item, depth + 1, max_depth)
                if depth > 0 or isinstance(item, dict):
                    formatted = formatted.replace("\n", " | ")
                formatted_items.append(formatted)

            if depth == 0:
                return "\n• " + "\n• ".join(formatted_items)
            else:
                return "; ".join(formatted_items)
