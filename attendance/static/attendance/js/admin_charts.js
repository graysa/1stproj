let charts = [];

function getDaysAgo(days) {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().split('T')[0];
}

function today() {
  return new Date().toISOString().split('T')[0];
}

async function loadAdminCharts(fromDate, toDate) {
  charts.forEach(c => c.destroy());
  charts = [];
  document.getElementById('group-charts').innerHTML = '';

  const res = await fetch(`${ADMIN_DATA_URL}?from=${fromDate}&to=${toDate}`);
  const data = await res.json();

  data.groups.forEach(group => {
    const section = document.createElement('div');
    section.className = 'chart-section';
    const safeId = 'chart-' + group.name.replace(/\W/g, '-');
    section.innerHTML = `
      <h3 class="chart-title">
        ${group.name}
        <span class="rate-badge">${group.overall_rate}%</span>
      </h3>
      <canvas id="${safeId}"></canvas>
    `;
    document.getElementById('group-charts').appendChild(section);

    charts.push(new Chart(document.getElementById(safeId), {
      type: 'bar',
      data: {
        labels: group.weekly.labels,
        datasets: [{
          label: 'Present',
          data: group.weekly.totals,
          backgroundColor: '#007AFF',
          borderRadius: 4,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
      }
    }));
  });
}

loadAdminCharts(getDaysAgo(91), today());

document.querySelectorAll('.preset-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    if (btn.dataset.custom) {
      document.getElementById('custom-range').classList.toggle('hidden');
    } else {
      document.getElementById('custom-range').classList.add('hidden');
      loadAdminCharts(getDaysAgo(parseInt(btn.dataset.days)), today());
    }
  });
});

document.getElementById('apply-range').addEventListener('click', () => {
  const from = document.getElementById('from-date').value;
  const to = document.getElementById('to-date').value;
  if (from && to) loadAdminCharts(from, to);
});
