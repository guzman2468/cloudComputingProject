document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#login-form");
  const email = document.querySelector("#email");
  const password = document.querySelector("#password");
  const emailError = document.querySelector("#email-error");
  const passwordError = document.querySelector("#password-error");
  const formMessage = document.querySelector("#form-message");
  const passwordToggle = document.querySelector(".password-toggle");

  fetch("/api/users/currentUser", { cache: "no-store" }).then((response) => {
    if (response.ok) {
      window.location.replace("/home");
    }
  });

  passwordToggle.addEventListener("click", () => {
    const isPassword = password.type === "password";
    password.type = isPassword ? "text" : "password";
    passwordToggle.textContent = isPassword ? "Hide" : "Show";
    passwordToggle.setAttribute(
      "aria-label",
      isPassword ? "Hide password" : "Show password"
    );
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    emailError.textContent = "";
    passwordError.textContent = "";
    formMessage.textContent = "";
    formMessage.classList.remove("success");

    let isValid = true;

    const normalizedEmail = email.value.trim().toLowerCase();

    if (!email.validity.valid || !normalizedEmail.endsWith("@unomaha.edu")) {
      emailError.textContent = email.value
        ? "Please use your @unomaha.edu email address."
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

    if (!isValid) {
      return;
    }

    const submitButton = form.querySelector(".submit-button");
    submitButton.disabled = true;
    submitButton.textContent = "Logging in...";

    try {
      const response = await fetch("/api/users/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.value.trim().toLowerCase(),
          password: password.value,
        }),
      });
      const result = await response.json();

      if (!response.ok) {
        formMessage.textContent = result.detail || "Invalid credentials, please try again.";
        return;
      }

      formMessage.textContent = `Welcome back, ${result.first_name}!`;
      formMessage.classList.add("success");
      window.location.href = "/home";
    } catch (error) {
      formMessage.textContent = "Unable to reach the server. Please try again.";
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Log in";
    }
  });
});
