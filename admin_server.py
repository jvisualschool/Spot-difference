from flask import Flask, request, jsonify, send_from_directory
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
import pymysql

app = Flask(__name__, static_folder='.', static_url_path='')

BASE_DIR = Path(__file__).parent.absolute()
UPLOAD_FOLDER = BASE_DIR / "IMG"
# In production (Bitnami/Apache), 'public' content is in the root.
if (BASE_DIR / "public" / "puzzles").exists():
    PUZZLES_DIR = BASE_DIR / "public" / "puzzles"
else:
    PUZZLES_DIR = BASE_DIR / "puzzles"
MANIFEST_PATH = PUZZLES_DIR / "manifest.json"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database Profile
try:
    from db_config import DB_CONFIG as IMPORTED_CONFIG
    DB_CONFIG = {**IMPORTED_CONFIG, "cursorclass": pymysql.cursors.DictCursor}
except ImportError:
    import os
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASS", ""),
        "database": os.getenv("DB_NAME", "FINDSPOT"),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor
    }

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

def sync_db_to_manifest():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, created_at, recommended, differences, status FROM puzzles ORDER BY id")
            db_puzzles = cursor.fetchall()
            
            # Format dates for JSON
            for p in db_puzzles:
                if p['created_at']:
                    p['created_at'] = p['created_at'].isoformat()
            
            manifest_data = {
                "puzzles": db_puzzles,
                "generated_at": datetime.now().isoformat()
            }
            
            with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        conn.close()
    except Exception as e:
        print(f"Error syncing DB to manifest: {e}")

@app.route('/')
def index():
    return send_from_directory('.', 'admin_dashboard.html')

@app.route('/save-puzzle', methods=['POST'])
def save_puzzle():
    data = request.json
    puzzle_id = data.get('puzzle_id')
    if not puzzle_id:
        return jsonify({"error": "Missing puzzle_id"}), 400

    answer_path = PUZZLES_DIR / puzzle_id / "answer.json"
    
    try:
        # 1. Save answer.json
        with open(answer_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        # 2. Update DB
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO puzzles (id, created_at, differences, data)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                differences = VALUES(differences),
                data = VALUES(data)
            """
            cursor.execute(sql, (
                puzzle_id, 
                data.get('created_at', datetime.now().isoformat()),
                data.get('total_differences', 10),
                json.dumps(data, ensure_ascii=False)
            ))
        conn.commit()
        conn.close()

        # 3. Sync to manifest.json for frontend
        sync_db_to_manifest()

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image part"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        
        # Determine next ID from DB
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM puzzles WHERE id LIKE 'i%'")
            rows = cursor.fetchall()
            ids = [int(r['id'].replace('i', '')) for r in rows if r['id'].startswith('i')]
            next_id = f"i{max(ids) + 1}" if ids else "i1"
        conn.close()
        
        extension = os.path.splitext(filename)[1]
        new_filename = f"{next_id}{extension}"
        file_path = UPLOAD_FOLDER / new_filename
        file.save(file_path)
        
        # Run generator
        print(f"🚀 Generating puzzle for {next_id}...")
        try:
            subprocess.run(["python3", "generator/generate_puzzle.py", str(file_path)], check=True)
            
            # Initial Save to DB
            answer_path = PUZZLES_DIR / next_id / "answer.json"
            if answer_path.exists():
                with open(answer_path, 'r', encoding='utf-8') as f:
                    ans_data = json.load(f)
                
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    sql = "INSERT INTO puzzles (id, created_at, differences, data) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql, (
                        next_id,
                        ans_data.get('created_at', datetime.now().isoformat()),
                        ans_data.get('total_differences', 10),
                        json.dumps(ans_data, ensure_ascii=False)
                    ))
                conn.commit()
                conn.close()
                sync_db_to_manifest()

            return jsonify({
                "status": "success",
                "puzzle_id": next_id,
                "review_url": f"./puzzles/review.html?ID={next_id}"
            })
        except Exception as e:
            return jsonify({"error": f"Generation failed: {str(e)}"}), 500

@app.route('/regenerate', methods=['POST'])
def regenerate_puzzle():
    data = request.json
    puzzle_id = data.get('puzzle_id')
    if not puzzle_id:
        return jsonify({"error": "Missing puzzle_id"}), 400

    possible_files = list(UPLOAD_FOLDER.glob(f"{puzzle_id}.*"))
    if not possible_files:
        return jsonify({"error": f"Original image for {puzzle_id} not found"}), 404
    
    file_path = possible_files[0]
    
    try:
        subprocess.run(["python3", "generator/generate_puzzle.py", str(file_path)], check=True)
        # Update DB after regeneration
        answer_path = PUZZLES_DIR / puzzle_id / "answer.json"
        if answer_path.exists():
            with open(answer_path, 'r', encoding='utf-8') as f:
                ans_data = json.load(f)
            conn = get_db_connection()
            with conn.cursor() as cursor:
                sql = "UPDATE puzzles SET differences = %s, data = %s WHERE id = %s"
                cursor.execute(sql, (ans_data.get('total_differences', 10), json.dumps(ans_data), puzzle_id))
            conn.commit()
            conn.close()
            sync_db_to_manifest()

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/toggle-recommended', methods=['POST'])
def toggle_recommended():
    data = request.json
    puzzle_id = data.get('puzzle_id')
    recommended = data.get('recommended')

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("UPDATE puzzles SET recommended = %s WHERE id = %s", (recommended, puzzle_id))
        conn.commit()
        conn.close()
        sync_db_to_manifest()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/toggle-status', methods=['POST'])
def toggle_status():
    data = request.json
    puzzle_id = data.get('puzzle_id')
    status = data.get('status') # 'ready' or 'pending'

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("UPDATE puzzles SET status = %s WHERE id = %s", (status, puzzle_id))
        conn.commit()
        conn.close()
        sync_db_to_manifest()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Initial sync from files to DB if DB is empty
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as cnt FROM puzzles")
            if cursor.fetchone()['cnt'] == 0:
                print("Initial DB Load from manifest.json...")
                if MANIFEST_PATH.exists():
                    with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                    for p in manifest.get('puzzles', []):
                        # try to load full data from answer.json
                        ans_p = PUZZLES_DIR / p['id'] / "answer.json"
                        ans_data = {}
                        created_at = datetime.now()
                        if ans_p.exists():
                            with open(ans_p, 'r', encoding='utf-8') as f:
                                ans_data = json.load(f)
                                if 'created_at' in ans_data:
                                    try: created_at = datetime.fromisoformat(ans_data['created_at'])
                                    except: pass
                        
                        cursor.execute("INSERT INTO puzzles (id, created_at, recommended, differences, data, status) VALUES (%s, %s, %s, %s, %s, %s)",
                                       (p['id'], created_at, p.get('recommended', False), p.get('differences', 10), json.dumps(ans_data), p.get('status', 'ready')))
                    conn.commit()
        conn.close()
    except Exception as e:
        print(f"Startup DB sync error: {e}")

    app.run(port=8001, debug=True)
