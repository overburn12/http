function saveChatList(){
    localStorage.setItem('oldChats', JSON.stringify(chatHistories)); 
}

function renameCurrentChat() {
    var newName = prompt("Enter the new name for the current chat:", chatHistories[currentChatIndex].title);
    
    if (newName === null) {
      // User cancelled the prompt
      return;
    }
    
    if (newName === "") {
      alert("Chat name cannot be empty.");
      return;
    }
  
    chatHistories[currentChatIndex].title = newName;
    saveChatList();
    populateChatList();  // Refresh the list of chats
}
  
function addNewChat() {
    chatHistories.unshift({ title: "New Chat", messages: [] });
    currentChatIndex = 0;
  
    saveChatList();
    clearFileInput();
    populateChatList();
    renderChatHistory(currentChatIndex);
}
  
function duplicateChat() {
    var selectedChat = chatHistories[currentChatIndex];
    var duplicatedChat = JSON.parse(JSON.stringify(selectedChat));
    duplicatedChat.title = "Copy of " + duplicatedChat.title; // Set a new title for the duplicated chat
    chatHistories.unshift(duplicatedChat); // Add the duplicated chat to the beginning of the chatHistories array
    currentChatIndex = 0; // Set the current chat index to the duplicated chat
    saveChatList();
    clearFileInput();
    populateChatList();
    renderChatHistory(currentChatIndex);
}

function clearLocalStorage() {
    var confirmation = confirm("This will delete all chats. Are you sure you want to proceed?");  // Prompt the user with a confirmation message
  
    if (confirmation) {
      localStorage.removeItem('oldChats');
      chatHistories = [];
      currentChatIndex = 0;
      populateChatList();
      renderChatHistory();
    }
}
  
function deleteCurrentChat() {
    if (chatHistories.length <= 1) {
      // If only one chat is left, clear local storage
      clearLocalStorage();
      return;
    }
  
    chatHistories.splice(currentChatIndex, 1);
    loadChat(currentChatIndex > 0 ? currentChatIndex - 1 : currentChatIndex);
  
    saveChatList();
    clearFileInput();
    populateChatList();
}
  
function loadChat(index) {
    currentChatIndex = index; // Update the index to the newly loaded old chat
    clearFileInput();
    renderChatHistory();
    highlightSelectedChat();
}