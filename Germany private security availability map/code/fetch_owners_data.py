"""Download the Destatis tables behind Part 3 (Owners) into data/raw/destatis/.

  73311-0011  VAT taxpayers and taxable turnover by Land, 2014-2024, WZ 2008 down
              to 5 digits: here division 80 and its classes 80.10 (private
              guarding and security), 80.20 (alarm systems) and 80.30 (detectives).
  73311-0002  The same for Germany as a whole, 2014-2024 (complete national series;
              a few Land cells are suppressed, so the Länder do not always sum).
  73311-0005  The same for Germany by legal form, 2020-2024 (sole proprietors,
              partnerships, GmbH, ...).

Run from the project folder:  python code/fetch_owners_data.py
"""

from pathlib import Path

from secmap import genesis as g

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "destatis"

WZ80 = g.node("WZ08-N", "WZ08P5", [
    g.node("WZ08-80", "WZ08P6", [
        g.node("WZ08-801", "WZ08P7", [g.node("WZ08-8010", "WZ08P8", [g.node("WZ08-80100")])]),
        g.node("WZ08-802", "WZ08P7", [g.node("WZ08-8020", "WZ08P8", [g.node("WZ08-80200")])]),
        g.node("WZ08-803", "WZ08P7", [g.node("WZ08-8030", "WZ08P8", [g.node("WZ08-80300")])]),
    ]),
])
MEASURES = ["STR040", "STR042"]  # taxpayers (count), taxable turnover from supplies and services (EUR 1000)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    t = "73311-0011"
    df = g.fetch_flat(t, {"JAHR": g.all_values(t, "JAHR"), "DLAND": g.all_values(t, "DLAND"),
                          "WZ08BA": [WZ80]}, contents=MEASURES)
    df.to_csv(OUT / f"{t}_wz80_laender.csv", index=False)
    print(t, df.shape)

    t = "73311-0002"
    df = g.fetch_flat(t, {"JAHR": g.all_values(t, "JAHR"), "WZ08BA": [WZ80]}, contents=MEASURES)
    df.to_csv(OUT / f"{t}_wz80_deutschland.csv", index=False)
    print(t, df.shape)

    t = "73311-0005"
    df = g.fetch_flat(t, {"JAHR": g.all_values(t, "JAHR"), "RECF03": g.all_values(t, "RECF03"),
                          "WZ08BA": [WZ80]}, contents=MEASURES)
    df.to_csv(OUT / f"{t}_wz80_rechtsformen.csv", index=False)
    print(t, df.shape)


if __name__ == "__main__":
    main()
