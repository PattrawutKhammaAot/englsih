const STORAGE = {
  HABIT: 'englishPlan_habitDays',
  CHECKLIST: 'englishPlan_checklist',
  CURRENT_DAY: 'englishPlan_currentDay',
};

const THAI_DAYS = ['อา', 'จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส'];
const THAI_MONTHS = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];

function formatDateKey(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function getHabitDays() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE.HABIT)) || [];
  } catch {
    return [];
  }
}

function saveHabitDays(days) {
  localStorage.setItem(STORAGE.HABIT, JSON.stringify(days));
}

function toggleHabitDay(dateKey) {
  const days = getHabitDays();
  const idx = days.indexOf(dateKey);
  if (idx >= 0) days.splice(idx, 1);
  else days.push(dateKey);
  saveHabitDays(days);
}

function calculateStreak() {
  const days = new Set(getHabitDays());
  if (!days.size) return 0;

  let streak = 0;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const check = new Date(today);

  if (!days.has(formatDateKey(check))) {
    check.setDate(check.getDate() - 1);
  }

  while (days.has(formatDateKey(check))) {
    streak++;
    check.setDate(check.getDate() - 1);
  }
  return streak;
}

function getMotivationMessage(streak) {
  if (streak >= 30) return '🏆 ครบ 30 วันต่อเนื่อง! นิสัยเรียนของคุณแข็งแกร่งมาก';
  if (streak >= 14) return '💪 ครบ 2 สัปดาห์แล้ว สู้ต่อไป!';
  if (streak >= 7) return '🎉 ครบ 1 สัปดาห์แล้ว เก่งมาก!';
  return '';
}

function getCurrentDay() {
  const n = parseInt(localStorage.getItem(STORAGE.CURRENT_DAY), 10);
  return Number.isFinite(n) && n >= 1 && n <= 180 ? n : 1;
}

function setCurrentDay(day) {
  localStorage.setItem(STORAGE.CURRENT_DAY, String(Math.max(1, Math.min(180, day))));
}

function getTodayChecklist(segmentCount) {
  const today = formatDateKey(new Date());
  try {
    const data = JSON.parse(localStorage.getItem(STORAGE.CHECKLIST));
    if (data?.date === today && Array.isArray(data.items) && data.items.length === segmentCount) {
      return data.items;
    }
  } catch {}
  return new Array(segmentCount).fill(false);
}

function saveChecklist(items) {
  localStorage.setItem(STORAGE.CHECKLIST, JSON.stringify({
    date: formatDateKey(new Date()),
    items,
  }));
}

function thaiDateString(date = new Date()) {
  return `${date.getDate()} ${THAI_MONTHS[date.getMonth()]} ${date.getFullYear() + 543}`;
}
