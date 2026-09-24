document.addEventListener("DOMContentLoaded", () => {
  document.title = "Home | MavChat";

  document.querySelector("#logout-button").addEventListener("click", async () => {
    try {
      await fetch("/api/users/logout", { method: "POST" });
    } finally {
      window.location.href = "/";
    }
  });

  fetch("/api/users/currentUser")
    .then((response) => {
      if (!response.ok) {
        window.location.href = "/";
        return null;
      }
      return response.json();
    })
    .then((user) => {
      if (user) {
        document.querySelector("#welcome-message").textContent =
          `Welcome, ${user.first_name} ${user.last_name}. Your account is ready to start chatting.`;
      }
    })
    .catch(() => {
      window.location.href = "/";
    });
});
