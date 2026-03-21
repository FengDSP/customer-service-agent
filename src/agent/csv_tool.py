import os
from pathlib import Path

import pandas as pd

from agent.config import BusinessConfig, DataSource

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def build_tool_definitions(config: BusinessConfig) -> list[dict]:
    """Generate Anthropic tool definitions from business config data sources."""
    tools = []
    for ds in config.data_sources:
        csv_path = PROJECT_ROOT / ds.path
        meta = _get_file_metadata(csv_path)
        tools.append(
            {
                "name": f"lookup_{ds.name}",
                "description": (
                    f"Look up data from {ds.name}. {ds.description}\n"
                    f"File: {meta['rows']} rows, {meta['size_human']}.\n"
                    f"Columns: {meta['columns_desc']}\n"
                    f"Filter by column+value or search with a keyword."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "column": {
                            "type": "string",
                            "description": (
                                "Column to filter on. One of: " + ", ".join(meta["columns"])
                            ),
                        },
                        "value": {
                            "type": "string",
                            "description": "Value to match (case-insensitive substring match).",
                        },
                        "keyword": {
                            "type": "string",
                            "description": (
                                "Search keyword across all columns "
                                "(use instead of column+value for broad search)."
                            ),
                        },
                    },
                },
            }
        )

    # Add grep tool that searches across all data files
    tools.append(_build_grep_tool(config))

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
        mask = df.apply(
            lambda row: row.str.contains(keyword, case=False, na=False).any(),
            axis=1,
        )
        result = df[mask]
    else:
        result = df

    if result.empty:
        return "No matching rows found."

    return result.to_string(index=False)


def execute_grep(config: BusinessConfig, args: dict) -> str:
    """Search across data files for a business."""
    query = args.get("query", "")
    sources = args.get("sources", [])
    max_results = int(args.get("max_results", 20))

    if not query:
        return "Error: query is required."

    results = []
    for ds in config.data_sources:
        if sources and ds.name not in sources:
            continue
        csv_path = PROJECT_ROOT / ds.path
        df = pd.read_csv(csv_path, dtype=str)
        mask = df.apply(
            lambda row: row.str.contains(query, case=False, na=False).any(),
            axis=1,
        )
        matched = df[mask]
        if not matched.empty:
            for _, row in matched.head(max_results - len(results)).iterrows():
                results.append(f"[{ds.name}] {row.to_dict()}")
                if len(results) >= max_results:
                    break
        if len(results) >= max_results:
            break

    if not results:
        return f"No matches found for '{query}' across data files."

    return "\n".join(results)


def _build_grep_tool(config: BusinessConfig) -> dict:
    source_names = [ds.name for ds in config.data_sources]
    return {
        "name": "grep_data",
        "description": (
            "Search across all data files for matching rows. "
            "Use this when you're not sure which data source to look in, "
            "or when you need to find something across multiple files. "
            f"Available sources: {', '.join(source_names)}."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term (case-insensitive match across all columns).",
                },
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Optional: limit search to specific sources. "
                        f"One or more of: {', '.join(source_names)}. "
                        "Omit to search all."
                    ),
                },
                "max_results": {
                    "type": "integer",
                    "description": "Max rows to return (default 20).",
                },
            },
            "required": ["query"],
        },
    }


def _get_file_metadata(csv_path: Path) -> dict:
    """Get metadata about a CSV file for tool descriptions."""
    df = pd.read_csv(csv_path, dtype=str, nrows=3)
    full_df = pd.read_csv(csv_path, dtype=str)
    row_count = len(full_df)
    file_size = os.path.getsize(csv_path)

    columns = list(df.columns)
    col_parts = []
    for col in columns:
        samples = df[col].dropna().head(2).tolist()
        if samples:
            sample_str = ", ".join(f'"{s}"' for s in samples)
            col_parts.append(f"{col} (e.g. {sample_str})")
        else:
            col_parts.append(col)

    return {
        "columns": columns,
        "columns_desc": "; ".join(col_parts),
        "rows": row_count,
        "size_human": _human_size(file_size),
    }


def _human_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def _find_data_source(config: BusinessConfig, name: str) -> DataSource | None:
    for ds in config.data_sources:
        if ds.name == name:
            return ds
    return None
