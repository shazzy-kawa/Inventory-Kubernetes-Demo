"""Small inventory reconciler used as a Kubernetes learning project.

Merges mock exports from several "sources" (AD, SCCM, Veeam) into one view and
reports which servers are missing from which source. All data is fictional.
"""
import os
from functools import lru_cache

import pandas as pd
from flask import Flask, jsonify, render_template, request

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
APP_ENV = os.environ.get("APP_ENV", "local")
SOURCES = ["ad", "sccm", "veeam"]

app = Flask(__name__)


def normalise(name: str) -> str:
    """Lower-case and strip the domain so 'SRV01.corp.local' matches 'srv01'."""
    return str(name).strip().lower().split(".")[0]


@lru_cache(maxsize=1)
def load_inventory() -> pd.DataFrame:
    frames = []
    for source in SOURCES:
        df = pd.read_csv(os.path.join(DATA_DIR, f"{source}.csv"))
        df["host"] = df["hostname"].map(normalise)
        df[source] = True
        frames.append(df[["host", source]].drop_duplicates("host"))

    merged = frames[0]
    for df in frames[1:]:
        merged = merged.merge(df, on="host", how="outer")
    for source in SOURCES:
        merged[source] = merged[source].fillna(False).astype(bool)
    return merged.sort_values("host").reset_index(drop=True)


@app.get("/")
def index():
    inv = load_inventory()
    selected = request.args.get("missing")
    if selected not in SOURCES:
        selected = None
    rows = inv[~inv[selected]] if selected else inv
    return render_template(
        "index.html",
        env=APP_ENV,
        pod=os.environ.get("HOSTNAME", "local"),  # pod name when running in Kubernetes
        total=int(len(inv)),
        sources=SOURCES,
        missing={s: int((~inv[s]).sum()) for s in SOURCES},
        selected=selected,
        rows=rows.to_dict(orient="records"),
    )


@app.get("/healthz")
def healthz():
    # Liveness: the process is up.
    return jsonify(status="ok")


@app.get("/readyz")
def readyz():
    # Readiness: the data loaded, so the app can serve useful answers.
    try:
        load_inventory()
    except Exception as exc:  # noqa: BLE001 - surface any load failure as not ready
        return jsonify(status="not ready", error=str(exc)), 503
    return jsonify(status="ready")


@app.get("/summary")
def summary():
    inv = load_inventory()
    return jsonify(
        environment=APP_ENV,
        total_servers=int(len(inv)),
        missing={s: int((~inv[s]).sum()) for s in SOURCES},
    )


@app.get("/servers")
def servers():
    """Optional filter: /servers?missing=veeam"""
    inv = load_inventory()
    missing = request.args.get("missing")
    if missing:
        if missing not in SOURCES:
            return jsonify(error=f"missing must be one of {SOURCES}"), 400
        inv = inv[~inv[missing]]
    return jsonify(inv.to_dict(orient="records"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
