import json
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent.absolute()
OUTPUT_DIR = BASE_DIR / "puzzles"
if not OUTPUT_DIR.exists():
    OUTPUT_DIR = BASE_DIR / "public" / "puzzles"

def update_manifest():
    puzzles = []
    for puzzle_id in sorted(os.listdir(OUTPUT_DIR)):
        puzzle_path = OUTPUT_DIR / puzzle_id
        if puzzle_path.is_dir():
            answer_path = puzzle_path / "answer.json"
            if answer_path.exists():
                with open(answer_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    puzzles.append({
                        "id": data["puzzle_id"],
                        "differences": data["total_differences"],
                        "path": f"puzzles/{data['puzzle_id']}"
                    })
    
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "total_puzzles": len(puzzles),
        "puzzles": puzzles
    }
    
    with open(OUTPUT_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"Manifest updated with {len(puzzles)} puzzles.")

if __name__ == "__main__":
    update_manifest()
