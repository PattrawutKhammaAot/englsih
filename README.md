# แผนเรียนภาษาอังกฤษ 6 เดือน + AI Tutor

เว็บเรียนภาษาอังกฤษแบบ static — เปิดได้จาก GitHub Pages ฟรี ไม่ต้องมีเครื่องเซิร์ฟเวอร์

- **แผนเรียน:** [`index.html`](index.html) — 180 วัน, streak, checklist
- **AI Tutor:** [`ai.html`](ai.html) — แชทฝึกพูด, โหมดฟรี (Groq / OpenRouter)

---

## เปิดบน GitHub Pages (แนะนำ)

### 1. Push ขึ้น GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/<username>/englsih.git
git push -u origin main
```

**แนะนำ:** ตั้ง repo เป็น **Private** (Settings → General → Change visibility) — กันคน clone โค้ดจาก GitHub

**ไม่ commit:** `cert.pem`, `key.pem` (อยู่ใน `.gitignore` แล้ว)

### 2. เปิด GitHub Pages

1. Repo → **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` / folder `/ (root)`
4. Save

URL จะเป็น: `https://<username>.github.io/englsih/`

### 3. แชร์ลิงก์

- แผนเรียน: `https://<username>.github.io/englsih/index.html`
- AI Tutor: `https://<username>.github.io/englsih/ai.html`

---

## API Key ฟรี (โหมด 🆓)

Key ฟรี (Groq + OpenRouter) ฝังอยู่ใน [`ai.html`](ai.html) ที่ `FREE_KEYS`

- ผู้ใช้กดปุ่ม **🆓 Groq** หรือ **🆓 OpenRouter** ได้เลย
- หรือใส่ API key ของตัวเองใน ⚙️ ตั้งค่า

**ความเสี่ยง:** ใครเปิดเว็บแล้วดู source ใน DevTools อาจเห็น key ได้ — Private repo ช่วยกันแค่การ clone จาก GitHub ไม่ได้ซ่อนจากคนเปิดเว็บ

**ถ้า key รั่ว:** สร้าง key ใหม่ที่ [Groq Console](https://console.groq.com/keys) / [OpenRouter](https://openrouter.ai/keys) แล้วอัปเดต `FREE_KEYS` ใน `ai.html`

---

## ฟีเจอร์บน GitHub Pages vs Local

| ฟีเจอร์ | GitHub Pages | Local (`start-server.bat`) |
|---------|--------------|----------------------------|
| แผนเรียน + streak | ✅ | ✅ |
| AI แชท (Groq/OpenRouter ฟรี) | ✅ | ✅ |
| AI ใส่ key เอง | ✅ | ✅ |
| Voice Web Speech | ✅ (HTTPS) | ✅ |
| Voice Whisper | ❌ | ✅ (`start-server-https.bat`) |
| MaxPlus ผ่าน proxy | ❌ | ✅ |

---

## รันบนเครื่องตัวเอง (dev / ฟีเจอร์เต็ม)

ต้องมี **Python 3**

```bat
start-server.bat          REM HTTP พอร์ต 8080
start-server-https.bat    REM HTTPS พอร์ต 8443 — ใช้ Voice / Whisper
```

- แผนเรียน: http://localhost:8080/index.html
- AI Tutor: http://localhost:8080/ai.html (HTTPS 8443 สำหรับไมค์)

`cert.pem` / `key.pem` สร้างอัตโนมัติตอนรัน HTTPS ครั้งแรก — ไม่ต้อง commit

---

## สร้าง/อัปเดตแผนเรียน (optional)

```bash
python scripts/generate_plan.py
python scripts/validate_plan.py
```

---

## Private repo + Pages

- **โค้ดใน Git:** เฉพาะคุณ + collaborator ที่เชิญ
- **เว็บ Pages:** ใครมี URL เปิดได้ (GitHub Free) — แชร์ลิงก์เฉพาะคนที่ต้องการ
