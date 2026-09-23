document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#login-form");
  const email = document.querySelector("#email");
  const password = document.querySelector("#password");
  const emailError = document.querySelector("#email-error");
  const passwordError = document.querySelector("#password-error");
  const formMessage = document.querySelector("#form-message");
  const passwordToggle = document.querySelector(".password-toggle");

  passwordToggle.addEventListener("click", () => {
    const isPassword = password.type === "password";
    password.type = isPassword ? "text" : "password";
    passwordToggle.textContent = isPassword ? "Hide" : "Show";
    passwordToggle.setAttribute(
      "aria-label",
      isPassword ? "Hide password" : "Show password"
    );
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    emailError.textContent = "";
    passwordError.textContent = "";
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

    if (!isValid) {
      return;
    }

    // Authentication is not connected yet. This confirms that the frontend form works.
    formMessage.textContent = "Your login details are ready to be submitted.";
    formMessage.classList.add("success");
  });
});
