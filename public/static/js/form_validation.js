/*
  Client-side behavior for the unified health form:
  - Shows/hides conditional fields (e.g. "cigarettes per day" only
    matters if the person is a smoker)
  - Basic real-time range validation on numeric fields
  - Loading spinner + double-submit prevention
  - Smooth-scroll for the section sidebar nav

  This is UX only. The prediction route re-validates everything
  server-side before it ever reaches a model.
*/

document.addEventListener("DOMContentLoaded", () => {
  initConditionalFields();
  initRangeValidation();
  initSubmitSpinner();
  initSectionNavHighlight();
});

function initConditionalFields() {
  // Smoker -> cigarettes per day
  const smokerRadios = document.querySelectorAll('input[name="current_smoker"]');
  const cigsField = document.getElementById("cigs_per_day_wrap");
  const toggleCigs = () => {
    const isSmoker = document.querySelector('input[name="current_smoker"]:checked');
    if (cigsField) {
      cigsField.classList.toggle("visible", isSmoker && isSmoker.value === "1");
    }
  };
  smokerRadios.forEach((r) => r.addEventListener("change", toggleCigs));
  toggleCigs();

  // Gender=female -> pregnancies field (diabetes model input)
  const genderRadios = document.querySelectorAll('input[name="gender"]');
  const pregField = document.getElementById("pregnancies_wrap");
  const togglePreg = () => {
    const isFemale = document.querySelector('input[name="gender"]:checked');
    if (pregField) {
      pregField.classList.toggle("visible", isFemale && isFemale.value === "0");
    }
  };
  genderRadios.forEach((r) => r.addEventListener("change", togglePreg));
  togglePreg();
}

// Sensible physiological ranges, just to catch obvious typos
// (e.g. typing 750 instead of 75 for weight-adjacent fields).
// Server-side validation in the prediction route is authoritative.
const RANGES = {
  age: [1, 120],
  bmi: [10, 70],
  resting_bp_systolic: [70, 250],
  resting_bp_diastolic: [40, 150],
  resting_heart_rate: [30, 200],
  max_heart_rate: [60, 220],
  glucose: [40, 500],
  total_cholesterol: [80, 600],
  hemoglobin: [3, 20],
};

function initRangeValidation() {
  Object.keys(RANGES).forEach((name) => {
    const input = document.querySelector(`[name="${name}"]`);
    if (!input) return;
    const field = input.closest(".field");
    const errorEl = field ? field.querySelector(".field-error-msg") : null;

    const validate = () => {
      if (input.value === "") {
        field.classList.remove("invalid");
        if (errorEl) errorEl.textContent = "";
        return;
      }
      const [min, max] = RANGES[name];
      const value = parseFloat(input.value);
      const ok = !isNaN(value) && value >= min && value <= max;
      field.classList.toggle("invalid", !ok);
      if (errorEl) errorEl.textContent = ok ? "" : `Expected between ${min} and ${max}.`;
    };

    input.addEventListener("input", validate);
    input.addEventListener("blur", validate);
  });
}

function initSubmitSpinner() {
  const form = document.querySelector("form[data-spinner-form]");
  if (!form) return;

  form.addEventListener("submit", (e) => {
    if (!form.checkValidity()) return;
    const btn = form.querySelector(".btn-primary");
    if (btn && !btn.classList.contains("loading")) {
      btn.classList.add("loading");
      btn.disabled = true;
    }
  });
}

function initSectionNavHighlight() {
  const links = document.querySelectorAll(".section-nav a");
  const sections = Array.from(links).map((link) =>
    document.querySelector(link.getAttribute("href"))
  );

  const onScroll = () => {
    let activeIndex = 0;
    sections.forEach((section, i) => {
      if (section && section.getBoundingClientRect().top < 140) {
        activeIndex = i;
      }
    });
    links.forEach((link, i) => {
      link.style.borderLeftColor = i === activeIndex ? "var(--coral)" : "transparent";
      link.style.color = i === activeIndex ? "var(--navy)" : "var(--ink-soft)";
    });
  };

  window.addEventListener("scroll", onScroll);
  onScroll();
}
