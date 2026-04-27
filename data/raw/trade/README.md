Place source-backed U.S. coffee imports-by-origin files in this folder.

Supported formats:
- CSV
- XLSX / XLS
- Parquet

The Stage 1 ingestion script (`scripts/05_stage1_map_ingest.py`) will read
the first available file and attempt to identify:
- country/partner origin column
- trade value or quantity column
- (optional) reporter/importer column to filter for United States

Recommended content:
- Bilateral U.S. coffee imports by origin country
- Single year or multi-year table (script will aggregate country totals)

