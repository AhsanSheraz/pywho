"""Allow running as `python -m pywho`."""

from pywho.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
