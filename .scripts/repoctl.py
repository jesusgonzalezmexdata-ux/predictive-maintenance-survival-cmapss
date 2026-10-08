#!/usr/bin/env python3
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from repoctl.cli import main
if __name__=='__main__':
    raise SystemExit(main())
