import os
from urllib.parse import urlparse
from collections import defaultdict
from itertools import chain
from typing import Optional

QLOG_FILENAMES = ['qlog', 'qlog.bz2']
QCAMERA_FILENAMES = ['qcamera.ts']
LOG_FILENAMES = ['rlog', 'rlog.bz2', 'raw_log.bz2']
CAMERA_FILENAMES = ['fcamera.hevc', 'video.hevc']
DCAMERA_FILENAMES = ['dcamera.hevc']
ECAMERA_FILENAMES = ['ecamera.hevc']

class Route:
  def __init__(self, name, data_dir='/data/media/0/realdata'):
    self._name = RouteName(name)
    self.files = None
    self._segments = self._get_segments_local(data_dir)
    self.max_seg_number = self._segments[-1].name.segment_num

  @property
  def name(self):
    return self._name

  @property
  def segments(self):
    return self._segments

  def log_paths(self):
    log_path_by_seg_num = {s.name.segment_num: s.log_path for s in self._segments}
    return [log_path_by_seg_num.get(i, None) for i in range(self.max_seg_number+1)]

  def qlog_paths(self):
    qlog_path_by_seg_num = {s.name.segment_num: s.qlog_path for s in self._segments}
    return [qlog_path_by_seg_num.get(i, None) for i in range(self.max_seg_number+1)]

  def camera_paths(self):
    camera_path_by_seg_num = {s.name.segment_num: s.camera_path for s in self._segments}
    return [camera_path_by_seg_num.get(i, None) for i in range(self.max_seg_number+1)]

  def dcamera_paths(self):
    dcamera_path_by_seg_num = {s.name.segment_num: s.dcamera_path for s in self._segments}
    return [dcamera_path_by_seg_num.get(i, None) for i in range(self.max_seg_number+1)]

  def ecamera_paths(self):
    ecamera_path_by_seg_num = {s.name.segment_num: s.ecamera_path for s in self._segments}
    return [ecamera_path_by_seg_num.get(i, None) for i in range(self.max_seg_number+1)]

  def qcamera_paths(self):
    qcamera_path_by_seg_num = {s.name.segment_num: s.qcamera_path for s in self._segments}
    return [qcamera_path_by_seg_num.get(i, None) for i in range(self.max_seg_number+1)]

  def _get_segments_local(self, data_dir):
    files = os.listdir(data_dir)
    segment_files = defaultdict(list)

    for f in files:
      fullpath = os.path.join(data_dir, f)
      # explorer_match = re.match(RE.EXPLORER_FILE, f)
      # op_match = re.match(RE.OP_SEGMENT_DIR, f)

      # if explorer_match:
      #   segment_name = explorer_match.group('segment_name')
      #   fn = explorer_match.group('file_name')
      #   if segment_name.replace('_', '|').startswith(self.name.canonical_name):
      #     segment_files[segment_name].append((fullpath, fn))
      # elif op_match and os.path.isdir(fullpath):
      #   segment_name = op_match.group('segment_name')
      #   if segment_name.startswith(self.name.canonical_name):
      #     for seg_f in os.listdir(fullpath):
      #       segment_files[segment_name].append((os.path.join(fullpath, seg_f), seg_f))
      if self.name.canonical_name in f:
        seg_num = f.split('--')[-1]

        segment_name = f'{self.name.canonical_name}--{seg_num}'
        for seg_f in os.listdir(fullpath):
          segment_files[segment_name].append((os.path.join(fullpath, seg_f), seg_f))

    segments = []
    for segment, files in segment_files.items():

      try:
        log_path = next(path for path, filename in files if filename in LOG_FILENAMES)
      except StopIteration:
        log_path = None

      try:
        qlog_path = next(path for path, filename in files if filename in QLOG_FILENAMES)
      except StopIteration:
        qlog_path = None

      try:
        camera_path = next(path for path, filename in files if filename in CAMERA_FILENAMES)
      except StopIteration:
        camera_path = None

      try:
        dcamera_path = next(path for path, filename in files if filename in DCAMERA_FILENAMES)
      except StopIteration:
        dcamera_path = None

      try:
        ecamera_path = next(path for path, filename in files if filename in ECAMERA_FILENAMES)
      except StopIteration:
        ecamera_path = None

      try:
        qcamera_path = next(path for path, filename in files if filename in QCAMERA_FILENAMES)
      except StopIteration:
        qcamera_path = None

      segments.append(Segment(segment, log_path, qlog_path, camera_path, dcamera_path, ecamera_path, qcamera_path))

    if len(segments) == 0:
      raise ValueError(f'Could not find segments for route {self.name.canonical_name} in data directory {data_dir}')
    return sorted(segments, key=lambda seg: seg.name.segment_num)

class Segment:
  def __init__(self, name, log_path, qlog_path, camera_path, dcamera_path, ecamera_path, qcamera_path):
    self._name = SegmentName(name)
    self.log_path = log_path
    self.qlog_path = qlog_path
    self.camera_path = camera_path
    self.dcamera_path = dcamera_path
    self.ecamera_path = ecamera_path
    self.qcamera_path = qcamera_path

  @property
  def name(self):
    return self._name

class RouteName:
  def __init__(self, name_str: str):
    self._name_str = name_str
    self._time_str = self._name_str
    self._dongle_id = ''

    assert len(self._time_str) == 20, self._name_str
    self._canonical_name = f"{self._time_str}"

  @property
  def canonical_name(self) -> str: return self._canonical_name

  @property
  def dongle_id(self) -> str: return self._dongle_id

  @property
  def time_str(self) -> str: return self._time_str

  def __str__(self) -> str: return self._canonical_name

class SegmentName:
  # TODO: add constructor that takes dongle_id, time_str, segment_num and then create instances
  # of this class instead of manually constructing a segment name (use canonical_name prop instead)
  def __init__(self, name_str: str, allow_route_name=False):
    data_dir_path_separator_index = name_str.rsplit("|", 1)[0].rfind("/")
    use_data_dir = (data_dir_path_separator_index != -1) and ("|" in name_str)
    self._name_str = name_str[data_dir_path_separator_index + 1:] if use_data_dir else name_str
    self._data_dir = name_str[:data_dir_path_separator_index] if use_data_dir else None

    seg_num_delim = "--" if self._name_str.count("--") == 2 else "/"
    name_parts = self._name_str.rsplit(seg_num_delim, 1)
    if allow_route_name and len(name_parts) == 1:
      name_parts.append("-1") # no segment number
    self._route_name = RouteName(name_parts[0])
    self._num = int(name_parts[1])
    self._canonical_name = f"{self._route_name._time_str}--{self._num}"

  @property
  def canonical_name(self) -> str: return self._canonical_name

  @property
  def dongle_id(self) -> str: return self._route_name.dongle_id

  @property
  def time_str(self) -> str: return self._route_name.time_str

  @property
  def segment_num(self) -> int: return self._num

  @property
  def route_name(self) -> RouteName: return self._route_name

  @property
  def data_dir(self) -> Optional[str]: return self._data_dir

  def __str__(self) -> str: return self._canonical_name