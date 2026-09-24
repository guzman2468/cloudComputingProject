document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#signup-form");
  const firstName = document.querySelector("#first-name");
  const lastName = document.querySelector("#last-name");
  const email = document.querySelector("#email");
  const password = document.querySelector("#password");
  const confirmPassword = document.querySelector("#confirm-password");
  const firstNameError = document.querySelector("#first-name-error");
  const lastNameError = document.querySelector("#last-name-error");
  const emailError = document.querySelector("#email-error");
  const passwordError = document.querySelector("#password-error");
  const confirmPasswordError = document.querySelector("#confirm-password-error");
  const formMessage = document.querySelector("#form-message");

  fetch("/api/users/currentUser", { cache: "no-store" }).then((response) => {
    if (response.ok) {
      window.location.replace("/home");
    }
  });

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

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    firstNameError.textContent = "";
    lastNameError.textContent = "";
    emailError.textContent = "";
    passwordError.textContent = "";
    confirmPasswordError.textContent = "";
    formMessage.textContent = "";
    formMessage.classList.remove("success");

    let isValid = true;

    if (!firstName.value.trim()) {
      firstNameError.textContent = "First name is required.";
      isValid = false;
    }

    if (!lastName.value.trim()) {
      lastNameError.textContent = "Last name is required.";
      isValid = false;
    }

    if (!email.validity.valid || !email.value.trim().toLowerCase().endsWith("@unomaha.edu")) {
      emailError.textContent = email.value
        ? "Use your @unomaha.edu email address."
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

    const submitButton = form.querySelector(".submit-button");
    submitButton.disabled = true;
    submitButton.textContent = "Creating account...";

    try {
      const response = await fetch("/api/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.value.trim().toLowerCase(),
          password: password.value,
          first_name: firstName.value.trim(),
          last_name: lastName.value.trim(),
        }),
      });
      const result = await response.json();

      if (!response.ok) {
        formMessage.textContent = result.detail || "Unable to create your account.";
        return;
      }

      formMessage.textContent = "Account created successfully. You can now log in.";
      formMessage.classList.add("success");
      form.reset();
    } catch (error) {
      formMessage.textContent = "Unable to reach the server. Please try again.";
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Create account";
    }
  });
});
