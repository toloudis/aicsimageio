from xml.etree import cElementTree as etree

import numpy as np
import pytest

from aicsimageio import AICSImage, exceptions, readers
from aicsimageio.vendor import omexml

# Example files
BMP_FILE = "example.bmp"
JPG_FILE = "example.jpg"
PNG_FILE = "example.png"
GIF_FILE = "example.gif"
TIF_FILE = "s_1_t_1_c_1_z_1.tiff"
CZI_FILE = "s_1_t_1_c_1_z_1.czi"
OME_FILE = "s_1_t_1_c_1_z_1.ome.tiff"
TXT_FILE = "example.txt"


@pytest.mark.parametrize("filename, expected_reader", [
    (BMP_FILE, readers.DefaultReader),
    (JPG_FILE, readers.DefaultReader),
    (PNG_FILE, readers.DefaultReader),
    (GIF_FILE, readers.DefaultReader),
    (TIF_FILE, readers.TiffReader),
    (OME_FILE, readers.OmeTiffReader),
    (CZI_FILE, readers.CziReader),
    pytest.param(TXT_FILE, None, marks=pytest.mark.raises(exception=exceptions.UnsupportedFileFormatError)),
    pytest.param("not/a/file.czi", None, marks=pytest.mark.raises(exception=FileNotFoundError))
])
def test_typing(filename, expected_reader, resources_dir):
    actual_reader = AICSImage.determine_reader(resources_dir / filename)
    assert actual_reader == expected_reader


def test_file_passed_was_byte_string():
    with pytest.raises(exceptions.UnsupportedFileFormatError):
        AICSImage(b"not-a-valid-image-byte-array")


@pytest.mark.parametrize("arr", [
    np.zeros((2, 2, 2)),
    np.ones((2, 2, 2)),
    np.random.rand(2, 2, 2),
])
def test_support_for_ndarray(arr):
    actual_reader = AICSImage.determine_reader(arr)
    assert actual_reader == readers.NdArrayReader


@pytest.mark.parametrize("data, expected", [
    (np.zeros((5, 4, 3)), (1, 1, 1, 5, 4, 3)),
    (np.zeros((1, 2, 3, 4, 5, 6)), (1, 2, 3, 4, 5, 6)),
    (np.random.rand(10), (1, 1, 1, 1, 1, 10)),
])
def test_default_dims(data, expected):
    img = AICSImage(data=data)
    assert img.data.shape == expected


@pytest.mark.parametrize("data_shape, dims, expected", [
    ((5, 4, 3), "STC", (5, 4, 3, 1, 1, 1)),
    ((1, 2, 3, 4, 5, 6), "XYZCTS", (6, 5, 4, 3, 2, 1)),
    ((5, 4, 3), "SCY", (5, 1, 4, 1, 3, 1)),
    ((1, 2, 3, 4, 5, 6), "STCZYX", (1, 2, 3, 4, 5, 6)),
])
def test_force_dims(data_shape, dims, expected):
    img = AICSImage(data=np.zeros(data_shape))
    img._reader.dims = dims
    assert img.data.shape == expected
    assert data_shape == img.get_image_data(out_orientation=dims).shape


@pytest.mark.parametrize("filepath", [
    OME_FILE,
    pytest.param("fakeimage.ome.tif", marks=pytest.mark.raises(exception=FileNotFoundError)),
])
def test_file_exceptions(resources_dir, filepath):
    f = resources_dir / filepath
    AICSImage(f)


def test_file_passed_was_directory(resources_dir):
    with pytest.raises(IsADirectoryError):
        AICSImage(resources_dir)


@pytest.mark.parametrize("filename, expected_metadata_type", [
    (PNG_FILE, (str, type(None))),
    (TIF_FILE, (str, type(None))),
    (OME_FILE, (str, omexml.OMEXML)),
    (CZI_FILE, (str, etree.Element)),
])
def test_metadata(resources_dir, filename, expected_metadata_type):
    img = AICSImage(resources_dir / filename)
    assert isinstance(img.metadata, expected_metadata_type)


@pytest.mark.parametrize("filename, expected_reader", [
    (PNG_FILE, readers.DefaultReader),
    (TIF_FILE, readers.TiffReader),
    (OME_FILE, readers.OmeTiffReader),
    (CZI_FILE, readers.CziReader),
    pytest.param("not/a/file.czi", None, marks=pytest.mark.raises(exception=FileNotFoundError)),
])
def test_reader(resources_dir, filename, expected_reader):
    img = AICSImage(resources_dir / filename)
    assert isinstance(img.reader, expected_reader)
