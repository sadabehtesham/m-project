/*
  Client-side behavior for login/signup/reset pages:
  - Real-time field validation (green/red border as you type)
  - Password show/hide toggle
  - Shake animation + error text on invalid submit
  - Loading spinner on submit (prevents double-click submits)
  - Simple password strength meter (signup/reset only)

  NOTE: this is UX only. All real validation and security checks
  happen server-side in forms.py / auth.py — never trust the client.
*/

document.addEventListener("DOMContentLoaded", () => {
  initFloatingLabels();
  initPasswordToggles();
  initRealtimeValidation();
  initPasswordStrength();
  initSubmitSpinner();
});

// Floating labels rely on :not(:placeholder-shown), so every input
// needs a placeholder attribute (even an empty space) - set here so
// templates stay clean.
function initFloatingLabels() {
  document.querySelectorAll(".field input").forEach((input) => {
    if (!input.hasAttribute("placeholder")) {
      input.setAttribute("placeholder", " ");
    }
  });
}

function initPasswordToggles() {
  document.querySelectorAll(".toggle-password").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = btn.parentElement.querySelector("input");
      const isPassword = input.type === "password";
      input.type = isPassword ? "text" : "password";
      btn.textContent = isPassword ? "Hide" : "Show";
      btn.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");
    });
  });
}

function initRealtimeValidation() {
  document.querySelectorAll(".field input[data-validate]").forEach((input) => {
    const field = input.closest(".field");
    const errorEl = field.querySelector(".field-error-msg");

    const validate = () => {
      const result = runValidator(input);
      field.classList.remove("valid", "invalid");
      if (input.value.trim() === "") {
        errorEl.textContent = "";
        return;
      }
      if (result.valid) {
        field.classList.add("valid");
        errorEl.textContent = "";
      } else {
        field.classList.add("invalid");
        errorEl.textContent = result.message;
      }
    };

    input.addEventListener("input", validate);
    input.addEventListener("blur", validate);
  });
}

function runValidator(input) {
  const type = input.dataset.validate;
  const value = input.value.trim();

  if (type === "email") {
    const ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
    return { valid: ok, message: "Enter a valid email address." };
  }

  if (type === "password") {
    const longEnough = value.length >= 8;
    const hasUpper = /[A-Z]/.test(value);
    const hasLower = /[a-z]/.test(value);
    const hasNumber = /\d/.test(value);
    const hasSpecial = /[^A-Za-z0-9]/.test(value);
    const ok = longEnough && hasUpper && hasLower && hasNumber && hasSpecial;
    return {
      valid: ok,
      message: "At least 8 characters, with uppercase, lowercase, a number, and a special character.",
    };
  }

  if (type === "confirm-password") {
    const originalId = input.dataset.matches;
    const original = document.getElementById(originalId);
    const ok = original && value === original.value && value.length > 0;
    return { valid: ok, message: "Passwords do not match." };
  }

  return { valid: true, message: "" };
}

function initPasswordStrength() {
  const pwInput = document.querySelector('input[data-validate="password"]');
  const meterFill = document.querySelector(".strength-meter-fill");
  if (!pwInput || !meterFill) return;

  pwInput.addEventListener("input", () => {
    const value = pwInput.value;
    let score = 0;
    if (value.length >= 8) score += 1;
    if (/[A-Z]/.test(value)) score += 1;
    if (/\d/.test(value)) score += 1;
    if (/[^A-Za-z0-9]/.test(value)) score += 1;

    const pct = (score / 4) * 100;
    meterFill.style.width = pct + "%";

    if (score <= 1) meterFill.style.background = "var(--error)";
    else if (score <= 2) meterFill.style.background = "#D9A441";
    else meterFill.style.background = "var(--teal)";
  });
}

function initSubmitSpinner() {
  document.querySelectorAll("form[data-spinner-form]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      // Let native/server validation run; only show spinner if the
      // browser considers the form valid so we don't spin on a
      // submit that's about to be blocked.
      if (!form.checkValidity()) return;

      const btn = form.querySelector(".btn-primary");
      if (btn && !btn.classList.contains("loading")) {
        btn.classList.add("loading");
        btn.disabled = true;
      }
    });
  });
}

// Triggered by the server (via a data attribute on <body>) when a
// flash error is present, to shake the relevant field on page load.
function shakeFieldOnError() {
  const body = document.body;
  const errorField = body.dataset.shakeField;
  if (!errorField) return;
  const field = document.querySelector(`[data-field-name="${errorField}"]`);
  if (field) {
    field.classList.add("shake");
    setTimeout(() => field.classList.remove("shake"), 400);
  }
}
document.addEventListener("DOMContentLoaded", shakeFieldOnError);
