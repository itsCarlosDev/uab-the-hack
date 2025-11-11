from pathlib import Path
import json
from datetime import datetime
import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def parse_timestamp_from_ap_filename(path: Path) -> datetime:
    """
    Ejemplo de nombre:
    AP-info-v2-2025-04-03T00_15_01+02_00.json
    """
    stem = path.stem  # sin .json
    parts = stem.split("-")
    # ['AP', 'info', 'v2', '2025', '04', '03T00_15_01+02_00']
    date_part = "-".join(parts[3:6])  # '2025-04-03T00_15_01+02_00'
    date_part = date_part.replace("_", ":")  # '2025-04-03T00:15:01+02:00'
    return datetime.fromisoformat(date_part)


def load_ap_snapshots():
    rows = []

    ap_files = sorted(DATA_DIR.glob("AP-info-v2-*.json"))

    for path in ap_files:
        ts = parse_timestamp_from_ap_filename(path)

        with path.open("r", encoding="utf-8") as f:
            aps = json.load(f)  # lista de APs

        # total de clientes conectados en ese snapshot
        total_clients = sum(ap.get("client_count", 0) for ap in aps)

        rows.append(
            {
                "snapshot_file": path.name,
                "timestamp": ts,
                "date": ts.date(),
                "day_of_week": ts.strftime("%A"),  # 'Monday', 'Tuesday', etc.
                "hour": ts.hour,
                "total_clients": total_clients,
            }
        )

    df = pd.DataFrame(rows)
    return df


def compute_peak_hours(df: pd.DataFrame):
    """
    Agrupa por día y hora para ver cuántos clientes hay de media en cada franja.
    """
    # si solo quieres por hora (mezclando todos los días):
    by_hour = df.groupby("hour")["total_clients"].mean().sort_values(ascending=False)

    # si quieres por día de la semana y hora:
    by_dow_hour = (
        df.groupby(["day_of_week", "hour"])["total_clients"]
        .mean()
        .reset_index()
        .sort_values("total_clients", ascending=False)
    )

    return by_hour, by_dow_hour


if __name__ == "__main__":
    df = load_ap_snapshots()
    print("Primeras filas:")
    print(df.head())

    by_hour, by_dow_hour = compute_peak_hours(df)

    print("\n>>> HORAS PICO (media de clientes, todos los días mezclados):")
    print(by_hour.head(10))

    print("\n>>> TOP FRANJAS (día de la semana + hora):")
    print(by_dow_hour.head(10))
