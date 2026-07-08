from __future__ import annotations

import argparse
import json

from rfq_agent.db.sql_connection import connect_sql_server
from rfq_agent.retrieval.assembly_search import (
    assembly_number_results_to_dicts,
    search_complete_assembly_number,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search SQL Server for complete assembly number matches."
    )

    parser.add_argument("assembly_number")
    parser.add_argument("--server", default=r".\SQLEXPRESS")
    parser.add_argument("--database", default="AI_RFQ_AGENT_DEV")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--include-invalid", action="store_true")
    parser.add_argument("--include-inactive-versions", action="store_true")

    args = parser.parse_args()

    connection = connect_sql_server(
        server=args.server,
        database=args.database,
    )

    try:
        results = search_complete_assembly_number(
            connection=connection,
            assembly_number=args.assembly_number,
            include_invalid=args.include_invalid,
            active_only=not args.include_inactive_versions,
            limit=args.limit,
        )

        print(
            json.dumps(
                assembly_number_results_to_dicts(results),
                indent=2,
                ensure_ascii=False,
            )
        )

        print(f"Assembly number search returned {len(results)} result(s).")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
