import pytest
from conjure.Conjure import Conjure


def test_conjure_csv_creation():
    """Test that Conjure can create an instance from a CSV file."""
    # Replace with a path to a test CSV file that exists in your test environment
    report = Conjure("tests/fixtures/Reader_Survey_responses_sample.csv")
    assert report is not None
    # Verify the correct type was returned
    from conjure.InputDataCSV import InputDataCSV
    assert isinstance(report, InputDataCSV)


def test_unsupported_file_type():
    """Test that Conjure raises ValueError for unsupported file types."""
    with pytest.raises(ValueError, match="Unsupported file type"):
        Conjure("unsupported_file.xyz")


# Additional tests you might want to add:
# - test_conjure_sav_creation
# - test_conjure_dta_creation
# - test_to_results_method