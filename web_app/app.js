document.addEventListener("DOMContentLoaded", () => {
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
  }

  // Get initData from Telegram SDK or fallback URL param for dev
  const urlParams = new URLSearchParams(window.location.search);
  const initData = tg?.initData || urlParams.get("initData") || "123456789";

  let weeklyChart = null;
  let gaugeChart = null;

  async function loadDashboard() {
    try {
      const response = await fetch(`/api/dashboard?initData=${encodeURIComponent(initData)}`);
      if (!response.ok) {
        throw new Error("Dashboard yuklashda xatolik");
      }
      const data = await response.json();
      renderDashboard(data);
    } catch (err) {
      console.error(err);
    }
  }

  function renderDashboard(data) {
    const user = data.user;
    const stats = data.today_stats;

    // Header
    document.getElementById("user-name").textContent = user.name || "Foydalanuvchi";
    document.getElementById("user-avatar").textContent = (user.name || "K")[0].toUpperCase();
    document.getElementById("user-streak").textContent = `🔥 ${user.streak_days} kun`;
    if (user.is_vip) {
      document.getElementById("user-vip").style.display = "inline-block";
    }

    // Calorie stats
    const consumed = Math.round(stats.total_calories);
    const goal = Math.round(user.daily_goal_kcal);
    document.getElementById("consumed-cal").textContent = consumed;
    document.getElementById("goal-cal").textContent = goal;

    const pct = goal > 0 ? Math.min(Math.round((consumed / goal) * 100), 100) : 0;
    document.getElementById("gauge-percent").textContent = `${pct}%`;

    // Render Radial Doughnut Chart
    renderGaugeChart(consumed, goal);

    // Macros
    document.getElementById("protein-val").textContent = `${stats.total_protein.toFixed(1)}g`;
    document.getElementById("fat-val").textContent = `${stats.total_fat.toFixed(1)}g`;
    document.getElementById("carbs-val").textContent = `${stats.total_carbs.toFixed(1)}g`;

    // Render Weekly Bar Chart
    renderWeeklyChart(data.weekly_stats);

    // Meals history
    const mealsList = document.getElementById("meals-list");
    mealsList.innerHTML = "";
    if (data.today_meals.length === 0) {
      mealsList.innerHTML = `<p class="empty-state">Bugun hali ovqat yozilmadi</p>`;
    } else {
      data.today_meals.forEach(m => {
        const item = document.createElement("div");
        item.className = "meal-item";
        item.innerHTML = `
          <div>
            <div class="meal-title">${m.food_name}</div>
            <div class="meal-meta">${m.time} • ${Math.round(m.weight_g)}g</div>
          </div>
          <div class="meal-cal">+${Math.round(m.calories)} kcal</div>
        `;
        mealsList.appendChild(item);
      });
    }

    // Badges grid
    const badgesGrid = document.getElementById("badges-grid");
    badgesGrid.innerHTML = "";
    if (data.badges.length === 0) {
      badgesGrid.innerHTML = `<p class="empty-state">Hali nishonlar olinmagan</p>`;
    } else {
      data.badges.forEach(b => {
        const badgeEl = document.createElement("div");
        badgeEl.className = "badge-item";
        badgeEl.textContent = b.name;
        badgesGrid.appendChild(badgeEl);
      });
    }

    // Populate modal inputs
    document.getElementById("input-goal-cal").value = goal;
    document.getElementById("input-weight").value = user.weight_kg || 70;
  }

  function renderGaugeChart(consumed, goal) {
    const ctx = document.getElementById("calorieGauge").getContext("2d");
    if (gaugeChart) gaugeChart.destroy();

    const remaining = Math.max(goal - consumed, 0);

    gaugeChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        datasets: [{
          data: [consumed, remaining],
          backgroundColor: ["#10b981", "rgba(255, 255, 255, 0.1)"],
          borderWidth: 0
        }]
      },
      options: {
        cutout: "80%",
        responsive: true,
        maintainAspectRatio: false,
        plugins: { tooltip: { enabled: false } }
      }
    });
  }

  function renderWeeklyChart(weeklyData) {
    const ctx = document.getElementById("weeklyChart").getContext("2d");
    if (weeklyChart) weeklyChart.destroy();

    const labels = weeklyData.map(d => {
      const dateParts = d.date.split("-");
      return `${dateParts[1]}/${dateParts[2]}`;
    });
    const values = weeklyData.map(d => Math.round(d.calories));

    weeklyChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: "Kaloriya (kcal)",
          data: values,
          backgroundColor: "rgba(16, 185, 129, 0.6)",
          borderColor: "#10b981",
          borderWidth: 1,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false }, ticks: { color: "#94a3b8" } },
          y: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#94a3b8" } }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  }

  // Modal Handlers
  const modal = document.getElementById("goal-modal");
  document.getElementById("open-goal-btn").onclick = () => modal.style.display = "flex";
  document.getElementById("close-modal-btn").onclick = () => modal.style.display = "none";

  document.getElementById("save-goal-btn").onclick = async () => {
    const newGoal = parseFloat(document.getElementById("input-goal-cal").value);
    const newWeight = parseFloat(document.getElementById("input-weight").value);

    try {
      const res = await fetch("/api/goals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          initData: initData,
          daily_goal_kcal: newGoal,
          weight_kg: newWeight
        })
      });
      if (res.ok) {
        modal.style.display = "none";
        loadDashboard();
      }
    } catch (err) {
      console.error(err);
    }
  };

  loadDashboard();
});
