document.addEventListener("DOMContentLoaded", () => {
  document.title = "Home | MavChat";

  const profileButton = document.querySelector("#profile-button");
  const profileDropdown = document.querySelector("#profile-dropdown");

  const setMenuOpen = (isOpen) => {
    profileButton.setAttribute("aria-expanded", String(isOpen));
    profileDropdown.hidden = !isOpen;
  };

  profileButton.addEventListener("click", () => {
    setMenuOpen(profileDropdown.hidden);
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest(".profile-menu")) {
      setMenuOpen(false);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      setMenuOpen(false);
      profileButton.focus();
    }
  });

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
        const initial = user.first_name.trim().charAt(0).toUpperCase();
        document.querySelector("#profile-initial").textContent = initial;
        profileButton.setAttribute("aria-label", `Open account menu for ${user.first_name}`);
        document.querySelector("#welcome-message").textContent =
          `Welcome, ${user.first_name} ${user.last_name}. Your account is ready to start chatting.`;
      }
    })
    .catch(() => {
      window.location.href = "/";
    });
});
