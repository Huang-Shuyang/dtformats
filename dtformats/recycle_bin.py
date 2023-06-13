# -*- coding: utf-8 -*-
"""Windows Recycle.Bin metadata ($I) files."""

from dtformats import data_format
from dtformats import errors


class RecycleBinMetadataFile(data_format.BinaryDataFile):
  """Windows Recycle.Bin metadata ($I) file.

  Attributes:
    deletion_time (int): FILETIME timestamp of the date and time the original
        file was deleted.
    format_version (int): format version of the metadata file.
    original_filename (str): original name of the deleted file.
    original_size (int): original size of the deleted file.
  """

  # Using a class constant significantly speeds up the time required to load
  # the dtFabric and dtFormats definition files.
  _FABRIC = data_format.BinaryDataFile.ReadDefinitionFile('recycle_bin.yaml')

  _DEBUG_INFORMATION = data_format.BinaryDataFile.ReadDebugInformationFile(
      'recycle_bin.debug.yaml', custom_format_callbacks={
          'filetime': '_FormatIntegerAsFiletime'})

  _SUPPORTED_FORMAT_VERSION = (1, 2)

  def __init__(self, debug=False, output_writer=None):
    """Initializes a Windows Recycle.Bin metadata ($I) file.

    Args:
      debug (Optional[bool]): True if debug information should be written.
      output_writer (Optional[OutputWriter]): output writer.
    """
    super(RecycleBinMetadataFile, self).__init__(
        debug=debug, output_writer=output_writer)
    self.deletion_time = None
    self.format_version = None
    self.original_filename = None
    self.original_file_size = None

  def _ReadFileHeader(self, file_object):
    """Reads the file header.

    Args:
      file_object (file): file-like object.

    Returns:
      recycle_bin_metadata_file_header: file header.

    Raises:
      ParseError: if the file header cannot be read.
    """
    data_type_map = self._GetDataTypeMap('recycle_bin_metadata_file_header')

    file_header, _ = self._ReadStructureFromFileObject(
        file_object, 0, data_type_map, 'file header')

    if self._debug:
      debug_info = self._DEBUG_INFORMATION.get(
          'recycle_bin_metadata_file_header', None)
      self._DebugPrintStructureObject(file_header, debug_info)

    if file_header.format_version not in self._SUPPORTED_FORMAT_VERSION:
      raise errors.ParseError(
          f'Unsupported format version: {file_header.format_version:d}')

    return file_header

  def _ReadOriginalFilename(self, file_object, format_version):
    """Reads the original filename.

    Args:
      file_object (file): file-like object.
      format_version (int): format version.

    Returns:
      str: filename or None on error.

    Raises:
      ParseError: if the original filename cannot be read.
    """
    if format_version == 1:
      data_type_map_name = 'recycle_bin_metadata_utf16le_string'
      description = 'UTF-16 little-endian string'
    else:
      data_type_map_name = 'recycle_bin_metadata_utf16le_string_with_size'
      description = 'UTF-16 little-endian string with size'

    file_offset = file_object.tell()
    data_type_map = self._GetDataTypeMap(data_type_map_name)

    try:
      original_filename, _ = self._ReadStructureFromFileObject(
          file_object, file_offset, data_type_map, description)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          f'Unable to parse original filename with error: {exception!s}')

    if format_version == 1:
      return original_filename.rstrip('\x00')

    return original_filename.string.rstrip('\x00')

  def ReadFileObject(self, file_object):
    """Reads a Windows Recycle.Bin metadata ($I) file-like object.

    Args:
      file_object (file): file-like object.

    Raises:
      ParseError: if the file cannot be read.
    """
    file_header = self._ReadFileHeader(file_object)

    self.format_version = file_header.format_version
    self.deletion_time = file_header.deletion_time
    self.original_file_size = file_header.original_file_size

    self.original_filename = self._ReadOriginalFilename(
        file_object, file_header.format_version)

    if self._debug:
      self._DebugPrintValue('Original filename', self.original_filename)

      self._DebugPrintText('\n')
