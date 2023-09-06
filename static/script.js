
var chatHistories = [];
var currentChatIndex = null;

window.addEventListener('load', function () {
  currentChatIndex = 0;
  populateChatList();
  renderChatHistory(currentChatIndex);
  
  var user_message = document.getElementById('user_message'); // Define it here

  user_message.addEventListener('keydown', function(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault(); // Prevent the default behavior of submitting a form
      sendMessage(); // Call the sendMessage function to send the message
    }
  });
});

function toggleFileContent(headerElement) {
  const fileBody = headerElement.parentNode.querySelector('.file-body');
  if (fileBody.style.display === 'none' || fileBody.style.display === '') {
      fileBody.style.display = 'block';
  } else {
      fileBody.style.display = 'none';
  }
}

function renderChatHistory() {
  var chatHistoryContainer = document.getElementById('chat_history');
  let htmlString = '';

  if (currentChatIndex !== null && chatHistories[currentChatIndex].messages) {
    chatHistories[currentChatIndex].messages.forEach(function (message) {
      htmlString += renderSingleMessage(message);
    });
  }

  chatHistoryContainer.innerHTML = htmlString;
  chatHistoryContainer.scrollTop = chatHistoryContainer.scrollHeight;
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
  localStorage.setItem('oldChats', JSON.stringify(chatHistories)); // Update local storage
  populateChatList();  // Refresh the list of old chats
}

function addNewChat() {
  currentChatIndex = chatHistories.length;
  chatHistories.push({ title: "New Chat", messages: [] });

  localStorage.setItem('oldChats', JSON.stringify(chatHistories));
  
  clearFileInput();
  populateChatList();
  renderChatHistory(currentChatIndex);
}

function highlightSelectedChat() {
  // Remove highlighting from all old chats
  document.querySelectorAll('.old-chat-title').forEach(function(chatTitle) {
    chatTitle.classList.remove('highlighted-chat');
  });

  // Add highlighting to the selected chat
  document.querySelectorAll('.old-chat-title')[currentChatIndex].classList.add('highlighted-chat');
}

function populateChatList() {
  var oldChatsString = localStorage.getItem('oldChats');
  chatHistories = oldChatsString ? JSON.parse(oldChatsString) : [];

  if (chatHistories.length === 0) {
    chatHistories = [{ title: "New Chat", messages: [] }];
  }

  var oldChatsContainer = document.getElementById('old_chats_list');
  oldChatsContainer.innerHTML = '<h3>Chat List</h3>';

  chatHistories.forEach(function (chat, index) {
    var chatContainer = document.createElement('div');
    var chatTitle = document.createElement('div');
    chatTitle.classList.add('old-chat-title');
    chatTitle.textContent = chat.title;
    chatTitle.onclick = function () {
      loadChat(index);
    };

    chatContainer.appendChild(chatTitle);
    oldChatsContainer.appendChild(chatContainer);
  });

  // Add management buttons
  var newChatButton = document.createElement('button');
  newChatButton.id = 'reset_button';
  newChatButton.textContent = 'New';
  newChatButton.onclick = addNewChat;

  var deleteChatButton = document.createElement('button');
  deleteChatButton.id = 'delete_button';
  deleteChatButton.textContent = 'Delete';
  deleteChatButton.onclick = deleteCurrentChat;

  var renameChatButton = document.createElement('button');
  renameChatButton.id = 'rename_button';
  renameChatButton.textContent = 'Rename';
  renameChatButton.onclick = renameCurrentChat;

  var clearStorageButton = document.createElement('button');
  clearStorageButton.id = 'clear_storage_button';
  clearStorageButton.textContent = 'Delete All';
  clearStorageButton.onclick = clearLocalStorage;

  oldChatsContainer.appendChild(newChatButton);
  oldChatsContainer.appendChild(renameChatButton);
  oldChatsContainer.appendChild(deleteChatButton);
  oldChatsContainer.appendChild(clearStorageButton);

  highlightSelectedChat();
}

function clearLocalStorage() {
  localStorage.removeItem('oldChats');
  chatHistories = [];
  currentChatIndex = 0;
  populateChatList();
  renderChatHistory();
}

function deleteCurrentChat() {
  if (chatHistories.length <= 1) {
    // If only one chat is left, clear local storage
    clearLocalStorage();
    return;
  }

  chatHistories.splice(currentChatIndex, 1);
  loadChat(currentChatIndex > 0 ? currentChatIndex - 1 : currentChatIndex);

  localStorage.setItem('oldChats', JSON.stringify(chatHistories));
  clearFileInput();
  populateChatList();
}


function loadChat(index) {
  currentChatIndex = index; // Update the index to the newly loaded old chat
  clearFileInput();
  renderChatHistory();
  highlightSelectedChat();
}


function render_codeblocks(input_message) {
  var regex = /```([\s\S]*?)```/g;
  var parts = input_message.split(regex);

  var output_message = parts.map(function (part, index) {
    if (index % 2 === 1) {
      var escapedCode = part.replace(/</g, "<").replace(/>/g, ">");
      return '<pre><code>' + escapedCode + '</code></pre>';
    } else {
      return part.replace(/\n/g, '<br>');
    }
  }).join('');

  return output_message;
}

function renderSingleMessage(message) {
  var roleName = message.role === 'user' ? 'User' : 'Bot';
  var className = message.role === 'user' ? 'user-name' : 'bot-name';
  var messageLineClass = message.role === 'user' ? 'user-message-line' : 'bot-message-line';  // New line
  var renderedContent = render_codeblocks(message.content);
  
  // Include messageLineClass in the surrounding <div> element
  return `<div class="${messageLineClass}"><p><span class="${className}">${roleName}:</span> ${renderedContent}</p></div>`;  // Updated line
}

function clearFileInput() {
  document.getElementById('codeFiles').value = '';
}

function handleFiles() {
  const files = document.getElementById('codeFiles').files;
  if (files.length === 0) {
      alert('Please select files to upload.');
      return;
  }
  // Iterate over each file, read its content, and append it as a user message to chat history
  Array.from(files).forEach(async (file) => {
      const content = await readFileContent(file);
      const formattedContent = formatFileContentForChat(file.name, content);
      const userMessage = { role: 'user', content: formattedContent };
      chatHistories[currentChatIndex].messages.push(userMessage);
      renderChatHistory();
  });
  // Feedback for successful upload
  document.getElementById('uploadButton').textContent = 'Files Uploaded!';
  setTimeout(() => {
      document.getElementById('uploadButton').textContent = 'Upload Files';
  }, 2000);
  clearFileInput();
}

function readFileContent(file) {
  return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (event) => resolve(event.target.result);
      reader.onerror = (error) => reject(error);
      reader.readAsText(file);
  });
}

function escapeHtml(text) {
  var map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

function formatFileContentForChat(filename, content) {
  const escapedContent = escapeHtml(content);
  return `
      <div class="file-content">
          <div class="file-header" onclick="toggleFileContent(this)">
              ${filename}
          </div>
          <div class="file-body" style="display:none;">
              ${escapedContent}
          </div>
      </div>
  `;
}




async function sendMessage() {
  var userMessageElement = document.getElementById('user_message');
  var userMessageContent = userMessageElement.value;
  var userMessage = { role: 'user', content: userMessageContent };
  
  // Add to existing chat
  chatHistories[currentChatIndex].messages.push(userMessage); 

  // Add loading and locked classes
  document.body.classList.add('loading');
  userMessageElement.classList.add('locked');

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_message: chatHistories[currentChatIndex].messages })
    });

    const data = await response.json();

    if (data.bot_message.error) {
      throw new Error(data.bot_message.error);
    }

    const botMessage = { role: 'assistant', content: data.bot_message.content };
    chatHistories[currentChatIndex].messages.push(botMessage);
    localStorage.setItem('oldChats', JSON.stringify(chatHistories));
    renderChatHistory();
    
    // Clear the text field if successful
    userMessageElement.value = '';
  } catch (error) {
    console.error(error);

    // Remove the last user message from the chat history if there's an error
    chatHistories[currentChatIndex].messages.pop();
    renderChatHistory();
  } finally {
    // Remove loading and locked classes
    document.body.classList.remove('loading');
    userMessageElement.classList.remove('locked');
  }
}


