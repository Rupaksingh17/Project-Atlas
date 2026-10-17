<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Python_service {
    private $api_url;
    private $api_key;
    private $timeout;

    public function __construct() {
        $this->api_url = getenv('PYTHON_API_URL') ?: 'http://127.0.0.1:8000';
        $this->api_key = getenv('PYTHON_API_KEY') ?: 'atlas-secret-key-2026';
        $this->timeout = 25;
    }

    public function send_chat($client_id, $query) {
        $endpoint = rtrim($this->api_url, '/') . '/chat';
        $payload = json_encode([
            'client_id' => $client_id,
            'query' => $query
        ]);

        $ch = curl_init($endpoint);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 3);
        curl_setopt($ch, CURLOPT_TIMEOUT, $this->timeout);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/json',
            'X-API-Key: ' . $this->api_key
        ]);

        $response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curl_error = curl_error($ch);
        curl_close($ch);

        if ($curl_error || $http_code !== 200) {
            return [
                'error' => true,
                'answer' => 'The Report Copilot service is temporarily unreachable. An analyst has been alerted. Please try again shortly.',
                'citations' => [],
                'conflicts' => [],
                'derived_values' => [],
                'confidence' => 0.0,
                'escalated' => true
            ];
        }

        $decoded = json_decode($response, true);
        if (!$decoded) {
            return [
                'error' => true,
                'answer' => 'Received an invalid response payload from the copilot engine.',
                'citations' => [],
                'conflicts' => [],
                'derived_values' => [],
                'confidence' => 0.0,
                'escalated' => true
            ];
        }

        return $decoded;
    }

    public function submit_feedback($chat_id, $feedback) {
        $endpoint = rtrim($this->api_url, '/') . '/feedback';
        $payload = json_encode([
            'chat_id' => (int)$chat_id,
            'feedback' => $feedback
        ]);

        $ch = curl_init($endpoint);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 2);
        curl_setopt($ch, CURLOPT_TIMEOUT, 5);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/json',
            'X-API-Key: ' . $this->api_key
        ]);

        $response = curl_exec($ch);
        curl_close($ch);
        return json_decode($response, true);
    }
}
