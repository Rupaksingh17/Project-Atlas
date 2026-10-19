<?php
defined('BASEPATH') OR exit('No direct script access allowed');

$config['base_url'] = getenv('ATLAS_PUBLIC_BASE_URL') ?: '/';
$config['index_page'] = 'index.php';
$config['enable_query_strings'] = FALSE;
$config['uri_protocol'] = 'REQUEST_URI';
$config['url_suffix'] = '';
$config['language'] = 'english';
$config['charset'] = 'UTF-8';
$config['enable_hooks'] = FALSE;
$config['subclass_prefix'] = 'MY_';
$config['composer_autoload'] = FALSE;
$config['permitted_uri_chars'] = 'a-z 0-9~%.:_\-';

$config['log_threshold'] = 1;
$config['log_path'] = '';
$config['log_file_extension'] = '';
$config['log_file_permissions'] = 0644;
$config['log_date_format'] = 'Y-m-d H:i:s';

$config['error_views_path'] = '';
$config['standardize_newlines'] = FALSE;
$config['global_xss_filtering'] = FALSE;

$config['csrf_protection'] = TRUE;
$config['csrf_token_name'] = 'atlas_csrf_token';
$config['csrf_cookie_name'] = 'atlas_csrf_cookie';
$config['csrf_expire'] = 7200;
$config['csrf_regenerate'] = TRUE;
$config['csrf_exclude_uris'] = array();

$ci_encryption_key = getenv('CI_ENCRYPTION_KEY') ?: '';
if (strlen($ci_encryption_key) < 32 || strpos($ci_encryption_key, 'CHANGE_ME') !== FALSE) {
    error_log('Project Atlas portal encryption key is missing or invalid.');
    http_response_code(503);
    exit('The portal is not configured.');
}
$config['encryption_key'] = $ci_encryption_key;
$config['sess_driver'] = 'files';
$config['sess_cookie_name'] = 'atlas_session';
$config['sess_expiration'] = 7200;
$config['sess_save_path'] = rtrim(sys_get_temp_dir(), '\\/');
$config['sess_match_ip'] = FALSE;
$config['sess_time_to_update'] = 300;
$config['sess_regenerate_destroy'] = TRUE;
$config['cookie_secure'] = filter_var(getenv('COOKIE_SECURE') ?: 'false', FILTER_VALIDATE_BOOLEAN);
$config['cookie_httponly'] = TRUE;
$config['cookie_samesite'] = 'Lax';
