"""Allow running as `python -m codename_generator`."""

import sys


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        import argparse

        parser = argparse.ArgumentParser(description="Codename Generator Web Server")
        parser.add_argument("mode")  # "web"
        parser.add_argument("--host", default="127.0.0.1")
        parser.add_argument("--port", type=int, default=8000)
        args = parser.parse_args()

        import uvicorn

        from .api import app

        uvicorn.run(app, host=args.host, port=args.port)
    else:
        from .server import mcp

        mcp.run()


main()
