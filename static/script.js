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
  init_chat_list();
  loadModels(); // Load the API models when the page loads
});

document.getElementById("menu_icon").addEventListener("click", function() {
  var hiddenElement = document.getElementById("chats_list");
  if (hiddenElement.style.display === "none") {
    hiddenElement.style.display = "block";
  } else {
    hiddenElement.style.display = "none";
  }
});

function renderChatHistory() {
  resetChatEdits();

  var chat_title = document.getElementById('chat_title_inner');
  chat_title.innerHTML = '</div><center><h3>' + chatHistories[currentChatIndex].title + '</h3></center>';

  var chatHistoryContainer = document.getElementById('chat_history');
  let htmlString = '';

  if (currentChatIndex !== null && chatHistories[currentChatIndex].messages) {
    chatHistories[currentChatIndex].messages.forEach(function (message, messageIndex) {
      var renderedMessage = renderSingleMessage(message, currentChatIndex, messageIndex);
      htmlString += renderedMessage;
    });
  }

  chatHistoryContainer.innerHTML = htmlString;
  chatHistoryContainer.scrollTop = chatHistoryContainer.scrollHeight;

  Prism.highlightAll();
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
  chatIcon.src = '/img/chat-icon.png';
  chatIcon.classList.add('list-icon');

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
      var escapedCode = escapeHtml(content);
      var languageClass = "language-" + title.toLowerCase();
      
      return `<div class="codeblock-container"><div class="codeblock-title">` + title + `</div><pre><code class="` + languageClass + `"><p>` + escapedCode + `</p></code></pre></div>`;
    } else {
      if (part.trim().startsWith('<div class="file-content">')) {
        return part;
      } else {
        var escapedCode = escapeHtml(part);
        return escapedCode.replace(/\n/g, '<br>');
      }
    }
  }).join('');

  return output_message;
}

function renderSingleMessage(message, currentChatIndex, messageIndex) {
  var renderedContent = render_codeblocks(message.content);
  var isUser = message.role === 'user';

  return `
      <div class="${isUser ? 'user' : 'bot'}-message-line">
          ${isUser ? '' : '<div class="bot-model">'}
            <div class="chat-icon">
              <img src='/img/${isUser ? 'overburn' : 'gpt'}.png'>
            </div>
            ${isUser ? '' : `<center>${message.model}</center>`}
          ${isUser ? '' : '</div>'}
          <div class="message-container">
              <div class="edit-icon" onclick="editMessage(this, ${currentChatIndex},${messageIndex})">
                  <img src="/img/edit.png">
              </div>
              <div class="message-content">${renderedContent}</div>
          </div>
      </div>`;
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
