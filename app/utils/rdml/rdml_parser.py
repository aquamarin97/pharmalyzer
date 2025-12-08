import ast
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple

RDML_NS = {"rdml": "http://www.rdml.org"}


def extract_run(root: ET.Element, run_id: str) -> ET.Element:
    run = root.find(f".//rdml:run[@id='{run_id}']", namespaces=RDML_NS)
    if run is None:
        raise ValueError(f"'{run_id}' koşusu bulunamadı.")
    return run


def parse_react(react: ET.Element, run_id: str) -> Dict:
    """
    react -> dict
    koordinat listesi artık string yerine list[tuple] olarak üretilebilir
    ama aşağıda legacy uyumluluk için string'e çevirmeden bırakıyorum.
    """
    row = {}
    row["React ID"] = react.get("id", "")

    sample = react.find("rdml:sample", namespaces=RDML_NS)
    row["Barkot No"] = sample.get("id") if sample is not None else ""

    tar = react.find(".//rdml:tar", namespaces=RDML_NS)
    row["Hasta Adı"] = tar.get("id") if tar is not None else ""

    cq = react.find(".//rdml:cq", namespaces=RDML_NS)
    row[f"{run_id} Ct"] = round(float(cq.text), 6) if cq is not None and cq.text else ""

    adps = react.findall(".//rdml:adp", namespaces=RDML_NS)
    coords = []
    for adp in adps:
        cyc = adp.find("rdml:cyc", namespaces=RDML_NS)
        fl = adp.find("rdml:fluor", namespaces=RDML_NS)
        if cyc is None or fl is None or cyc.text is None or fl.text is None:
            continue
        coords.append((int(cyc.text), round(float(fl.text), 6)))

    # eskisi gibi string istiyorsan:
    row[f"{run_id} koordinat list"] = str(coords)
    return row


def merge_fam_hex_rows(root: ET.Element) -> List[Dict]:
    fam_run = extract_run(root, "Amp Step 3_FAM")
    hex_run = extract_run(root, "Amp Step 3_HEX")

    rows: List[Dict] = []

    # HEX react'leri id ile indexleyelim (O(1))
    hex_map = {}
    for hx in hex_run.findall("rdml:react", namespaces=RDML_NS):
        rid = hx.get("id", "")
        if rid:
            hex_map[rid] = hx

    for fam_react in fam_run.findall("rdml:react", namespaces=RDML_NS):
        row = parse_react(fam_react, run_id="FAM")
        rid = row["React ID"]

        hx = hex_map.get(rid)
        if hx is not None:
            hx_row = parse_react(hx, run_id="HEX")
            row["HEX Ct"] = hx_row.get("HEX Ct", "")
            row["HEX koordinat list"] = hx_row.get("HEX koordinat list", "")
        else:
            row["HEX Ct"] = ""
            row["HEX koordinat list"] = ""

        rows.append(row)

    return rows
