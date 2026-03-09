import logging
import sys


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    from logseq_mcp.server import mcp
    mcp.run()


if __name__ == "__main__":
    main()
