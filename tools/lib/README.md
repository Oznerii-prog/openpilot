## LogReader

Route is a class for conveniently accessing all the [logs](/system/loggerd/) from your routes. The LogReader class reads the non-video logs, i.e. rlog.bz2 and qlog.bz2. There's also a matching FrameReader class for reading the videos.

```python
from openpilot.tools.lib.route import Route
from openpilot.tools.lib.logreader import LogReader
import os

sep = '--'
directories = set()
for dir_name in os.listdir('/data/media/0/realdata'):
  try:
    split_dir_name = dir_name.split(sep)
    directories.add(sep.join(dir_name.split(sep)[:-1]))
  except:
    pass

directories = sorted(directories)
print(directories)
print(directories[-1])

r = Route(directories[-1])

# get a list of paths for the route's rlog files
print(r.log_paths())

# and road camera (fcamera.hevc) files
print(r.camera_paths())

# setup a LogReader to read the route's first rlog
lr = LogReader(r.log_paths()[-1])

# print all the events values from all the logs in the route
from collections import defaultdict
events = defaultdict(list)
for msg in lr:
  if msg.which() == "carState":
    for event in msg.carState.events:
      events[event.name].append(msg)
      # if event.immediateDisable or event.softDisable:
      #   events[event.name].append(event)

print(list(events.keys()))

for name, msg in events.items():
  print(f'***************** {name}')
  for m in msg:
    print(m)
    print()
  print()

# print out all the messages in the log
import codecs
codecs.register_error("strict", codecs.backslashreplace_errors)
for msg in lr:
  print(msg)
  print()

# print all the steering angles values from the log
for msg in lr:
  if msg.which() == "carState":
    print(msg.carState)
    print()

# print all the steering angles values from the log
for msg in lr:
  if msg.which() == "carControl":
    if msg.carControl.enabled:
      print(msg.carControl)
      print()

```

### MultiLogIterator

`MultiLogIterator` is similar to `LogReader`, but reads multiple logs. 

```python
from openpilot.tools.lib.route import Route
from openpilot.tools.lib.logreader import MultiLogIterator
import os
from tqdm import tqdm

sep = '--'
directories = set()
for dir_name in os.listdir('/data/media/0/realdata'):
  try:
    split_dir_name = dir_name.split(sep)
    directories.add(sep.join(dir_name.split(sep)[:-1]))
  except:
    pass

directories = sorted(directories)
print(directories)
print(directories[-1])

# setup a MultiLogIterator to read all the logs in the route
r = Route(directories[-1])
lr = [msg for msg in tqdm(MultiLogIterator(r.log_paths()))]

sorted({msg.which() for msg in lr})

msgs = sorted(lr, key=lambda m: m.logMonoTime)

from queue import Queue
q = Queue()
for msg in msgs:
  # if msg.which() == "errorLogMessage":
  if q.full():
    t = q.get()
  if msg.which() in ['logMessage']:
    q.put(msg)
  if msg.logMonoTime == 741697858204:
    break

# Get items from the queue
while not q.empty():
    print(q.get())
    print()


# print all the events values from all the logs in the route
import json
for msg in lr:
  if msg.which() == "logMessage":
    log_msg = json.loads(msg.logMessage)
    if log_msg.get('level', '') == 'ERROR':
      print(log_msg)

# print all the events values from all the logs in the route
for msg in lr:
  if msg.which() == "logMessage":
    print(msg.logMessage)

# print all the steering angles values from all the logs in the route
for msg in lr:
  if msg.which() == "carState":
    print(msg.carState.steeringAngleDeg)
```