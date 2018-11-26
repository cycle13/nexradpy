#!/usr/bin/env python3

import sys
import os

## Import module from dir up
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nexradpy import utils