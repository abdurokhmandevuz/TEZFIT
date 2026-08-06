// Initialize Telegram WebApp SDK
const tg = window.Telegram ? window.Telegram.WebApp : null;
if (tg) {
  tg.ready();
  tg.expand();
}

let initData = tg ? tg.initData : '';
let currentSlide = 0;
let selectedFile = null;
let currentScanResult = null;
let calorieChart = null;
let weeklyChart = null;

// Check onboarding on startup
document.addEventListener('DOMContentLoaded', () => {
  const onboarded = localStorage.getItem('tezfit_onboarded_v2');
  if (!onboarded) {
    showSplashThenSlides();
  } else {
    hideOnboarding();
    loadDashboard();
  }
});

function showSplashThenSlides() {
  document.getElementById('onboarding-flow').style.display = 'flex';
  setTimeout(() => {
    nextSlide(1);
  }, 2200);
}

function nextSlide(slideNum) {
  currentSlide = slideNum;
  document.querySelectorAll('.onboard-slide').forEach(s => s.classList.remove('active'));
  const target = document.getElementById(`slide-${slideNum}`);
  if (target) {
    target.classList.add('active');
  }
}

function finishOnboarding() {
  localStorage.setItem('tezfit_onboarded_v2', 'true');
  hideOnboarding();
  loadDashboard();
}

function hideOnboarding() {
  const wrapper = document.getElementById('onboarding-flow');
  if (wrapper) wrapper.style.display = 'none';
  const mainApp = document.getElementById('app-main');
  if (mainApp) mainApp.style.display = 'flex';
}

// Navigation Tabs
function switchTab(tabName) {
  document.querySelectorAll('.tab-page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.dock-item').forEach(n => n.classList.remove('active'));

  const targetPage = document.getElementById(`page-${tabName}`);
  const targetNav = document.getElementById(`nav-${tabName}`);
  if (targetPage) targetPage.classList.add('active');
  if (targetNav) targetNav.classList.add('active');
}

// Load Dashboard Data
async function loadDashboard() {
  try {
    const res = await fetch(`/api/dashboard?initData=${encodeURIComponent(initData)}`);
    if (!res.ok) throw new Error('Dashboard xatosi');
    const data = await res.json();
    renderDashboard(data);
  } catch (err) {
    console.warn('Backend ga ulanishda ogohlantirish:', err);
    // Demo fallback rendering
    renderDashboard({
      user: { name: 'Foydalanuvchi', daily_goal_kcal: 2000, streak_days: 1 },
      today_stats: { total_calories: 328, total_protein: 60, total_fat: 18, total_carbs: 140, remaining_calories: 1672, progress_percent: 16 },
      weekly_stats: [
        { day: 'Du', calories: 1850 }, { day: 'Se', calories: 2100 },
        { day: 'Ch', calories: 1900 }, { day: 'Pa', calories: 1650 },
        { day: 'Ju', calories: 2200 }, { day: 'Sh', calories: 1950 },
        { day: 'Ya', calories: 328 }
      ],
      today_meals: [],
      badges: []
    });
  }
}

function renderDashboard(data) {
  const { user, today_stats, weekly_stats, today_meals } = data;

  if (user) {
    document.getElementById('user-name').innerText = user.name || 'Foydalanuvchi';
    document.getElementById('user-avatar').innerText = (user.name || 'T')[0].toUpperCase();
    document.getElementById('prof-name').innerText = user.name || 'Foydalanuvchi';
    document.getElementById('prof-avatar').innerText = (user.name || 'T')[0].toUpperCase();
    document.getElementById('prof-goal').innerText = `${user.daily_goal_kcal || 2000} kcal`;
    document.getElementById('prof-streak').innerText = `🔥 ${user.streak_days || 0} kun`;
  }

  if (today_stats) {
    const consumed = Math.round(today_stats.total_calories || 0);
    const goal = Math.round(user ? user.daily_goal_kcal : 2000);
    const remaining = Math.max(0, goal - consumed);

    document.getElementById('remaining-cal').innerText = remaining;

    const carbsVal = Math.round(today_stats.total_carbs || 0);
    const proteinVal = Math.round(today_stats.total_protein || 0);

    const carbsGoal = 200;
    const proteinGoal = 120;

    document.getElementById('carbs-consumed').innerText = `${carbsVal}g`;
    document.getElementById('carbs-goal').innerText = `${carbsGoal}g`;
    document.getElementById('carbs-bar-fill').style.width = `${Math.min(100, (carbsVal / carbsGoal) * 100)}%`;

    document.getElementById('protein-consumed').innerText = `${proteinVal}g`;
    document.getElementById('protein-goal').innerText = `${proteinGoal}g`;
    document.getElementById('protein-bar-fill').style.width = `${Math.min(100, (proteinVal / proteinGoal) * 100)}%`;

    initCalorieRing(consumed, goal);
  }

  if (today_meals && today_meals.length > 0) {
    const listEl = document.getElementById('meals-list');
    listEl.innerHTML = today_meals.map(m => `
      <div class="meal-item-row" style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.05)">
        <div>
          <strong>${m.food_name}</strong> (${m.weight_g}g)
          <div style="font-size:12px; color:#94a3b8">⏰ ${m.time}</div>
        </div>
        <div style="color:#ff6b4a; font-weight:700">🔥 ${Math.round(m.calories)} kcal</div>
      </div>
    `).join('');
  }

  if (weekly_stats) {
    initWeeklyChart(weekly_stats);
  }
}

function initCalorieRing(consumed, goal) {
  const ctx = document.getElementById('calorieRingCanvas').getContext('2d');
  if (calorieChart) calorieChart.destroy();

  const remaining = Math.max(0, goal - consumed);
  calorieChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [consumed, remaining],
        backgroundColor: ['#000000', 'rgba(0, 0, 0, 0.12)'],
        borderWidth: 0,
        borderRadius: 20
      }]
    },
    options: {
      rotation: -90,
      circumference: 180,
      cutout: '80%',
      responsive: true,
      maintainAspectRatio: false,
      plugins: { tooltip: { enabled: false } }
    }
  });
}

function initWeeklyChart(weeklyStats) {
  const ctx = document.getElementById('weeklyChart').getContext('2d');
  if (weeklyChart) weeklyChart.destroy();

  const labels = weeklyStats.map(w => w.day);
  const dataVals = weeklyStats.map(w => w.calories);

  weeklyChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        data: dataVals,
        backgroundColor: '#ff6b4a',
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
      }
    }
  });
}

// Scanner Functions
function toggleScanMode(mode) {
  document.getElementById('btn-mode-photo').classList.toggle('active', mode === 'photo');
  document.getElementById('btn-mode-text').classList.toggle('active', mode === 'text');
  document.getElementById('box-photo').style.display = mode === 'photo' ? 'block' : 'none';
  document.getElementById('box-text').style.display = mode === 'text' ? 'block' : 'none';
}

function onFileSelected(event) {
  const file = event.target.files[0];
  if (!file) return;
  selectedFile = file;

  const reader = new FileReader();
  reader.onload = function(e) {
    document.getElementById('image-preview').src = e.target.result;
    document.getElementById('image-preview-container').style.display = 'block';
    document.getElementById('btn-submit-photo').style.display = 'block';
  };
  reader.readAsDataURL(file);
}

async function submitPhotoScan() {
  if (!selectedFile) return;
  document.getElementById('scan-loading').style.display = 'flex';

  const formData = new FormData();
  formData.append('initData', initData);
  formData.append('file', selectedFile);

  try {
    const res = await fetch('/api/scan-photo', { method: 'POST', body: formData });
    const data = await res.json();
    document.getElementById('scan-loading').style.display = 'none';

    if (data.status === 'success' && data.data && data.data.items && data.data.items.length > 0) {
      showResultModal(data.data.items[0]);
    } else {
      alert('AI ovqatni aniqlay olmadi. Iltimos boshqa rasm yuklang.');
    }
  } catch (err) {
    document.getElementById('scan-loading').style.display = 'none';
    alert('Skan qilishda xatolik yuz berdi');
  }
}

async function submitTextScan() {
  const textVal = document.getElementById('text-food-input').value.trim();
  if (!textVal) return;
  document.getElementById('scan-loading').style.display = 'flex';

  try {
    const res = await fetch('/api/scan-text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ initData: initData, text: textVal })
    });
    const data = await res.json();
    document.getElementById('scan-loading').style.display = 'none';

    if (data.status === 'success' && data.data && data.data.items && data.data.items.length > 0) {
      showResultModal(data.data.items[0]);
    } else {
      alert('Taom tahlil qilinmadi.');
    }
  } catch (err) {
    document.getElementById('scan-loading').style.display = 'none';
    alert('Matnli tahlilda xatolik');
  }
}

function showResultModal(item) {
  currentScanResult = item;
  document.getElementById('result-food-name').innerText = item.name || 'Taom';
  document.getElementById('result-calories').innerText = `🔥 ${Math.round(item.calories || 0)} kcal`;
  document.getElementById('result-weight').innerText = `⚖️ ${item.weight_g || 100}g`;
  document.getElementById('result-macros').innerText = `🥩 Oqsil: ${item.protein_g}g | 🧈 Yog': ${item.fat_g}g | 🍚 Uglevod: ${item.carbs_g}g`;
  document.getElementById('result-modal').style.display = 'flex';
}

function closeResultModal() {
  document.getElementById('result-modal').style.display = 'none';
}

async function confirmSaveMeal() {
  if (!currentScanResult) return;
  closeResultModal();

  try {
    const res = await fetch('/api/save-meal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        initData: initData,
        food_name: currentScanResult.name,
        weight_g: currentScanResult.weight_g,
        calories: currentScanResult.calories,
        protein_g: currentScanResult.protein_g,
        fat_g: currentScanResult.fat_g,
        carbs_g: currentScanResult.carbs_g
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      alert('✅ Taom muvaffaqiyatli saqlandi!');
      switchTab('home');
      loadDashboard();
    }
  } catch (err) {
    alert('Saqlashda xatolik yuz berdi');
  }
}

// Goal Edit Modal
function openGoalModal() {
  document.getElementById('goal-modal').style.display = 'flex';
}
function closeGoalModal() {
  document.getElementById('goal-modal').style.display = 'none';
}

async function submitGoalUpdate() {
  const goalVal = parseFloat(document.getElementById('input-goal-cal').value);
  const weightVal = parseFloat(document.getElementById('input-weight').value);
  closeGoalModal();

  try {
    const res = await fetch('/api/goals', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        initData: initData,
        daily_goal_kcal: goalVal || undefined,
        weight_kg: weightVal || undefined
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      loadDashboard();
    }
  } catch (err) {
    alert('Maqsadni yangilashda xatolik');
  }
}
