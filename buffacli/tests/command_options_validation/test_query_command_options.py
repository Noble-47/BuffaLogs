import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from buffacli.exceptions import InvalidArgsException
from buffacli.options import RISK_LEVEL_MAP, RISK_SCORE_TYPE, AlertQueryOptions, QueryOptions, generate_start_and_end_date, risk_level_to_int
from dateutil.relativedelta import relativedelta
from pydantic import ValidationError


class MockFormatOptions:
    def __init__(self, name):
        self.name = name
        self.formatter = lambda *args, **kwargs: "Formatted Content"
        self.print = None

    def __eq__(self, other):
        return self.name == other.name


class MockBaseExporter:
    def __init__(self):
        self.exported_data = None

    def export(self, content):
        self.exported_data = content


# Mock the external 'export' object
mock_export = MagicMock()
mock_export.get_exporter.return_value = MockBaseExporter()


def mock_make_renderable(formatter, mode=None, page_size=None, exporter=None):
    """Mock the function that configures the formatter with render logic."""
    formatter.print = MagicMock(name="MockRenderObject")
    formatter.print.mode = mode
    formatter.print.exporter = exporter
    return formatter


FIXED_TIME = datetime(2025, 3, 15, 12, 0, 0)
LATER_TIME = datetime(2025, 3, 15, 13, 0, 0)
EARLIER_TIME = datetime(2025, 3, 15, 11, 0, 0)


class TestRiskLevelToIn(unittest.TestCase):
    """Tests the risk_level_to_int utility function."""

    def test_valid_string_levels(self):
        self.assertEqual(risk_level_to_int("HIGH"), 8)
        self.assertEqual(risk_level_to_int("medium"), 4)
        self.assertEqual(risk_level_to_int("lOw"), 1)
        self.assertEqual(risk_level_to_int("No Risk"), 0)

    def test_valid_integer_levels(self):
        self.assertEqual(risk_level_to_int(1), 1)
        self.assertEqual(risk_level_to_int(8), 8)
        self.assertEqual(risk_level_to_int(5), 5)

    def test_valid_string_as_integer(self):
        self.assertEqual(risk_level_to_int("0"), 0)
        self.assertEqual(risk_level_to_int("3"), 3)
        self.assertEqual(risk_level_to_int("8"), 8)

    def test_none_input(self):
        self.assertIsNone(risk_level_to_int(None))

    def test_invalid_string(self):
        with self.assertRaisesRegex(
            InvalidArgsException,
            "Risk score must be an integer between 0-8 or one of NO RISK, LOW, MEDIUM, HIGH. Got Extreme",
        ):
            risk_level_to_int("Extreme")

    def test_invalid_integer(self):
        with self.assertRaisesRegex(InvalidArgsException, "Risk score must be an integer between 0-8 or one of NO RISK, LOW, MEDIUM, HIGH"):
            risk_level_to_int(9)


class TestQueryOptions(unittest.TestCase):
    """Tests the QueryOptions Pydantic model."""

    def test_default_options(self):
        options = QueryOptions()
        self.assertIsNone(options.mode)
        self.assertEqual(options.formatter.name, "table")

    def test_process_mappings_valid(self):
        data = {"mappings": "field1:alias1 field2:alias2"}
        options = QueryOptions(**data)
        self.assertEqual(options.mappings, {"field1": "alias1", "field2": "alias2"})

    def test_process_mappings_none(self):
        options = QueryOptions()
        self.assertIsNone(options.mappings)

    def test_process_mappings_invalid(self):
        data = {"mappings": "field1 alias1"}
        with self.assertRaisesRegex(InvalidArgsException, "Mappings must follow the format 'field1:alias1 field2:alias2'"):
            QueryOptions(**data)

    # @patch.object(mock_export, "buffacli.options.export.get_exporter")
    @patch("buffacli.options.export.get_exporter")
    @patch("buffacli.render.make_renderable", new=mock_make_renderable)
    @patch("buffacli.formatters.FormatOptions", new=MockFormatOptions)
    def test_exporter_creation(self, mock_get_exporter):
        mock_exporter_instance = MockBaseExporter()
        mock_get_exporter.return_value = mock_exporter_instance

        file_path = Path("/tmp/output.csv")
        options = QueryOptions(output_file=file_path)

        mock_get_exporter.assert_called_once_with(file_path)
        self.assertEqual(options.formatter.print.exporter, mock_exporter_instance)


class TestAlertQueryOptions(unittest.TestCase):
    """Tests the AlertQueryOptions Pydantic model and its date logic."""

    def setUp(self):
        self.mock_patcher = patch("buffacli.options.datetime", autospec=True)
        self.mock_datetime = self.mock_patcher.start()

        # Freeze time for testing 'since'
        self.mock_datetime.now.return_value = FIXED_TIME
        self.mock_datetime.strptime = datetime.strptime
        self.mock_datetime.timedelta = timedelta
        self.mock_datetime.relativedelta = relativedelta
        self.mock_datetime.now.side_effect = lambda: FIXED_TIME

    def tearDown(self):
        self.mock_patcher.stop()

    @patch("buffacli.options.generate_start_and_end_date", side_effect=generate_start_and_end_date)
    def test_date_range_generation_from_since(self, mock_gen_dates):
        options = AlertQueryOptions(since="2H")

        self.assertEqual(options.end_date, FIXED_TIME)
        self.assertEqual(options.start_date, FIXED_TIME - timedelta(hours=2))
        mock_gen_dates.assert_called_once_with("2H")

    def test_since_and_explicit_date_conflict(self):
        data = {"since": "1d", "start_date": EARLIER_TIME}
        with self.assertRaisesRegex(InvalidArgsException, "Cannot specify start_date/end_date when using 'since'"):
            AlertQueryOptions(**data)

    def test_date_sequence_validation_alert(self):
        # start_date > end_date
        data = {"start_date": LATER_TIME, "end_date": EARLIER_TIME}
        with self.assertRaisesRegex(InvalidArgsException, "Alert End date cannot be earlier than start date"):
            AlertQueryOptions(**data)

    def test_date_sequence_validation_login(self):
        # login_start_time > login_end_time
        data = {"login_start_time": LATER_TIME, "login_end_time": EARLIER_TIME}
        with self.assertRaisesRegex(InvalidArgsException, "Login end date cannot be earlier than login start date"):
            AlertQueryOptions(**data)

    def test_valid_date_sequence(self):
        # start_date < end_date and login_start_time < login_end_time
        data = {
            "start_date": EARLIER_TIME,
            "end_date": LATER_TIME,
            "login_start_time": EARLIER_TIME,
            "login_end_time": LATER_TIME,
        }
        options = AlertQueryOptions(**data)
        self.assertEqual(options.start_date, EARLIER_TIME)
        self.assertEqual(options.end_date, LATER_TIME)
        self.assertEqual(options.login_start_time, EARLIER_TIME)
        self.assertEqual(options.login_end_time, LATER_TIME)

    def test_risk_score_validation(self):
        # Valid risk scores via validator
        options_min = AlertQueryOptions(min_risk_score="LOW")
        self.assertEqual(options_min.min_risk_score, 1)

        options_max = AlertQueryOptions(max_risk_score=8)
        self.assertEqual(options_max.max_risk_score, 8)

        # Invalid risk score format should raise InvalidArgsException
        with self.assertRaises(InvalidArgsException) as cm:
            AlertQueryOptions(risk_score="invalid-level")

        self.assertIn(
            "Risk score must be an integer between 0-8 or one of NO RISK, LOW, MEDIUM, HIGH. Got invalid-level",
            str(cm.exception),
        )


if __name__ == "__main__":
    unittest.main()
