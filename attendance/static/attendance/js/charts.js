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

function updateSummary(data) {
  const summary = document.getElementById('analytics-summary');
  if (!summary) return;

  const meetingCount = data.weekly.labels.length;
  document.getElementById('sum-meetings').textContent = meetingCount;

  const rates = data.member_rates.map(m => m.rate);
  const avgRate = rates.length
    ? Math.round(rates.reduce((a, b) => a + b, 0) / rates.length)
    : 0;
  document.getElementById('sum-rate').textContent = avgRate + '%';

  const best = data.member_rates.reduce((a, b) => (b.rate > a.rate ? b : a), { name: '—', rate: 0 });
  const firstName = best.name.split(' ')[0];
  document.getElementById('sum-best').textContent = firstName;

  summary.classList.add('loaded');
}

async function loadCharts(fromDate, toDate) {
  const res = await fetch(`${DATA_URL}?from=${fromDate}&to=${toDate}`);
  const data = await res.json();

  updateSummary(data);

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
