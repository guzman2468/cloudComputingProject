document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#signup-form");
  const email = document.querySelector("#email");
  const password = document.querySelector("#password");
  const confirmPassword = document.querySelector("#confirm-password");
  const emailError = document.querySelector("#email-error");
  const passwordError = document.querySelector("#password-error");
  const confirmPasswordError = document.querySelector("#confirm-password-error");
  const formMessage = document.querySelector("#form-message");

  document.querySelectorAll(".password-toggle").forEach((toggle) => {
    toggle.addEventListener("click", () => {
      const input = toggle.previousElementSibling;
      const isPassword = input.type === "password";

      input.type = isPassword ? "text" : "password";
      toggle.textContent = isPassword ? "Hide" : "Show";
      toggle.setAttribute(
        "aria-label",
        isPassword ? "Hide password" : "Show password"
      );
    });
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    emailError.textContent = "";
    passwordError.textContent = "";
    confirmPasswordError.textContent = "";
    formMessage.textContent = "";
    formMessage.classList.remove("success");

    let isValid = true;

    if (!email.validity.valid) {
      emailError.textContent = email.value
        ? "Enter a valid email address."
        : "Email address is required.";
      isValid = false;
    }

    if (!password.value) {
      passwordError.textContent = "Password is required.";
      isValid = false;
    } else if (password.value.length < 8) {
      passwordError.textContent = "Password must be at least 8 characters.";
      isValid = false;
    }

    if (!confirmPassword.value) {
      confirmPasswordError.textContent = "Please confirm your password.";
      isValid = false;
    } else if (password.value !== confirmPassword.value) {
      confirmPasswordError.textContent = "Passwords do not match.";
      isValid = false;
    }

    if (!isValid) {
      return;
    }

    // Account creation is not connected to a backend yet.
    formMessage.textContent = "Your account details are ready to be submitted.";
    formMessage.classList.add("success");
  });
});
