// Initialize Telegram WebApp SDK
const tg = window.Telegram ? window.Telegram.WebApp : null;
if (tg) {
  tg.ready();
  tg.expand();
}

let initData = tg ? tg.initData : '';
let currentSlide = 0;
let currentSelectedFile = null;
let currentParsedItems = [];
let currentTotalMealData = null;

let calorieChart = null;
let weeklyChart = null;

// Startup check
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

  if (today_meals) {
    renderMealsList('meals-list', today_meals);
    renderMealsList('diet-page-meals-list', today_meals);
  }

  if (weekly_stats) {
    initWeeklyChart(weekly_stats);
  }
}

function renderMealsList(elementId, meals) {
  const listEl = document.getElementById(elementId);
  if (!listEl) return;
  if (!meals || meals.length === 0) {
    listEl.innerHTML = '<p class="empty-text">Bugun hali ovqat kiritilmadi</p>';
    return;
  }
  listEl.innerHTML = meals.map(m => `
    <div class="meal-item-row" style="display:flex; justify-content:space-between; padding:12px 0; border-bottom:1px solid rgba(255,255,255,0.05)">
      <div>
        <strong>${m.food_name}</strong> (${m.weight_g}g)
        <div style="font-size:12px; color:#94a3b8">⏰ ${m.time} &nbsp;|&nbsp; Oqsil: ${m.protein_g}g | Yog': ${m.fat_g}g | Uglevod: ${m.carbs_g}g</div>
      </div>
      <div style="color:#ff6b4a; font-weight:700">🔥 ${Math.round(m.calories)} kcal</div>
    </div>
  `).join('');
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

// ================= CAMERA & GALLERY CHOICE MODAL =================
function openCameraChoiceModal() {
  document.getElementById('camera-choice-modal').style.display = 'flex';
}

function closeCameraChoiceModal() {
  document.getElementById('camera-choice-modal').style.display = 'none';
}

function triggerNativeCamera() {
  closeCameraChoiceModal();
  const camInput = document.getElementById('input-camera');
  if (camInput) {
    camInput.value = '';
    camInput.click();
  }
}

function triggerNativeGallery() {
  closeCameraChoiceModal();
  const galInput = document.getElementById('input-gallery');
  if (galInput) {
    galInput.value = '';
    galInput.click();
  }
}

function handleFileSelected(event) {
  const file = event.target.files[0];
  if (!file) return;

  currentSelectedFile = file;

  const reader = new FileReader();
  reader.onload = function(e) {
    submitImageScanToAI(file, e.target.result);
  };
  reader.readAsDataURL(file);
}

async function submitImageScanToAI(fileOrBlob, imageSrc) {
  let loadingEl = document.getElementById('cam-loading');
  if (!loadingEl) {
    loadingEl = document.createElement('div');
    loadingEl.id = 'cam-loading';
    loadingEl.className = 'camera-loading-overlay';
    loadingEl.innerHTML = '<div class="spinner"></div><p style="margin-top:12px; font-weight:700;">🔍 AI Taomni tahlil qilmoqda...</p>';
    document.body.appendChild(loadingEl);
  }
  loadingEl.style.display = 'flex';

  const formData = new FormData();
  formData.append('initData', initData || '');
  formData.append('file', fileOrBlob, 'food_scan.jpg');

  try {
    const res = await fetch('/api/scan-photo', { method: 'POST', body: formData });
    const data = await res.json();
    loadingEl.style.display = 'none';

    if (data && data.status === 'success' && data.data && data.data.items && data.data.items.length > 0) {
      renderResultSheet(data.data, imageSrc);
    } else {
      const errMsg = (data && (data.error || data.detail || data.message)) || "AI javob bermadi yoki kalit topilmadi.";
      alert("⚠️ AI Xatoligi: " + errMsg);
    }
  } catch (err) {
    loadingEl.style.display = 'none';
    alert("⚠️ Internet yoki server bilan ulanishda xatolik yuz berdi.");
  }
}

// Render Result Sheet (Figma Screen 2)
function renderResultSheet(aiData, imageSrc) {
  currentTotalMealData = aiData;
  currentParsedItems = aiData.items || [];

  if (imageSrc) {
    document.getElementById('sheet-food-img').src = imageSrc;
  }

  const totalCal = Math.round(aiData.total_calories || aiData.calories || 0);
  const firstItem = currentParsedItems[0] || {};
  const totalProtein = Math.round(aiData.total_protein || firstItem.protein_g || 0);
  const totalCarbs = Math.round(aiData.total_carbs || firstItem.carbs_g || 0);
  const totalFat = Math.round(aiData.total_fat || firstItem.fat_g || 0);

  document.getElementById('res-cal-val').innerText = `${totalCal.toLocaleString()} kcal`;

  const proteinPct = Math.min(100, Math.round((totalProtein / 120) * 100));
  const carbsPct = Math.min(100, Math.round((totalCarbs / 200) * 100));
  const fatPct = Math.min(100, Math.round((totalFat / 65) * 100));

  document.getElementById('res-protein-fill').style.width = `${proteinPct}%`;
  document.getElementById('res-protein-pct').innerText = `${proteinPct}%`;

  document.getElementById('res-carbs-fill').style.width = `${carbsPct}%`;
  document.getElementById('res-carbs-pct').innerText = `${carbsPct}%`;

  document.getElementById('res-fat-fill').style.width = `${fatPct}%`;
  document.getElementById('res-fat-pct').innerText = `${fatPct}%`;

  const itemsContainer = document.getElementById('res-items-container');
  if (currentParsedItems && currentParsedItems.length > 0) {
    itemsContainer.innerHTML = currentParsedItems.map(item => `
      <div class="item-breakdown-card">
        <h4>${item.name || 'Taom'}</h4>
        <p>${Math.round(item.calories)} kcal &nbsp;|&nbsp; Protein: ${item.protein_g}g &nbsp;|&nbsp; Carbs: ${item.carbs_g}g &nbsp;|&nbsp; Fat: ${item.fat_g}g</p>
      </div>
    `).join('');
  } else {
    itemsContainer.innerHTML = `
      <div class="item-breakdown-card">
        <h4>Taom</h4>
        <p>${totalCal} kcal &nbsp;|&nbsp; Protein: ${totalProtein}g &nbsp;|&nbsp; Carbs: ${totalCarbs}g &nbsp;|&nbsp; Fat: ${totalFat}g</p>
      </div>
    `;
  }

  document.getElementById('result-sheet').style.display = 'block';
}

function closeResultSheet() {
  document.getElementById('result-sheet').style.display = 'none';
}

function toggleFavorite() {
  alert('❤️ Taom sevimlilarga qo\'shildi!');
}

async function saveResultMealToDiet() {
  if (!currentTotalMealData) return;
  closeResultSheet();

  const mainItem = (currentParsedItems && currentParsedItems.length > 0)
    ? currentParsedItems[0]
    : { name: 'Sog\'lom taom', weight_g: 350, calories: 620, protein_g: 28, fat_g: 22, carbs_g: 70 };

  try {
    const res = await fetch('/api/save-meal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        initData: initData,
        food_name: mainItem.name || 'Taom',
        weight_g: mainItem.weight_g || 350,
        calories: currentTotalMealData.total_calories || mainItem.calories,
        protein_g: currentTotalMealData.total_protein || mainItem.protein_g,
        fat_g: currentTotalMealData.total_fat || mainItem.fat_g,
        carbs_g: currentTotalMealData.total_carbs || mainItem.carbs_g
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      alert('✅ Taom muvaffaqiyatli Dietangizga qo\'shildi!');
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
