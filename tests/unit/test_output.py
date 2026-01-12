import pytest
import json
from io import StringIO
from unittest.mock import patch

from netcupctl.output import OutputFormatter


@pytest.mark.unit
class TestOutputFormatter:

    def test_init_default_format(self):
        formatter = OutputFormatter()

        assert formatter.format == "list"

    @pytest.mark.parametrize("format_type", ["json", "table", "list"])
    def test_init_with_format(self, format_type):
        formatter = OutputFormatter(format=format_type)

        assert formatter.format == format_type

    def test_output_json_dict(self, capsys):
        formatter = OutputFormatter(format="json")
        data = {"id": "123", "name": "test"}

        formatter.output(data)

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output == data

    def test_output_json_list(self, capsys):
        formatter = OutputFormatter(format="json")
        data = [{"id": "1"}, {"id": "2"}]

        formatter.output(data)

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output == data

    def test_output_json_invalid_data(self, capsys):
        formatter = OutputFormatter(format="json")

        class NotSerializable:
            pass

        formatter.output(NotSerializable())

        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_output_list_empty_dict(self):
        formatter = OutputFormatter(format="list")

        with patch.object(formatter.console, "print") as mock_print:
            formatter.output({})

        mock_print.assert_called()

    def test_output_list_empty_list(self):
        formatter = OutputFormatter(format="list")

        with patch.object(formatter.console, "print") as mock_print:
            formatter.output([])

        mock_print.assert_called()

    def test_output_list_single_dict(self):
        formatter = OutputFormatter(format="list")
        data = {"id": "123", "name": "test"}

        with patch.object(formatter.console, "print") as mock_print:
            formatter.output(data)

        mock_print.assert_called()

    def test_output_list_multiple_dicts(self):
        formatter = OutputFormatter(format="list")
        data = [{"id": "1"}, {"id": "2"}]

        with patch.object(formatter.console, "print") as mock_print:
            formatter.output(data)

        assert mock_print.call_count >= 2

    def test_output_table_empty_dict(self):
        formatter = OutputFormatter(format="table")

        with patch.object(formatter.console, "print") as mock_print:
            formatter.output({})

        mock_print.assert_called()

    def test_output_table_empty_list(self):
        formatter = OutputFormatter(format="table")

        with patch.object(formatter.console, "print") as mock_print:
            formatter.output([])

        mock_print.assert_called()

    def test_output_table_single_dict(self):
        formatter = OutputFormatter(format="table")
        data = {"id": "123", "name": "test"}

        with patch.object(formatter.console, "print") as mock_print:
            formatter.output(data)

        mock_print.assert_called()

    def test_output_table_list_of_dicts(self):
        formatter = OutputFormatter(format="table")
        data = [{"id": "1", "name": "a"}, {"id": "2", "name": "b"}]

        with patch.object(formatter.console, "print") as mock_print:
            formatter.output(data)

        mock_print.assert_called()

    def test_output_table_list_of_non_dicts(self):
        formatter = OutputFormatter(format="table")
        data = ["item1", "item2"]

        with patch.object(formatter.console, "print") as mock_print:
            formatter.output(data)

        mock_print.assert_called()

    def test_format_value_none(self):
        formatter = OutputFormatter()

        result = formatter._format_value(None)

        assert result == ""

    def test_format_value_bool_true(self):
        formatter = OutputFormatter()

        result = formatter._format_value(True)

        assert result == "Yes"

    def test_format_value_bool_false(self):
        formatter = OutputFormatter()

        result = formatter._format_value(False)

        assert result == "No"

    def test_format_value_string(self):
        formatter = OutputFormatter()

        result = formatter._format_value("test string")

        assert result == "test string"

    def test_format_value_number(self):
        formatter = OutputFormatter()

        result = formatter._format_value(42)

        assert result == "42"

    def test_format_value_dict(self):
        formatter = OutputFormatter()

        result = formatter._format_value({"key": "value"})

        assert "key" in result
        assert "value" in result

    def test_format_value_empty_dict(self):
        formatter = OutputFormatter()

        result = formatter._format_value({})

        assert result == "{}"

    def test_format_value_list(self):
        formatter = OutputFormatter()

        result = formatter._format_value(["a", "b", "c"])

        assert "a" in result
        assert "b" in result

    def test_format_value_empty_list(self):
        formatter = OutputFormatter()

        result = formatter._format_value([])

        assert result == "[]"

    def test_format_value_nested_dict_max_depth(self):
        formatter = OutputFormatter()
        deeply_nested = {"l1": {"l2": {"l3": {"l4": {"l5": "value"}}}}}

        result = formatter._format_value(deeply_nested, depth=0, max_depth=4)

        assert "l1" in result

    def test_format_list_primitives(self):
        formatter = OutputFormatter()

        result = formatter._format_list([1, 2, 3], depth=0, max_depth=4)

        assert "1" in result
        assert "2" in result
        assert "3" in result

    def test_format_list_with_dicts(self):
        formatter = OutputFormatter()

        result = formatter._format_list([{"a": 1}, {"b": 2}], depth=0, max_depth=4)

        assert "a" in result
        assert "b" in result

    def test_output_unknown_format_defaults_to_list(self):
        formatter = OutputFormatter(format="unknown")

        with patch.object(formatter, "_output_list") as mock_list:
            formatter.output({"test": "data"})

        mock_list.assert_called_once()
