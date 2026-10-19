<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Copilot extends CI_Controller {
    private $demo_mode = false;

    public function __construct() {
        parent::__construct();
        $this->load->library('session');
        $this->load->library('python_service');
        $this->load->helper(['url', 'security', 'form']);
        
        $this->demo_mode = filter_var(getenv('ATLAS_DEMO_MODE') ?: 'false', FILTER_VALIDATE_BOOLEAN);
        if ($this->demo_mode && !$this->session->userdata('active_client')) {
            $this->session->set_userdata('active_client', 'C-01');
        } elseif (!$this->demo_mode) {
            // The host portal must set this session value only after authenticating
            // the user and resolving their organization from its trusted identity store.
            $session_field = getenv('ATLAS_CLIENT_SESSION_FIELD') ?: 'authenticated_client_id';
            $authenticated_client = $this->session->userdata($session_field);
            if (is_int($authenticated_client)) {
                $authenticated_client = (string)$authenticated_client;
            }
            if (is_string($authenticated_client) && preg_match('/^[A-Za-z0-9_-]{1,64}$/', $authenticated_client)) {
                $this->session->set_userdata('active_client', $authenticated_client);
            } else {
                $this->session->unset_userdata('active_client');
            }
        }
    }

    public function index() {
        $active_client = $this->session->userdata('active_client');
        if (!$active_client) {
            show_error('Sign in through your organization portal to use Report Copilot.', 401);
            return;
        }
        $data['active_client'] = $this->session->userdata('active_client');
        $data['demo_mode'] = $this->demo_mode;
        $data['dataset_label'] = getenv('DATASET_LABEL') ?: 'production';
        $data['csrf_name'] = $this->security->get_csrf_token_name();
        $data['csrf_hash'] = $this->security->get_csrf_hash();
        $this->load->view('copilot/chat', $data);
    }

    public function switch_client() {
        if (!$this->demo_mode) {
            show_error('Client switching is disabled outside demo mode.', 403);
            return;
        }
        $client_id = $this->input->post('client_id', TRUE);
        if (in_array($client_id, ['C-01', 'C-02'])) {
            $this->session->set_userdata('active_client', $client_id);
        }
        redirect('copilot');
    }

    public function send() {
        // Enforce JSON POST
        $client_id = $this->session->userdata('active_client');
        if (!$client_id) {
            $this->output->set_status_header(401)->set_content_type('application/json')
                ->set_output(json_encode(['error' => true, 'message' => 'Authenticated client account is required.']));
            return;
        }
        $query = $this->input->post('query', TRUE);
        if (!is_string($query) || trim($query) === '' || strlen($query) > 8000) {
            $this->output->set_status_header(422)->set_content_type('application/json')
                ->set_output(json_encode(['error' => true, 'message' => 'Enter a question of 1 to 8000 characters.']));
            return;
        }

        // Call backend service
        $result = $this->python_service->send_chat($client_id, $query);

        // Include updated CSRF hash for front-end token renewal
        $result['csrf_token'] = $this->security->get_csrf_hash();
        
        $this->output
             ->set_content_type('application/json')
             ->set_output(json_encode($result));
    }

    public function feedback() {
        $chat_id = filter_var($this->input->post('chat_id', TRUE), FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);
        $feedback = $this->input->post('feedback', TRUE);

        if (!$chat_id || !in_array($feedback, ['up', 'down'], TRUE)) {
            $this->output->set_status_header(422)->set_content_type('application/json')
                ->set_output(json_encode(['status' => 'error', 'message' => 'Invalid feedback request.']));
            return;
        }

        $client_id = $this->session->userdata('active_client');
        if (!$client_id) {
            $this->output->set_status_header(401)->set_content_type('application/json')
                ->set_output(json_encode(['status' => 'error', 'message' => 'Authenticated client account is required.']));
            return;
        }
        $res = $this->python_service->submit_feedback($chat_id, $feedback, $client_id);
        $res['csrf_token'] = $this->security->get_csrf_hash();
        
        $this->output
             ->set_content_type('application/json')
             ->set_output(json_encode($res));
    }
}
