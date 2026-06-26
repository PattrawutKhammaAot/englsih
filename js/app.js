(function () {
  const plan = window.ENGLISH_PLAN || [];
  let viewingDay = getCurrentDay();

  const SEG_COLORS = ['seg-1', 'seg-2', 'seg-3', 'seg-4'];

  function getDayData(day) {
    return plan.find((d) => d.day === day) || plan[0];
  }

  const KIND_LABELS = {
    vocab: 'ศัพท์',
    listen: 'ฟัง',
    speak: 'พูด',
    study: 'เรียน',
  };

  function kindClass(kind) {
    return kind ? `seg-kind-${kind}` : '';
  }

  function renderSegmentActions(s, data, index) {
    const isAi = s.url && !s.url.includes('youtube.com');
    if (s.replayOf) {
      const listenIdx = data.segments.findIndex((x) => x.kind === s.replayOf);
      return `<button type="button" class="btn-replay" data-scroll="${listenIdx}">↩ กลับไปเปิดคลิปฟังด้านบน แล้วพูดตาม</button>`;
    }
    if (s.url) {
      return `<a href="${s.url}" target="_blank" rel="noopener" class="btn-watch ${isAi ? 'ai' : ''}">${isAi ? '💬 เปิดเลย' : '▶ ดูคลิปเลย'}</a>`;
    }
    return '';
  }

  function renderDay() {
    const data = getDayData(viewingDay);
    if (!data) return;

    document.getElementById('dayNum').textContent = data.day;
    document.getElementById('phaseTag').textContent =
      `${data.phaseEmoji} ${data.phaseName} (${data.phaseMonths})`;

    const typeTag = document.getElementById('dayTypeTag');
    if (data.type === 'chill') {
      typeTag.textContent = `🏖️ วันชิล — กิจกรรมเบา ๆ ${data.totalMinutes} นาที`;
      typeTag.className = 'day-type-tag chill';
    } else {
      typeTag.textContent = `📖 วันเรียน — เย็น ${data.totalMinutes} นาที`;
      typeTag.className = 'day-type-tag study';
    }

    const list = document.getElementById('segmentList');
    list.innerHTML = data.segments.map((s, i) => {
      const colorCls = data.type === 'chill' ? 'seg-chill' : SEG_COLORS[i % SEG_COLORS.length];
      const kindBadge = s.kind && KIND_LABELS[s.kind]
        ? `<span class="kind-badge kind-${s.kind}">${KIND_LABELS[s.kind]}</span>`
        : '';
      return `
        <div class="lesson-card ${colorCls} ${kindClass(s.kind)}" id="segment-${i}" data-kind="${s.kind || ''}">
          <div class="slot-label">
            ${s.emoji} ${s.label}
            ${kindBadge}
            <span class="minutes-badge">${s.minutes} นาที</span>
          </div>
          <h3>${s.title || '—'}</h3>
          ${s.channel ? `<div class="channel">📺 ${s.channel}</div>` : ''}
          ${s.note ? `<div class="note">💡 ${s.note}</div>` : ''}
          ${renderSegmentActions(s, data, i)}
        </div>
      `;
    }).join('');

    list.querySelectorAll('.btn-replay').forEach((btn) => {
      btn.addEventListener('click', () => {
        const idx = btn.dataset.scroll;
        const target = document.getElementById(`segment-${idx}`);
        if (target) {
          target.scrollIntoView({ behavior: 'smooth', block: 'center' });
          target.classList.add('highlight-pulse');
          setTimeout(() => target.classList.remove('highlight-pulse'), 1500);
        }
      });
    });

    document.getElementById('btnPrev').disabled = viewingDay <= 1;
    document.getElementById('btnNext').disabled = viewingDay >= 180;
    document.getElementById('dayInput').value = viewingDay;

    const isToday = viewingDay === getCurrentDay();
    document.getElementById('btnSetToday').classList.toggle('primary', isToday);
    document.getElementById('todayHint').textContent = isToday
      ? '✅ นี่คือวันที่คุณกำลังเรียนอยู่'
      : `กำลังดูแผนวันที่ ${viewingDay} (วันเรียนปัจจุบัน: วันที่ ${getCurrentDay()})`;

    renderChecklist();
  }

  function renderCalendar() {
    const grid = document.getElementById('calendarGrid');
    if (!grid) return;

    const habitDays = new Set(getHabitDays());
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    grid.innerHTML = '';

    THAI_DAYS.forEach((d) => {
      const h = document.createElement('div');
      h.className = 'calendar-header';
      h.textContent = d;
      grid.appendChild(h);
    });

    const days = [];
    for (let i = 29; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      days.push(d);
    }

    for (let i = 0; i < days[0].getDay(); i++) {
      grid.appendChild(document.createElement('div'));
    }

    days.forEach((date) => {
      const key = formatDateKey(date);
      const cell = document.createElement('div');
      cell.className = 'calendar-day';
      if (habitDays.has(key)) cell.classList.add('checked');
      if (date.getTime() === today.getTime()) cell.classList.add('today');
      if (date > today) cell.classList.add('future');
      cell.innerHTML = `<span>${date.getDate()}</span>`;
      if (date <= today) {
        cell.addEventListener('click', () => {
          toggleHabitDay(key);
          renderCalendar();
          updateStreak();
        });
      }
      grid.appendChild(cell);
    });
  }

  function updateStreak() {
    const streak = calculateStreak();
    const el = document.getElementById('streakCount');
    if (el) el.textContent = streak;
    const msgEl = document.getElementById('motivationMsg');
    if (!msgEl) return;
    const msg = getMotivationMessage(streak);
    msgEl.textContent = msg;
    msgEl.classList.toggle('show', !!msg);
  }

  // Checklist follows the segments of the CURRENT study day
  function renderChecklist() {
    const dateEl = document.getElementById('checklistDate');
    if (dateEl) dateEl.textContent = `วันนี้: ${thaiDateString()} · แผนวันที่ ${getCurrentDay()}`;

    const data = getDayData(getCurrentDay());
    const box = document.getElementById('checklistItems');
    if (!box || !data) return;

    const items = getTodayChecklist(data.segments.length);
    let done = 0;

    box.innerHTML = data.segments.map((s, i) => {
      if (items[i]) done++;
      return `
        <div class="checklist-item ${items[i] ? 'done' : ''}" data-idx="${i}">
          <div class="check-circle">✓</div>
          <div><strong>${s.emoji} ${s.label}</strong> — ${s.minutes} นาที</div>
        </div>
      `;
    }).join('');

    box.querySelectorAll('.checklist-item').forEach((item) => {
      item.addEventListener('click', () => {
        const idx = parseInt(item.dataset.idx, 10);
        const current = getTodayChecklist(data.segments.length);
        current[idx] = !current[idx];
        saveChecklist(current);
        renderChecklist();

        if (current.every(Boolean)) {
          const todayKey = formatDateKey(new Date());
          const habitDays = getHabitDays();
          if (!habitDays.includes(todayKey)) {
            habitDays.push(todayKey);
            saveHabitDays(habitDays);
            renderCalendar();
            updateStreak();
          }
        }
      });
    });

    const prog = document.getElementById('checklistProgress');
    if (prog) prog.innerHTML = `ทำแล้ว <strong>${done}/${data.segments.length}</strong> ช่วง`;
  }

  function renderChannels() {
    const grid = document.getElementById('channelGrid');
    if (!grid || !window.CHANNELS) return;
    grid.innerHTML = window.CHANNELS.map(
      (c) => `<div class="channel-card"><strong>${c.name}</strong><br><span style="color:var(--text-muted)">${c.group}</span><br><a href="${c.url}" target="_blank" rel="noopener">▶ ไปช่อง</a></div>`
    ).join('');
  }

  function bindDayNav() {
    document.getElementById('btnPrev')?.addEventListener('click', () => {
      viewingDay = Math.max(1, viewingDay - 1);
      renderDay();
    });

    document.getElementById('btnNext')?.addEventListener('click', () => {
      if (viewingDay < 180) {
        viewingDay++;
        renderDay();
      }
    });

    document.getElementById('btnSetToday')?.addEventListener('click', () => {
      setCurrentDay(viewingDay);
      renderDay();
    });

    document.getElementById('btnCompleteDay')?.addEventListener('click', () => {
      const next = Math.min(180, getCurrentDay() + 1);
      setCurrentDay(next);
      viewingDay = next;
      renderDay();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    document.getElementById('dayInput')?.addEventListener('change', (e) => {
      const n = parseInt(e.target.value, 10);
      if (n >= 1 && n <= 180) {
        viewingDay = n;
        renderDay();
      }
    });

    document.getElementById('btnGoDay')?.addEventListener('click', () => {
      const n = parseInt(document.getElementById('dayInput').value, 10);
      if (n >= 1 && n <= 180) {
        viewingDay = n;
        renderDay();
      }
    });
  }

  function init() {
    if (!plan.length) {
      document.getElementById('todaySection').innerHTML =
        '<p style="text-align:center;color:red">โหลดแผนไม่สำเร็จ — ตรวจสอบไฟล์ data/plan.js</p>';
      return;
    }

    viewingDay = getCurrentDay();
    bindDayNav();
    renderDay();
    renderCalendar();
    updateStreak();
    renderChannels();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
