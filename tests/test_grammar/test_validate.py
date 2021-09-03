"""Unit tests for BEL grammar validation."""

import os
import pathlib
import pandas as pd

from ebel.validate import validate_bel_file


VALIDATION_TEST_DIR = pathlib.Path(__file__).parent.absolute()
TEST_DATA_DIR = os.path.join(VALIDATION_TEST_DIR, "..", "data")

FUNC_REL_TEST_FILE = os.path.join(TEST_DATA_DIR, "function_relation_bel_tests.bel")
TERM_TEST_FILE = os.path.join(TEST_DATA_DIR, "terminology_bel_tests.bel")
BEL2_1_TEST_FILE = os.path.join(TEST_DATA_DIR, "bel_2_1_test_statements.bel")
CORRECT_BEL_FILE = os.path.join(TEST_DATA_DIR, "correct_statements.bel")


class TestValidation:
    """Class for checking the BEL grammar and syntax validation."""

    @staticmethod
    def check_files(grammar_file: str, version: str):
        """Wrapper method to perform the checks."""
        error_report = "function_errors.xlsx"

        with open(grammar_file, "r") as bel_file:
            content = bel_file.readlines()

        num_false_statements = 0
        false_lines = set()
        for line_number, line_text in enumerate(content):
            if line_text == "# Return False\n":
                num_false_statements += 1
                false_lines.add(line_number + 2)  # Add 2 - index starts at 0 and stmt is line after "Return False"

        validate_bel_file(grammar_file, bel_version=version, json_file=False, reports=error_report)

        assert os.path.isfile(error_report)
        error_df = pd.read_excel(error_report)
        num_found_errors = len(error_df)
        assert num_false_statements == num_found_errors
        reported_error_lines = set(error_df["line_number"])
        assert false_lines == reported_error_lines  # Should be the same due to matching line reports
        os.remove(error_report)
        assert not os.path.isfile(error_report)

    def test_function_relation_validation_2_0(self):
        """Check basic grammar and syntax rules using the BEL 2.0 grammar file."""
        self.check_files(grammar_file=FUNC_REL_TEST_FILE, version="2")

    def test_function_relation_validation_2_1(self):
        """Check basic grammar and syntax rules using the BEL 2.1 grammar file."""
        self.check_files(grammar_file=FUNC_REL_TEST_FILE, version="2_1")

    def test_2_1_additions(self):
        """Goes through the new additions to the grammar in BEL 2.1 and verifies they are acceptable."""
        self.check_files(grammar_file=BEL2_1_TEST_FILE, version="2_1")

    def test_json_generation(self):
        error_file_path = os.path.join(TEST_DATA_DIR, "function_errors.xlsx")
        assert not os.path.isfile(error_file_path)
        json_file_path = CORRECT_BEL_FILE + ".json"
        assert not os.path.isfile(json_file_path)

        validate_bel_file(CORRECT_BEL_FILE, bel_version="2_1", json_file=True, reports=error_file_path)
        assert not os.path.isfile(error_file_path)
        assert os.path.isfile(json_file_path)
        os.remove(json_file_path)
        assert not os.path.isfile(json_file_path)
