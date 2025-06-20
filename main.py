#!/usr/bin/env python3

import sys
import os

root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(root_dir, 'src'))

from server import main

if __name__ == '__main__':
    main()
