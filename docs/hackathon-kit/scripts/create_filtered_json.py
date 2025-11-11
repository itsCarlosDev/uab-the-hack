"""
Utility script to build a lightweight JSON snapshot with the
fields needed for the ROOKIE analysis walkthrough.

It collects data from the AP and Client datasets, keeps only the
required columns, and stores them in a single JSON file:

{
    "aps": [{"timestamp": "...", "client_count": ...}, ...],
    "clients": [
        {"timestamp": "...", "hour": 12, "day_of_week": "Monday", "date": "2025-04-03"},
        ...
    ]
}
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Tuple, Dict, Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter APS and Client datasets into a lightweight JSON dump."
    )
    repo_root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--aps-dir",
        type=Path,
        default=repo_root / "anonymized_data" / "aps",
        help="Directory containing AP snapshot JSON files.",
    )
    parser.add_argument(
        "--clients-dir",
        type=Path,
        default=repo_root / "anonymized_data" / "clients",
        help="Directory containing client snapshot JSON files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=repo_root / "data" / "rookie_filtered_dataset.json",
        help="Output JSON file path.",
    )
    parser.add_argument(
        "--max-aps-files",
        type=int,
        default=None,
        help="Optional limit for AP files (useful for quick tests).",
    )
    parser.add_argument(
        "--max-client-files",
        type=int,
        default=None,
        help="Optional limit for client files.",
    )
    parser.add_argument(
        "--aps-output",
        type=Path,
        default=repo_root / "data" / "rookie_filtered_aps.json",
        help="Path for the AP-only JSON output.",
    )
    parser.add_argument(
        "--clients-output",
        type=Path,
        default=repo_root / "data" / "rookie_filtered_clients.json",
        help="Path for the client-only JSON output.",
    )
    parser.add_argument(
        "--skip-combined",
        action="store_true",
        help="Skip writing the combined JSON payload.",
    )
    parser.add_argument(
        "--aps-geojson",
        type=Path,
        default=repo_root.parent / "geolocation_package" / "data" / "aps_geolocalizados_etrs89.geojson",
        help="GeoJSON file providing AP location metadata.",
    )
    return parser.parse_args()


def iter_json_files(directory: Path, max_files: Optional[int] = None) -> Iterator[Path]:
    files: List[Path] = sorted(directory.glob("*.json"))
    if max_files is not None:
        files = files[:max_files]
    for file in files:
        if not file.is_file():
            continue
        yield file


def iter_json_records(files: Iterable[Path]) -> Iterator[dict]:
    for file in files:
        with file.open("r", encoding="utf-8") as handle:
            try:
                data = json.load(handle)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {file}: {exc}") from exc
        if isinstance(data, list):
            for record in data:
                if isinstance(record, dict):
                    yield record


def load_geo_index(geojson_path: Path) -> Dict[str, Dict[str, Any]]:
    if not geojson_path.exists():
        return {}
    with geojson_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    features = payload.get("features", [])
    index: Dict[str, Dict[str, Any]] = {}
    for feature in features:
        props = feature.get("properties", {})
        ap_name = props.get("USER_NOM_A")
        if not ap_name:
            continue
        index[ap_name] = {
            "space": props.get("USER_Espai"),
            "building_code": props.get("Nom_Edific"),
            "building_name": props.get("USER_EDIFI"),
            "floor": props.get("Num_Planta"),
            "short_ref": props.get("Ref_Curta"),
            "x": props.get("X"),
            "y": props.get("Y"),
        }
    return index


def build_aps_slice(
    directory: Path, max_files: Optional[int], geo_index: Dict[str, Dict[str, Any]]
) -> Tuple[List[dict], int]:
    files = list(iter_json_files(directory, max_files))
    results: List[dict] = []
    for record in iter_json_records(files):
        last_modified = record.get("last_modified")
        client_count = record.get("client_count")
        if last_modified is None:
            continue
        try:
            ts = datetime.fromtimestamp(float(last_modified), tz=timezone.utc)
        except (ValueError, TypeError):
            continue
        ts_date = ts.date().isoformat()
        ts_time = ts.time().isoformat(timespec="seconds")
        ap_name = record.get("name")
        results.append(
            {
                "name": ap_name,
                "serial": record.get("serial"),
                "timestamp": ts.isoformat(),
                "date": ts_date,
                "time": ts_time,
                "client_count": client_count,
                "location": geo_index.get(ap_name),
            }
        )
    return results, len(files)


def build_clients_slice(directory: Path, max_files: Optional[int]) -> Tuple[List[dict], int]:
    files = list(iter_json_files(directory, max_files))
    results: List[dict] = []
    for record in iter_json_records(files):
        last_connection = record.get("last_connection_time")
        if last_connection is None:
            continue
        try:
            # Convert from milliseconds to seconds.
            ts = datetime.fromtimestamp(float(last_connection) / 1000, tz=timezone.utc)
        except (ValueError, TypeError):
            continue
        rounded_hour = ts.hour + (1 if ts.minute >= 30 else 0)
        rounded_hour = rounded_hour % 24
        results.append(
            {
                "timestamp": ts.isoformat(),
                "hour": rounded_hour,
                "day_of_week": ts.strftime("%A"),
                "date": ts.date().isoformat(),
                "dia": ts.day,
                "health": record.get("health"),
                "signal_db": record.get("signal_db"),
                "associated_device_name": record.get("associated_device_name"),
            }
        )
    return results, len(files)


def main() -> None:
    args = parse_args()
    geo_index = load_geo_index(args.aps_geojson)
    aps_slice, aps_files_count = build_aps_slice(
        args.aps_dir, args.max_aps_files, geo_index
    )
    clients_slice, client_files_count = build_clients_slice(
        args.clients_dir, args.max_client_files
    )

    outputs_written = []

    if not args.skip_combined and args.output:
        output_path: Path = args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "aps": aps_slice,
            "clients": clients_slice,
            "meta": {
                "aps_files": aps_files_count,
                "client_files": client_files_count,
            },
        }
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=True, indent=2)
        outputs_written.append(
            f"Combined JSON → {output_path} (APS {len(aps_slice)}, Clients {len(clients_slice)})"
        )

    if args.aps_output:
        aps_path: Path = args.aps_output
        aps_path.parent.mkdir(parents=True, exist_ok=True)
        with aps_path.open("w", encoding="utf-8") as handle:
            json.dump(aps_slice, handle, ensure_ascii=True, indent=2)
        outputs_written.append(f"AP slice → {aps_path} ({len(aps_slice)} registros)")

    if args.clients_output:
        clients_path: Path = args.clients_output
        clients_path.parent.mkdir(parents=True, exist_ok=True)
        with clients_path.open("w", encoding="utf-8") as handle:
            json.dump(clients_slice, handle, ensure_ascii=True, indent=2)
        outputs_written.append(
            f"Client slice → {clients_path} ({len(clients_slice)} registros)"
        )

    print("✅ JSON generado:")
    for line in outputs_written:
        print(f"   • {line}")


if __name__ == "__main__":
    main()
