var chatHistories = [];
var currentChatIndex = null;
var currentModels = null;

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
  init_chat_list();
  loadModels(); // Load the API models when the page loads
});

async function loadModels() {
  try {
    const response = await fetch('/models'); // Fetch the models from the Flask route

    if (response.ok) {
      const models = await response.text(); // Get the list of models as text

      // Split the models by line breaks and populate the drop-down box options
      const modelOptions = models.trim().split('<br>');
      const dropdown = document.getElementById('chat-model');
      dropdown.innerHTML = '';

      modelOptions.forEach(function (option) {
        const optionElement = document.createElement('option');
        optionElement.text = option;
        optionElement.value = option;

        dropdown.add(optionElement);
      });
    } else {
      console.error('Error fetching API models: ' + response.status);
    }
  } catch (error) {
    console.error('Error fetching API models:', error);
  }
}

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
  chat_title.innerHTML = '<div class="chat-icon"></div><center><h3>' + chatHistories[currentChatIndex].title + '</h3></center>';

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
  document.querySelectorAll('.chat-title').forEach(function(chatTitle) {
    chatTitle.classList.remove('highlighted-chat');
  });

  // Add highlighting to the selected chat
  document.querySelectorAll('.chat-title')[currentChatIndex].classList.add('highlighted-chat');
}

function populateChatList() {
  var oldChatsString = localStorage.getItem('oldChats');
  chatHistories = oldChatsString ? JSON.parse(oldChatsString) : [];

  if (chatHistories.length === 0) {
    chatHistories = [{ title: "New Chat", messages: [] }];
  }

  var ChatsListContainer = document.getElementById('list_container');
  ChatsListContainer.innerHTML = '';

  var chatIcon = document.createElement('img');
  chatIcon.src = 'chat-icon.png';
  chatIcon.classList.add('list-icon');
/*
  var deleteIcon = document.createElement('img');
  deleteIcon.src = 'delete-icon.png';
  deleteIcon.classList.add('list-icon');
  deleteIcon.onclick = function () {
    deleteCurrentChat();
  };
  
  var renameIcon = document.createElement('img');
  renameIcon.src = 'rename-icon.png';
  renameIcon.classList.add('list-icon');
  renameIcon.onclick = function () {
    renameCurrentChat();
  };
*/
  chatHistories.forEach(function (chat, index) {
    var chatContainer = document.createElement('div');
    var chatTitle = document.createElement('div');
    chatTitle.classList.add('chat-title');
    chatTitle.appendChild(chatIcon.cloneNode(true));
    chatTitle.appendChild(document.createTextNode(chat.title));
    chatTitle.onclick = function () {
      loadChat(index);
    };

    chatContainer.appendChild(chatTitle);
    ChatsListContainer.appendChild(chatContainer);
  });
 
  /*init_chat_list();*/
  highlightSelectedChat();
}

function init_chat_list(){
  var chat_list_head = document.getElementById('list_head');
  chat_list_head.innerHTML = '<select id="chat-model" name="chat-model"></select>';
  loadModels();
  
  //add management buttons
  var chat_list_end = document.getElementById('list_end');
  chat_list_end.innerHTML = `
    <button id="reset_button" onclick="addNewChat()">New</button>
    <button id="rename_button" onclick="renameCurrentChat()">Rename</button>
    <button id="copy_button" onclick="duplicateChat()">Copy</button>
    <br>
    <button id="delete_button" onclick="deleteCurrentChat()">Delete</button>
    <button id="clear_storage_button" onclick="clearLocalStorage()">Delete All</button>
    <br><br>
  `;
  
  //add page links  
  chat_list_end.innerHTML += `
    <a href="/view_count">Counts</a><br>
    <a href="/update">Update</a><br>
    <a href="/about">About</a><br>
  `;
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
    const selectedModel = document.getElementById('chat-model').value;
    const summaryResponse = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_message: temp_copy.messages, model: selectedModel })
    });

    const summaryData = await summaryResponse.json();

    if (summaryData.bot_message.error) {
      throw new Error(summaryData.bot_message.error);
    }

    const botMessage = { role: 'assistant', content: summaryData.bot_message.content.replace(/["']/g, "") };
    const spaceCount = (botMessage.match(/ /g) || []).length;

    if (spaceCount > 4) {
      return "too long :(";
    } else {
      return botMessage.content;
    }

  } catch (error) {
    return "error";
  }
}


let tempBotMessage = { role: 'assistant', content: '' };
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
    const selectedModel = document.getElementById('chat-model').value;
    
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_message: chatHistories[currentChatIndex].messages, model: selectedModel })
    });

    // Assume the response body is a ReadableStream
    const reader = response.body.getReader();
    
    // Start reading the stream
    let buffer = "";

    //add a blank bot response to the end of the chat history, this is where the api stream will be saved
    chatHistories[currentChatIndex].messages.push(tempBotMessage);
    const lastElement = chatHistories[currentChatIndex].messages.length - 1; //the index of the specific message we are directing the api data to
    const responseIndex = currentChatIndex; //incase currentChatIndex changes during the api stream

    renderChatHistory();

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;

      buffer += new TextDecoder("utf-8").decode(value);

      // Try to find the complete JSON objects in the buffer
      while (true) {
        const endOfObjectIndex = buffer.indexOf("}}");
        if (endOfObjectIndex === -1) {
          break;
        }

        const objectStr = buffer.slice(0, endOfObjectIndex + 2);
        buffer = buffer.slice(endOfObjectIndex + 2);    
        try {
          const jsonMessage = JSON.parse(objectStr);
          const finishReason = jsonMessage.bot_message.choices[0].finish_reason;
          
          if (finishReason) {
            // This is the last message
            saveChatList(); //save the chat after the bot response is finished
            tempBotMessage = { role: 'assistant', content: '' };
          } else {
            // Append to the temporary bot message
            const chunk_msg = jsonMessage.bot_message.choices[0].delta.content;
            if (chunk_msg !== undefined) {
              chatHistories[responseIndex].messages[lastElement].content += chunk_msg;
            }
          }
          // Always re-render to show updates
          renderChatHistory();
        } catch (e) {
          console.error("Error parsing JSON: ", e);
        }
      }
    }
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
  /*if (isNewChat) {
    var newTitle = await generateTitle(chatHistories[currentChatIndex]);
    chatHistories[currentChatIndex].title = newTitle.replace(/&quot;/g, '');
    saveChatList();
    populateChatList();
  }*/
}

  
