import os
import tempfile

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .forms import FrequencyField, _hz_to_suffixed
from .models import Device, DeviceCategory, Document
from .touchstone_utils import generate_s_param_plot_data, parse_touchstone

# Minimal valid Touchstone files for testing (no external fixtures needed)
S1P_CONTENT = b"""\
# GHz S RI R 50.0
1.0  -0.5  0.3
2.0  -0.4  0.2
3.0  -0.3  0.1
"""

S2P_CONTENT = b"""\
# GHz S RI R 50.0
1.0  0.1 0.2  0.7 -0.7  0.7 -0.7  0.1 0.2
2.0  0.05 0.1  0.8 -0.6  0.8 -0.6  0.05 0.1
3.0  0.02 0.05  0.9 -0.4  0.9 -0.4  0.02 0.05
"""


# ---------------------------------------------------------------------------
# Frequency parsing
# ---------------------------------------------------------------------------
class FrequencyFieldCleanTest(TestCase):
    """FrequencyField.clean() converts suffixed strings to Hz integers."""

    def setUp(self):
        self.field = FrequencyField(required=False)

    def test_gigahertz(self):
        self.assertEqual(self.field.clean("2.4G"), 2_400_000_000)

    def test_megahertz(self):
        self.assertEqual(self.field.clean("100M"), 100_000_000)

    def test_kilohertz(self):
        self.assertEqual(self.field.clean("10.7k"), 10_700)

    def test_plain_hz(self):
        self.assertEqual(self.field.clean("1500"), 1500)

    def test_with_unit_suffix(self):
        """Accepts '2.4GHz', '100MHz', etc."""
        self.assertEqual(self.field.clean("2.4GHz"), 2_400_000_000)
        self.assertEqual(self.field.clean("100MHz"), 100_000_000)

    def test_whitespace_tolerance(self):
        self.assertEqual(self.field.clean("  2.4 G  "), 2_400_000_000)

    def test_empty_returns_none(self):
        self.assertIsNone(self.field.clean(""))

    def test_invalid_raises(self):
        with self.assertRaises(Exception):
            self.field.clean("not a frequency")


class FrequencyDisplayTest(TestCase):
    """_hz_to_suffixed() and FrequencyField.prepare_value() round-trip."""

    def test_ghz_display(self):
        self.assertEqual(_hz_to_suffixed(2_400_000_000), "2.4G")

    def test_mhz_display(self):
        self.assertEqual(_hz_to_suffixed(100_000_000), "100M")

    def test_khz_display(self):
        self.assertEqual(_hz_to_suffixed(10_700), "10.7k")

    def test_hz_display(self):
        self.assertEqual(_hz_to_suffixed(500), "500")

    def test_none_display(self):
        self.assertEqual(_hz_to_suffixed(None), "")

    def test_round_trip(self):
        """clean(prepare_value(hz)) == hz for representative values."""
        field = FrequencyField(required=False)
        for hz in [2_400_000_000, 100_000_000, 10_700, 1500]:
            displayed = field.prepare_value(hz)
            self.assertEqual(field.clean(displayed), hz, f"Round-trip failed for {hz}")


# ---------------------------------------------------------------------------
# Asset tag auto-generation
# ---------------------------------------------------------------------------
class AssetTagTest(TestCase):
    def setUp(self):
        # Use get_or_create since seed migration already creates these
        self.cat, _ = DeviceCategory.objects.get_or_create(
            slug="attenuator", defaults={"name": "Attenuator", "prefix": "ATT"}
        )

    def test_auto_generates_first_tag(self):
        device = Device(name="Test ATT", category=self.cat)
        device.save()
        self.assertEqual(device.asset_tag, "ATT-001")

    def test_sequential_numbering(self):
        Device.objects.create(name="ATT 1", category=self.cat)
        device2 = Device(name="ATT 2", category=self.cat)
        device2.save()
        self.assertEqual(device2.asset_tag, "ATT-002")

    def test_preserves_explicit_tag(self):
        device = Device(name="Custom", category=self.cat, asset_tag="CUSTOM-42")
        device.save()
        self.assertEqual(device.asset_tag, "CUSTOM-42")

    def test_different_categories_independent(self):
        cat2, _ = DeviceCategory.objects.get_or_create(
            slug="cable_assembly", defaults={"name": "Cable Assembly", "prefix": "CBL"}
        )
        Device.objects.create(name="ATT", category=self.cat)
        device = Device(name="Cable", category=cat2)
        device.save()
        self.assertEqual(device.asset_tag, "CBL-001")

    def test_gap_in_sequence(self):
        """If ATT-001 exists and ATT-002 is deleted, next should be ATT-002."""
        d1 = Device.objects.create(name="ATT 1", category=self.cat)
        d2 = Device.objects.create(name="ATT 2", category=self.cat)
        d2.delete()
        d3 = Device(name="ATT 3", category=self.cat)
        d3.save()
        # After deleting ATT-002, highest remaining is ATT-001, so next is ATT-002
        self.assertEqual(d3.asset_tag, "ATT-002")


# ---------------------------------------------------------------------------
# Touchstone parsing
# ---------------------------------------------------------------------------
class TouchstoneParseTest(TestCase):
    def _upload(self, content, filename):
        return SimpleUploadedFile(filename, content, content_type="application/octet-stream")

    def test_parse_s1p(self):
        f = self._upload(S1P_CONTENT, "test.s1p")
        meta = parse_touchstone(f, "test.s1p")
        self.assertEqual(meta.port_count, 1)
        self.assertEqual(meta.frequency_npoints, 3)
        self.assertAlmostEqual(meta.frequency_min_hz, 1e9)
        self.assertAlmostEqual(meta.frequency_max_hz, 3e9)
        self.assertAlmostEqual(meta.impedance_ohms, 50.0)

    def test_parse_s2p(self):
        f = self._upload(S2P_CONTENT, "test.s2p")
        meta = parse_touchstone(f, "test.s2p")
        self.assertEqual(meta.port_count, 2)
        self.assertEqual(meta.frequency_npoints, 3)


class PlotDataTest(TestCase):
    def _write_temp(self, content, suffix):
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp.write(content)
        tmp.close()
        return tmp.name

    def test_s1p_single_reflection_trace(self):
        path = self._write_temp(S1P_CONTENT, ".s1p")
        try:
            data = generate_s_param_plot_data(path)
            self.assertEqual(len(data["traces"]), 1)
            trace = data["traces"][0]
            self.assertEqual(trace["name"], "S11")
            self.assertTrue(trace["is_reflection"])
            self.assertIn("real", trace)
            self.assertIn("imag", trace)
            self.assertEqual(len(trace["x"]), 3)
            self.assertEqual(len(trace["y"]), 3)
        finally:
            os.unlink(path)

    def test_s2p_four_traces(self):
        path = self._write_temp(S2P_CONTENT, ".s2p")
        try:
            data = generate_s_param_plot_data(path)
            self.assertEqual(len(data["traces"]), 4)
            names = [t["name"] for t in data["traces"]]
            self.assertEqual(names, ["S11", "S12", "S21", "S22"])
            # Only diagonal entries are reflection
            for t in data["traces"]:
                if t["name"] in ("S11", "S22"):
                    self.assertTrue(t["is_reflection"])
                    self.assertIn("real", t)
                else:
                    self.assertFalse(t["is_reflection"])
                    self.assertNotIn("real", t)
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Document validation (file or URL required)
# ---------------------------------------------------------------------------
class DocumentValidationTest(TestCase):
    def setUp(self):
        cat, _ = DeviceCategory.objects.get_or_create(
            slug="other", defaults={"name": "Other", "prefix": "OTH"}
        )
        self.device = Device.objects.create(name="Test", category=cat)

    def test_url_only_is_valid(self):
        doc = Document(
            device=self.device,
            title="Datasheet",
            url="https://example.com/datasheet.pdf",
            doc_type="datasheet",
        )
        doc.full_clean()  # should not raise

    def test_file_only_is_valid(self):
        doc = Document(
            device=self.device,
            title="Manual",
            file=SimpleUploadedFile("manual.pdf", b"fake pdf"),
            doc_type="manual",
        )
        doc.full_clean()  # should not raise

    def test_neither_file_nor_url_raises(self):
        doc = Document(
            device=self.device,
            title="Empty",
            doc_type="other",
        )
        with self.assertRaises(ValidationError):
            doc.full_clean()

    def test_measurement_type_exists(self):
        """The 'measurement' doc_type is a valid choice."""
        doc = Document(
            device=self.device,
            title="Spectrum capture",
            url="https://example.com/spectrum.png",
            doc_type="measurement",
        )
        doc.full_clean()  # should not raise
