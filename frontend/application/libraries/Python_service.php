<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Python_service {
    private $api_url;
    private $api_key;

    public function __construct() {
        $this->api_url = getenv('PYTHON_API_URL') ?: 'http://127.0.0.1:8000';
        $this->api_key = getenv('PYTHON_API_KEY') ?: '';
    }

    public function send_chat($client_id, $query) {
        $result = $this->request_json('/chat', [
            'client_id' => $client_id,
            'query' => $query
        ], 25);

        if (!isset($result['answer'])) {
            return array_merge($this->chat_error(), $result);
        }
        return $result;
    }

    public function submit_feedback($chat_id, $feedback, $client_id) {
        return $this->request_json('/feedback', [
            'chat_id' => (int)$chat_id,
            'client_id' => $client_id,
            'feedback' => $feedback
        ], 8);
    }

    private function request_json($path, $payload, $timeout) {
        if (!$this->api_key || !function_exists('curl_init')) {
            log_message('error', 'Report Copilot API key or cURL extension is unavailable.');
            return ['error' => true, 'message' => 'The Report Copilot service is temporarily unavailable.'];
        }

        $body = json_encode($payload);
        if ($body === FALSE) {
            log_message('error', 'Report Copilot request could not be encoded as JSON.');
            return ['error' => true, 'message' => 'The request could not be processed.'];
        }

        $handle = curl_init(rtrim($this->api_url, '/') . $path);
        if ($handle === FALSE) {
            log_message('error', 'Could not initialize the Report Copilot HTTP client.');
            return ['error' => true, 'message' => 'The Report Copilot service is temporarily unavailable.'];
        }

        curl_setopt_array($handle, [
            CURLOPT_RETURNTRANSFER => TRUE,
            CURLOPT_POST => TRUE,
            CURLOPT_POSTFIELDS => $body,
            CURLOPT_CONNECTTIMEOUT => 3,
            CURLOPT_TIMEOUT => $timeout,
            CURLOPT_HTTPHEADER => [
                'Content-Type: application/json',
                'X-API-Key: ' . $this->api_key
            ]
        ]);

        $response = curl_exec($handle);
        $http_code = (int)curl_getinfo($handle, CURLINFO_HTTP_CODE);
        $curl_error = curl_error($handle);
        curl_close($handle);

        if ($response === FALSE || $http_code < 200 || $http_code >= 300) {
            log_message('error', 'Report Copilot request failed (HTTP ' . $http_code . '): ' . substr($curl_error, 0, 300));
            return ['error' => true, 'message' => 'The Report Copilot service is temporarily unavailable.'];
        }

        $decoded = json_decode($response, TRUE);
        if (!is_array($decoded) || json_last_error() !== JSON_ERROR_NONE) {
            log_message('error', 'Report Copilot returned an invalid JSON response.');
            return ['error' => true, 'message' => 'The Report Copilot service returned an invalid response.'];
        }
        return $decoded;
    }

    private function chat_error() {
        return [
            'error' => true,
            'answer' => 'The Report Copilot service is temporarily unavailable. Please contact your support team or try again shortly.',
            'citations' => [],
            'conflicts' => [],
            'derived_values' => [],
            'confidence' => 0.0,
            'escalated' => true
        ];
    }
}
