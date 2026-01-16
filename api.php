<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

$db_config = file_exists(__DIR__ . '/db_config.php') 
    ? include(__DIR__ . '/db_config.php') 
    : [
        'host' => 'localhost',
        'dbname' => 'FINDSPOT',
        'user' => 'root',
        'pass' => '' // .env 사용 권장
    ];

try {
    $pdo = new PDO("mysql:host={$db_config['host']};dbname={$db_config['dbname']};charset=utf8mb4", $db_config['user'], $db_config['pass']);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

    // Ensure status column exists
    try {
        $pdo->query("SELECT status FROM puzzles LIMIT 1");
    } catch (Exception $e) {
        $pdo->query("ALTER TABLE puzzles ADD COLUMN status VARCHAR(20) DEFAULT 'ready'");
    }
} catch (PDOException $e) {
    echo json_encode(['error' => 'DB Connection failed: ' . $e->getMessage()]);
    exit;
}

$action = $_GET['action'] ?? '';
$input = json_decode(file_get_contents('php://input'), true);

try {
    switch ($action) {
        case 'list-puzzles':
            $stmt = $pdo->query("SELECT id, created_at, recommended, differences, status FROM puzzles ORDER BY id");
            $puzzles = $stmt->fetchAll();
            echo json_encode([
                "puzzles" => $puzzles,
                "total_puzzles" => count($puzzles),
                "generated_at" => date('c')
            ]);
            break;

        case 'get-puzzle':
            $id = $_GET['id'] ?? '';
            $stmt = $pdo->prepare("SELECT data FROM puzzles WHERE id = ?");
            $stmt->execute([$id]);
            $row = $stmt->fetch();
            if ($row) {
                echo $row['data']; 
            } else {
                http_response_code(404);
                echo json_encode(['error' => 'Puzzle not found']);
            }
            break;

        case 'save-puzzle':
            $puzzle_id = $input['puzzle_id'] ?? '';
            if (!$puzzle_id) throw new Exception("Missing puzzle_id");

            $stmt = $pdo->prepare("INSERT INTO puzzles (id, created_at, differences, data) 
                                   VALUES (?, ?, ?, ?) 
                                   ON DUPLICATE KEY UPDATE differences = VALUES(differences), data = VALUES(data)");
            $stmt->execute([
                $puzzle_id,
                $input['created_at'] ?? date('Y-m-d H:i:s'),
                $input['total_differences'] ?? count($input['differences'] ?? []),
                json_encode($input, JSON_UNESCAPED_UNICODE)
            ]);

            echo json_encode(['status' => 'success']);
            break;

        case 'upload':
            if (!isset($_FILES['image'])) throw new Exception("No image uploaded");

            // Determine next ID
            $stmt = $pdo->query("SELECT id FROM puzzles WHERE id LIKE 'i%'");
            $rows = $stmt->fetchAll();
            $ids = array_map(function($r) { 
                preg_match('/\d+/', $r['id'], $matches);
                return (int)($matches[0] ?? 0); 
            }, $rows);
            $next_num = ($ids ? max($ids) + 1 : 1);
            $puzzle_id = 'i' . $next_num;

            $upload_dir = __DIR__ . '/IMG';
            if (!is_dir($upload_dir)) mkdir($upload_dir, 0777, true);

            $ext = pathinfo($_FILES['image']['name'], PATHINFO_EXTENSION);
            $file_path = $upload_dir . '/' . $puzzle_id . '.' . $ext;
            if (!move_uploaded_file($_FILES['image']['tmp_name'], $file_path)) {
                throw new Exception("Failed to save uploaded image.");
            }

            // Run AI generator
            $generator_path = __DIR__ . '/generator/generate_puzzle.py';
            $cmd = "python3 " . escapeshellarg($generator_path) . " " . escapeshellarg($file_path) . " 2>&1";
            exec($cmd, $output, $return_var);
            if ($return_var !== 0) throw new Exception("Nano Banana Pro failed: " . implode("\n", $output));

            // Sync AI result (answer.json) to DB
            $puzzles_dir = __DIR__ . '/puzzles';
            if (!is_dir($puzzles_dir)) $puzzles_dir = __DIR__ . '/public/puzzles';
            $answer_path = $puzzles_dir . '/' . $puzzle_id . '/answer.json';
            
            if (file_exists($answer_path)) {
                $ans_data = json_decode(file_get_contents($answer_path), true);
                $stmt = $pdo->prepare("INSERT INTO puzzles (id, created_at, differences, data) VALUES (?, ?, ?, ?)");
                $stmt->execute([
                    $puzzle_id,
                    $ans_data['created_at'] ?? date('Y-m-d H:i:s'),
                    $ans_data['total_differences'] ?? 10,
                    json_encode($ans_data, JSON_UNESCAPED_UNICODE)
                ]);
            }

            echo json_encode([
                'status' => 'success',
                'puzzle_id' => $puzzle_id,
                'review_url' => './puzzles/review.html?ID=' . $puzzle_id
            ]);
            break;

        case 'regenerate':
            $puzzle_id = $input['puzzle_id'] ?? '';
            if (!$puzzle_id) throw new Exception("Missing puzzle_id");
            
            $upload_dir = __DIR__ . '/IMG';
            $puzzles_dir = __DIR__ . '/puzzles';
            if (!is_dir($puzzles_dir)) $puzzles_dir = __DIR__ . '/public/puzzles';

            // 1. Try IMG directory first
            $files = glob($upload_dir . '/' . $puzzle_id . '.*');
            
            // 2. Try puzzles/ID/original.* directory
            if (!$files) {
                $files = glob($puzzles_dir . '/' . $puzzle_id . '/original.*');
            }

            if (!$files) throw new Exception("Original image not found for ID: " . $puzzle_id);

            $generator_path = __DIR__ . '/generator/generate_puzzle.py';
            $cmd = "python3 " . escapeshellarg($generator_path) . " " . escapeshellarg($files[0]) . " 2>&1";
            exec($cmd, $output, $return_var);

            if ($return_var !== 0) {
                throw new Exception("Nano Banana Pro failed: " . implode("\n", $output));
            }

            $answer_path = $puzzles_dir . '/' . $puzzle_id . '/answer.json';
            if (file_exists($answer_path)) {
                $ans_data = json_decode(file_get_contents($answer_path), true);
                $stmt = $pdo->prepare("UPDATE puzzles SET differences = ?, data = ? WHERE id = ?");
                $stmt->execute([
                    $ans_data['total_differences'] ?? 10,
                    json_encode($ans_data, JSON_UNESCAPED_UNICODE),
                    $puzzle_id
                ]);
            }
            echo json_encode(['status' => 'success']);
            break;

        case 'toggle-recommended':
            $puzzle_id = $input['puzzle_id'] ?? '';
            $recommended = $input['recommended'] ? 1 : 0;
            $stmt = $pdo->prepare("UPDATE puzzles SET recommended = ? WHERE id = ?");
            $stmt->execute([$recommended, $puzzle_id]);
            echo json_encode(['status' => 'success']);
            break;

        case 'toggle-status':
            $puzzle_id = $input['puzzle_id'] ?? '';
            $status = $input['status'] ?? 'ready';
            $stmt = $pdo->prepare("UPDATE puzzles SET status = ? WHERE id = ?");
            $stmt->execute([$status, $puzzle_id]);
            echo json_encode(['status' => 'success']);
            break;

        default:
            throw new Exception("Unknown action: " . $action);
    }
} catch (Exception $e) {
    echo json_encode(['error' => 'Server Error: ' . $e->getMessage()]);
}
