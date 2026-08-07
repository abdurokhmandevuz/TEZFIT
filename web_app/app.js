// Initialize Telegram WebApp SDK
const tg = window.Telegram ? window.Telegram.WebApp : null;
if (tg) {
  tg.ready();
  tg.expand();
}

let initData = tg ? tg.initData : '';
let tgUser = (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) ? tg.initDataUnsafe.user : null;

// Fallback: If tg.initData is empty, encode tgUser or cached user profile so backend receives real user ID
if (!initData && tgUser) {
  initData = `user=${encodeURIComponent(JSON.stringify(tgUser))}`;
} else if (!initData) {
  const cachedProfile = localStorage.getItem('tezfit_user_profile_v2');
  if (cachedProfile) {
    try {
      const p = JSON.parse(cachedProfile);
      if (p && p.id) {
        initData = `user=${encodeURIComponent(JSON.stringify(p))}`;
      }
    } catch(e) {}
  }
}

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

// Wizard State Variables
let selectedGender = 'Male';
let selectedHeight = 170;
let selectedHeightUnit = 'cm';
let selectedWeight = 70;
let selectedWeightUnit = 'kg';
let selectedTargetWeight = 65;
let selectedTargetWeightUnit = 'kg';
let selectedActivity = 'Lightly active';
let selectedDietPref = 'No preference';
let calculatedDailyKcal = 2000;

function getTimeGreeting() {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 12) return 'Xayrli tong ☀️';
  if (hour >= 12 && hour < 18) return 'Xayrli kun 🌤️';
  return 'Xayrli kech 🌙';
}

let DIET_PLANS = [];

async function fetchDietsFromBackend() {
  try {
    const res = await fetch('/api/diets');
    if (!res.ok) throw new Error('Diets API error');
    const data = await res.json();
    if (data && data.status === 'success' && data.diets && data.diets.length > 0) {
      DIET_PLANS = data.diets;
      renderDietsPage();
    }
  } catch (err) {
    console.warn('Backend diet rejimlarini yuklashda ogohlantirish, zaxira ishlatilmoqda:', err);
    if (!DIET_PLANS || DIET_PLANS.length === 0) {
      DIET_PLANS = [
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
      renderDietsPage();
    }
  }
}

// Startup check
document.addEventListener('DOMContentLoaded', () => {
  renderDynamicCalendar();
  setupSwipeWheelPickers();
  updatePickerLabels('height');
  updatePickerLabels('weight');
  updatePickerLabels('target-weight');
  fetchDietsFromBackend();
  
  // Cache Telegram SDK user if present
  if (tgUser) {
    localStorage.setItem('tezfit_user_profile_v2', JSON.stringify({
      first_name: tgUser.first_name,
      last_name: tgUser.last_name,
      username: tgUser.username,
      id: tgUser.id,
      photo_url: tgUser.photo_url || ''
    }));
  }

  const onboarded = localStorage.getItem('tezfit_onboarded_v2');
  if (!onboarded) {
    showSplashThenSlides();
  } else {
    hideOnboarding();
    loadDashboard();
  }
});

// Dynamic Horizontal Wheel Picker Helpers (Height, Weight, Target Weight)
function updatePickerLabels(type) {
  let inputId, prevId, nextId;
  if (type === 'height') {
    inputId = 'input-height-val';
    prevId = 'height-sub-prev';
    nextId = 'height-sub-next';
  } else if (type === 'weight') {
    inputId = 'input-weight-val';
    prevId = 'weight-sub-prev';
    nextId = 'weight-sub-next';
  } else if (type === 'target-weight') {
    inputId = 'input-target-weight-val';
    prevId = 'target-weight-sub-prev';
    nextId = 'target-weight-sub-next';
  }

  const input = document.getElementById(inputId);
  if (!input) return;

  const val = parseInt(input.value) || 0;
  const prevEl = document.getElementById(prevId);
  const nextEl = document.getElementById(nextId);

  if (prevEl) prevEl.innerText = val - 1;
  if (nextEl) nextEl.innerText = val + 1;

  calculatePlanSummary();
}

function stepPicker(type, delta) {
  let inputId;
  if (type === 'height') inputId = 'input-height-val';
  else if (type === 'weight') inputId = 'input-weight-val';
  else if (type === 'target-weight') inputId = 'input-target-weight-val';

  const input = document.getElementById(inputId);
  if (!input) return;

  let val = (parseInt(input.value) || 0) + delta;
  val = Math.max(1, val);
  input.value = val;
  updatePickerLabels(type);
}

function setupSwipeWheelPickers() {
  const pickers = [
    { type: 'height', containerId: 'picker-container-height' },
    { type: 'weight', containerId: 'picker-container-weight' },
    { type: 'target-weight', containerId: 'picker-container-target-weight' }
  ];

  pickers.forEach(p => {
    const el = document.getElementById(p.containerId);
    if (!el) return;

    let startX = 0;
    let isDragging = false;
    let lastStepTime = 0;

    // Touch events
    el.addEventListener('touchstart', (e) => {
      startX = e.touches[0].clientX;
      isDragging = true;
    }, { passive: true });

    el.addEventListener('touchmove', (e) => {
      if (!isDragging) return;
      const currentX = e.touches[0].clientX;
      const diff = currentX - startX;
      const now = Date.now();

      if (Math.abs(diff) > 45 && (now - lastStepTime > 120)) {
        if (diff > 0) {
          stepPicker(p.type, -1); // Dragged right -> decrease value (e.g. 70 -> 69)
        } else {
          stepPicker(p.type, 1);  // Dragged left -> increase value (e.g. 70 -> 71)
        }
        startX = currentX;
        lastStepTime = now;
      }
    }, { passive: true });

    el.addEventListener('touchend', () => { isDragging = false; });

    // Mouse drag events for Desktop/Web
    el.addEventListener('mousedown', (e) => {
      startX = e.clientX;
      isDragging = true;
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const currentX = e.clientX;
      const diff = currentX - startX;
      const now = Date.now();

      if (Math.abs(diff) > 45 && (now - lastStepTime > 120)) {
        if (diff > 0) {
          stepPicker(p.type, -1);
        } else {
          stepPicker(p.type, 1);
        }
        startX = currentX;
        lastStepTime = now;
      }
    });

    window.addEventListener('mouseup', () => { isDragging = false; });

    // Wheel mouse scroll event
    el.addEventListener('wheel', (e) => {
      e.preventDefault();
      const now = Date.now();
      if (now - lastStepTime > 100) {
        if (e.deltaY > 0) {
          stepPicker(p.type, -1);
        } else {
          stepPicker(p.type, 1);
        }
        lastStepTime = now;
      }
    }, { passive: false });
  });
}

function renderDynamicCalendar(selectedDateStr = null) {
  const container = document.getElementById('calendar-strip');
  if (!container) return;

  const now = new Date();
  const todayStr = now.toISOString().split('T')[0];
  const activeTargetDate = selectedDateStr || todayStr;

  // Determine Monday of current week
  const dayOfWeek = now.getDay(); // 0 is Sunday
  const distanceToMonday = (dayOfWeek === 0 ? 6 : dayOfWeek - 1);
  
  const monday = new Date(now);
  monday.setDate(now.getDate() - distanceToMonday);

  const dayNames = ['Dush', 'Sesh', 'Chor', 'Pay', 'Jum', 'Shan', 'Yak'];
  let html = '';

  for (let i = 0; i < 7; i++) {
    const dayDate = new Date(monday);
    dayDate.setDate(monday.getDate() + i);

    const dateIso = dayDate.toISOString().split('T')[0];
    const dayNum = String(dayDate.getDate()).padStart(2, '0');
    const isSelected = (dateIso === activeTargetDate);

    html += `
      <div class="day-col ${isSelected ? 'active-day' : ''}" onclick="selectCalendarDate('${dateIso}')">
        <span class="d-name">${dayNames[i]}</span>
        <span class="d-num ${isSelected ? 'active-pill' : ''}">${dayNum}</span>
      </div>
    `;
  }

  container.innerHTML = html;
}

function selectCalendarDate(dateIso) {
  const now = new Date();
  const todayStr = now.toISOString().split('T')[0];

  // Block future dates for everyone
  if (dateIso > todayStr) {
    return; // Future dates are not viewable
  }
  
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  const yesterdayStr = yesterday.toISOString().split('T')[0];

  const isPremiumUser = currentUserData && (currentUserData.is_vip || currentUserData.is_premium);

  // Free User History Limitation (Only Today and 1 day ago allowed)
  if (!isPremiumUser && dateIso !== todayStr && dateIso !== yesterdayStr) {
    openPremiumModal();
    return;
  }

  renderDynamicCalendar(dateIso);
  // Reload dashboard for selected date
  loadDashboardForDate(dateIso);
}

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

// Onboarding Wizard Selection Handlers
function selectGender(genderVal) {
  selectedGender = genderVal;
  document.getElementById('gender-male').classList.remove('active');
  document.getElementById('gender-female').classList.remove('active');
  if (genderVal === 'Male') {
    document.getElementById('gender-male').classList.add('active');
  } else {
    document.getElementById('gender-female').classList.add('active');
  }
}

function toggleHeightUnit(unit) {
  selectedHeightUnit = unit;
  document.querySelectorAll('#slide-3 .unit-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
}

function toggleWeightUnit(unit) {
  selectedWeightUnit = unit;
  document.querySelectorAll('#slide-4 .unit-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
}

function toggleTargetWeightUnit(unit) {
  selectedTargetWeightUnit = unit;
  document.querySelectorAll('#slide-5 .unit-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
}

function selectActivity(actMode) {
  selectedActivity = actMode;
  document.querySelectorAll('.activity-card-item').forEach(c => c.classList.remove('active'));
  const target = document.getElementById(`act-${actMode.toLowerCase().split(' ')[0]}`);
  if (target) target.classList.add('active');
}

function selectDietPref(prefVal) {
  selectedDietPref = prefVal;
  document.querySelectorAll('.diet-circle-item').forEach(c => c.classList.remove('active'));
  const target = document.getElementById(`pref-${prefVal.toLowerCase().split(' ')[0]}`);
  if (target) target.classList.add('active');
}

// Calculate Plan Summary via 3-Step Mifflin-St Jeor Formula
function calculatePlanSummary() {
  const heightInput = parseFloat(document.getElementById('input-height-val').value) || 170;
  const weightInput = parseFloat(document.getElementById('input-weight-val').value) || 70;
  const targetWeightInput = parseFloat(document.getElementById('input-target-weight-val').value) || 65;

  selectedHeight = (selectedHeightUnit === 'ft') ? heightInput * 30.48 : heightInput;
  selectedWeight = (selectedWeightUnit === 'lbs') ? weightInput * 0.453592 : weightInput;
  selectedTargetWeight = (selectedTargetWeightUnit === 'lbs') ? targetWeightInput * 0.453592 : targetWeightInput;

  // 1-QADAM: BMR (asosiy almashinuv) — Mifflin-St Jeor formulasi
  const age = 25;
  let bmr = (10 * selectedWeight) + (6.25 * selectedHeight) - (5 * age);
  if (selectedGender === 'Female') {
    bmr -= 161;
  } else {
    bmr += 5;
  }

  // 2-QADAM: TDEE (kunlik umumiy sarf) — faollik koeffitsientiga ko'paytirish
  let mult = 1.2;
  if (selectedActivity.includes('Lightly')) mult = 1.375;
  else if (selectedActivity.includes('Moderately')) mult = 1.55;
  else if (selectedActivity.includes('Very')) mult = 1.725;
  else if (selectedActivity.includes('Athlete')) mult = 1.9;
  else if (selectedActivity.includes('Sedentary')) mult = 1.2;

  let tdee = bmr * mult;

  // 3-QADAM: Maqsadga qarab yakuniy kaloriya
  let dailyKcal = tdee;
  if (selectedTargetWeight < selectedWeight) {
    dailyKcal = tdee - 500; // Vazn kamaytirish
  } else if (selectedTargetWeight > selectedWeight) {
    dailyKcal = tdee + 400; // Vazn oshirish
  } else {
    dailyKcal = tdee;       // Vazn saqlash
  }

  // MUHIM XAVFSIZLIK QOIDASI:
  // Erkaklar: minimal 1500 kcal
  // Ayollar: minimal 1200 kcal
  // 4-QADAM: Diet turiga qarab makronutrientlarni hisoblash
  // Foiz taqsimotlari:
  // Farqi yo'q (Balanced): Protein 30%, Yog' 30%, Uglevod 40%
  // Keto: Protein 25%, Yog' 70%, Uglevod 5%
  // Vegetarian: Protein 25%, Yog' 30%, Uglevod 45%
  // Vegan: Protein 25%, Yog' 25%, Uglevod 50%
  // Paleo: Protein 30%, Yog' 40%, Uglevod 30%
  let pPct = 0.30, fPct = 0.30, cPct = 0.40;

  if (selectedDietPref.includes('Keto')) {
    pPct = 0.25; fPct = 0.70; cPct = 0.05;
  } else if (selectedDietPref.includes('Vegetarian')) {
    pPct = 0.25; fPct = 0.30; cPct = 0.45;
  } else if (selectedDietPref.includes('Vegan')) {
    pPct = 0.25; fPct = 0.25; cPct = 0.50;
  } else if (selectedDietPref.includes('Paleo')) {
    pPct = 0.30; fPct = 0.40; cPct = 0.30;
  } else {
    pPct = 0.30; fPct = 0.30; cPct = 0.40;
  }

  const proteinKcal = Math.round(calculatedDailyKcal * pPct);
  const fatKcal = Math.round(calculatedDailyKcal * fPct);
  const carbsKcal = Math.round(calculatedDailyKcal * cPct);

  // Grammga o'tkazish formulasi: 1g protein = 4 kcal, 1g fat = 9 kcal, 1g carbs = 4 kcal
  const proteinGrams = Math.round(proteinKcal / 4);
  const fatGrams = Math.round(fatKcal / 9);
  const carbsGrams = Math.round(carbsKcal / 4);

  document.getElementById('plan-kcal-val').innerHTML = `${calculatedDailyKcal.toLocaleString()} <small>kcal</small>`;
  
  // Update Tri-color Bar
  const triCarbs = document.querySelector('.tri-fill.tri-carbs');
  const triProtein = document.querySelector('.tri-fill.tri-protein');
  const triFat = document.querySelector('.tri-fill.tri-fat');

  if (triCarbs) {
    triCarbs.style.width = `${Math.round(cPct * 100)}%`;
    triCarbs.innerText = `${Math.round(cPct * 100)}%`;
  }
  if (triProtein) {
    triProtein.style.width = `${Math.round(pPct * 100)}%`;
    triProtein.innerText = `${Math.round(pPct * 100)}%`;
  }
  if (triFat) {
    triFat.style.width = `${Math.round(fPct * 100)}%`;
    triFat.innerText = `${Math.round(fPct * 100)}%`;
  }

  document.getElementById('plan-carbs-kcal').innerText = `${carbsGrams}g (${carbsKcal} kcal)`;
  document.getElementById('plan-protein-kcal').innerText = `${proteinGrams}g (${proteinKcal} kcal)`;
  document.getElementById('plan-fat-kcal').innerText = `${fatGrams}g (${fatKcal} kcal)`;
}

async function finishOnboardingWithPlan() {
  localStorage.setItem('tezfit_onboarded_v2', 'true');
  
  try {
    await fetch('/api/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        initData: initData,
        gender: selectedGender,
        height_cm: selectedHeight,
        weight_kg: selectedWeight,
        target_weight_kg: selectedTargetWeight,
        activity_level: selectedActivity,
        diet_preference: selectedDietPref,
        daily_goal_kcal: calculatedDailyKcal
      })
    });
  } catch (err) {
    console.warn('Profile save warning:', err);
  }

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

  const appHeader = document.querySelector('.app-header');
  if (appHeader) {
    appHeader.style.display = (tabName === 'home') ? 'flex' : 'none';
  }

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
  return loadDashboardForDate(new Date().toISOString().split('T')[0]);
}

async function loadDashboardForDate(dateStr) {
  try {
    const res = await fetch(`/api/dashboard?initData=${encodeURIComponent(initData)}&date=${dateStr}`);
    if (!res.ok) throw new Error('Dashboard xatosi');
    const data = await res.json();
    renderDashboard(data);
  } catch (err) {
    console.warn('Backend ga ulanishda ogohlantirish:', err);
    
    let fallbackName = 'Foydalanuvchi';
    let fallbackContact = 'ID: 8817446491';
    let photoUrl = '';

    const cachedProfile = localStorage.getItem('tezfit_user_profile_v2');
    if (cachedProfile) {
      try {
        const p = JSON.parse(cachedProfile);
        fallbackName = `${p.first_name || ''} ${p.last_name || ''}`.trim() || p.username || 'Foydalanuvchi';
        fallbackContact = `ID: ${p.id || 8817446491}`;
        photoUrl = p.photo_url || '';
      } catch (e) {}
    }

    if (tgUser) {
      fallbackName = `${tgUser.first_name || ''} ${tgUser.last_name || ''}`.trim() || tgUser.username || 'Foydalanuvchi';
      fallbackContact = tgUser.phone_number ? tgUser.phone_number : `ID: ${tgUser.id}`;
      photoUrl = tgUser.photo_url || photoUrl;
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
        dob: '2000-01-01'
      },
      today_stats: { total_calories: 0, total_protein: 0, total_fat: 0, total_carbs: 0, remaining_calories: 2000, progress_percent: 0 },
      weekly_stats: [
        { day: 'Dush', calories: 1850 }, { day: 'Sesh', calories: 2100 },
        { day: 'Chor', calories: 1900 }, { day: 'Pay', calories: 1650 },
        { day: 'Jum', calories: 2200 }, { day: 'Shan', calories: 1950 },
        { day: 'Yak', calories: 0 }
      ],
      today_meals: [],
      badges: []
    });
  }
}

function renderDashboard(data) {
  const { user, today_stats, weekly_stats, today_meals } = data;
  currentUserData = user;

  // Store for analysis page use
  if (weekly_stats) lastWeeklyStats = weekly_stats;
  if (today_stats) window._lastTodayStats = today_stats;

  let displayName = user ? (user.name || 'Foydalanuvchi') : 'Foydalanuvchi';
  let photoUrl = user ? (user.photo_url || '') : '';
  let contactInfo = user ? (user.contact_info || user.phone_number) : 'ID: 8817446491';

  // Override with Telegram WebApp SDK data if available
  if (tgUser) {
    const realTgName = `${tgUser.first_name || ''} ${tgUser.last_name || ''}`.trim() || tgUser.username;
    if (realTgName) displayName = realTgName;
    if (tgUser.photo_url) photoUrl = tgUser.photo_url;
    if (tgUser.phone_number) contactInfo = tgUser.phone_number;
    else if (tgUser.id) contactInfo = `ID: ${tgUser.id}`;
  }

  const isPremium = user && user.is_vip;

  // 1. Hide Premium promo banner & top crown button for Premium users
  const bannerEl = document.getElementById('premium-banner');
  if (bannerEl) bannerEl.style.display = isPremium ? 'none' : 'flex';

  const crownBtn = document.getElementById('header-crown-btn');
  if (crownBtn) crownBtn.style.display = isPremium ? 'none' : 'flex';

  // 2. User Name & Avatar: NO crown for free users!
  const nameEl = document.getElementById('user-name');
  if (nameEl) {
    if (isPremium) {
      nameEl.innerHTML = `${displayName} <span class="vip-badge-span">👑 VIP</span>`;
    } else {
      nameEl.innerText = displayName;
    }
  }

  document.getElementById('greeting-title').innerText = getTimeGreeting();

  const avatarTxt = document.getElementById('user-avatar');
  if (avatarTxt) {
    if (isPremium) {
      avatarTxt.classList.add('gold-vip-avatar');
    } else {
      avatarTxt.classList.remove('gold-vip-avatar');
    }

    if (photoUrl) {
      avatarTxt.innerHTML = `<img src="${photoUrl}" style="width:100%;height:100%;object-fit:cover;border-radius:50%">`;
    } else {
      avatarTxt.innerText = displayName[0].toUpperCase();
    }
  }

  // 3. AI Camera Scanner Banner text & counter button
  const scanBtn = document.getElementById('banner-scan-btn');
  const remScans = (user && user.remaining_scans !== undefined && user.remaining_scans >= 0) ? user.remaining_scans : 15;
  updateUserLimitBadge(remScans, isPremium);

  // 4. Settings menu item status update
  const settingPremText = document.getElementById('setting-premium-text');
  if (settingPremText) {
    if (isPremium) {
      settingPremText.innerHTML = `👑 Premium Status: <strong style="color:#a855f7;">Faol (Cheksiz Rejim)</strong>`;
    } else {
      settingPremText.innerText = "To'lov Usuli / Premium-ga O'tish";
    }
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
  renderSettingsPage();
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
  let contactInfo = user.contact_info || user.phone_number;
  let photoUrl = user.photo_url || '';

  if (tgUser) {
    const realTgName = `${tgUser.first_name || ''} ${tgUser.last_name || ''}`.trim() || tgUser.username;
    if (realTgName) displayName = realTgName;
    if (tgUser.photo_url) photoUrl = tgUser.photo_url;
    if (tgUser.phone_number) contactInfo = tgUser.phone_number;
    else if (tgUser.id) contactInfo = `ID: ${tgUser.id}`;
  }

  if (!contactInfo || contactInfo.includes('8817446491')) {
    contactInfo = tgUser ? `ID: ${tgUser.id}` : 'ID: 8817446491';
  }

  document.getElementById('settings-user-name').innerText = displayName;
  document.getElementById('settings-user-contact').innerText = contactInfo;

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

function openProfileEditSheet() {
  const user = currentUserData || {};
  let displayName = user.name || 'Foydalanuvchi';
  let contactInfo = user.contact_info || user.phone_number;
  let photoUrl = user.photo_url || '';

  if (tgUser) {
    const realTgName = `${tgUser.first_name || ''} ${tgUser.last_name || ''}`.trim() || tgUser.username;
    if (realTgName) displayName = realTgName;
    if (tgUser.photo_url) photoUrl = tgUser.photo_url;
    if (tgUser.phone_number) contactInfo = tgUser.phone_number;
    else if (tgUser.id) contactInfo = `ID: ${tgUser.id}`;
  }

  document.getElementById('prof-input-name').value = displayName;
  document.getElementById('prof-input-contact').value = contactInfo || 'ID: 8817446491';
  document.getElementById('prof-input-dob').value = user.dob || '2000-01-01';
  document.getElementById('prof-input-gender').value = user.gender || 'Male';
  document.getElementById('prof-input-height').value = `${user.height_cm || 170} cm`;
  document.getElementById('prof-input-weight').value = `${user.weight_kg || 70} kg`;

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

// Logout Confirmation Modal Handlers
function openLogoutModal() {
  document.getElementById('logout-modal').style.display = 'flex';
}

function closeLogoutModal() {
  document.getElementById('logout-modal').style.display = 'none';
}

async function confirmLogoutReset() {
  closeLogoutModal();
  localStorage.removeItem('tezfit_onboarded_v2');
  localStorage.removeItem('tezfit_user_profile_v2');
  
  try {
    await fetch('/api/reset-user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ initData: initData })
    });
  } catch (err) {
    console.warn('User reset warning:', err);
  }

  location.reload();
}

function openNotificationSheet() {
  loadNotifSettings();
  document.getElementById('notification-sheet').style.display = 'block';
}

function closeNotificationSheet() {
  document.getElementById('notification-sheet').style.display = 'none';
}

function saveNotifSettings() {
  const settings = {
    meals: document.getElementById('notif-meals')?.checked ?? true,
    weekly: document.getElementById('notif-weekly')?.checked ?? true,
    goals: document.getElementById('notif-goals')?.checked ?? false,
    premium: document.getElementById('notif-premium')?.checked ?? true
  };
  localStorage.setItem('tezfit_notif_settings', JSON.stringify(settings));
}

function loadNotifSettings() {
  try {
    const saved = JSON.parse(localStorage.getItem('tezfit_notif_settings') || '{}');
    const ids = ['meals', 'weekly', 'goals', 'premium'];
    const defaults = { meals: true, weekly: true, goals: false, premium: true };
    ids.forEach(key => {
      const el = document.getElementById(`notif-${key}`);
      if (el) el.checked = (key in saved) ? saved[key] : defaults[key];
    });
  } catch(e) {}
}

let userFavorites = [];
try {
  userFavorites = JSON.parse(localStorage.getItem('tezfit_favorites_v3') || '[]');
} catch (e) { userFavorites = []; }

function openFavoriteSheet() {
  renderFavoriteSheet();
  document.getElementById('favorite-sheet').style.display = 'block';
}

function closeFavoriteSheet() {
  document.getElementById('favorite-sheet').style.display = 'none';
}

function renderFavoriteSheet() {
  const container = document.getElementById('favorite-cards-list');
  if (!container) return;

  if (!userFavorites || userFavorites.length === 0) {
    container.innerHTML = `
      <div style="text-align:center; padding:48px 20px; color:#94a3b8;">
        <span style="font-size:48px; display:block; margin-bottom:12px;">❤️</span>
        <h4 style="color:#ffffff; font-size:18px; font-weight:700; margin-bottom:6px;">Hali sevimlilar yo'q</h4>
        <p style="font-size:13px; margin:0;">Taomlar yoki rejimlar oynasida <strong>♥</strong> tugmasini bossangiz, ular shu yerda ko'rinadi.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = userFavorites.map((fav, index) => `
    <div class="diet-card" style="position:relative; margin-bottom:12px;">
      <img src="${fav.image || 'assets/watermelon_good.png'}" alt="${fav.title}" class="diet-card-img">
      <div class="diet-card-body" style="flex:1;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
          <h3 class="diet-card-title">${fav.title}</h3>
          <button onclick="removeFavoriteItem(${index})" style="background:rgba(239, 68, 68, 0.15); border:none; color:#ef4444; width:28px; height:28px; border-radius:50%; font-size:14px; cursor:pointer; display:flex; align-items:center; justify-content:center;" title="O'chirish">✕</button>
        </div>
        <p class="diet-card-subtext">${fav.calories ? fav.calories + ' kcal' : ''} ${fav.subtext ? ' &nbsp;|&nbsp; ' + fav.subtext : ''}</p>
      </div>
    </div>
  `).join('');
}

function removeFavoriteItem(index) {
  userFavorites.splice(index, 1);
  localStorage.setItem('tezfit_favorites_v3', JSON.stringify(userFavorites));
  renderFavoriteSheet();
}

function showMoreInfo() {
  alert('ℹ️ TezFIT AI v2.5 — Aqlli Kaloriya va Nutritsiya Hamrohingiz.\nVersiya: 2.5.0\nYaratuvchi: TezFIT Dev Team');
}

// ================= FIGMA ANALYSIS SCREEN LOGIC =================
function setTimeframe(mode) {
  currentTimeframe = mode;
  document.querySelectorAll('.tf-btn').forEach(btn => btn.classList.remove('active'));
  const activeBtn = document.getElementById(`tf-${mode}`);
  if (activeBtn) activeBtn.classList.add('active');

  renderAnalysisPage();
}

// Store last weekly stats globally for re-use in renderAnalysisPage
let lastWeeklyStats = null;

function renderAnalysisPage() {
  const canvas = document.getElementById('calorieTrendsCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (trendsChart) trendsChart.destroy();

  let labels, consumedData, goalData;
  const weeklyGoal = currentUserData ? Math.round(currentUserData.daily_goal_kcal || 2000) : 2000;

  if (currentTimeframe === 'daily' && lastWeeklyStats && lastWeeklyStats.length > 0) {
    labels = lastWeeklyStats.map(d => d.day);
    consumedData = lastWeeklyStats.map(d => d.calories || 0);
    goalData = lastWeeklyStats.map(() => weeklyGoal);
  } else if (currentTimeframe === 'weekly') {
    labels = ['1-Hafta', '2-Hafta', '3-Hafta', '4-Hafta'];
    consumedData = lastWeeklyStats ?
      [lastWeeklyStats.slice(0,2).reduce((s,d)=>s+(d.calories||0),0)/2,
       lastWeeklyStats.slice(2,4).reduce((s,d)=>s+(d.calories||0),0)/2,
       lastWeeklyStats.slice(4,6).reduce((s,d)=>s+(d.calories||0),0)/2,
       lastWeeklyStats[6] ? (lastWeeklyStats[6].calories||0) : 0]
      : [0, 0, 0, 0];
    goalData = [weeklyGoal, weeklyGoal, weeklyGoal, weeklyGoal];
  } else if (currentTimeframe === 'monthly') {
    labels = ['1-Hafta', '2-Hafta', '3-Hafta', '4-Hafta'];
    consumedData = [0, 0, 0, 0];
    goalData = [weeklyGoal, weeklyGoal, weeklyGoal, weeklyGoal];
  } else {
    labels = ['Dush', 'Sesh', 'Chor', 'Pay', 'Jum', 'Shan', 'Yak'];
    consumedData = [0, 0, 0, 0, 0, 0, 0];
    goalData = Array(7).fill(weeklyGoal);
  }

  trendsChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: "Iste'mol qilingan",
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

  // Update macros from real today data
  if (currentUserData) {
    const ts = window._lastTodayStats || null;
    if (ts) {
      const total = (ts.total_fat || 0) + (ts.total_carbs || 0) + (ts.total_protein || 0);
      if (total > 0) {
        document.getElementById('fat-pct-val').innerText = Math.round((ts.total_fat / total) * 100) + '%';
        document.getElementById('carbs-pct-val').innerText = Math.round((ts.total_carbs / total) * 100) + '%';
        document.getElementById('protein-pct-val').innerText = Math.round((ts.total_protein / total) * 100) + '%';
      } else {
        document.getElementById('fat-pct-val').innerText = '—';
        document.getElementById('carbs-pct-val').innerText = '—';
        document.getElementById('protein-pct-val').innerText = '—';
      }
    }
  }
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

// ================= LIVE CAMERA STREAM & MODAL HANDLERS =================
let mediaStream = null;

async function openLiveCameraStream() {
  closeCameraChoiceModal();
  const modal = document.getElementById('live-camera-modal');
  const video = document.getElementById('live-video-feed');
  
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false
      });
      if (video) {
        video.srcObject = mediaStream;
        video.play();
      }
      if (modal) modal.style.display = 'flex';
      return;
    } catch (err) {
      console.warn('getUserMedia camera stream failed, falling back to native file input:', err);
    }
  }

  // Fallback to native file input if getUserMedia is restricted
  const camInput = document.getElementById('input-camera');
  if (camInput) {
    camInput.value = '';
    camInput.click();
  }
}

function closeLiveCamera() {
  const modal = document.getElementById('live-camera-modal');
  if (modal) modal.style.display = 'none';
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop());
    mediaStream = null;
  }
}

let currentScanMode = 'food';

function captureLiveVideoFrame() {
  const video = document.getElementById('live-video-feed');
  const canvas = document.getElementById('camera-snapshot-canvas');
  if (!video || !canvas) return;

  const ctx = canvas.getContext('2d');
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  const imageSrc = canvas.toDataURL('image/jpeg', 0.9);
  closeLiveCamera();

  canvas.toBlob((blob) => {
    if (blob) {
      if (currentScanMode === 'drink') {
        submitDrinkScanToAI(blob);
      } else {
        submitImageScanToAI(blob, imageSrc);
      }
    }
  }, 'image/jpeg', 0.9);
}

// ================= CAMERA & GALLERY CHOICE MODAL =================
function openCameraChoiceModal(mode = 'food') {
  currentScanMode = mode;
  const modal = document.getElementById('camera-choice-modal');
  const title = modal ? modal.querySelector('.choice-modal-header h3') : null;
  if (title) {
    title.textContent = mode === 'drink' ? "🥤 Suv / Ichimlik Rasmini Kiriting" : "📸 Taom Rasmini Kiriting";
  }
  if (modal) modal.style.display = 'flex';
}

function closeCameraChoiceModal() {
  document.getElementById('camera-choice-modal').style.display = 'none';
}

function triggerNativeCamera() {
  openLiveCameraStream();
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

  if (currentScanMode === 'drink') {
    submitDrinkScanToAI(file);
  } else {
    const reader = new FileReader();
    reader.onload = function(e) {
      submitImageScanToAI(file, e.target.result);
    };
    reader.readAsDataURL(file);
  }
}

async function submitImageScanToAI(fileOrBlob, imageSrc) {
  closeCameraChoiceModal();
  closeLiveCamera();

  let loadingEl = document.getElementById('cam-loading');
  if (!loadingEl) {
    loadingEl = document.createElement('div');
    loadingEl.id = 'cam-loading';
    loadingEl.className = 'camera-loading-overlay';
    loadingEl.innerHTML = `
      <div class="ai-loader-box">
        <div class="ai-spinner"></div>
        <h3 style="color:#ffffff; font-family:'Outfit', sans-serif; font-size:18px; font-weight:900; margin-top:20px; margin-bottom:6px;">🔍 AI Taomni tahlil qilmoqda...</h3>
        <p style="color:#94a3b8; font-size:13px; margin:0; line-height:1.4;">Bir oz kuting, kaloriya va BJU hisoblanmoqda ✨</p>
      </div>
    `;
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

    if (data && data.status === 'limit_reached') {
      openPremiumModal();
      alert("🔒 " + (data.message || "Bugungi 15 ta tekin skan limiti tugadi! Cheksiz skan uchun Premium-ga o'ting 👑"));
      return;
    }

    if (data && data.remaining !== undefined && data.remaining >= 0) {
      updateUserLimitBadge(data.remaining);
    }

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

// Render Redesigned AI Result Breakdown Items
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
    itemsContainer.innerHTML = currentParsedItems.map((item, idx) => {
      const foodEmojis = ['🍱', '🍖', '🥗', '🥙', '🍳', '🥩'];
      const emoji = foodEmojis[idx % foodEmojis.length];
      return `
        <div class="item-breakdown-card">
          <div class="item-card-header">
            <div class="item-title-box">
              <span class="item-emoji">${emoji}</span>
              <h4 class="item-name">${item.name || 'Taom'}</h4>
            </div>
            <span class="item-cal-badge">🔥 ${Math.round(item.calories)} kcal</span>
          </div>
          
          <div class="item-macros-row">
            <div class="m-pill m-protein">
              <span class="m-lbl">Oqsil</span>
              <strong>${item.protein_g || 0}g</strong>
            </div>
            <div class="m-pill m-carbs">
              <span class="m-lbl">Uglevod</span>
              <strong>${item.carbs_g || 0}g</strong>
            </div>
            <div class="m-pill m-fat">
              <span class="m-lbl">Yog'</span>
              <strong>${item.fat_g || 0}g</strong>
            </div>
          </div>
        </div>
      `;
    }).join('');
  } else {
    itemsContainer.innerHTML = `
      <div class="item-breakdown-card">
        <div class="item-card-header">
          <div class="item-title-box">
            <span class="item-emoji">🍱</span>
            <h4 class="item-name">Taom</h4>
          </div>
          <span class="item-cal-badge">🔥 ${totalCal} kcal</span>
        </div>
        
        <div class="item-macros-row">
          <div class="m-pill m-protein">
            <span class="m-lbl">Oqsil</span>
            <strong>${totalProtein}g</strong>
          </div>
          <div class="m-pill m-carbs">
            <span class="m-lbl">Uglevod</span>
            <strong>${totalCarbs}g</strong>
          </div>
          <div class="m-pill m-fat">
            <span class="m-lbl">Yog'</span>
            <strong>${totalFat}g</strong>
          </div>
        </div>
      </div>
    `;
  }

  document.getElementById('result-sheet').style.display = 'block';
}

function closeResultSheet() {
  document.getElementById('result-sheet').style.display = 'none';
}

function toggleFavorite() {
  if (!currentTotalMealData) {
    alert('❤️ Sevimlilarga qo\'shish uchun taom ma\'lumotlari topilmadi');
    return;
  }

  const mainItem = (currentParsedItems && currentParsedItems.length > 0)
    ? currentParsedItems[0]
    : { name: 'Sog\'lom taom', calories: currentTotalMealData.total_calories || 600 };

  const title = mainItem.name || 'Sog\'lom Taom';
  const existingIndex = userFavorites.findIndex(f => f.title === title);

  if (existingIndex >= 0) {
    userFavorites.splice(existingIndex, 1);
    localStorage.setItem('tezfit_favorites_v3', JSON.stringify(userFavorites));
    alert(`💔 "${title}" sevimlilardan olib tashlandi`);
  } else {
    const photoImg = document.getElementById('sheet-food-img');
    const imageSrc = photoImg ? photoImg.src : 'assets/watermelon_good.png';
    const cal = Math.round(currentTotalMealData.total_calories || mainItem.calories || 0);

    userFavorites.push({
      id: 'meal_' + Date.now(),
      title: title,
      calories: cal,
      subtext: `Oqsil: ${mainItem.protein_g || 0}g | Yog': ${mainItem.fat_g || 0}g | Uglevod: ${mainItem.carbs_g || 0}g`,
      image: imageSrc
    });
    localStorage.setItem('tezfit_favorites_v3', JSON.stringify(userFavorites));
    alert(`❤️ "${title}" sevimlilarga qo'shildi!`);
  }
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

// Premium Multi-Step Flow Handlers
let selectedPremiumPlan = 'monthly';
let currentReceiptBase64 = '';

function showPremiumScreen(screenId) {
  document.querySelectorAll('.p-flow-screen').forEach(s => s.style.display = 'none');
  const target = document.getElementById(`p-screen-${screenId}`);
  if (target) target.style.display = 'block';
}

function openPremiumModal() {
  openPremiumPage();
}

function openPremiumPage() {
  const modal = document.getElementById('premium-modal');
  if (modal) {
    showPremiumScreen('offer');
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
  }
}

function closePremiumModal() {
  const modal = document.getElementById('premium-modal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

function selectPlanAndGoDetail(planType) {
  selectedPremiumPlan = planType;
  const isMonthly = (planType === 'monthly');
  
  document.getElementById('plan-detail-header').innerText = isMonthly ? 'Oylik Rejim' : 'Yillik Rejim';
  document.getElementById('btn-detail-continue').innerText = isMonthly ? "29,000 so'm bilan davom etish" : "299,000 so'm bilan davom etish";
  
  document.getElementById('review-plan-name').innerText = isMonthly ? 'Oylik Rejim' : 'Yillik Rejim';
  document.getElementById('review-plan-price').innerText = isMonthly ? "29,000 so'm / oy" : "299,000 so'm / yil";

  showPremiumScreen('detail');
}

function copyCardNumber() {
  const cardNumText = document.getElementById('card-number-text');
  const cardNum = cardNumText ? cardNumText.innerText.replace(/\s+/g, '') : "5614682113062543";
  navigator.clipboard.writeText(cardNum).then(() => {
    alert("📋 Karta raqami nusxalandi: " + cardNum);
  }).catch(() => {
    alert("Karta raqami: 5614 6821 1306 2543");
  });
}

function triggerReceiptUpload() {
  const fileInput = document.getElementById('receipt-file-input');
  if (fileInput) {
    fileInput.value = '';
    fileInput.click();
  }
}

function handleReceiptSelected(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function(e) {
    currentReceiptBase64 = e.target.result;
    const previewImg = document.getElementById('receipt-preview-img');
    const placeholder = document.getElementById('receipt-dropzone-placeholder');
    if (previewImg) {
      previewImg.src = currentReceiptBase64;
      previewImg.style.display = 'block';
    }
    if (placeholder) placeholder.style.display = 'none';
  };
  reader.readAsDataURL(file);
}

async function submitReceiptToAdmin() {
  if (!currentReceiptBase64) {
    alert("⚠️ Iltimos, oldin to'lov cheki (skrinshot) rasmini yuklang!");
    return;
  }

  const amountSom = (selectedPremiumPlan === 'monthly') ? 29000 : 299000;

  try {
    const res = await fetch('/api/submit-receipt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        initData: initData,
        plan_type: selectedPremiumPlan,
        amount_som: amountSom,
        receipt_b64: currentReceiptBase64
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      showPremiumScreen('success');
    } else {
      alert("Xatolik: " + (data.message || "Chek yuborilmadi"));
    }
  } catch (err) {
    alert("Chekni yuborishda ulanish xatosi");
  }
}

// PDF Export Feature Handler
function downloadWeeklyPDFReport() {
  const isPremiumUser = currentUserData && (currentUserData.is_vip || currentUserData.is_premium);

  if (!isPremiumUser) {
    openPremiumModal();
    alert("🔒 Haftalik PDF Hisobot yuklab olish faqat TezFIT Premium foydalanuvchilar uchun!\n\nHisobotni yuklash uchun Premium-ga o'ting 👑");
    return;
  }

  window.print();
}


// ==================== 💧 WATER TRACKING ====================
function renderWaterUI(glasses, goal) {
  const label = document.getElementById('water-count-label');
  if (label) label.textContent = `${glasses} / ${goal} stakan`;
  const row = document.getElementById('water-glasses-row');
  if (row) {
    const spans = row.querySelectorAll('.water-glass');
    spans.forEach((s, i) => {
      if (i < glasses) s.classList.add('filled');
      else s.classList.remove('filled');
    });
  }
}

async function updateWater(action) {
  try {
    const res = await fetch('/api/water', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ initData: initData || '', action })
    });
    const data = await res.json();
    if (data.status === 'success') renderWaterUI(data.glasses, data.goal);
  } catch(e) { console.error('Water error:', e); }
}


// ==================== 🏋️ EXERCISES ====================
function openExerciseSheet() { document.getElementById('exercise-sheet').style.display = 'block'; }
function closeExerciseSheet() { document.getElementById('exercise-sheet').style.display = 'none'; }

function renderExercises(exercises, totalBurned) {
  const list = document.getElementById('exercise-list');
  const label = document.getElementById('exercise-burned-label');
  if (label) label.textContent = `🔥 ${Math.round(totalBurned)} kcal yoqildi`;
  if (!list) return;
  if (!exercises || exercises.length === 0) {
    list.innerHTML = '<p class="empty-text">Bugun mashq qilinmadi</p>';
    return;
  }
  const emojis = {'Yurish':'🚶','Yugurish':'🏃','Velosiped':'🚴','Suzish':'🏊','Yoga':'🧘','Kuch mashqi':'💪','Raqslar':'💃','Boshqa':'🏋️'};
  list.innerHTML = exercises.map(e => `
    <div class="exercise-item">
      <span class="ex-info">${emojis[e.type]||'🏋️'} ${e.type} — ${e.duration} daq</span>
      <span class="ex-cal">🔥 ${Math.round(e.calories)} kcal</span>
    </div>
  `).join('');
}

async function saveExercise() {
  const exType = document.getElementById('exercise-type-select').value;
  const dur = parseInt(document.getElementById('exercise-duration-input').value) || 30;
  try {
    const res = await fetch('/api/exercises', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ initData: initData || '', exercise_type: exType, duration_min: dur })
    });
    const data = await res.json();
    if (data.status === 'success') {
      closeExerciseSheet();
      alert(`✅ ${data.exercise_type} — ${data.duration} daq, ${Math.round(data.calories_burned)} kcal yoqildi!`);
      loadDashboard();
    }
  } catch(e) { alert('Xatolik: ' + e.message); }
}


// ==================== 🍽️ MEAL TIME FILTER ====================
let allMealsData = [];

function filterMealsByTime(time) {
  document.querySelectorAll('.meal-tab').forEach(t => t.classList.remove('active'));
  document.querySelector(`.meal-tab[data-time="${time}"]`)?.classList.add('active');
  
  const filtered = time === 'all' ? allMealsData : allMealsData.filter(m => m.meal_time === time);
  renderMealsList(filtered);
}

function renderMealsList(meals) {
  const list = document.getElementById('meals-list');
  if (!list) return;
  if (!meals || meals.length === 0) {
    list.innerHTML = '<p class="empty-text">Bu kategoriyada taom yo\'q</p>';
    return;
  }
  list.innerHTML = meals.map(m => `
    <div class="meal-entry-card">
      <div class="meal-info">
        <span class="meal-name">${m.food_name}</span>
        <span class="meal-time-tag">${m.time || ''}</span>
      </div>
      <span class="meal-cal">${Math.round(m.calories)} kcal</span>
    </div>
  `).join('');
}


// ==================== ⚖️ WEIGHT TRACKING ====================
let weightChart = null;

function openWeightLogSheet() {
  const input = document.getElementById('weight-input-val');
  if (input && currentUserData) input.value = currentUserData.weight_kg || 70;
  document.getElementById('weight-log-sheet').style.display = 'block';
}
function closeWeightLogSheet() { document.getElementById('weight-log-sheet').style.display = 'none'; }

async function saveWeightLog() {
  const wt = parseFloat(document.getElementById('weight-input-val').value);
  if (!wt || wt < 30) { alert('Vazn noto\'g\'ri kiritildi'); return; }
  try {
    const res = await fetch('/api/weight-log', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ initData: initData || '', weight_kg: wt })
    });
    const data = await res.json();
    if (data.status === 'success') {
      closeWeightLogSheet();
      alert(`✅ Bugungi vazn: ${wt} kg saqlandi!`);
      loadDashboard();
    }
  } catch(e) { alert('Xatolik: ' + e.message); }
}

function renderWeightChart(history) {
  const canvas = document.getElementById('weightChartCanvas');
  if (!canvas || !history || history.length === 0) return;
  if (weightChart) weightChart.destroy();
  const sorted = [...history].reverse();
  weightChart = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: {
      labels: sorted.map(w => w.date.slice(5)),
      datasets: [{
        label: 'Vazn (kg)',
        data: sorted.map(w => w.kg),
        borderColor: '#c084fc',
        backgroundColor: 'rgba(192,132,252,0.1)',
        fill: true, tension: 0.4, pointRadius: 4, pointBackgroundColor: '#c084fc', borderWidth: 2
      }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
      scales: { x: { ticks: { color: '#64748b', font: { size: 10 } }, grid: { display: false } },
               y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.04)' } } }
    }
  });
  document.getElementById('current-weight-val').textContent = sorted[sorted.length-1]?.kg || 70;
  if (currentUserData) document.getElementById('target-weight-val').textContent = currentUserData.target_weight_kg || 65;
}


// ==================== 🤖 AI CHAT ====================
function createChatBubble(text, className) {
  const bubble = document.createElement('div');
  bubble.className = `ai-chat-bubble ${className}`;
  const safeText = String(text || '')
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
  bubble.innerHTML = safeText;
  return bubble;
}

async function sendAIChat() {
  const input = document.getElementById('ai-chat-input');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';

  const container = document.getElementById('ai-chat-messages');
  container.appendChild(createChatBubble(msg, 'user-bubble'));
  
  const typing = document.createElement('div');
  typing.className = 'ai-chat-bubble ai-bubble';
  typing.id = 'ai-typing';
  typing.textContent = '⏳ AI Javob yozmoqda...';
  container.appendChild(typing);
  container.scrollTop = container.scrollHeight;

  try {
    const res = await fetch('/api/ai-chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ initData: initData || '', message: msg })
    });
    const data = await res.json();
    if (typing.parentNode) typing.remove();

    if (data.status === 'error') {
      container.appendChild(createChatBubble('🔒 ' + (data.message || 'Xatolik'), 'ai-bubble'));
    } else {
      container.appendChild(createChatBubble(data.reply || 'Javob topilmadi', 'ai-bubble'));
    }
    container.scrollTop = container.scrollHeight;
  } catch(e) {
    if (typing.parentNode) typing.remove();
    container.appendChild(createChatBubble('⚠️ Internet yoki ulanishda xatolik yuz berdi.', 'ai-bubble'));
    container.scrollTop = container.scrollHeight;
  }
}

function switchMealsSubTab(tab) {
  document.getElementById('tab-ai-chat').classList.toggle('active', tab === 'ai');
  document.getElementById('tab-favs').classList.toggle('active', tab === 'favs');
  document.getElementById('ai-chat-section').style.display = tab === 'ai' ? 'block' : 'none';
  document.getElementById('favs-section').style.display = tab === 'favs' ? 'block' : 'none';
  if (tab === 'favs') loadFavorites();
}


// ==================== 📋 FAVORITES ====================
async function loadFavorites() {
  try {
    const res = await fetch(`/api/favorites?initData=${encodeURIComponent(initData||'')}`);
    const data = await res.json();
    const list = document.getElementById('favorites-list');
    if (!list) return;
    if (!data.favorites || data.favorites.length === 0) {
      list.innerHTML = '<p class="empty-text">Hali sevimli taom yo\'q. Taom skanlaganda ❤️ bosing!</p>';
      return;
    }
    list.innerHTML = data.favorites.map(f => `
      <div class="fav-item">
        <div class="fav-item-info">
          <h4>🍱 ${f.food_name}</h4>
          <span>🔥 ${Math.round(f.calories)} kcal | O: ${f.protein_g}g | Y: ${f.fat_g}g | U: ${f.carbs_g}g</span>
        </div>
        <div class="fav-item-actions">
          <button class="btn-fav-add" onclick="addFavToMeal(${f.id}, '${f.food_name}', ${f.calories}, ${f.protein_g}, ${f.fat_g}, ${f.carbs_g}, ${f.weight_g})">+</button>
          <button class="btn-fav-delete" onclick="deleteFavorite(${f.id})">✕</button>
        </div>
      </div>
    `).join('');
  } catch(e) { console.error('Favorites error:', e); }
}

async function addFavToMeal(id, name, cal, protein, fat, carbs, weight) {
  try {
    const res = await fetch('/api/save-meal', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ initData: initData||'', food_name: name, calories: cal, protein_g: protein, fat_g: fat, carbs_g: carbs, weight_g: weight, meal_time: 'snack' })
    });
    const data = await res.json();
    if (data.status === 'success') {
      alert(`✅ ${name} bugungi ovqatlarga qo'shildi!`);
      loadDashboard();
    }
  } catch(e) { alert('Xatolik: ' + e.message); }
}

async function deleteFavorite(favId) {
  try {
    await fetch(`/api/favorites/${favId}?initData=${encodeURIComponent(initData||'')}`, { method: 'DELETE' });
    loadFavorites();
  } catch(e) { console.error(e); }
}


// ==================== 🎯 GOAL SETTING ====================
function openGoalSheet() {
  if (currentUserData) {
    document.getElementById('goal-type-select').value = currentUserData.goal_type || 'maintain';
    document.getElementById('goal-target-weight').value = currentUserData.target_weight_kg || 65;
    document.getElementById('goal-daily-cal').value = currentUserData.daily_goal_kcal || 2000;
  }
  document.getElementById('goal-sheet').style.display = 'block';
}
function closeGoalSheet() { document.getElementById('goal-sheet').style.display = 'none'; }

async function saveGoal() {
  const goalType = document.getElementById('goal-type-select').value;
  const targetWt = parseFloat(document.getElementById('goal-target-weight').value);
  const dailyCal = parseFloat(document.getElementById('goal-daily-cal').value);
  try {
    const res = await fetch('/api/goals', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ initData: initData||'', goal_type: goalType, target_weight_kg: targetWt, daily_goal_kcal: dailyCal })
    });
    const data = await res.json();
    if (data.status === 'success') {
      closeGoalSheet();
      alert(`✅ Maqsad saqlandi! Kunlik: ${dailyCal} kcal`);
      loadDashboard();
    }
  } catch(e) { alert('Xatolik: ' + e.message); }
}


// ==================== 🏆 ACHIEVEMENTS ====================
const ALL_BADGES = [
  {code:'first_meal', emoji:'🍽', name:'Birinchi Taom'},
  {code:'streak_3', emoji:'🔥', name:'3 Kun Streak'},
  {code:'streak_7', emoji:'⚡', name:'7 Kun Streak'},
  {code:'streak_30', emoji:'💎', name:'30 Kun Streak'},
  {code:'water_master', emoji:'💧', name:'Suv Ustasi'},
  {code:'exercise_start', emoji:'🏋️', name:'Birinchi Mashq'},
  {code:'scanner_pro', emoji:'📸', name:'Skan Pro'},
  {code:'goal_reached', emoji:'🎯', name:'Maqsadga Erishdi'},
  {code:'favorite_5', emoji:'❤️', name:'5 ta Sevimli'}
];

function openAchievementsSheet() {
  document.getElementById('achievements-sheet').style.display = 'block';
  if (currentUserData) {
    document.getElementById('ach-streak-val').textContent = currentUserData.streak_days || 0;
    document.getElementById('ach-points-val').textContent = currentUserData.points || 0;
    document.getElementById('ach-level-val').textContent = currentUserData.level || 1;
  }
  const grid = document.getElementById('badges-grid');
  const earned = (dashboardData && dashboardData.badges) || [];
  const earnedCodes = earned.map(b => b.badge_code || b);
  grid.innerHTML = ALL_BADGES.map(b => {
    const isEarned = earnedCodes.includes(b.code);
    return `<div class="badge-card ${isEarned ? 'earned' : 'locked'}">
      <span class="badge-emoji">${b.emoji}</span>
      <span class="badge-name">${b.name}</span>
    </div>`;
  }).join('');
}
function closeAchievementsSheet() { document.getElementById('achievements-sheet').style.display = 'none'; }


// ==================== 👥 LEADERBOARD ====================
function openLeaderboardSheet() {
  document.getElementById('leaderboard-sheet').style.display = 'block';
  loadLeaderboard();
}
function closeLeaderboardSheet() { document.getElementById('leaderboard-sheet').style.display = 'none'; }

async function loadLeaderboard() {
  try {
    const res = await fetch(`/api/leaderboard?initData=${encodeURIComponent(initData||'')}`);
    const data = await res.json();
    const list = document.getElementById('leaderboard-list');
    if (!data.leaderboard || data.leaderboard.length === 0) {
      list.innerHTML = '<p class="empty-text">Hali foydalanuvchilar yo\'q</p>';
      return;
    }
    const medals = ['🥇','🥈','🥉'];
    list.innerHTML = data.leaderboard.map((u, i) => `
      <div class="lb-item ${u.is_me ? 'is-me' : ''}">
        <span class="lb-rank">${i < 3 ? medals[i] : (i+1)}</span>
        <div class="lb-info">
          <span class="lb-name">${u.name}${u.is_me ? ' (Siz)' : ''}</span>
          <span class="lb-details">⭐ ${u.points} ball | 📊 Lvl ${u.level}</span>
        </div>
        <span class="lb-streak">🔥 ${u.streak}</span>
      </div>
    `).join('');
  } catch(e) { console.error('Leaderboard error:', e); }
}


// ==================== 📤 WEEKLY REPORT SHARE ====================
async function shareWeeklyReport() {
  try {
    const res = await fetch(`/api/weekly-report?initData=${encodeURIComponent(initData||'')}`);
    const data = await res.json();
    if (data.status !== 'success') { alert('Hisobot yuklanmadi'); return; }
    const r = data.report;
    const text = `📊 TezFIT Haftalik Hisobot\n\n` +
      `👤 ${r.name}\n📅 ${r.period}\n\n` +
      `🔥 Jami: ${r.total_calories} kcal\n` +
      `📈 O'rtacha: ${r.avg_daily_calories} kcal/kun\n` +
      `🍽 Taomlar: ${r.total_meals} ta\n` +
      `🔥 Streak: ${r.streak} kun\n` +
      `🎯 Maqsad: ${r.goal_kcal} kcal/kun`;
    
    if (navigator.share) {
      await navigator.share({ title: 'TezFIT Haftalik Hisobot', text });
    } else {
      await navigator.clipboard.writeText(text);
      alert('📋 Hisobot nusxalandi!');
    }
  } catch(e) { alert('Xatolik: ' + e.message); }
}


// ==================== DASHBOARD DATA HOOK ====================
let dashboardData = null;

const origRenderDashboard = typeof renderDashboard === 'function' ? renderDashboard : null;

// Hook into renderDashboard to also render new features
const _origFetch = window._origFetchDash;
function hookDashboardData(data) {
  dashboardData = data;
  // Water
  if (data.water_today !== undefined) {
    renderWaterUI(data.water_today, data.user?.water_goal || 8);
  }
  // Exercises
  if (data.exercises_today) {
    renderExercises(data.exercises_today, data.total_burned || 0);
  }
  // Meals with time filter
  if (data.today_meals) {
    allMealsData = data.today_meals;
  }
  // Weight
  if (data.weight_history) {
    renderWeightChart(data.weight_history);
  }
}

// Patch the existing loadDashboard fetch to also call hookDashboardData
const _realFetch = window.fetch;
window.fetch = async function(...args) {
  const res = await _realFetch.apply(this, args);
  if (typeof args[0] === 'string' && args[0].includes('/api/dashboard')) {
    const cloned = res.clone();
    cloned.json().then(data => {
      if (data && data.status === 'success') hookDashboardData(data);
    }).catch(() => {});
  }
  return res;
};

// Automatically hide bottom floating dock when chat input is focused on mobile
document.addEventListener('focusin', (e) => {
  if (e.target && e.target.id === 'ai-chat-input') {
    document.body.classList.add('chat-keyboard-active');
  }
});
document.addEventListener('focusout', (e) => {
  if (e.target && e.target.id === 'ai-chat-input') {
    document.body.classList.remove('chat-keyboard-active');
  }
});

// ==================== 🥤 DRINK SCANNER HANDLERS ====================
function triggerDrinkScan() {
  openCameraChoiceModal('drink');
}

function closeDrinkResultSheet() {
  document.getElementById('drink-result-sheet').style.display = 'none';
}

async function submitDrinkScanToAI(fileOrBlob) {
  closeCameraChoiceModal();
  closeLiveCamera();

  let loadingEl = document.getElementById('cam-loading-drink');
  if (!loadingEl) {
    loadingEl = document.createElement('div');
    loadingEl.id = 'cam-loading-drink';
    loadingEl.className = 'camera-loading-overlay';
    loadingEl.innerHTML = `
      <div class="ai-loader-box">
        <div class="ai-spinner"></div>
        <h3 style="color:#ffffff; font-family:'Outfit', sans-serif; font-size:18px; font-weight:900; margin-top:20px; margin-bottom:6px;">🥤 AI Suv va Ichimlikni tahlil qilmoqda...</h3>
        <p style="color:#94a3b8; font-size:13px; margin:0; line-height:1.4;">Bir oz kuting, brend, shakar, halollik va zarar/foydasi tekshirilmoqda ✨</p>
      </div>
    `;
    document.body.appendChild(loadingEl);
  }
  loadingEl.style.display = 'flex';

  const formData = new FormData();
  formData.append('initData', initData || '');
  formData.append('file', fileOrBlob, 'drink_scan.jpg');

  try {
    const res = await fetch('/api/scan-drink', { method: 'POST', body: formData });
    const result = await res.json();
    loadingEl.style.display = 'none';

    if (result && result.status === 'limit_reached') {
      openPremiumModal();
      alert("🔒 " + (result.message || "Bugungi tekin skan limiti tugadi! Premium-ga o'ting 👑"));
      return;
    }

    if (result && result.remaining !== undefined && result.remaining >= 0) {
      updateUserLimitBadge(result.remaining);
    }

    if (result && result.status === 'success' && result.data) {
      showDrinkAnalysisResult(result.data);
    } else {
      alert("⚠️ Kechirasiz, ichimlikni tahlil qilishda xatolik yuz berdi.");
    }
  } catch (err) {
    loadingEl.style.display = 'none';
    alert("⚠️ Internet yoki server bilan ulanishda xatolik yuz berdi.");
  }
}

let currentRemainingScans = 15;

function updateUserLimitBadge(remScans, isPremium) {
  if (remScans !== undefined && remScans !== null) {
    currentRemainingScans = Math.max(0, remScans);
  }
  const isPrem = isPremium || (currentUserData && (currentUserData.is_vip || currentUserData.is_premium));
  
  const crownBtn = document.getElementById('header-crown-btn');
  if (crownBtn) {
    if (isPrem) {
      crownBtn.innerHTML = `<span>👑</span>`;
      crownBtn.title = "TezFIT Premium (Cheksiz)";
    } else {
      crownBtn.innerHTML = `<span class="free-limit-pill">⚡ ${currentRemainingScans}/15</span>`;
      crownBtn.title = "Bugungi tekin skan limiti";
    }
  }

  const scanBtn = document.getElementById('banner-scan-btn');
  const scanSub = document.getElementById('banner-scan-sub');
  if (isPrem) {
    if (scanBtn) scanBtn.innerText = "AI Kamera (♾️)";
    if (scanSub) scanSub.innerText = "Kameradan oling yoki galereyadan tanlang (♾️ Cheksiz)";
  } else {
    if (scanBtn) scanBtn.innerText = `AI Kamera (${currentRemainingScans}/15)`;
    if (scanSub) scanSub.innerText = `Kameradan oling yoki galereyadan tanlang (${currentRemainingScans} ta tekin skan qoldi)`;
  }
}

function showDrinkAnalysisResult(data) {
  document.getElementById('drink-res-title').textContent = data.drink_name || 'Ichimlik / Suv';
  document.getElementById('drink-res-cal').textContent = `${data.calories || 0} kcal`;
  document.getElementById('drink-res-sugar').textContent = `${data.sugar_g || 0}g (${data.sugar_level || 'Normal'})`;
  
  const halalBadge = document.getElementById('drink-halal-badge');
  if (halalBadge) {
    halalBadge.textContent = data.halal_status || (data.is_halal ? '🟢 Halol — Harom moddalar aniqlanmadi' : '⚠️ Shubhali');
    if (data.is_halal) {
      halalBadge.style.background = 'rgba(34,197,94,0.15)';
      halalBadge.style.color = '#22c55e';
    } else {
      halalBadge.style.background = 'rgba(239,68,68,0.15)';
      halalBadge.style.color = '#ef4444';
    }
  }

  document.getElementById('drink-res-health').textContent = data.health_assessment || '';
  document.getElementById('drink-res-details').textContent = data.details || '';

  document.getElementById('drink-result-sheet').style.display = 'block';
}



