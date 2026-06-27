#!/usr/bin/env python3
"""
Entry point for all automation services.
Usage: python3 run.py --<service> [options]

Services:
  --admaven     speedy-links task locker (AdMaven)

Run python3 run.py --admaven --help for service-specific options.
"""
import sys
import os

SERVICES = {
    "--admaven": "services.admaven.scripts.auto_admaven",
}

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 run.py --<service> [options]")
        print("Services:", ", ".join(SERVICES.keys()))
        sys.exit(1)

    service_flag = sys.argv[1]
    if service_flag not in SERVICES:
        print(f"Unknown service: {service_flag!r}")
        print("Available:", ", ".join(SERVICES.keys()))
        sys.exit(1)

    # Remove the service flag and let the service script parse the rest
    sys.argv = [sys.argv[0]] + sys.argv[2:]

    # Add project root to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    module_path = SERVICES[service_flag]
    import importlib
    mod = importlib.import_module(module_path)
    mod.main()

if __name__ == "__main__":
    main()
