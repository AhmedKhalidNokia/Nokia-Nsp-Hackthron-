# Nokia NSP Hackathon - Disk Monitor & Dashboard

A comprehensive monitoring solution for Nokia NSP (Network Services Platform) infrastructure that provides real-time disk usage tracking across distributed cluster nodes with an interactive web dashboard.

## Overview

This project was developed for the Nokia NSP Hackathon and provides automated monitoring and management of disk resources across multiple Nokia network infrastructure nodes. It combines remote SSH command execution with a web-based dashboard for centralized monitoring.

## Features

- **Remote Node Management**: SSH-based connection to Nokia NSP nodes with automated service startup
- **Real-Time Disk Monitoring**: Live disk usage tracking across multiple servers
- **Web Dashboard**: Interactive HTTP-based interface for visualizing disk metrics
- **Automated Scheduling**: Background scheduler for periodic log backups and data management
- **Multi-Server Support**: Monitor multiple cluster nodes and deployer instances simultaneously
- **Persistent Data Tracking**: Automatic backup and archival of historical monitoring data

## Project Structure

```
├── Nokia.py              # SSH connector for remote Nokia node management
├── Web_Dashboard.py      # HTTP server providing web-based monitoring dashboard
└── README.md            # Project documentation
```

## Components

### Nokia.py
Main script for connecting to Nokia NSP nodes and launching the monitoring service.

**Functionality:**
- Establishes SSH connection to remote nodes
- Executes remote Python web monitor process
- Auto-launches browser dashboard
- Maintains persistent SSH transport

### Web_Dashboard.py
HTTP server that aggregates disk monitoring data from multiple cluster nodes.

**Features:**
- Serves dashboard interface on port 8080
- Queries multiple servers via SSH for disk metrics
- Scheduled backup tasks for log files
- Real-time disk usage aggregation

## Installation

### Requirements
- Python 3.x
- Paramiko (SSH client library)
- SSH access to target Nokia nodes
- Network connectivity to cluster nodes

### Setup

1. **Install Dependencies**
   ```bash
   pip install paramiko
   ```

2. **Update Configuration**
   Edit the IP addresses, credentials, and server details in both scripts:
   - Update `HOST`, `USER`, and `PASS` in `Nokia.py`
   - Update `SERVERS` list in `Web_Dashboard.py`
   - Configure `LOGO_PATH`, `ICON_PATH`, and `BACKUP_DIR` paths

3. **Ensure SSH Access**
   - Verify SSH connectivity to all target nodes
   - Ensure the user has sufficient permissions on remote systems
   - Test connection: `ssh root@<NODE_IP>`

## Usage

### Quick Start

```bash
python Nokia.py
```

This command will:
1. Connect to the specified Nokia node via SSH
2. Start the remote web monitor service
3. Automatically open your default browser to the dashboard
4. Keep the SSH transport alive

### Dashboard Access

Once running, access the dashboard at:
```
http://<NODE_IP>:8080
```

The dashboard will display:
- Live disk usage across all configured nodes
- Filesystem details (mount points, size, used space, utilization %)
- Historical monitoring data
- System status

### Stopping the Service

1. Close the terminal window running `Nokia.py`, or
2. Press `Ctrl+C` to terminate

Note: Closing the terminal will terminate the SSH transport and stop the remote service.

## Configuration

### Security Considerations
⚠️ **Important**: The credentials are hardcoded in the scripts. For production use:
- Use SSH key-based authentication instead of passwords
- Store credentials in environment variables
- Implement proper secret management
- Use configuration files with restricted permissions

### Backup Settings
Configure automatic backup behavior in `Web_Dashboard.py`:
```python
BACKUP_DIR = "/root/disk_web/backups"        # Backup storage location
```

### Port Configuration
The dashboard runs on port 8080 by default. Modify as needed in `Web_Dashboard.py`.

## Architecture

```
┌─────────────────┐
│   Local Machine │
│   (Nokia.py)    │
└────────┬────────┘
         │ SSH (Port 22)
         │
┌────────▼────────────────────────┐
│   Nokia NSP Cluster Node        │
│   (Web_Dashboard running)       │
│   - HTTP Server (Port 8080)     │
│   - Disk Monitoring Service     │
└─────────────────────────────────┘
```

## Troubleshooting

### Authentication Failed
- Verify SSH credentials are correct
- Check node IP addresses are reachable
- Ensure user account exists on remote system
- Verify firewall allows SSH connections (port 22)

### Connection Timeout
- Check network connectivity to cluster nodes
- Verify firewall rules allow outbound SSH
- Ensure target nodes are running and accessible
- Check DNS resolution if using hostnames

### Dashboard Not Loading
- Verify port 8080 is not already in use
- Check firewall allows HTTP traffic on port 8080
- Ensure `Web_Dashboard.py` started successfully on remote node
- Verify browser can reach the node IP address

### SSH Transport Errors
- Check if the transport window was closed
- Verify persistent SSH connection is maintained
- Re-run `Nokia.py` to restart the service

## Development

### Future Enhancements
- Web-based authentication and authorization
- Historical trending and analytics
- Alert thresholds and notifications
- Multi-user dashboard access
- Automated cleanup policies
- Performance metrics and reporting

## Requirements & Dependencies

- **Python 3.6+**
- **paramiko**: For SSH operations
- **Standard Library**: http.server, subprocess, threading, time, json, os, datetime, urllib

## License

Nokia NSP Hackathon Project

## Support

For issues or questions, please refer to the Nokia NSP documentation or contact your system administrator.

---

**Note**: This project is designed for the Nokia NSP Hackathon. Ensure you have proper authorization before accessing any networked infrastructure.
