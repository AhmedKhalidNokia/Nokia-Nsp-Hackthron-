from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess, datetime, json, urllib.parse, os, threading, time

# --- CONFIGURATION ---
SERVERS = [
    {"ip": "100.124.168.21",  "name": "Cluster Node 1"},
    {"ip": "100.124.169.165", "name": "NSP Deployer"},
]
# File Paths
LOGO_PATH = "/root/disk_web/Nokia-Logo-removebg-preview.png"
ICON_PATH = "/root/disk_web/nokiaico.png"
BACKUP_DIR = "/root/disk_web/backups"

if not os.path.exists(BACKUP_DIR): os.makedirs(BACKUP_DIR)

SCHEDULES = {}

def scheduler_worker():
    while True:
        now = time.time()
        for (ip, path), info in list(SCHEDULES.items()):
            if now - info['last_run'] >= (info['interval_hrs'] * 3600):
                try:
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
                    local_path = os.path.join(BACKUP_DIR, f"{ip}_{os.path.basename(path)}_{ts}.log")
                    subprocess.run(f"ssh root@{ip} 'cat \"{path}\"' > {local_path}", shell=True)
                    subprocess.run(f"ssh root@{ip} 'true > \"{path}\"'", shell=True)
                    SCHEDULES[(ip, path)]['last_run'] = now
                except: pass
        time.sleep(60)

threading.Thread(target=scheduler_worker, daemon=True).start()

class DiskMonitorHandler(BaseHTTPRequestHandler):
    def get_disk_data(self):
        results = {}
        for server in SERVERS:
            cmd = f"ssh -o ConnectTimeout=3 root@{server['ip']} 'df -h -x tmpfs -x devtmpfs'"
            try:
                output = subprocess.check_output(cmd, shell=True).decode()
                lines = output.strip().split('\n')[1:]
                parsed = []
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 6:
                        try: p_val = int(parts[4].replace('%', ''))
                        except: p_val = 0
                        parsed.append({'mount': parts[5], 'size': parts[1], 'used': parts[2], 'p_str': parts[4], 'p_val': p_val})
                results[server['ip']] = sorted(parsed, key=lambda x: x['p_val'], reverse=True)
            except: results[server['ip']] = "error"
        return results

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = json.loads(self.rfile.read(content_length).decode())
        if self.path == '/add-cluster':
            SERVERS.append({"ip": post_data['ip'], "name": post_data['name']})
            self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
        elif self.path == '/set-schedule':
            ip, path, hrs = post_data['ip'], post_data['path'], float(post_data['hours'])
            if hrs > 0: SCHEDULES[(ip, path)] = {"interval_hrs": hrs, "last_run": time.time()}
            else: SCHEDULES.pop((ip, path), None)
            self.send_response(200); self.end_headers(); self.wfile.write(b"OK")

    def do_GET(self):
        # Serve the Header Logo
        if self.path == '/logo':
            if os.path.exists(LOGO_PATH):
                self.send_response(200); self.send_header('Content-type', 'image/png'); self.end_headers()
                with open(LOGO_PATH, 'rb') as f: self.wfile.write(f.read())
                return

        # NEW: Serve the Favicon Icon
        if self.path == '/favicon.ico' or self.path == '/nokiaico.png':
            if os.path.exists(ICON_PATH):
                self.send_response(200); self.send_header('Content-type', 'image/png'); self.end_headers()
                with open(ICON_PATH, 'rb') as f: self.wfile.write(f.read())
                return

        if self.path == '/data':
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps({"timestamp": datetime.datetime.now().strftime("%H:%M:%S"), "servers": self.get_disk_data()}).encode())
            return

        if self.path.startswith('/download'):
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            ip, path = params.get('ip', [''])[0], params.get('path', [''])[0]
            try:
                content = subprocess.check_output(f"ssh root@{ip} 'cat \"{path}\"'", shell=True)
                self.send_response(200); self.send_header('Content-type', 'application/octet-stream')
                self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(path)}"'); self.end_headers()
                self.wfile.write(content)
            except: self.send_error(404); return

        if self.path.startswith('/ls-mount'):
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            ip, path = params.get('ip', [''])[0], params.get('path', [''])[0]
            cmd = f"ssh root@{ip} \"find '{path}' -maxdepth 2 -type f -exec du -h {{}} + 2>/dev/null | sort -hr | head -n 100\""
            files = []
            try:
                output = subprocess.check_output(cmd, shell=True).decode()
                for line in output.strip().split('\n'):
                    if '\t' in line:
                        size, fpath = line.split('\t')
                        files.append({"size": size, "path": fpath})
            except: pass
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers(); self.wfile.write(json.dumps({"files": files}).encode()); return

        if self.path.startswith('/scan-logs'):
            ip = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('ip', [''])[0]
            scan_cmd = f"ssh root@{ip} \"find /var/log /opt/nsp /root -maxdepth 5 -name '*.log*' -type f -exec du -h {{}} + 2>/dev/null | sort -hr\""
            log_data = []
            try:
                output = subprocess.check_output(scan_cmd, shell=True).decode()
                for line in output.strip().split('\n'):
                    if '\t' in line:
                        size, fpath = line.split('\t')
                        log_data.append({"size": size, "path": fpath})
            except: pass
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers(); self.wfile.write(json.dumps({"files": log_data}).encode()); return

        self.send_response(200); self.send_header('Content-type', 'text/html; charset=utf-8'); self.end_headers()
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Nokia NSP Global Monitor</title>
            <link rel="icon" type="image/png" href="/nokiaico.png">
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; background: #eaeff2; padding: 20px; }}
                .card {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 25px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
                .scroll-box {{ max-height: 400px; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px; margin-top: 10px; background: #fff; }}
                table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
                th {{ position: sticky; top: 0; background: #f1f4f9; padding: 10px; text-align: left; border-bottom: 2px solid #124191; font-size: 0.8em; z-index: 5; }}
                td {{ padding: 8px; border-bottom: 1px solid #eee; font-size: 0.85em; vertical-align: top; word-break: break-all; }}
                .btn {{ border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 0.75em; }}
                .btn-primary {{ background: #124191; color: white; }}
                .btn-outline {{ background: white; border: 1px solid #124191; color: #124191; }}
                .bar-container {{ width: 100%; background: #eee; height: 10px; border-radius: 5px; overflow: hidden; }}
                .bar-fill {{ height: 100%; transition: 0.8s; }}
                .search-box {{ width: 100%; padding: 8px; margin-bottom: 10px; border: 2px solid #124191; border-radius: 6px; box-sizing: border-box; }}
                .total-usage-container {{ background: #124191; color:white; padding:25px; border-radius:12px; margin-bottom:20px; position: relative; }}
                .nokia-logo-img {{ height: 50px; width: auto; margin-bottom: 10px; filter: brightness(0) invert(1); display: block; }}
                .node-header-stats {{ display: flex; align-items: center; gap: 15px; margin-top: 5px; }}
                .node-mini-bar {{ width: 150px; background: #ddd; height: 8px; border-radius: 4px; overflow: hidden; }}
                .footer-admin {{ background: #f8f9fa; padding: 20px; border-radius: 12px; border: 2px dashed #124191; margin-top: 40px; text-align: center; }}
                input {{ padding: 8px; border: 1px solid #ccc; border-radius: 4px; }}
            </style>
            <script>
                async function addCluster() {{
                    const name = document.getElementById('new-name').value;
                    const ip = document.getElementById('new-ip').value;
                    if(!name || !ip) return alert("Please enter both Name and IP");
                    await fetch('/add-cluster', {{ method: 'POST', body: JSON.stringify({{name, ip}}) }});
                    location.reload();
                }}
                function filterTable(inputId, tableBodyId) {{
                    const input = document.getElementById(inputId).value.toLowerCase();
                    const rows = document.getElementById(tableBodyId).getElementsByTagName('tr');
                    for (let row of rows) {{
                        row.style.display = row.innerText.toLowerCase().includes(input) ? '' : 'none';
                    }}
                }}
                async function updateDisk() {{
                    const res = await fetch('/data');
                    const data = await res.json();
                    document.getElementById('ts').innerText = data.timestamp;
                    let grandTotalP = 0, count = 0;
                    for (const [ip, parts] of Object.entries(data.servers)) {{
                        const sId = ip.replace(/\./g, '-');
                        if (parts === "error") continue;
                        let rows = "";
                        let nodeTotalP = 0, nodeCount = 0;
                        parts.forEach((p) => {{
                            grandTotalP += p.p_val; count++;
                            nodeTotalP += p.p_val; nodeCount++;
                            const color = p.p_val >= 90 ? '#d32f2f' : (p.p_val >= 75 ? '#ffa000' : '#388e3c');
                            const mId = btoa(p.mount).replace(/=/g, '').substring(0,10);
                            rows += `<tr>
                                <td style="width:50%;"><button class="btn btn-outline" style="padding:2px 5px; margin-right:5px;" onclick="lsMount('${{ip}}', '${{p.mount}}', '${{sId}}-${{mId}}')">📁 Scan</button><b>${{p.mount}}</b><div id="ls-${{sId}}-${{mId}}" style="display:none; padding:10px; background:#f9f9f9; border:1px solid #ddd; margin-top:5px;"></div></td>
                                <td style="width:15%;">${{p.size}}<br><small>${{p.used}} used</small></td>
                                <td style="width:35%;"><div class="bar-container"><div class="bar-fill" style="width:${{p.p_val}}%; background:${{color}};"></div></div><small>${{p.p_str}} Full</small></td>
                            </tr>`;
                        }});
                        if(nodeCount > 0) {{
                            const nodeAvg = Math.round(nodeTotalP / nodeCount);
                            document.getElementById('node-bar-'+sId).style.width = nodeAvg + "%";
                            document.getElementById('node-text-'+sId).innerText = nodeAvg + "% Load";
                            document.getElementById('node-bar-'+sId).style.background = nodeAvg >= 80 ? '#d32f2f' : '#124191';
                        }}
                        document.getElementById('body-'+sId).innerHTML = rows;
                    }}
                    if(count > 0) {{
                        const avg = Math.round(grandTotalP / count);
                        document.getElementById('global-bar').style.width = avg + "%";
                        document.getElementById('global-text').innerText = avg + "%";
                    }}
                }}
                async function lsMount(ip, path, divId) {{
                    const target = document.getElementById('ls-'+divId);
                    if(target.style.display === 'block') {{ target.style.display = 'none'; return; }}
                    target.style.display = 'block'; target.innerHTML = "Listing files...";
                    const res = await fetch(`/ls-mount?ip=${{ip}}&path=${{path}}`);
                    const data = await res.json();
                    let h = `<input type="text" placeholder="Search files..." class="search-box" onkeyup="filterTable('search-ls-${{divId}}', 'ls-body-${{divId}}')" id="search-ls-${{divId}}">`;
                    h += `<table><tbody id="ls-body-${{divId}}">`;
                    data.files.forEach(f => {{
                        h += `<tr><td>${{f.size}}</td><td style="font-size:0.8em;">${{f.path}}</td><td><a href="/download?ip=${{ip}}&path=${{f.path}}" class="btn btn-outline">DL</a></td></tr>`;
                    }});
                    target.innerHTML = h + "</tbody></table>";
                }}
                async function scanLogs(ip) {{
                    const sId = ip.replace(/\./g, '-');
                    const box = document.getElementById('logs-'+sId);
                    box.style.display = 'block'; box.innerHTML = "Scanning Logs...";
                    const res = await fetch('/scan-logs?ip=' + ip);
                    const data = await res.json();
                    let html = `<input type="text" placeholder="Filter logs..." class="search-box" id="search-log-${{sId}}" onkeyup="filterTable('search-log-${{sId}}', 'log-body-${{sId}}')">`;
                    html += `<div class="scroll-box"><table><thead><tr><th>Size</th><th>Path</th><th>Auto-Clear (Hrs)</th><th>Action</th></tr></thead><tbody id="log-body-${{sId}}">`;
                    data.files.forEach(f => {{
                        const fId = btoa(f.path).replace(/=/g,'');
                        html += `<tr><td>${{f.size}}</td><td style="font-family:monospace; font-size:0.75em;">${{f.path}}</td>
                        <td><input type="number" id="hr-${{fId}}" style="width:40px;" placeholder="0"> <button class="btn btn-outline" onclick="saveSched('${{ip}}','${{f.path}}','${{fId}}',this)">Set</button></td>
                        <td><a href="/download?ip=${{ip}}&path=${{f.path}}" class="btn btn-outline">DL</a></td></tr>`;
                    }});
                    box.innerHTML = html + "</tbody></table></div>";
                }}
                async function saveSched(ip, path, fId, btn) {{
                    const hrs = document.getElementById('hr-'+fId).value;
                    await fetch('/set-schedule', {{ method: 'POST', body: JSON.stringify({{ip, path, hours: hrs}}) }});
                    btn.innerText = "Active"; btn.classList.add('btn-primary');
                }}
                window.onload = updateDisk; setInterval(updateDisk, 30000);
            </script>
        </head>
        <body>
            <div class="total-usage-container">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <img src="/logo" class="nokia-logo-img" alt="Nokia">
                        <h1 style="margin:0; font-weight:300;">NSP Maintenance & Log Archiver</h1>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:1.5em; font-weight:bold;" id="ts">--:--:--</div>
                        <small>Global Utilization: <span id="global-text">0%</span></small>
                    </div>
                </div>
                <div class="bar-container" style="background:rgba(255,255,255,0.2); height:15px; margin-top:15px;">
                    <div id="global-bar" class="bar-fill" style="width:0%; background:white;"></div>
                </div>
            </div>
        """
        for s in SERVERS:
            safe_id = s['ip'].replace('.', '-')
            html += f"""
            <div class='card'>
                <div style="display:flex; justify-content:space-between; align-items:flex-start; border-bottom:2px solid #eee; padding-bottom:10px; margin-bottom:10px;">
                    <div>
                        <h2 style="margin:0; color:#124191;">{s['name']}</h2>
                        <code>{s['ip']}</code>
                        <div class="node-header-stats">
                            <div class="node-mini-bar"><div id="node-bar-{safe_id}" style="height:100%; width:0%; transition:1s;"></div></div>
                            <small id="node-text-{safe_id}" style="font-weight:bold;">0% Load</small>
                        </div>
                    </div>
                    <button class="btn btn-primary" onclick="scanLogs('{s['ip']}')">Analyze & Schedule Logs</button>
                </div>
                <input type="text" placeholder="Search mounts..." class="search-box" id="search-mnt-{safe_id}" onkeyup="filterTable('search-mnt-{safe_id}', 'body-{safe_id}')">
                <div class="scroll-box">
                    <table>
                        <thead><tr><th>Mount Point</th><th>Disk Info</th><th>Usage</th></tr></thead>
                        <tbody id="body-{safe_id}"></tbody>
                    </table>
                </div>
                <div id="logs-{safe_id}" style="display:none; margin-top:20px; border-top:1px solid #ccc; padding-top:15px;"></div>
            </div>"""

        html += f"""
            <div class="footer-admin">
                <h3 style="margin-top:0; color:#124191;">Cluster Administration</h3>
                <input type="text" id="new-name" placeholder="Server Name">
                <input type="text" id="new-ip" placeholder="IP Address">
                <button class="btn btn-primary" onclick="addCluster()">+ Register New Node</button>
            </div>
        </body></html>
        """
        self.wfile.write(html.encode('utf-8'))

HTTPServer(('0.0.0.0', 8080), DiskMonitorHandler).serve_forever()