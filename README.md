# cyp_test_lib spec


## Description
**cyp_test_lib** is library providing utilities for remote SSH management, systemd service control, log processing, and test automation.  
Below is a description of each module, organized by their relevance and usage.


## ssh_client
- `class SShResponse`  
Data container for command execution results: stdout, stderr, and return code.
- `class UnexpectedSshResponseException`  
Exception raised for unexpected SSH command return codes.
- `class SshClient`  
Manages secure remote command execution and file transfers over SSH.
- - `connect`  
Establish SSH connection with optional timeout and handle authentication fallback.
- - `exec`  
Execute a command via SSH, returning stdout, stderr, and rc; raises if unexpected return code.
(Hides password in logs for sudo commands.)
- - `exec_sudo`  
Execute a command remotely using sudo with optional bash shell.
- - `exec_nohup_sudo`  
Execute a command remotely using nohup and sudo with optional bash shell.
- - `close`  
Close the SSH connection.
- - `get_file`  
Get file via SCP from remote to local.
- - `put_file`  
Put file via SCP from local to remote, optionally recursive.
- - `put_file_sudo`  
Put file via SCP with sudo: uploads to temp location then moves to destination.
- - `create_remote_dir`  
Create directory on remote host.
- - `remove_dir_from_host`  
Remove directory from remote host using sudo.
- - `write_text_to_remote`  
Write given text content to a remote file via temporary local file upload and sudo move.


## systemd
- `class Systemd`  
Provides static methods to manage and control systemd services remotely via SSH.
- - `service_enable`  
Enable a systemd service.
- - `service_disable`  
Disable a systemd service.
- - `daemon_reload`  
Reload systemd daemon.
- - `reset_failed`  
Reset service start failures.
- - `service_is_active`  
Check if a service is active, retrying a number of times before failing.
- - `service_status`  
Get status of a service.
- - `service_start`  
Start a service and verify its status.
- - `service_restart`  
Restart a service and verify its status.
- - `service_reload`  
Reload a service and verify its status.
- - `service_stop`  
Stop a service.
- - `get_service_sdnotify_status`  
Get the sdnotify status of a service.
- - `service_is_sdnotify_ready`  
Verify the service reports sdnotify readiness, retrying up to 4 times.


## os_helper
- `is_file_present`  
Check if a file exists on the remote server.
- `count_file_lines`  
Count the number of lines in a remote file.
- `grep_file`  
Search for a substring inside a remote file, optionally after a specific line.
- `grep_file_with_wait`  
Repeatedly search for a substring in a file until found or timeout.
- `get_server_seconds_since_epoch`  
Get server seconds since epoch.
- `get_latest_pid`  
Get pid from systemd status.
- `add_line_to_file`  
Add a line to a remote file, optionally cleaning up empty lines.
- `move_file`  
Temporarily moves a file on the remote server, restoring it after operations complete.
- `get_service_build_info`  
Gets build information for a service on the remote host.
- `make_backup`  
Create a backup copy of a file.
- `restore_backup`  
Restore a backup copy of a file.
- `add_or_update_line_in_file`  
Add or update a line in a file, replacing or appending it.
- `get_recent_logs`  
Get recent logs
- `run_service_from_console`  
Run service from cmd
- `send_signals`  
Run a service and send it a specified Linux signal.
- `get_service_version`  
Get service version


## journalctl_helper
- `get_journalctl_output_with_delta_seconds`  
Get journalctl output for a given service from N seconds ago.
- `get_journalctl_output_for_pid`  
Get journalctl output filtered by service and specific PID.
- `get_journalctl_for_latest_pid`  
Get journalctl records for the latest pid of a service. Retries if fewer lines than requested.
- `grep_journalctl_for_latest_pid`  
Grep journalctl records for latest pid searching for a substring, waiting up to specified seconds. Returns matched records or raises exception.
- `grep_journalctl`  
Grep journalctl records for a given substring starting from specified seconds ago.
- `grep_journalctl_with_wait`  
Grep journalctl records for substring with retries and wait time, returning results or raising exceptions.


## remote_info
- `class RemoteTargetInfo`  
Manages SSH connection setup using environment or file-based config and provides remote system information.
- - `target_kernel`  
Returns the kernel version of the remote target.
- - `is_virtual`  
Checks if the remote host is a virtual machine.
- - `is_qemu`  
Checks if the remote host is running on QEMU virtualization.
- - `is_dns_enable`  
Determines if DNS resolution is enabled on the remote host by pinging an external address.


## remote_actions
- `class RemoteActions`  
Handles SSH connection setup and remote command execution using an SSH client.
- - `kill_process_by_name`  
Kills processes by name on the remote host, optionally using sudo and supporting single or multiple process killing.
- - `exec_in_dedicated_session`  
Executes a command on the remote host in a dedicated SSH session and returns the result, then closes the connection.


## service_check
- `check_services`  
Checks the status of provided services.


## randomization
- `rand_str`  
Generates random string


## skip_if
- `skip_virtual`  
Decorator to skip tests if running on a virtual machine.
- `skip_qemu`  
Decorator to skip tests if running on QEMU virtualization.
- `skip_dns`  
Decorator to skip tests if DNS resolution is disabled.


## string_check
- `check_elements_in_a_string`  
Validates presence of specified elements within a string.