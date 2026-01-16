<?php
header('Content-Type: application/json');
$db_config = include(__DIR__ . '/db_config.php');
try {
    $pdo = new PDO("mysql:host={$db_config['host']};dbname={$db_config['dbname']};charset=utf8mb4", $db_config['user'], $db_config['pass']);
    $stmt = $pdo->prepare("SELECT id, differences, data FROM puzzles WHERE id = ?");
    $stmt->execute(['i4']);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    echo json_encode($row, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
} catch (Exception $e) {
    echo json_encode(['error' => $e->getMessage()]);
}
