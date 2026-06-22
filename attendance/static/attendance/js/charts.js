let weeklyChart = null;
let memberChart = null;

function getDaysAgo(days) {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().split('T')[0];
}

function today() {
  return new Date().toISOString().split('T')[0];
}

async function loadCharts(fromDate, toDate) {
  const res = await fetch(`${DATA_URL}?from=${fromDate}&to=${toDate}`);
  const data = await res.json();

  if (weeklyChart) weeklyChart.destroy();
  if (memberChart) memberChart.destroy();

  weeklyChart = new Chart(document.getElementById('weekly-chart'), {
    type: 'line',
    data: {
      labels: data.weekly.labels,
      datasets: [{
        label: 'Total Present',
        data: data.weekly.totals,
        borderColor: '#007AFF',
        backgroundColor: 'rgba(0,122,255,0.1)',
        tension: 0.3,
        fill: true,
        pointBackgroundColor: '#007AFF',
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
    }
  });

  memberChart = new Chart(document.getElementById('member-chart'), {
    type: 'bar',
    data: {
      labels: data.member_rates.map(m => m.name),
      datasets: [{
        label: 'Attendance %',
        data: data.member_rates.map(m => m.rate),
        backgroundColor: '#34C759',
        borderRadius: 6,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { x: { beginAtZero: true, max: 100 } },
    }
  });
}

// Default: 3 months (active preset)
loadCharts(getDaysAgo(91), today());

document.querySelectorAll('.preset-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    if (btn.dataset.custom) {
      document.getElementById('custom-range').classList.toggle('hidden');
    } else {
      document.getElementById('custom-range').classList.add('hidden');
      loadCharts(getDaysAgo(parseInt(btn.dataset.days)), today());
    }
  });
});

document.getElementById('apply-range').addEventListener('click', () => {
  const from = document.getElementById('from-date').value;
  const to = document.getElementById('to-date').value;
  if (from && to) loadCharts(from, to);
});
