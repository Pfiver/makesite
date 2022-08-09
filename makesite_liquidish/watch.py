#!/usr/bin/env python
""""asdf"""

import logging

from watchdog.observers import Observer
from watchdog.tricks import LoggerTrick

logging.basicConfig(level=logging.INFO)

observer = Observer()
observer.schedule(LoggerTrick(), ".", recursive=True)
observer.start()
observer.join()
