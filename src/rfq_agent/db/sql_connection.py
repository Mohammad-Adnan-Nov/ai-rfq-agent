from __future__ import annotations

from typing import Any


def connect_sql_server(server: str, database: str) -> Any:
    """
    Create a trusted-connection SQL Server connection.

    pyodbc is imported inside this function so unit tests can import the
    db package without requiring SQL Server drivers on every environment.
    """
    import pyodbc

    drivers = list(pyodbc.drivers())

    preferred_drivers = [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "SQL Server",
    ]

    selected_driver = next((driver for driver in preferred_drivers if driver in drivers), None)

    if selected_driver is None:
        raise RuntimeError(
            "No supported SQL Server ODBC driver found. "
            f"Installed drivers: {drivers}"
        )

    encrypt_part = "Encrypt=no;" if selected_driver == "ODBC Driver 18 for SQL Server" else ""

    connection_string = (
        f"DRIVER={{{selected_driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
        f"{encrypt_part}"
    )

    return pyodbc.connect(connection_string, autocommit=False)
