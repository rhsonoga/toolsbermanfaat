# Email Verification & Authentication Implementation Blueprint

**Last Updated:** April 19, 2026  
**Status:** Planning Phase (Ready for Implementation)

---

## 1. OVERVIEW

Implementasi sistem signup/login dengan email verification berbasis **Supabase Native Auth** dan **REST API** di Flask backend.

### Key Features:
- ✅ User signup dengan email verification required
- ✅ Auto-login setelah email verified
- ✅ Converter access completely blocked jika email belum verified
- ✅ Resend verification email (max 3x per jam)
- ✅ Logout functionality
- ✅ Modular architecture (backend + frontend modules)

---

## 2. ARCHITECTURE OVERVIEW

### Technology Stack
- **Auth Provider:** Supabase (Native Auth)
- **Password Hashing:** Supabase bcrypt (automatic)
- **Email Service:** Supabase native email (default template)
- **Backend:** Flask Python (custom REST endpoints)
- **Frontend:** Vanilla JS (organized in modules)
- **Database:** Supabase PostgreSQL (auth.users + custom tables)

### User Flow (Signup → Verify → Login → Access)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SIGNUP FLOW                                 │
└─────────────────────────────────────────────────────────────────────┘

1. User clicks "Sign Up" button
   ↓
2. Opens signup modal → fills email, password, full name
   ↓
3. Frontend POST /auth/signup (JSON payload)
   ↓
4. Backend:
   - Calls Supabase REST API /auth/v1/signup
   - Supabase creates user in auth.users with email_verified_at = NULL
   - Supabase sends verification email (built-in template)
   - Backend stores verification details in session
   ↓
5. User sees success message: "Registrasi berhasil. Cek email untuk verifikasi."
   ↓
6. User clicks link di email: https://domain.com/auth/verify?token=xxx
   ↓
7. Backend /auth/verify route:
   - Validates token via Supabase REST API
   - Sets email_verified_at timestamp on auth.users
   - Creates Flask session automatically
   - Redirects to homepage
   ↓
8. User sudah login + verified, bisa akses converters

┌─────────────────────────────────────────────────────────────────────┐
│                         LOGIN FLOW                                  │
└─────────────────────────────────────────────────────────────────────┘

1. User clicks "Login" button
   ↓
2. Opens login modal → fills email, password
   ↓
3. Frontend POST /auth/login (JSON payload)
   ↓
4. Backend:
   - Calls Supabase REST API /auth/v1/token (email + password)
   - Checks if user exists
   - Checks if email_verified_at NOT NULL
   - If verified: creates Flask session + returns user data
   - If not verified: returns error "Email belum diverifikasi"
   ↓
5. Frontend closes modal + shows auth status in topbar
   ↓
6. User can access converters

┌─────────────────────────────────────────────────────────────────────┐
│                   CONVERTER ACCESS GUARD                            │
└─────────────────────────────────────────────────────────────────────┘

1. User tries to access converter (cable, hpdb, boq)
   ↓
2. Backend checks @require_verified_email decorator
   ↓
3. If email_verified_at = NULL:
   - Redirect to homepage
   - Show banner: "Please verify your email"
   - Show "Resend Verification" button
   ↓
4. If email_verified_at = NOT NULL:
   - Allow converter access normally

┌─────────────────────────────────────────────────────────────────────┐
│                   RESEND VERIFICATION                              │
└─────────────────────────────────────────────────────────────────────┘

1. User clicks "Resend Verification" button
   ↓
2. Frontend POST /auth/resend-verification
   ↓
3. Backend:
   - Check rate limit (max 3 resends per hour per user)
   - Call Supabase API to resend verification email
   - Return success/error message
   ↓
4. User sees: "Email verification sent. Check your inbox."
```

---

## 3. FILE STRUCTURE

### Backend Modules (New)

```
webapp/
├── auth/
│   ├── __init__.py                 (module initialization)
│   ├── handlers.py                 (signup, login, verify, logout, resend)
│   ├── decorators.py               (require_verified_email)
│   └── utils.py                    (email validator, rate limiter)
├── app.py                          (main Flask app - updated with new routes)
├── requirements.txt                (add: no new deps needed, Supabase via requests)
└── config.py                       (NEW - centralized config for auth)
```

### Frontend Modules (New)

```
webapp/static/
├── js/
│   ├── auth.js                     (NEW - modular auth handlers)
│   │   ├── initSignupForm()        (event listener + submit handler)
│   │   ├── initLoginForm()         (event listener + submit handler)
│   │   ├── initLogoutButton()      (NEW - logout handler)
│   │   ├── initResendButton()      (NEW - resend verification)
│   │   ├── showFeedback()          (reusable feedback display)
│   │   ├── updateAuthStrip()       (reusable auth status update)
│   │   └── closeAuthModals()       (helper to close all modals)
│   └── main.js                     (orchestrator - calls auth.js init + other modules)
├── launcher.css                    (existing - may need minor updates)
└── ...
```

### Templates (Updates)

```
webapp/templates/
├── main.html                       (UPDATED:
│                                    - Add logout button (replace Sign Up/Login when logged in)
│                                    - Add resend verification form (in home panel if needed)
│                                    - Add email verification banner)
└── verify.html                     (OPTIONAL - simple "verifying..." page during email click)
```

---

## 4. DATABASE SCHEMA

### Supabase auth.users (Native)
✅ Sudah ada, tidak perlu custom:
- `id` (UUID) - user ID
- `email` (VARCHAR) - email address
- `encrypted_password` - bcrypt hash (automatic)
- `email_verified_at` (TIMESTAMP) - NULL jika belum verified
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### Custom Table: verification_resend_log (Optional but Recommended)
```sql
CREATE TABLE verification_resend_log (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  resend_count INT DEFAULT 0,
  last_resend_at TIMESTAMP,
  reset_at TIMESTAMP,  -- Reset count setiap jam
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. API ENDPOINTS SPECIFICATION

### Endpoint: POST /auth/signup

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "full_name": "John Doe"
}
```

**Response Success (201):**
```json
{
  "ok": true,
  "message": "Registrasi berhasil. Cek email untuk verifikasi.",
  "user": {
    "id": "uuid-xxx",
    "email": "user@example.com",
    "user_metadata": {
      "full_name": "John Doe"
    }
  }
}
```

**Response Error (400):**
```json
{
  "ok": false,
  "error": "Email sudah terdaftar" | "Password terlalu pendek" | ...
}
```

### Endpoint: POST /auth/login

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```

**Response Success (200):**
```json
{
  "ok": true,
  "message": "Login berhasil.",
  "user": {
    "id": "uuid-xxx",
    "email": "user@example.com",
    "email_verified_at": "2026-04-19T10:30:00Z",
    "user_metadata": {
      "full_name": "John Doe"
    }
  }
}
```

**Response Error (401):**
```json
{
  "ok": false,
  "error": "Email belum diverifikasi" | "Email atau password salah" | ...
}
```

### Endpoint: GET /auth/verify?token=XXX

**Behavior:**
- Supabase mengirim `confirmation_token` di email
- Token format: Supabase JWT confirmation token
- Token validity: 1 jam
- Endpoint validates token via Supabase
- Marks `email_verified_at` = NOW()
- Auto-creates Flask session
- Redirects homepage dengan query: `?verified=true`

**Response Success (302 Redirect):**
```
Location: /?menu=home&verified=true
Set-Cookie: session_id=xxx
```

**Response Error (400/401 Redirect):**
```
Location: /?verification_error=token_expired
```

### Endpoint: POST /auth/resend-verification

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response Success (200):**
```json
{
  "ok": true,
  "message": "Email verifikasi dikirim. Cek inbox Anda."
}
```

**Response Error (429 - Rate Limited):**
```json
{
  "ok": false,
  "error": "Terlalu banyak resend. Coba lagi dalam 1 jam.",
  "retry_after_seconds": 3600
}
```

### Endpoint: POST /auth/logout

**Request:**
```json
{}
```

**Response Success (200):**
```json
{
  "ok": true,
  "message": "Logout berhasil."
}
```

---

## 6. CONVERTER ACCESS GUARD

### Decorator: @require_verified_email

**Logic:**
```python
@require_verified_email
def cable_calculate():
    # Handle cable calculation
    ...
```

**Behavior:**
- Check if user in session
- If NOT logged in → redirect to login modal (with redirect_after_login)
- If logged in but email_verified_at = NULL → show protected page with warning banner
- If logged in AND email_verified_at = NOT NULL → allow access

**Protected Routes:**
- `/cable/calculate`
- `/hpdb/process` (all steps)
- `/boq/convert`
- `/hpdb/reset`, `/boq/reset` (converters only, not calculator)

**Non-Protected Routes:**
- `/` (homepage)
- `/auth/*` (all auth endpoints)
- `/static/*` (assets)

---

## 7. FRONTEND AUTH MODULE (auth.js)

### Structure

```javascript
// Main orchestrator functions
function initAll() {
  initSignupForm();
  initLoginForm();
  initLogoutButton();
  initResendButton();
  checkVerificationMessage();
}

// Signup handler
async function handleSignupSubmit(e) {
  // Validate inputs
  // POST /auth/signup
  // Show success/error feedback
  // Clear form
  // Auto-close modal after 2 seconds
}

// Login handler
async function handleLoginSubmit(e) {
  // Validate inputs
  // POST /auth/login
  // Show success/error feedback
  // Update auth strip
  // Close modal
}

// Logout handler
async function handleLogoutClick(e) {
  // POST /auth/logout
  // Update auth strip
  // Reset UI to logged-out state
  // Redirect to homepage
}

// Resend verification
async function handleResendClick(e) {
  // Prompt email re-confirmation
  // POST /auth/resend-verification
  // Show rate limit error if needed
  // Show success message
}

// Helper: Show feedback in modal
function showFeedback(modalId, message, isSuccess) {
  // Update .auth-feedback element
  // Add 'ok' or 'error' class
  // Auto-clear after 5 seconds
}

// Helper: Update top auth strip
function updateAuthStrip(email) {
  // Update text: "Login sebagai {email}" or "Belum login"
}

// Helper: Check verification query param
function checkVerificationMessage() {
  // If ?verified=true → show "Email verified! Now you can use converters"
  // If ?verification_error=... → show error message banner
}
```

### DOM Elements Required (in main.html)

```html
<!-- Already exist, keep as is -->
<button type="button" class="top-btn" id="openSignupBtn">Sign Up</button>
<button type="button" class="top-btn" id="openLoginBtn">Login</button>

<!-- NEW: Logout button (hidden by default, shown when logged in) -->
<button type="button" class="top-btn" id="logoutBtn" style="display:none;">Logout</button>

<!-- NEW: Verification message banner (on homepage) -->
<div id="verificationBanner" style="display:none;" class="verification-warning">
  Please verify your email to use converters.
  <button type="button" id="resendVerificationBtn">Resend Email</button>
</div>

<!-- Existing modals (keep, but update with new feedback divs) -->
<div class="auth-modal" id="signupModal">
  <!-- ... existing form ... -->
  <div class="auth-feedback" id="signupFeedback"></div>
  <!-- + new resend info message -->
</div>

<div class="auth-modal" id="loginModal">
  <!-- ... existing form ... -->
  <div class="auth-feedback" id="loginFeedback"></div>
</div>
```

---

## 8. ERROR HANDLING & EDGE CASES

### Error Scenarios

| Scenario | Status | Client Message | Backend Action |
|----------|--------|-----------------|----------------|
| Email sudah terdaftar | 400 | "Email sudah digunakan. Login atau gunakan email lain." | Return error from Supabase |
| Password < 8 chars | 400 | "Password minimal 8 karakter." | Validate before sending to Supabase |
| Invalid email format | 400 | "Format email tidak valid." | Validate before sending |
| Token expired | 401 | "Link verifikasi sudah kadaluarsa. Klik Resend." | Redirect to homepage with error |
| Token invalid/tampered | 401 | "Link tidak valid. Minta ulang email verifikasi." | Return 401 |
| Rate limit (resend) | 429 | "Terlalu sering. Coba lagi dalam 1 jam." | Check resend_log table |
| Email/password salah | 401 | "Email atau password salah." | Supabase returns auth error |
| Email belum verified (login) | 401 | "Email belum diverifikasi. Cek inbox atau resend." | Check email_verified_at |
| User not found | 401 | "User tidak ditemukan." | Supabase returns user_not_found |

### Rate Limiting (Resend)
```
Max 3 resend attempts per 1 hour per user
After 3rd attempt: 429 error with retry_after_seconds
Stored in: verification_resend_log table
Reset: Automatically after 1 hour
```

### Session Management
- Session duration: Flask default session lifetime (use environment variable for prod)
- Session invalidation: After logout or manual session.clear()
- Session security: HttpOnly cookies (default Flask behavior)

---

## 9. IMPLEMENTATION PHASES

### Phase 1: Backend Setup (Handlers + Decorators)
- [ ] Create `webapp/auth/` folder structure
- [ ] Implement `handlers.py` with signup/login/verify/logout/resend
- [ ] Implement `decorators.py` with @require_verified_email
- [ ] Update `app.py` routes registration
- [ ] Test all endpoints with Postman/curl

### Phase 2: Database (Optional - for rate limiting)
- [ ] Create `verification_resend_log` table in Supabase
- [ ] Implement rate limiter logic in `utils.py`
- [ ] Test rate limit functionality

### Phase 3: Frontend Module
- [ ] Create `webapp/static/js/auth.js` with all handlers
- [ ] Update `main.html` with new elements (logout btn, verification banner)
- [ ] Test signup/login/logout flow
- [ ] Test email verification link

### Phase 4: Integration & Polish
- [ ] Add converter access guard to protected routes
- [ ] Test verified vs unverified user access
- [ ] Add UI/UX polish (loading states, animations)
- [ ] Test on Vercel deployment

### Phase 5: Testing & Deployment
- [ ] Manual testing: complete signup→verify→login→converter access flow
- [ ] Test error scenarios
- [ ] Test resend functionality
- [ ] Deploy to Vercel
- [ ] Monitor for bugs

---

## 10. KEY DECISIONS & RATIONALE

| Decision | Why |
|----------|-----|
| Supabase native auth | Secure, managed, built-in email support, easy Vercel integration |
| Bcrypt (automatic) | Industry standard, Supabase handles automatically |
| Email token 1 hour | Balance between security (short) and UX (reasonable time) |
| Rate limit 3/hour | Prevent spam, allow reasonable retry attempts |
| Completely block unverified | Security + encourage email verification |
| Auto-login after verify | Smooth UX, already verified so safe |
| Modular JS (auth.js) | Maintainable, reusable, clear separation of concerns |
| No custom user table | Supabase auth.users is sufficient, reduces complexity |

---

## 11. OPEN QUESTIONS / CLARIFICATIONS

✅ **All clarified & decided:**
1. ✅ Email service → Supabase default
2. ✅ Token validity → 1 hour
3. ✅ Resend behavior → User-initiated, max 3x/hour
4. ✅ Auto-login → Yes, after email verification
5. ✅ Converter access → Completely block if not verified
6. ✅ Password hashing → Supabase bcrypt
7. ✅ Frontend module → Separated into auth.js
8. ✅ Database → Use Supabase auth.users native

---

## 12. SUMMARY

**What we're building:**
- Complete signup/login/logout system with **email verification requirement**
- Supabase as auth backend
- Flask REST API as bridge between frontend & Supabase
- Modular, maintainable code structure
- Complete converter access guard for unverified users

**Why this approach:**
- Secure (Supabase managed security)
- Scalable (Supabase handles auth at scale)
- Maintainable (modular code)
- Fast to implement (leverages Supabase native features)
- User-friendly (clear flow, good error messages)

**Ready for:** Implementation Phase 1 (Backend Setup)

---

**Checkpoint:** ✅ Blueprint complete and documented. Ready for coding approval.
