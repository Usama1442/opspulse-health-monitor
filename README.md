# opspulse-health-monitor
Built a Python/Flask monitoring service that reports CPU, memory and disk health on a live dashboard. It exposes /health and /ready probe endpoints for load balancers and Kubernetes, plus a Prometheus-format /metrics endpoint. 
