import io
import zipfile

import pytest

from src.config import SAMPLE_GTFS
from src.validation.validate_feed import FeedValidationError, valid_coordinates, validate_zip


def test_sample_feed_is_valid():
    with zipfile.ZipFile(SAMPLE_GTFS) as zf:
        validate_zip(zf)


def test_missing_file_rejected():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("stops.txt", "stop_id,stop_name,stop_lat,stop_lon\n")
    with zipfile.ZipFile(buf) as zf, pytest.raises(FeedValidationError):
        validate_zip(zf)


def test_coordinates():
    assert valid_coordinates(-1.29, 36.82)
    assert not valid_coordinates(0, 0)
    assert not valid_coordinates(95, 10)
