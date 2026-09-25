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
  const chatInfoModal = document.querySelector("#chat-info-modal");
  const addMemberModal = document.querySelector("#add-member-modal");
  const leaveRoomModal = document.querySelector("#leave-room-modal");
  const removeMemberModal = document.querySelector("#remove-member-modal");
  const hideRoomModal = document.querySelector("#hide-room-modal");
  const recipientSearch = document.querySelector("#recipient-search");
  const contactList = document.querySelector("#contact-list");
  const roomMemberList = document.querySelector("#room-member-list");
  const memberSearch = document.querySelector("#member-search");
  const memberContactList = document.querySelector("#member-contact-list");
  const roomNameInput = document.querySelector("#room-name-input");
  const activeName = document.querySelector("#active-name");
  const roomNameEditor = document.querySelector("#room-name-editor");
  const removeMemberCopy = document.querySelector("#remove-member-copy");

  let currentUserEmail = "";
  let conversations = [];
  let displayedConversations = [];
  let activeRoomId = null;
  let contactSearchController;
  let contactSearchRequestId = 0;
  let roomSearchController;
  let roomSearchRequestId = 0;
  let memberSearchController;
  let memberSearchRequestId = 0;
  let messageRequestId = 0;
  let chatSocket;
  let chatSocketReconnectTimer;
  let pendingSocketSync = false;
  let pendingRemoveMember = null;
  let pendingHideRoomId = null;

  const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  }[character]));
  const initials = (name) => name.split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
  const setMenuOpen = (isOpen) => { profileButton.setAttribute("aria-expanded", String(isOpen)); profileDropdown.hidden = !isOpen; };
  const roomColor = (room) => ["#d0d0d0", "#a8a8a8", "#eeeeee", "#777777"][Number(room.id) % 4];
  const roomName = (room) => room.name || room.members.map((member) => `${member.first_name} ${member.last_name}`).join(", ");
  const lastMessageText = (room) => room.last_message?.content || "No messages yet";
  const formatTime = (value) => {
    if (!value) return "";
    const date = new Date(value);
    const today = new Date();
    if (date.toDateString() === today.toDateString()) return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
    return date.toLocaleDateString([], { month: "short", day: "numeric" });
  };

  const renderConversations = () => {
    const visible = displayedConversations;
    conversationList.innerHTML = visible.length ? visible.map((room) => `
      <div class="conversation-item ${room.id === activeRoomId ? "active" : ""}">
        <button class="conversation-select" type="button" data-room-id="${room.id}" aria-label="Open ${escapeHtml(roomName(room))}">
          <span class="avatar" style="background: ${roomColor(room)}" aria-hidden="true">${escapeHtml(initials(roomName(room)))}</span>
          <span class="conversation-details">
            <span class="conversation-name">${escapeHtml(roomName(room))}${room.is_removed ? " <span class=\"removed-label\">Removed</span>" : ""}</span>
            <span class="conversation-preview">${escapeHtml(lastMessageText(room))}</span>
          </span>
          <span class="conversation-time">${escapeHtml(formatTime(room.last_message?.created_at || room.created_at))}</span>
        </button>
        <button class="conversation-remove-button" type="button" data-hide-room-id="${room.id}" aria-label="Remove ${escapeHtml(roomName(room))} from your chat list" title="Remove chat from list">×</button>
      </div>`).join("") : '<p class="no-results">No conversations found.</p>';
  };

  const showEmptyChat = () => {
    messageRequestId += 1;
    messageList.replaceChildren();
    messageInput.value = "";
    document.querySelector("#active-avatar").textContent = "?";
    document.querySelector("#active-status").textContent = "MavChat";
    activeName.textContent = "Select a conversation";
    activeName.hidden = false;
    roomNameEditor.hidden = true;
    document.querySelector("#empty-chat").hidden = false;
    document.querySelector("#active-chat").hidden = true;
  };

  const renderActiveHeader = (room) => {
    document.querySelector("#active-avatar").textContent = initials(roomName(room));
    document.querySelector("#active-avatar").style.background = roomColor(room);
    activeName.textContent = roomName(room);
    roomNameEditor.hidden = true;
    activeName.hidden = false;
    document.querySelector("#active-status").textContent = room.is_removed
      ? "You were removed from this chat"
      : `${room.members.length} member${room.members.length === 1 ? "" : "s"}`;
    messageInput.disabled = room.is_removed;
    messageInput.placeholder = room.is_removed ? "You can no longer send messages" : "Message...";
    document.querySelector("#send-button").disabled = room.is_removed;
    document.querySelector("#rename-room-button").hidden = room.is_removed;
    document.querySelector("#add-member-button").hidden = room.is_removed;
    document.querySelector("#leave-room-button").hidden = room.is_removed;
    document.querySelector("#empty-chat").hidden = true;
    document.querySelector("#active-chat").hidden = false;
  };

  const renderMessages = (messages) => {
    messageList.innerHTML = messages.length ? `
      <p class="message-date">Messages</p>
      ${messages.map((message) => {
        if (message.is_system) return `<div class="system-message">${escapeHtml(message.content)}</div>`;
        const sent = message.sender_email.toLowerCase() === currentUserEmail.toLowerCase();
        return `<div class="message-row ${sent ? "sent" : "received"}">
          <div class="message-content">
            <div class="message-bubble">${escapeHtml(message.content)}<span class="message-time">${escapeHtml(formatTime(message.created_at))}</span></div>
            <div class="message-author"><span class="message-author-avatar" aria-hidden="true">${escapeHtml(initials(message.sender_name))}</span><span>${escapeHtml(message.sender_name)}</span></div>
          </div>
        </div>`;
      }).join("")}
    ` : '<p class="message-date">No messages yet</p>';
    messageList.scrollTop = messageList.scrollHeight;
  };

  const loadMessages = async (roomId) => {
    const requestId = ++messageRequestId;
    const response = await fetch(`/api/chat/rooms/${encodeURIComponent(roomId)}/messages`);
    if (!response.ok) throw new Error("Unable to load messages");
    const messages = await response.json();
    if (requestId === messageRequestId && activeRoomId === roomId) renderMessages(messages);
  };

  const selectConversation = async (roomId) => {
    const room = conversations.find((item) => item.id === roomId);
    if (!room) return;
    activeRoomId = roomId;
    renderConversations();
    renderActiveHeader(room);
    chatApp.classList.add("show-messages");
    messageList.innerHTML = '<p class="message-date">Loading messages...</p>';
    messageInput.focus();
    try {
      await loadMessages(roomId);
    } catch {
      messageList.innerHTML = '<p class="message-date">Unable to load messages.</p>';
    }
  };

  const loadRooms = async () => {
    const response = await fetch("/api/chat/rooms");
    if (!response.ok) throw new Error("Unable to load chat rooms");
    conversations = await response.json();
    displayedConversations = conversations;
    renderConversations();
    if (activeRoomId && conversations.some((room) => room.id === activeRoomId)) {
      renderActiveHeader(conversations.find((room) => room.id === activeRoomId));
    } else {
      activeRoomId = null;
      showEmptyChat();
    }
  };

  const syncFromSocketEvent = async (payload) => {
    const roomId = Number(payload.room_id);
    if (payload.change === "left" && payload.member_email.toLowerCase() === currentUserEmail.toLowerCase()) {
      conversations = conversations.filter((room) => room.id !== roomId);
      displayedConversations = displayedConversations.filter((room) => room.id !== roomId);
      activeRoomId = null;
      chatApp.classList.remove("show-messages");
      showEmptyChat();
      renderConversations();
      return;
    }
    if (!roomNameEditor.hidden) {
      pendingSocketSync = true;
      return;
    }
    const selectedRoomId = activeRoomId;
    try {
      if (conversationSearch.value.trim()) await searchRooms();
      else await loadRooms();
      if (selectedRoomId && activeRoomId === selectedRoomId && conversations.some((room) => room.id === selectedRoomId)) {
        await loadMessages(selectedRoomId);
      }
      if (!chatInfoModal.hidden) {
      const room = conversations.find((item) => item.id === roomId);
        if (room) renderRoomMembers(room);
      }
    } catch {
      // Keep the current UI visible if an event refresh briefly fails.
    }
  };

  const flushPendingSocketSync = () => {
    if (pendingSocketSync && roomNameEditor.hidden) {
      pendingSocketSync = false;
      syncFromSocketEvent({ room_id: activeRoomId });
    }
  };

  const connectChatSocket = () => {
    if (!currentUserEmail) return;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    chatSocket = new WebSocket(`${protocol}//${window.location.host}/api/chat/socket`);
    chatSocket.addEventListener("message", (event) => {
      const payload = JSON.parse(event.data);
      if (["room.created", "message.created", "room.member_changed", "room.renamed"].includes(payload.type)) {
        syncFromSocketEvent(payload);
      }
    });
    chatSocket.addEventListener("close", () => {
      chatSocket = null;
      if (currentUserEmail) {
        chatSocketReconnectTimer = window.setTimeout(connectChatSocket, 2000);
      }
    });
  };

  const searchRooms = async () => {
    const query = conversationSearch.value.trim();
    const requestId = ++roomSearchRequestId;
    if (roomSearchController) roomSearchController.abort();
    if (!query) {
      await loadRooms();
      return;
    }
    roomSearchController = new AbortController();
    try {
      const response = await fetch(`/api/chat/rooms/search?q=${encodeURIComponent(query)}`, { signal: roomSearchController.signal });
      if (!response.ok) throw new Error("Unable to search chat rooms");
      const rooms = await response.json();
      if (requestId !== roomSearchRequestId || query !== conversationSearch.value.trim()) return;
      displayedConversations = rooms;
      renderConversations();
    } catch (error) {
      if (error.name !== "AbortError") {
        displayedConversations = [];
        renderConversations();
      }
    }
  };

  const renderContactMessage = (message) => { contactList.innerHTML = `<p class="no-results">${message}</p>`; };
  const contactColor = (contact) => ["#d0d0d0", "#a8a8a8", "#eeeeee", "#777777"][contact.email.length % 4];
  const renderContacts = (contacts) => {
    contactList.innerHTML = contacts.length ? contacts.map((contact) => `
      <button class="contact-option" type="button" data-contact-email="${escapeHtml(contact.email)}">
        <span class="avatar" style="background: ${contact.color}" aria-hidden="true">${escapeHtml(initials(contact.name))}</span>
        <span class="contact-meta"><strong>${escapeHtml(contact.name)}</strong><span>@${escapeHtml(contact.email)}</span></span>
      </button>`).join("") : '<p class="no-results">No people found.</p>';
  };

  const searchContacts = async () => {
    const query = recipientSearch.value.trim();
    const requestId = ++contactSearchRequestId;
    if (contactSearchController) contactSearchController.abort();
    if (!query) { renderContactMessage("Start typing a name or email to find people."); return; }
    contactSearchController = new AbortController();
    renderContactMessage("Searching...");
    try {
      const response = await fetch(`/api/users/search?q=${encodeURIComponent(query)}`, { signal: contactSearchController.signal });
      if (!response.ok) throw new Error("Unable to search users");
      const users = await response.json();
      if (requestId !== contactSearchRequestId || query !== recipientSearch.value.trim()) return;
      const normalizedQuery = query.toLocaleLowerCase();
      const contacts = users.filter((user) => `${user.first_name} ${user.last_name} ${user.email.split("@")[0]}`.toLocaleLowerCase().includes(normalizedQuery)).map((user) => ({
        email: user.email,
        name: `${user.first_name} ${user.last_name}`,
        color: contactColor(user),
      }));
      renderContacts(contacts);
    } catch (error) {
      if (error.name !== "AbortError") renderContactMessage("Unable to load people. Try again.");
    }
  };

  const setModalOpen = (isOpen) => {
    newChatModal.hidden = !isOpen;
    if (isOpen) { recipientSearch.value = ""; renderContactMessage("Start typing a name or email to find people."); recipientSearch.focus(); }
  };

  const setChatInfoOpen = (isOpen) => {
    chatInfoModal.hidden = !isOpen;
  };

  const setAddMemberOpen = (isOpen) => {
    addMemberModal.hidden = !isOpen;
    if (isOpen) {
      memberSearch.value = "";
      memberContactList.innerHTML = '<p class="no-results">Start typing a name or email to find people.</p>';
      memberSearch.focus();
    }
  };

  const setLeaveRoomOpen = (isOpen) => {
    leaveRoomModal.hidden = !isOpen;
  };

  const setRemoveMemberOpen = (isOpen, member = null) => {
    pendingRemoveMember = isOpen ? member : null;
    if (isOpen && member) {
      const fullName = `${member.first_name} ${member.last_name}`;
      removeMemberCopy.textContent = `Are you sure you would like to remove ${fullName} from the chat?`;
    }
    removeMemberModal.hidden = !isOpen;
  };

  const hideRoomFromList = async (roomId) => {
    const response = await fetch(`/api/chat/rooms/${encodeURIComponent(roomId)}/visibility`, { method: "DELETE" });
    if (!response.ok) throw new Error("Unable to remove chat from list");
    conversations = conversations.filter((room) => room.id !== roomId);
    displayedConversations = displayedConversations.filter((room) => room.id !== roomId);
    if (activeRoomId === roomId) {
      activeRoomId = null;
      chatApp.classList.remove("show-messages");
      showEmptyChat();
    }
    renderConversations();
  };

  const setHideRoomOpen = (isOpen, roomId = null) => {
    pendingHideRoomId = isOpen ? roomId : null;
    hideRoomModal.hidden = !isOpen;
  };

  const renderRoomMembers = (room) => {
    const isCreator = room.created_by_email.toLowerCase() === currentUserEmail.toLowerCase();
    roomMemberList.innerHTML = room.members.map((member) => {
      const fullName = `${member.first_name} ${member.last_name}`;
      const isCurrentUser = member.email.toLowerCase() === currentUserEmail.toLowerCase();
      const removeButton = isCreator && !isCurrentUser ? `
          <button class="remove-member-button" type="button" data-remove-member-email="${escapeHtml(member.email)}" aria-label="Remove ${escapeHtml(fullName)} from chat" title="Remove ${escapeHtml(fullName)} from chat">×</button>` : "";
      return `
      <div class="contact-option">
        <span class="avatar" style="background: ${roomColor(room)}" aria-hidden="true">${escapeHtml(initials(fullName))}</span>
        <span class="contact-meta"><strong>${escapeHtml(fullName)}</strong><span>${escapeHtml(member.email)}</span></span>
        ${removeButton}
      </div>`;
    }).join("");
  };

  const renderMemberSearchMessage = (message) => { memberContactList.innerHTML = `<p class="no-results">${message}</p>`; };
  const renderMemberSearchResults = (contacts) => {
    memberContactList.innerHTML = contacts.length ? contacts.map((contact) => `
      <button class="contact-option" type="button" data-member-email="${escapeHtml(contact.email)}">
        <span class="avatar" style="background: ${contact.color}" aria-hidden="true">${escapeHtml(initials(contact.name))}</span>
        <span class="contact-meta"><strong>${escapeHtml(contact.name)}</strong><span>@${escapeHtml(contact.email)}</span></span>
      </button>`).join("") : '<p class="no-results">No people found.</p>';
  };

  const searchMembersToAdd = async () => {
    const query = memberSearch.value.trim();
    const requestId = ++memberSearchRequestId;
    if (memberSearchController) memberSearchController.abort();
    if (!query) { renderMemberSearchMessage("Start typing a name or email to find people."); return; }
    const room = conversations.find((item) => item.id === activeRoomId);
    if (!room) return;
    memberSearchController = new AbortController();
    renderMemberSearchMessage("Searching...");
    try {
      const response = await fetch(`/api/users/search?q=${encodeURIComponent(query)}`, { signal: memberSearchController.signal });
      if (!response.ok) throw new Error("Unable to search users");
      const users = await response.json();
      if (requestId !== memberSearchRequestId || query !== memberSearch.value.trim()) return;
      const existingMembers = new Set(room.members.map((member) => member.email.toLowerCase()));
      const normalizedQuery = query.toLocaleLowerCase();
      const contacts = users
        .filter((user) => !existingMembers.has(user.email.toLowerCase()))
        .filter((user) => `${user.first_name} ${user.last_name} ${user.email.split("@")[0]}`.toLocaleLowerCase().includes(normalizedQuery))
        .map((user) => ({ email: user.email, name: `${user.first_name} ${user.last_name}`, color: contactColor(user) }));
      renderMemberSearchResults(contacts);
    } catch (error) {
      if (error.name !== "AbortError") renderMemberSearchMessage("Unable to load people. Try again.");
    }
  };

  profileButton.addEventListener("click", () => setMenuOpen(profileDropdown.hidden));
  document.addEventListener("click", (event) => {
    if (!event.target.closest(".profile-menu")) setMenuOpen(false);
    if (event.target === newChatModal) setModalOpen(false);
    if (event.target === chatInfoModal) setChatInfoOpen(false);
    if (event.target === addMemberModal) setAddMemberOpen(false);
    if (event.target === leaveRoomModal) setLeaveRoomOpen(false);
    if (event.target === removeMemberModal) setRemoveMemberOpen(false);
    if (event.target === hideRoomModal) setHideRoomOpen(false);
  });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape") { setMenuOpen(false); setModalOpen(false); setChatInfoOpen(false); setAddMemberOpen(false); setLeaveRoomOpen(false); setRemoveMemberOpen(false); setHideRoomOpen(false); } });
  conversationList.addEventListener("click", async (event) => {
    const hideButton = event.target.closest("[data-hide-room-id]");
    if (hideButton) {
      setHideRoomOpen(true, Number(hideButton.dataset.hideRoomId));
      return;
    }
    const item = event.target.closest("[data-room-id]");
    if (item) selectConversation(Number(item.dataset.roomId));
  });
  conversationSearch.addEventListener("input", searchRooms);
  document.querySelector("#new-chat-button").addEventListener("click", () => setModalOpen(true));
  document.querySelector("#empty-new-chat-button").addEventListener("click", () => setModalOpen(true));
  document.querySelector("#close-new-chat").addEventListener("click", () => setModalOpen(false));
  document.querySelector("#chat-info-button").addEventListener("click", () => {
    const room = conversations.find((item) => item.id === activeRoomId);
    if (!room) return;
    renderRoomMembers(room);
    setChatInfoOpen(true);
  });
  document.querySelector("#close-chat-info").addEventListener("click", () => setChatInfoOpen(false));
  document.querySelector("#add-member-button").addEventListener("click", () => {
    if (activeRoomId) setAddMemberOpen(true);
  });
  document.querySelector("#close-add-member").addEventListener("click", () => setAddMemberOpen(false));
  document.querySelector("#leave-room-button").addEventListener("click", () => {
    if (activeRoomId) setLeaveRoomOpen(true);
  });
  document.querySelector("#close-leave-room").addEventListener("click", () => setLeaveRoomOpen(false));
  document.querySelector("#cancel-leave-room").addEventListener("click", () => setLeaveRoomOpen(false));
  document.querySelector("#close-remove-member").addEventListener("click", () => setRemoveMemberOpen(false));
  document.querySelector("#cancel-remove-member").addEventListener("click", () => setRemoveMemberOpen(false));
  document.querySelector("#close-hide-room").addEventListener("click", () => setHideRoomOpen(false));
  document.querySelector("#cancel-hide-room").addEventListener("click", () => setHideRoomOpen(false));
  document.querySelector("#confirm-hide-room").addEventListener("click", async () => {
    if (pendingHideRoomId === null) return;
    const roomId = pendingHideRoomId;
    try {
      await hideRoomFromList(roomId);
      setHideRoomOpen(false);
    } catch {
      setHideRoomOpen(false);
    }
  });
  roomMemberList.addEventListener("click", (event) => {
    const removeButton = event.target.closest("[data-remove-member-email]");
    if (!removeButton) return;
    const room = conversations.find((item) => item.id === activeRoomId);
    const member = room?.members.find((item) => item.email.toLowerCase() === removeButton.dataset.removeMemberEmail.toLowerCase());
    if (member) setRemoveMemberOpen(true, member);
  });
  document.querySelector("#confirm-remove-member").addEventListener("click", async () => {
    if (!activeRoomId || !pendingRemoveMember) return;
    const roomId = activeRoomId;
    try {
      const response = await fetch(`/api/chat/rooms/${encodeURIComponent(roomId)}/members/${encodeURIComponent(pendingRemoveMember.email)}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Unable to remove room member");
      setRemoveMemberOpen(false);
      await loadRooms();
      const room = conversations.find((item) => item.id === roomId);
      if (room) {
        renderRoomMembers(room);
        await loadMessages(roomId);
      }
    } catch {
      removeMemberCopy.textContent = "Unable to remove this person. Please try again.";
    }
  });
  document.querySelector("#confirm-leave-room").addEventListener("click", async () => {
    if (!activeRoomId) return;
    const roomId = activeRoomId;
    const response = await fetch(`/api/chat/rooms/${encodeURIComponent(roomId)}/members/me`, { method: "DELETE" });
    if (!response.ok) return;
    conversations = conversations.filter((room) => room.id !== roomId);
    displayedConversations = displayedConversations.filter((room) => room.id !== roomId);
    activeRoomId = null;
    setLeaveRoomOpen(false);
    chatApp.classList.remove("show-messages");
    showEmptyChat();
    renderConversations();
  });
  memberSearch.addEventListener("input", searchMembersToAdd);
  memberContactList.addEventListener("click", async (event) => {
    const option = event.target.closest("[data-member-email]");
    if (!option || !activeRoomId) return;
    try {
      const response = await fetch(`/api/chat/rooms/${encodeURIComponent(activeRoomId)}/members`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ member_email: option.dataset.memberEmail }),
      });
      if (!response.ok) throw new Error("Unable to add room member");
      const updatedRoom = await response.json();
      const room = conversations.find((item) => item.id === activeRoomId);
      if (room) Object.assign(room, updatedRoom);
      const displayedRoom = displayedConversations.find((item) => item.id === activeRoomId);
      if (displayedRoom && displayedRoom !== room) Object.assign(displayedRoom, updatedRoom);
      renderConversations();
      if (room) renderActiveHeader(room);
      setAddMemberOpen(false);
    } catch {
      renderMemberSearchMessage("Unable to add this person. Try again.");
    }
  });
  document.querySelector("#rename-room-button").addEventListener("click", () => {
    const room = conversations.find((item) => item.id === activeRoomId);
    if (!room) return;
    roomNameInput.value = roomName(room);
    activeName.hidden = true;
    roomNameEditor.hidden = false;
    roomNameInput.focus();
    roomNameInput.select();
  });
  document.querySelector("#cancel-room-name").addEventListener("click", () => {
    roomNameEditor.hidden = true;
    activeName.hidden = false;
    flushPendingSocketSync();
  });
  roomNameEditor.addEventListener("submit", async (event) => {
    event.preventDefault();
    const room = conversations.find((item) => item.id === activeRoomId);
    const name = roomNameInput.value.trim();
    if (!room || !name) return;
    const response = await fetch(`/api/chat/rooms/${encodeURIComponent(room.id)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    if (!response.ok) return;
    const updatedRoom = await response.json();
    Object.assign(room, updatedRoom);
    renderConversations();
    renderActiveHeader(room);
    flushPendingSocketSync();
  });
  recipientSearch.addEventListener("input", searchContacts);
  contactList.addEventListener("click", async (event) => {
    const option = event.target.closest("[data-contact-email]");
    if (!option) return;
    try {
      const response = await fetch("/api/chat/rooms", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ member_emails: [option.dataset.contactEmail] }),
      });
      if (!response.ok) throw new Error("Unable to create chat room");
      const room = await response.json();
      setModalOpen(false);
      await loadRooms();
      await selectConversation(room.id);
    } catch {
      renderContactMessage("Unable to create this chat. Try again.");
    }
  });
  document.querySelector("#back-button").addEventListener("click", () => chatApp.classList.remove("show-messages"));
  messageForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const content = messageInput.value.trim();
    if (!content || !activeRoomId) return;
    const room = conversations.find((item) => item.id === activeRoomId);
    if (room?.is_removed) return;
    const response = await fetch(`/api/chat/rooms/${encodeURIComponent(activeRoomId)}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });
    if (!response.ok) return;
    messageInput.value = "";
    await loadMessages(activeRoomId);
    await loadRooms();
  });

  document.querySelector("#logout-button").addEventListener("click", async () => { try { await fetch("/api/users/logout", { method: "POST" }); } finally { window.location.href = "/"; } });

  fetch("/api/users/currentUser")
    .then((response) => { if (!response.ok) { window.location.href = "/"; return null; } return response.json(); })
    .then(async (user) => {
      if (!user) return;
      currentUserEmail = user.email;
      const userInitials = `${user.first_name.trim().charAt(0)}${user.last_name.trim().charAt(0)}`.toUpperCase();
      document.querySelector("#profile-initial").textContent = userInitials;
      document.querySelector("#profile-summary-avatar").textContent = userInitials;
      document.querySelector("#profile-name").textContent = `${user.first_name} ${user.last_name}`;
      document.querySelector("#profile-email").textContent = user.email;
      profileButton.setAttribute("aria-label", `Open account menu for ${user.first_name}`);
      await loadRooms();
      connectChatSocket();
    })
    .catch(() => { window.location.href = "/"; });
});
