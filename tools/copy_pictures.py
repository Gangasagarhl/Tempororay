"""Copy the docs' pictures next to the lab so they show without internet."""
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "source" / "docs_repo" / "src"
count = 0
for picture in SOURCE.rglob("*"):
    if picture.is_file() and picture.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}:
        target = ROOT / "site" / "media" / picture.relative_to(SOURCE)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(picture, target)
        count += 1
print("pictures available offline:", count)
