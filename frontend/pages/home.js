document.addEventListener("DOMContentLoaded", () => {
  document.title = "Messages | MavChat";

  const profileButton = document.querySelector("#profile-button");
  const profileDropdown = document.querySelector("#profile-dropdown");
  const chatApp = document.querySelector(".chat-app");
  const conversationList = document.querySelector("#conversation-list");
  const conversationSearch = document.querySelector("#conversation-search");
  const messageList = document.querySelector("#message-list");
  const messageForm = document.querySelector("#message-form");
  const messageInput = document.querySelector("#message-input");
  const newChatModal = document.querySelector("#new-chat-modal");
  const recipientSearch = document.querySelector("#recipient-search");
  const contactList = document.querySelector("#contact-list");

  const conversations = [
    { id: "maya", name: "Maya Rodriguez", username: "maya.rodriguez", color: "#d0d0d0", lastMessage: "That sounds perfect! See you soon.", time: "10:42 AM", messages: [
      { text: "Hey! Are you free to meet up this week?", sent: false, time: "10:38 AM" },
      { text: "That sounds perfect! See you soon.", sent: false, time: "10:42 AM" },
    ] },
    { id: "jordan", name: "Jordan Lee", username: "jordan.lee", color: "#a8a8a8", lastMessage: "Did you see the update?", time: "Yesterday", messages: [{ text: "Did you see the update?", sent: false, time: "Yesterday" }] },
    { id: "sam", name: "Sam Wilson", username: "sam.wilson", color: "#eeeeee", lastMessage: "Thanks for your help!", time: "Mon", messages: [{ text: "Thanks for your help!", sent: false, time: "Mon" }] },
  ];
  let activeConversationId = conversations[0].id;
  let contactSearchController;
  let contactSearchRequestId = 0;

  const initials = (name) => name.split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase();
  const setMenuOpen = (isOpen) => { profileButton.setAttribute("aria-expanded", String(isOpen)); profileDropdown.hidden = !isOpen; };
  const matchesConversationSearch = (conversation, query) => {
    if (!query) return true;
    const searchableText = `${conversation.name} ${conversation.username} ${conversation.lastMessage}`.toLocaleLowerCase();
    return searchableText.split(/[^a-z0-9@.]+/).some((word) => word.startsWith(query));
  };

  const renderConversations = () => {
    const query = conversationSearch.value.trim().toLowerCase();
    const visible = conversations.filter((conversation) => matchesConversationSearch(conversation, query));
    conversationList.innerHTML = visible.length ? visible.map((conversation) => `
      <button class="conversation-item ${conversation.id === activeConversationId ? "active" : ""}" type="button" data-conversation-id="${conversation.id}">
        <span class="avatar" style="background: ${conversation.color}" aria-hidden="true">${initials(conversation.name)}</span>
        <span class="conversation-details"><span class="conversation-name">${conversation.name}</span><span class="conversation-preview">${conversation.lastMessage}</span></span>
        <span class="conversation-time">${conversation.time}</span>
      </button>`).join("") : '<p class="no-results">No conversations found.</p>';
  };

  const renderActiveConversation = () => {
    const conversation = conversations.find((item) => item.id === activeConversationId);
    if (!conversation) return;
    const activeAvatar = document.querySelector("#active-avatar");
    activeAvatar.textContent = initials(conversation.name);
    activeAvatar.style.background = conversation.color;
    document.querySelector("#active-name").textContent = conversation.name;
    document.querySelector("#active-status").textContent = `@${conversation.username}`;
    messageList.innerHTML = `<p class="message-date">Today</p>${conversation.messages.map((message) => `
      <div class="message-row ${message.sent ? "sent" : "received"}"><div class="message-bubble">${message.text}<span class="message-time">${message.time}</span></div></div>`).join("")}`;
    messageList.scrollTop = messageList.scrollHeight;
    renderConversations();
  };

  const selectConversation = (id) => { activeConversationId = id; renderActiveConversation(); chatApp.classList.add("show-messages"); messageInput.focus(); };
  const renderContactMessage = (message) => {
    contactList.innerHTML = `<p class="no-results">${message}</p>`;
  };

  const contactColor = (contact) => {
    const shades = ["#d0d0d0", "#a8a8a8", "#eeeeee", "#777777"];
    const hash = [...contact.email].reduce((total, character) => total + character.charCodeAt(0), 0);
    return shades[hash % shades.length];
  };

  const renderContacts = (contacts) => {
    contactList.innerHTML = contacts.length ? contacts.map((contact) => `
      <button class="contact-option" type="button" data-contact-id="${contact.id}"><span class="avatar" style="background: ${contact.color}" aria-hidden="true">${initials(contact.name)}</span><span class="contact-meta"><strong>${contact.name}</strong><span>@${contact.username}</span></span></button>`).join("") : '<p class="no-results">No people found.</p>';
  };

  const searchContacts = async () => {
    const query = recipientSearch.value.trim();
    const requestId = ++contactSearchRequestId;
    if (contactSearchController) contactSearchController.abort();
    if (!query) {
      renderContactMessage("Start typing a name or email to find people.");
      return;
    }
    if (query.length < 1) return;

    contactSearchController = new AbortController();
    renderContactMessage("Searching...");
    try {
      const response = await fetch(`/api/users/search?q=${encodeURIComponent(query)}`, { signal: contactSearchController.signal });
      if (!response.ok) throw new Error("Unable to search users");
      const users = await response.json();
      // A request can finish after it was aborted, so ignore anything that is
      // no longer associated with the current input value.
      if (requestId !== contactSearchRequestId || query !== recipientSearch.value.trim()) return;
      const normalizedQuery = query.toLocaleLowerCase();
      const contacts = users
        .filter((user) => `${user.first_name} ${user.last_name} ${user.email.split("@")[0]}`.toLocaleLowerCase().includes(normalizedQuery))
        .map((user) => ({
        id: user.email,
        email: user.email,
        name: `${user.first_name} ${user.last_name}`,
        username: user.email,
        color: contactColor(user),
        }));
      renderContacts(contacts);
    } catch (error) {
      if (error.name !== "AbortError") renderContactMessage("Unable to load people. Try again.");
    }
  };

  const setModalOpen = (isOpen) => {
    newChatModal.hidden = !isOpen;
    if (isOpen) {
      recipientSearch.value = "";
      renderContactMessage("Start typing a name or email to find people.");
      recipientSearch.focus();
    }
  };

  profileButton.addEventListener("click", () => setMenuOpen(profileDropdown.hidden));
  document.addEventListener("click", (event) => { if (!event.target.closest(".profile-menu")) setMenuOpen(false); if (event.target === newChatModal) setModalOpen(false); });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape") { setMenuOpen(false); setModalOpen(false); } });
  conversationList.addEventListener("click", (event) => { const item = event.target.closest("[data-conversation-id]"); if (item) selectConversation(item.dataset.conversationId); });
  conversationSearch.addEventListener("input", renderConversations);
  document.querySelector("#new-chat-button").addEventListener("click", () => setModalOpen(true));
  document.querySelector("#empty-new-chat-button").addEventListener("click", () => setModalOpen(true));
  document.querySelector("#close-new-chat").addEventListener("click", () => setModalOpen(false));
  recipientSearch.addEventListener("input", searchContacts);
  contactList.addEventListener("click", (event) => {
    const option = event.target.closest("[data-contact-id]");
    if (!option) return;
    const button = option;
    const contact = {
      id: button.dataset.contactId,
      email: button.dataset.contactId,
      name: button.querySelector("strong").textContent,
      username: button.querySelector("span span").textContent.slice(1),
      color: button.querySelector(".avatar").style.background,
    };
    if (!conversations.some((item) => item.id === contact.id)) conversations.unshift({ ...contact, lastMessage: "Start a conversation", time: "Now", messages: [] });
    setModalOpen(false);
    selectConversation(contact.id);
  });
  document.querySelector("#back-button").addEventListener("click", () => chatApp.classList.remove("show-messages"));
  messageForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const text = messageInput.value.trim();
    const conversation = conversations.find((item) => item.id === activeConversationId);
    if (!text || !conversation) return;
    conversation.messages.push({ text, sent: true, time: "Now" });
    conversation.lastMessage = text;
    conversation.time = "Now";
    messageInput.value = "";
    renderActiveConversation();
  });

  document.querySelector("#logout-button").addEventListener("click", async () => { try { await fetch("/api/users/logout", { method: "POST" }); } finally { window.location.href = "/"; } });
  renderActiveConversation();

  fetch("/api/users/currentUser")
    .then((response) => { if (!response.ok) { window.location.href = "/"; return null; } return response.json(); })
    .then((user) => { if (user) { const initial = user.first_name.trim().charAt(0).toUpperCase(); document.querySelector("#profile-initial").textContent = initial; profileButton.setAttribute("aria-label", `Open account menu for ${user.first_name}`); } })
    .catch(() => { window.location.href = "/"; });
});
