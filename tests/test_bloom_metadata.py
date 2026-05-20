"""Tests for BloomMetaData."""

import pytest

from budtestlibrary.bloom_metadata import BloomMetaData


class TestBloomMetaData:
    def test_full_tc_id_format(self):
        bm = BloomMetaData(project="MyProject", tc_id_suffix="001")
        assert bm.get_full_tc_id() == "MyProject-TC-001"

    def test_url_with_configurable_base(self):
        bm = BloomMetaData(project="MyProject", tc_id_suffix="001")
        url = bm.get_url(base_url="https://custom-bloom.example.com/")
        assert url == "https://custom-bloom.example.com/projects/MyProject/test-cases/001"

    def test_url_defaults_to_empty_base(self):
        bm = BloomMetaData(project="MyProject", tc_id_suffix="001")
        url = bm.get_url(base_url="")
        assert url == "/projects/MyProject/test-cases/001"

    def test_to_dict(self):
        bm = BloomMetaData(project="MyProject", tc_id_suffix="002", description="A test case")
        d = bm.to_dict()
        assert d["project"] == "MyProject"
        assert d["tc_id"] == "MyProject-TC-002"
        assert d["display_id"] == "MyProject-TC-002"
        assert d["description"] == "A test case"
        assert "url" in d

    def test_optional_description(self):
        bm = BloomMetaData(project="Proj", tc_id_suffix="X")
        assert bm.description is None
        assert bm.to_dict()["description"] is None

    def test_field_validation_rejects_empty_project(self):
        """Validate that project and tc_id_suffix are non-empty strings."""
        with pytest.raises(ValueError):
            BloomMetaData(project="", tc_id_suffix="001")

    def test_field_validation_rejects_empty_suffix(self):
        with pytest.raises(ValueError):
            BloomMetaData(project="Proj", tc_id_suffix="")

    def test_field_validation_rejects_invalid_suffix_format(self):
        """tc_id_suffix should match alphanumeric pattern."""
        with pytest.raises(ValueError):
            BloomMetaData(project="Proj", tc_id_suffix="##invalid##")
