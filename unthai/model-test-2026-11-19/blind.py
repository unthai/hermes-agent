"""Relabel outputs A-E per case in a seeded random order. Writes blind/<case>.txt (judge view, no model names)
and blind_key.json (label -> model), read only after scoring."""
import json, pathlib, random

HERE = pathlib.Path(__file__).parent
(HERE / "blind").mkdir(exist_ok=True)
rng = random.Random(20261119)
key = {}
for cf in sorted((HERE / "cases").glob("*.json")):
    c = json.loads(cf.read_text())
    outs = sorted((HERE / "raw").glob(f"{c['id']}__*.txt"))
    rng.shuffle(outs)
    key[c["id"]] = {}
    parts = [f"CASE {c['id']} ({c['job']})\nEXPECT: {c['expect']}\n"]
    for label, p in zip("ABCDE", outs):
        key[c["id"]][label] = p.stem.split("__")[1]
        parts.append(f"===== {label} =====\n{p.read_text().strip()}\n")
    (HERE / "blind" / f"{c['id']}.txt").write_text("\n".join(parts))
(HERE / "blind_key.json").write_text(json.dumps(key, indent=1))
print("blinded", len(key))
