from pathlib import Path
RAW = Path(__file__).parent.parent / "raw"
R = lambda k: str(RAW / f"{k}.jpg")
