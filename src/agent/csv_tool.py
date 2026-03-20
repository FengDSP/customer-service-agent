from pathlib import Path

import pandas as pd

from agent.config import BusinessConfig, DataSource

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def build_tool_definitions(config: BusinessConfig) -> list[dict]:
    """Generate Anthropic tool definitions from business config data sources."""
    tools = []
    for ds in config.data_sources:
        csv_path = PROJECT_ROOT / ds.path
        columns = _get_columns(csv_path)
        tools.append({
            "name": f"lookup_{ds.name}",
            "description": (
                f"Look up data from {ds.name}. {ds.description} "
                f"Available columns: {', '.join(columns)}. "
                f"You can filter by column value or search with a keyword."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "column": {
                        "type": "string",
                        "description": f"Column to filter on. One of: {', '.join(columns)}",
                    },
                    "value": {
                        "type": "string",
                        "description": "Value to match (case-insensitive substring match).",
                    },
                    "keyword": {
                        "type": "string",
                        "description": "Search keyword across all columns (use instead of column+value for broad search).",
                    },
                },
            },
        })
    return tools


def execute_csv_lookup(config: BusinessConfig, tool_name: str, args: dict) -> str:
    """Execute a CSV lookup tool call and return matching rows as text."""
    source_name = tool_name.removeprefix("lookup_")
    ds = _find_data_source(config, source_name)
    if ds is None:
        return f"Error: unknown data source '{source_name}'"

    csv_path = PROJECT_ROOT / ds.path
    df = pd.read_csv(csv_path, dtype=str)

    column = args.get("column")
    value = args.get("value")
    keyword = args.get("keyword")

    if column and value:
        if column not in df.columns:
            return f"Error: column '{column}' not found. Available: {', '.join(df.columns)}"
        mask = df[column].str.contains(value, case=False, na=False)
        result = df[mask]
    elif keyword:
        mask = df.apply(lambda row: row.str.contains(keyword, case=False, na=False).any(), axis=1)
        result = df[mask]
    else:
        result = df

    if result.empty:
        return "No matching rows found."

    return result.to_string(index=False)


def _get_columns(csv_path: Path) -> list[str]:
    df = pd.read_csv(csv_path, nrows=0)
    return list(df.columns)


def _find_data_source(config: BusinessConfig, name: str) -> DataSource | None:
    for ds in config.data_sources:
        if ds.name == name:
            return ds
    return None
