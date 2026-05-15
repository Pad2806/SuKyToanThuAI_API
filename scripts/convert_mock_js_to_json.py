import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MOCK_DIR = ROOT / "SuKyAI_Web" / "src" / "data" / "mock"
OUT_DIR = ROOT / "SuKyAI_API" / "scripts" / "seed-json"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MOCK_DIR / "eras.json", OUT_DIR / "eras.json")
    shutil.copyfile(MOCK_DIR / "events.json", OUT_DIR / "events.json")

    for source in sorted(MOCK_DIR.glob("*.js")):
        data = load_es_module_object(source)
        target = OUT_DIR / f"{source.stem}.json"
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"converted {source.name} -> {target.name}")


def load_es_module_object(path: Path) -> dict:
    script = """
const modulePath = process.argv[1];
const mod = await import(modulePath);
const data = Object.values(mod).find((value) =>
  value && typeof value === 'object' && !Array.isArray(value) && value.slug
);
if (!data) {
  throw new Error(`No exported event object found in ${modulePath}`);
}
console.log(JSON.stringify(data));
"""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script, path.as_uri()],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(result.stdout)


if __name__ == "__main__":
    main()

