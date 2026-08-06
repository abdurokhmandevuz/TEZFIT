// Initialize Telegram WebApp SDK
const tg = window.Telegram ? window.Telegram.WebApp : null;
if (tg) {
  tg.ready();
  tg.expand();
}

let initData = tg ? tg.initData : '';
let tgUser = (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) ? tg.initDataUnsafe.user : null;

let currentSlide = 0;
let currentSelectedFile = null;
let currentParsedItems = [];
let currentTotalMealData = null;

let calorieChart = null;
let trendsChart = null;
let currentTimeframe = 'daily';
let currentDietTab = 'all';
let selectedDietId = null;
let currentUserData = null;

function getTimeGreeting() {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 12) return 'Xayrli tong ☀️';
  if (hour >= 12 && hour < 18) return 'Xayrli kun 🌤️';
  return 'Xayrli kech 🌙';
}

const DIET_PLANS = [
  {
    id: 'mediterranean',
    title: "O'rta Yer Dengizi Parhezi",
    description: "Ushbu rejim tabiiy va to'liq mahsulotlarga yo'naltirilgan bo'lib, yangi sabzavotlar, sifatli zaytun yog'i, yog'siz baliq, yong'oqlar va foydali don mahsulotlarini o'z ichiga oladi.",
    calories: 2000,
    protein: 120,
    carbs: 200,
    fat: 70,
    goal: "Yurak Salomatligi, Vaznni Saqlash",
    image: 'assets/diet_mediterranean.jpg',
    isMyDiet: false
  },
  {
    id: 'lowcarb',
    title: "Past Uglevodli Yog' Erituvchi",
    description: "Tana yog' almashinuvini jadallashtirish uchun uglevodlarni cheklab, foydali yog'lar, avokado va oqsillarga asoslangan rejim.",
    calories: 1800,
    protein: 160,
    carbs: 100,
    fat: 80,
    goal: "Tezkor Yog' Yo'qotish, Insulinga Sezgirlik",
    image: 'assets/diet_lowcarb.jpg',
    isMyDiet: true
  },
  {
    id: 'vegan',
    title: "Vegalarning Quvvat Rejasi",
    description: "100% o'simlikka asoslangan, dukkakli ekinlar, dimlangan brokkoli, kinoa va foydali urug'lar bilan boyitilgan to'yimli diet.",
    calories: 2000,
    protein: 125,
    carbs: 300,
    fat: 55,
    goal: "Toza Energiya, Hujayraviy Yangilanish",
    image: 'assets/diet_vegan.jpg',
    isMyDiet: true
  }
];

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

  if (tabName === 'stats') {
    renderAnalysisPage();
  } else if (tabName === 'meals') {
    renderDietsPage();
  } else if (tabName === 'profile') {
    renderSettingsPage();
  }
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
    
    let fallbackName = 'Foydalanuvchi';
    let fallbackContact = 'ID: 8817446491';
    let photoUrl = '';

    if (tgUser) {
      fallbackName = `${tgUser.first_name || ''} ${tgUser.last_name || ''}`.trim() || tgUser.username || 'Foydalanuvchi';
      fallbackContact = tgUser.phone_number ? tgUser.phone_number : `ID: ${tgUser.id}`;
      photoUrl = tgUser.photo_url || '';
    }

    renderDashboard({
      user: {
        name: fallbackName,
        contact_info: fallbackContact,
        phone_number: fallbackContact,
        photo_url: photoUrl,
        daily_goal_kcal: 2000,
        streak_days: 1,
        weight_kg: 70,
        height_cm: 170,
        gender: 'Male',
        dob: '2003-05-21'
      },
      today_stats: { total_calories: 328, total_protein: 60, total_fat: 18, total_carbs: 140, remaining_calories: 1672, progress_percent: 16 },
      weekly_stats: [
        { day: 'Dush', calories: 1850 }, { day: 'Sesh', calories: 2100 },
        { day: 'Chor', calories: 1900 }, { day: 'Pay', calories: 1650 },
        { day: 'Jum', calories: 2200 }, { day: 'Shan', calories: 1950 },
        { day: 'Yak', calories: 328 }
      ],
      today_meals: [],
      badges: []
    });
  }
}

function renderDashboard(data) {
  const { user, today_stats, weekly_stats, today_meals } = data;
  currentUserData = user;

  if (user) {
    let name = user.name || 'Foydalanuvchi';
    if (tgUser && (!user.name || user.name === 'Foydalanuvchi')) {
      name = `${tgUser.first_name || ''} ${tgUser.last_name || ''}`.trim() || tgUser.username || 'Foydalanuvchi';
    }

    document.getElementById('user-name').innerText = name;
    document.getElementById('greeting-title').innerText = getTimeGreeting();

    const avatarTxt = document.getElementById('user-avatar');
    if (user.photo_url) {
      avatarTxt.innerHTML = `<img src="${user.photo_url}" style="width:100%;height:100%;object-fit:cover;border-radius:50%">`;
    } else {
      avatarTxt.innerText = name[0].toUpperCase();
    }

    renderSettingsPage();
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
  }

  renderAnalysisPage();
  renderDietsPage();
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

// ================= FIGMA SETTINGS PAGE LOGIC =================
function renderSettingsPage() {
  const user = currentUserData || {};

  let displayName = user.name || 'Foydalanuvchi';
  if (tgUser && (!user.name || user.name === 'Foydalanuvchi')) {
    displayName = `${tgUser.first_name || ''} ${tgUser.last_name || ''}`.trim() || tgUser.username || 'Foydalanuvchi';
  }

  let contactInfo = user.contact_info || user.phone_number;
  if (!contactInfo || contactInfo.includes('123456789')) {
    if (tgUser) {
      contactInfo = tgUser.phone_number ? tgUser.phone_number : `ID: ${tgUser.id}`;
    } else {
      contactInfo = 'ID: 8817446491';
    }
  }

  document.getElementById('settings-user-name').innerText = displayName;
  document.getElementById('settings-user-contact').innerText = contactInfo;

  const photoUrl = user.photo_url || (tgUser ? tgUser.photo_url : '');
  const avatarTxt = document.getElementById('settings-avatar-text');
  const avatarImg = document.getElementById('settings-avatar-img');

  if (photoUrl) {
    avatarImg.src = photoUrl;
    avatarImg.style.display = 'block';
    avatarTxt.style.display = 'none';
  } else {
    avatarTxt.innerText = displayName[0].toUpperCase();
    avatarTxt.style.display = 'block';
    avatarImg.style.display = 'none';
  }
}

// Sub-sheets
function openProfileEditSheet() {
  const user = currentUserData || {};
  let displayName = user.name || 'Foydalanuvchi';
  if (tgUser && (!user.name || user.name === 'Foydalanuvchi')) {
    displayName = `${tgUser.first_name || ''} ${tgUser.last_name || ''}`.trim() || tgUser.username || 'Foydalanuvchi';
  }
  let contactInfo = user.contact_info || user.phone_number || (tgUser ? (tgUser.phone_number || `ID: ${tgUser.id}`) : 'ID: 8817446491');

  document.getElementById('prof-input-name').value = displayName;
  document.getElementById('prof-input-contact').value = contactInfo;
  document.getElementById('prof-input-dob').value = user.dob || '2003-05-21';
  document.getElementById('prof-input-gender').value = user.gender || 'Male';
  document.getElementById('prof-input-height').value = `${user.height_cm || 170} cm`;
  document.getElementById('prof-input-weight').value = `${user.weight_kg || 70} kg`;

  const photoUrl = user.photo_url || (tgUser ? tgUser.photo_url : '');
  const editTxt = document.getElementById('edit-avatar-text');
  const editImg = document.getElementById('edit-avatar-img');

  if (photoUrl) {
    editImg.src = photoUrl;
    editImg.style.display = 'block';
    editTxt.style.display = 'none';
  } else {
    editTxt.innerText = displayName[0].toUpperCase();
    editTxt.style.display = 'block';
    editImg.style.display = 'none';
  }

  document.getElementById('profile-edit-sheet').style.display = 'block';
}

function closeProfileEditSheet() {
  document.getElementById('profile-edit-sheet').style.display = 'none';
}

async function saveProfileChanges() {
  const name = document.getElementById('prof-input-name').value;
  const contact = document.getElementById('prof-input-contact').value;
  const dob = document.getElementById('prof-input-dob').value;
  const gender = document.getElementById('prof-input-gender').value;
  const heightVal = parseFloat(document.getElementById('prof-input-height').value);
  const weightVal = parseFloat(document.getElementById('prof-input-weight').value);

  try {
    const res = await fetch('/api/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        initData: initData,
        name: name,
        phone_number: contact,
        dob: dob,
        gender: gender,
        height_cm: heightVal || undefined,
        weight_kg: weightVal || undefined
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      alert('✅ Profil ma\'lumotlari muvaffaqiyatli saqlandi!');
      closeProfileEditSheet();
      loadDashboard();
    }
  } catch (err) {
    alert('Saqlashda xatolik yuz berdi');
  }
}

function openNotificationSheet() {
  document.getElementById('notification-sheet').style.display = 'block';
}

function closeNotificationSheet() {
  document.getElementById('notification-sheet').style.display = 'none';
}

function openFavoriteSheet() {
  document.getElementById('favorite-sheet').style.display = 'block';
}

function closeFavoriteSheet() {
  document.getElementById('favorite-sheet').style.display = 'none';
}

function showMoreInfo() {
  alert('ℹ️ TezFIT AI v2.5 — Aqlli Kaloriya va Nutritsiya Hamrohingiz.\nVersiya: 2.5.0\nYaratuvchi: TezFIT Dev Team');
}

function closeWebApp() {
  if (tg) {
    tg.close();
  } else {
    alert('🔒 Web App yopilmoqda...');
  }
}

// ================= FIGMA ANALYSIS SCREEN LOGIC =================
function setTimeframe(mode) {
  currentTimeframe = mode;
  document.querySelectorAll('.tf-btn').forEach(btn => btn.classList.remove('active'));
  const activeBtn = document.getElementById(`tf-${mode}`);
  if (activeBtn) activeBtn.classList.add('active');

  renderAnalysisPage();
}

function renderAnalysisPage() {
  const canvas = document.getElementById('calorieTrendsCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (trendsChart) trendsChart.destroy();

  let labels = ['Dush', 'Sesh', 'Chor', 'Pay', 'Jum', 'Shan', 'Yak'];
  let consumedData = [120, 180, 140, 420, 310, 160, 190];
  let goalData = [250, 210, 300, 190, 260, 180, 240];

  if (currentTimeframe === 'weekly') {
    labels = ['1-Hafta', '2-Hafta', '3-Hafta', '4-Hafta'];
    consumedData = [1420, 1890, 1650, 2100];
    goalData = [2000, 2000, 2000, 2000];
  } else if (currentTimeframe === 'monthly') {
    labels = ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'Iyun'];
    consumedData = [1850, 1920, 1780, 2050, 1900, 1870];
    goalData = [2000, 2000, 2000, 2000, 2000, 2000];
  }

  trendsChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Iste\'mol qilingan',
          data: consumedData,
          borderColor: '#ff6b4a',
          borderWidth: 3,
          tension: 0.45,
          pointRadius: 0,
          fill: false
        },
        {
          label: 'Maqsadli Norma',
          data: goalData,
          borderColor: '#000000',
          borderWidth: 2.5,
          tension: 0.45,
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { enabled: true }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#1e293b', font: { family: 'Plus Jakarta Sans', weight: '700' } }
        },
        y: {
          grid: { color: 'rgba(0, 0, 0, 0.06)' },
          ticks: { color: '#475569', font: { family: 'Plus Jakarta Sans', weight: '600' } },
          border: { dash: [4, 4] }
        }
      }
    }
  });

  // Dynamic Macro percentages
  document.getElementById('fat-pct-val').innerText = '53%';
  document.getElementById('carbs-pct-val').innerText = '28%';
  document.getElementById('protein-pct-val').innerText = '19%';
}

// ================= FIGMA DIETS SCREEN LOGIC =================
function switchDietTab(mode) {
  currentDietTab = mode;
  document.querySelectorAll('.diet-tab-btn').forEach(btn => btn.classList.remove('active'));

  if (mode === 'all') {
    document.getElementById('tab-all-diets').classList.add('active');
    document.getElementById('diets-purple-banner').style.display = 'block';
  } else {
    document.getElementById('tab-my-diets').classList.add('active');
    document.getElementById('diets-purple-banner').style.display = 'none';
  }

  renderDietsPage();
}

function renderDietsPage() {
  const container = document.getElementById('diet-cards-list');
  if (!container) return;

  const filteredDiets = (currentDietTab === 'my')
    ? DIET_PLANS.filter(d => d.isMyDiet)
    : DIET_PLANS;

  container.innerHTML = filteredDiets.map(d => `
    <div class="diet-card" onclick="openDietDetailSheet('${d.id}')">
      <img src="${d.image}" alt="${d.title}" class="diet-card-img">
      <div class="diet-card-body">
        <h3 class="diet-card-title">${d.title}</h3>
        <p class="diet-card-subtext">${d.calories.toLocaleString()} kcal &nbsp;|&nbsp; Oqsil: ${d.protein}g &nbsp;|&nbsp; Uglevod: ${d.carbs}g &nbsp;|&nbsp; Yog': ${d.fat}g</p>
      </div>
    </div>
  `).join('');
}

function openDietDetailSheet(dietId) {
  selectedDietId = dietId;
  const diet = DIET_PLANS.find(d => d.id === dietId);
  if (!diet) return;

  document.getElementById('diet-detail-img').src = diet.image;
  document.getElementById('diet-detail-title').innerText = diet.title;
  document.getElementById('diet-detail-desc').innerText = diet.description;
  document.getElementById('diet-detail-cal').innerText = `${diet.calories.toLocaleString()} kcal`;

  const proteinPct = Math.min(100, Math.round((diet.protein / 120) * 100));
  const carbsPct = Math.min(100, Math.round((diet.carbs / 200) * 100));
  const fatPct = Math.min(100, Math.round((diet.fat / 65) * 100));

  document.getElementById('diet-protein-bar').style.width = `${proteinPct}%`;
  document.getElementById('diet-protein-pct').innerText = `${proteinPct}%`;

  document.getElementById('diet-carbs-bar').style.width = `${carbsPct}%`;
  document.getElementById('diet-carbs-pct').innerText = `${carbsPct}%`;

  document.getElementById('diet-fat-bar').style.width = `${fatPct}%`;
  document.getElementById('diet-fat-pct').innerText = `${fatPct}%`;

  document.getElementById('diet-detail-goal').innerText = diet.goal;

  document.getElementById('diet-detail-sheet').style.display = 'block';
}

function closeDietDetailSheet() {
  document.getElementById('diet-detail-sheet').style.display = 'none';
}

function toggleDietMenuOptions() {
  alert('⚙️ Diet rejim parametrlari');
}

function addSelectedDietToUser() {
  if (!selectedDietId) return;
  const diet = DIET_PLANS.find(d => d.id === selectedDietId);
  if (diet) {
    diet.isMyDiet = true;
    alert(`✅ "${diet.title}" diyetangizga biriktirildi!`);
    closeDietDetailSheet();
    switchDietTab('my');
  }
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

// Render Result Sheet
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
        <p>${Math.round(item.calories)} kcal &nbsp;|&nbsp; Oqsil: ${item.protein_g}g &nbsp;|&nbsp; Uglevod: ${item.carbs_g}g &nbsp;|&nbsp; Yog': ${item.fat_g}g</p>
      </div>
    `).join('');
  } else {
    itemsContainer.innerHTML = `
      <div class="item-breakdown-card">
        <h4>Taom</h4>
        <p>${totalCal} kcal &nbsp;|&nbsp; Oqsil: ${totalProtein}g &nbsp;|&nbsp; Uglevod: ${totalCarbs}g &nbsp;|&nbsp; Yog': ${totalFat}g</p>
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
