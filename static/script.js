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

function saveChatList(){
  localStorage.setItem('oldChats', JSON.stringify(chatHistories)); 
}

function renderChatHistory() {
  var chat_title = document.getElementById('chat_title');
  chat_title.innerHTML = '<center><h3>' + chatHistories[currentChatIndex].title + '</h3></center>';

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

  var oldChatsContainer = document.getElementById('chats_list');
  oldChatsContainer.innerHTML = '<center><h3>OpenAI Chat</h3></center>';

  chatHistories.forEach(function (chat, index) {
    var chatContainer = document.createElement('div');
    var chatTitle = document.createElement('div');
    chatTitle.classList.add('old-chat-title');
    chatTitle.textContent = '\u2022 ' + chat.title; // Add the bullet point before the chat title
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

  var duplicateChatButton = document.createElement('button');
  duplicateChatButton.id = 'copy_button'; // using the same id for the button for styling purposes
  duplicateChatButton.textContent = 'Copy';
  duplicateChatButton.onclick = duplicateChat;

  oldChatsContainer.appendChild(newChatButton);
  oldChatsContainer.appendChild(renameChatButton);
  oldChatsContainer.appendChild(duplicateChatButton);
  oldChatsContainer.appendChild(deleteChatButton);
  oldChatsContainer.appendChild(clearStorageButton);

  //oldChatsContainer.innerHTML += '<img src="favicon.ico"><a href="/view_count">Connection Counts</a><br>'; 
  //oldChatsContainer.innerHTML += '<img src="favicon.ico"><a href="/update">Update Server</a><br>';
  //oldChatsContainer.innerHTML += '<img src="favicon.ico"><a href="/about">About</a>';

  highlightSelectedChat();
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

function render_codeblocks(input_message) {
  var regex = /```([\s\S]*?)```/g;
  var parts = input_message.split(regex);

  var output_message = parts.map(function (part, index) {
    if (index % 2 === 1) {
      // Split the code into title and content
      var codeParts = part.split('\n');
      var title = codeParts[0].trim();
      var content = codeParts.slice(1).join('\n').trim();

      // Escape the content inside the code blocks
      var escapedCode = escapeHtml(content);

      // Create the title and code blocks with appropriate styling
      return '<pre><code><div class="codeblock-title">' + title + '</div><div class="code">' + escapedCode + '</div></code></pre>';
    } else {
      if (part.trim().startsWith('<div class="file-content">')) {
        // Return the original content without escaping, file content has already been escaped when it was attached
        return part;
      } else {
        // Escape the other content
        var escapedCode = escapeHtml(part);
        return escapedCode.replace(/\n/g, '<br>');
      }
    }
  }).join('');

  return output_message;
}


function renderSingleMessage(message) {
  var roleName = message.role === 'user' ? 'overburn.png' : 'gpt.png';
  var className = message.role === 'user' ? 'chat-icon' : 'chat-icon';
  var messageLineClass = message.role === 'user' ? 'user-message-line' : 'bot-message-line';
  var renderedContent = render_codeblocks(message.content);

  return `
    <div class="${messageLineClass}">
      <div class="${className}"><img src='${roleName}'></div>
      <div class="message-content">${renderedContent}</div>
    </div>
  `;
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
      "'": '&#039;',
      '`': '&#96;'
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

async function generateTitle(chat_history) {
  var temp_copy = JSON.parse(JSON.stringify(chat_history));
  var userMessage = { role: 'user', content: 'generate a 1-3 word phrase for the title of this chat' };
  temp_copy.messages.push(userMessage);

  try {
    // Send an additional request to get a summary for the chat title
    const summaryResponse = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_message: temp_copy.messages })
    });

    const summaryData = await summaryResponse.json();

    if (summaryData.bot_message.error) {
      throw new Error(summaryData.bot_message.error);
    }

    const botMessage = { role: 'assistant', content: summaryData.bot_message.content };
    return botMessage.content; // Return the content directly

  } catch (error) {
    // ... (existing error handling code)
  }
  return "Error";
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

  var isNewChat = chatHistories[currentChatIndex].messages.length === 1; 

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
    saveChatList();
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
  
  if (isNewChat) {
    var newTitle = await generateTitle(chatHistories[currentChatIndex]);
    chatHistories[currentChatIndex].title = newTitle.replace(/"/g, "");
    saveChatList();
    populateChatList();
  }
  
}