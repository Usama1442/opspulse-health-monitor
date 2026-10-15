
resource "aws_instance" "opspulse" {
  ami                         = "ami-0fa5967347d08d2df"
  instance_type               = "t3.micro"
  vpc_security_group_ids      = [aws_security_group.opspulse_sg.id]
  associate_public_ip_address = true

  user_data = <<-EOF
    #!/bin/bash
    set -eux

    export DEBIAN_FRONTEND=noninteractive

    apt-get update
    apt-get install -y python3 python3-venv python3-pip git nginx

    cd /opt
    git clone https://github.com/Usama1442/opspulse-health-monitor.git opspulse

    cd /opt/opspulse
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt

    cat > /etc/systemd/system/opspulse.service <<'SERVICE'
    [Unit]
    Description=OpsPulse Health Monitor
    After=network-online.target
    Wants=network-online.target

    [Service]
    WorkingDirectory=/opt/opspulse
    Environment=HOST=127.0.0.1
    Environment=PORT=5000
    Environment=APP_ENV=production
    ExecStart=/opt/opspulse/venv/bin/gunicorn -w 2 -b 127.0.0.1:5000 app:app
    Restart=always
    RestartSec=5

    [Install]
    WantedBy=multi-user.target
    SERVICE

    cat > /etc/nginx/sites-available/opspulse <<'NGINX'
    server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;

        location / {
            proxy_pass http://127.0.0.1:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    NGINX

    rm -f /etc/nginx/sites-enabled/default
    ln -s /etc/nginx/sites-available/opspulse /etc/nginx/sites-enabled/opspulse

    nginx -t
    systemctl daemon-reload
    systemctl enable --now opspulse
    systemctl enable --now nginx
    systemctl restart nginx
  EOF

  tags = {
    Name = "OpsPulse-Health-Monitor"
  }
}

