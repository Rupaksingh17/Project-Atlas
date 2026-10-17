<?php
defined('BASEPATH') OR exit('No direct script access allowed');

class Copilot extends CI_Controller {

    public function __construct() {
        parent::__construct();
        $this->load->library('session');
        $this->load->library('python_service');
        $this->load->helper(['url', 'security', 'form']);
        
        // Default to client C-01 (Northwind Utilities)
        if (!$this->session->userdata('active_client')) {
            $this->session->set_userdata('active_client', 'C-01');
        }
    }

    public function index() {
        $data['active_client'] = $this->session->userdata('active_client');
        $data['csrf_name'] = $this->security->get_csrf_token_name();
        $data['csrf_hash'] = $this->security->get_csrf_hash();
        $this->load->view('copilot/chat', $data);
    }

    public function switch_client() {
        $client_id = $this->input->post('client_id', TRUE);
        if (in_array($client_id, ['C-01', 'C-02'])) {
            $this->session->set_userdata('active_client', $client_id);
        }
        redirect('copilot');
    }

    public function send() {
        // Enforce JSON POST
        $client_id = $this->session->userdata('active_client') ?: 'C-01';
        $query = $this->input->post('query', TRUE);

        if (empty($query)) {
            echo json_encode(['error' => true, 'message' => 'Query cannot be empty.']);
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
        $chat_id = $this->input->post('chat_id', TRUE);
        $feedback = $this->input->post('feedback', TRUE);

        if (!in_array($feedback, ['up', 'down'])) {
            echo json_encode(['status' => 'error', 'message' => 'Invalid feedback value.']);
            return;
        }

        $res = $this->python_service->submit_feedback($chat_id, $feedback);
        $res['csrf_token'] = $this->security->get_csrf_hash();
        
        $this->output
             ->set_content_type('application/json')
             ->set_output(json_encode($res));
    }
}
