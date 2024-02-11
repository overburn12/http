function resetChatEdits() {
    chatHistories.forEach(history => {
      history.isEditing = false;
      history.editIndex = -1;
    });
  }
  
  function cancelEdit(event) {
    event.stopPropagation();
    renderChatHistory(currentChatIndex);
  }
  
  function editMessage(editIcon, currentChatIndex, messageIndex) {
    var messageContainer = editIcon.parentNode;
    var messageContent = messageContainer.querySelector('.message-content');
    
    // Check if messageContent already has a textarea inside (indicating it's in edit mode)
    if (messageContent.querySelector('textarea')) {
      // Save the edited text
      var editedText = messageContent.querySelector('textarea').value;
      
      // Update the chat history JSON object with the edited text
      chatHistories[currentChatIndex].messages[messageIndex].content = editedText;
      chatHistories[currentChatIndex].isEditing = false;
      
      // save then re-render the chat history
      saveChatList();
      renderChatHistory(currentChatIndex);
       
    } else {
      var switchEditing = false;
      chatHistories.forEach(history => {
        if(history.isEditing && (messageIndex != history.editIndex)){
          switchEditing = true;
        }
      });
  
      if(!switchEditing){ 
        // Create a textarea element to replace the message content
        var textarea = document.createElement('textarea');
        textarea.classList.add('edit-textarea');
        textarea.value = chatHistories[currentChatIndex].messages[messageIndex].content;
        
        // Style the textarea to take up the entire size of the "message-content" div
        textarea.style.width = '98%';
        textarea.style.height = messageContent.offsetHeight + 'px';
        
        // Replace the message content with the textarea
        messageContent.innerHTML = `<div class="cancel-icon" onclick="cancelEdit(event)"><img src="/img/cancel.png"></div>`;
        messageContent.appendChild(textarea);
        textarea.focus();
        chatHistories[currentChatIndex].isEditing = true;
        chatHistories[currentChatIndex].editIndex = messageIndex;
      }
    }
  }