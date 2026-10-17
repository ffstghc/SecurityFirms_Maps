"""Download tables from the Destatis GENESIS-Online database without an account.

GENESIS-Online's web app (https://genesis.destatis.de/datenbank/online) calls a
REST API that serves public tables without a login. This module uses that API:
read a table's structure, narrow it to the rows we need, and fetch the result as
a flat CSV ("ffcsv").

The official GENESIS web service (genesisWS) needs a registered account; this
route does not, but it is the web app's internal API and may change.
"""

from __future__ import annotations

import copy
import io
import json
import urllib.request
import zipfile

import pandas as pd

BASE = "https://genesis.destatis.de/genesis/api/rest"
UA = "Mozilla/5.0 (secmap research script)"


def _request(url: str, body: dict | None = None, timeout: int = 180) -> bytes:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="GET" if body is None else "POST")
    req.add_header("User-Agent", UA)
    req.add_header("Accept", "*/*")
    # The API answers 405 to POSTs that do not come from its own web app.
    req.add_header("Origin", "https://genesis.destatis.de")
    req.add_header("Referer", "https://genesis.destatis.de/datenbank/online/")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def structure(table: str, language: str = "de") -> dict:
    return json.loads(_request(f"{BASE}/tables/{table}/structure?language={language}"))


def node(code: str, child_var: str | None = None, children: list[dict] | tuple = ()) -> dict:
    """One selected value of a variable block; `children` are values of `child_var`.

    Hierarchical classifications (WZ 2008) are selected as trees, e.g.
    node("WZ08-80", "WZ08P6", [node("WZ08-801")]).
    """
    return {"attribute": code, "childVariable": child_var if children else None,
            "childAttributes": list(children), "isHidden": False, "isDocumentary": False}


def fetch_flat(table: str, select: dict[str, list], contents: list[str] | None = None,
               language: str = "de") -> pd.DataFrame:
    """Fetch `table` as a DataFrame of the flat CSV (one row per value).

    `select` maps a variable block's main variable (e.g. "JAHR", "DLAND",
    "WZ08BA") to the values to keep: plain codes, or trees built with `node`.
    Blocks not named in `select` keep the table's default selection.
    `contents` keeps only these measures (e.g. ["STR040"]); the API rejects a
    table state with measures removed, so this filters the rows afterwards.
    """
    st = structure(table, language)
    state = copy.deepcopy(st["initialState"])
    for block in state["variableBlocks"].values():
        main = block["mainVariable"]
        if main in select:
            block["mainAttributes"] = [a if isinstance(a, dict) else node(a) for a in select[main]]
    raw = _request(f"{BASE}/tables/{table}/download/ffcsv/{language}", body=state)
    if raw[:2] == b"PK":  # the flat CSV arrives zipped
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            raw = zf.read(zf.namelist()[0])
    df = pd.read_csv(io.StringIO(raw.decode("utf-8-sig")), sep=";", dtype=str)
    if contents:
        df = df[df["value_variable_code"].isin(contents)].reset_index(drop=True)
    return df


def all_values(table: str, variable: str, language: str = "de") -> list[str]:
    """Every value code of `variable` in `table` (e.g. all 16 Länder, all years)."""
    return list(structure(table, language)["variables"][variable]["variableValues"])
