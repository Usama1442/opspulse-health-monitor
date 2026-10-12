// Fetches /api/status every 3 seconds and updates rings, chart and system info.
(function () {
  "use strict";

  var REFRESH_MS = 3000;
  var MAX_POINTS = 30;
  var CIRCUMFERENCE = 2 * Math.PI * 52; // matches r="52" in the ring SVG
  var cpuHistory = [];
  var memHistory = [];

  function $(id) { return document.getElementById(id); }

  function setRing(name, percent, level, detail) {
    var ring = $(name + "-ring");
    var clamped = Math.max(0, Math.min(percent, 100));
    ring.style.strokeDashoffset = String(CIRCUMFERENCE * (1 - clamped / 100));
    $(name + "-value").textContent = clamped.toFixed(0) + "%";
    $("card-" + name).classList.toggle("warn", level === "warning");
    $(name + "-detail").textContent = detail;
  }

  function toPoints(history) {
    if (history.length === 1) { history = [history[0], history[0]]; }
    var step = 300 / (MAX_POINTS - 1);
    var offset = (MAX_POINTS - history.length) * step; // draw newest on the right
    return history.map(function (value, i) {
      var x = offset + i * step;
      var y = 84 - (Math.max(0, Math.min(value, 100)) / 100) * 78;
      return x.toFixed(1) + "," + y.toFixed(1);
    }).join(" ");
  }

  function push(history, value) {
    history.push(value);
    if (history.length > MAX_POINTS) { history.shift(); }
  }

  function formatUptime(seconds) {
    var d = Math.floor(seconds / 86400);
    var h = Math.floor((seconds % 86400) / 3600);
    var m = Math.floor((seconds % 3600) / 60);
    var s = seconds % 60;
    return (d ? d + "d " : "") + h + "h " + m + "m " + s + "s";
  }

  function setStatus(kind, text) {
    var pill = $("overall");
    pill.className = "status-pill " + kind;
    $("overall-text").textContent = text;
  }

  function render(data) {
    var m = data.metrics, c = data.checks, t = data.thresholds;

    setRing("cpu", m.cpu_percent, c.cpu, "Warning above " + t.cpu + "%");
    setRing("memory", m.memory_percent, c.memory, m.memory_used_mb + " of " + m.memory_total_mb + " MB used");
    setRing("disk", m.disk_percent, c.disk, m.disk_used_gb + " of " + m.disk_total_gb + " GB used");

    push(cpuHistory, m.cpu_percent);
    push(memHistory, m.memory_percent);
    $("line-cpu").setAttribute("points", toPoints(cpuHistory));
    $("line-mem").setAttribute("points", toPoints(memHistory));

    setStatus(data.status, data.status === "healthy" ? "Healthy" : "Degraded");

    var load = data.system.load_average[0] === null
      ? "n/a"
      : data.system.load_average.map(function (n) { return n.toFixed(2); }).join(" / ");

    var rows = [
      ["Hostname", data.system.hostname],
      ["Uptime (app)", formatUptime(data.app.uptime_seconds)],
      ["Load (1/5/15 min)", load],
      ["CPU cores", data.system.cpu_cores],
      ["Operating system", data.system.os],
      ["Python", data.system.python]
    ];

    var list = $("system-info");
    list.innerHTML = "";
    rows.forEach(function (row) {
      var box = document.createElement("div");
      var dt = document.createElement("dt");
      var dd = document.createElement("dd");
      box.className = "stat";
      dt.textContent = row[0];
      dd.textContent = row[1];
      box.appendChild(dt);
      box.appendChild(dd);
      list.appendChild(box);
    });

    $("updated").textContent = "Last updated " + new Date().toLocaleTimeString() + ", showing the last " + MAX_POINTS + " readings";
  }

  function refresh() {
    fetch("/api/status")
      .then(function (response) {
        if (!response.ok) { throw new Error("HTTP " + response.status); }
        return response.json();
      })
      .then(render)
      .catch(function () { setStatus("offline", "Cannot reach server"); });
  }

  refresh();
  setInterval(refresh, REFRESH_MS);
})();
