async function loadModels() {
    try {
      const response = await fetch('/models'); // Fetch the models from the Flask route
  
      if (response.ok) {
        const models = await response.json(); // Parse the response as JSON
  
        // Populate the drop-down box options with the models
        const dropdown = document.getElementById('chat-model');
        dropdown.innerHTML = '';
  
        models.forEach(function (model) {
          const optionElement = document.createElement('option');
          optionElement.text = model;
          optionElement.value = model;
  
          dropdown.add(optionElement);
        });
      } else {
        console.error('Error fetching API models: ' + response.status);
      }
    } catch (error) {
      console.error('Error fetching API models:', error);
    }
}

async function generateTitle(chat_history, selectedModel) {
    var temp_copy = JSON.parse(JSON.stringify(chat_history));
  
    // Modify the temp copy by removing model elements
    temp_copy.messages = chat_history.messages.map(message => {
      if (message.role === 'assistant') {
        const { model, ...rest } = message; // Destructure the message object 
        return rest; // Return the modified message object without the model property
      }
      return message;
    });
    
    var userMessage = { role: 'user', content: 'generate a 1-3 word phrase for the title of this chat' };
    temp_copy.messages.push(userMessage);
  
    try {
      const summaryResponse = await fetch('/title', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_message: temp_copy.messages, model: selectedModel })
      });
       const summaryData = await summaryResponse.json();
  
      if (summaryData.bot_message.error) {
        throw new Error(summaryData.bot_message.error);
      }
  
      var botMessage = { role: 'assistant', content: summaryData.bot_message.content.replace(/["\\]/g, "") };
      var spaceCount = (botMessage.content.match(/ /g) || []).length;
      if (spaceCount > 7) {
        return "too long :(";
      } else {
        return botMessage.content;
      }
  
    } catch (error) {
      return "error :(";
    }
}
  
  async function sendMessage() {
    var tempBotMessage = { role: 'assistant', model: '', content: '' };
    var userMessageElement = document.getElementById('user_message');
    var userMessageContent = userMessageElement.value;
    var userMessage = { role: 'user', content: userMessageContent };
    var isNewChat = chatHistories[currentChatIndex].messages.length === 0;
    var selectedModel = document.getElementById('chat-model').value;
    
    // Add to existing chat
    chatHistories[currentChatIndex].messages.push(userMessage); 
  
    // Add loading and locked classes
    document.body.classList.add('loading');
    userMessageElement.classList.add('locked');
  
    // Create a temporary copy of the chat history
    const tempChatHistory = Object.assign({}, chatHistories[currentChatIndex]);
  
    // Modify the temp copy by removing model elements
    tempChatHistory.messages = tempChatHistory.messages.map(message => {
      if (message.role === 'assistant') {
        const { model, ...rest } = message; // Destructure the message object 
        return rest; // Return the modified message object without the model property
      }
      return message;
    });
  
    try {
      
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_message: tempChatHistory.messages, model: selectedModel })
      });
  
      // Assume the response body is a ReadableStream
      const reader = response.body.getReader();
      
      // Start reading the stream
      let buffer = "";
  
      //add a blank bot response to the end of the chat history, this is where the api stream will be saved
      tempBotMessage.model = selectedModel;
      chatHistories[currentChatIndex].messages.push(tempBotMessage);
      const lastElement = chatHistories[currentChatIndex].messages.length - 1; //the index of the specific message we are directing the api data to
      const responseIndex = currentChatIndex; //in case currentChatIndex changes during the api stream
  
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
            if (jsonMessage.error) {
              throw new Error("Bot Response Error");
            }
            const finishReason = jsonMessage.bot_message.choices[0].finish_reason;
            
            if (finishReason) {
              saveChatList(); //save the chat after the bot response is finished
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
    if (isNewChat) {
      var newTitle = await generateTitle(chatHistories[currentChatIndex], selectedModel);
      chatHistories[currentChatIndex].title = newTitle;
      saveChatList();
      populateChatList();
      renderChatHistory();
    }
}
  
    