import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from urllib.parse import urlparse


def extract_hostname(url: Optional[str]) -> Optional[str]:
    """Return hostname (e.g., www.mims.com) from a URL-like string.

    - Returns None if input is empty or hostname cannot be parsed.
    - Adds a default scheme if missing to ensure correct parsing.
    """
    if not isinstance(url, str):
        return None

    trimmed = url.strip()
    if not trimmed:
        return None

    # Ensure there is a scheme to make urlparse extract netloc reliably
    to_parse = trimmed if "://" in trimmed or trimmed.startswith("//") else f"http://{trimmed}"
    try:
        parsed = urlparse(to_parse)
        hostname = parsed.hostname  # excludes port automatically
        return hostname
    except Exception:
        return None


def main() -> None:
    """Read Excel, extract hostname from `link` column into new `domain` column, and save."""
    # Defaults
    workspace_dir = Path(__file__).resolve().parent
    default_input = workspace_dir / "aitep_references_need_fulltext.xlsx"
    default_output = workspace_dir / "aitep_references_need_fulltext_with_domain.xlsx"

    # CLI: allow custom input/output paths
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_input
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else default_output

    if not input_path.exists():
        raise FileNotFoundError(f"Input Excel not found: {input_path}")

    # Read the first sheet by default
    df = pd.read_excel(input_path)

    if "link" not in df.columns:
        raise KeyError("Column 'link' not found in the Excel file.")

    df["domain"] = df["link"].map(extract_hostname)

    # Save to a new file to avoid overwriting original
    df.to_excel(output_path, index=False)
    print(f"Wrote file with 'domain' column: {output_path}")


if __name__ == "__main__":
    main()


