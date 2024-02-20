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

function prepareChatHistory(chatHistory) {
  const preparedChatHistory = { ...chatHistory };

  preparedChatHistory.messages = preparedChatHistory.messages.map(message => {
    if (message.role === 'assistant') {
      const { model, ...rest } = message;
      return rest;
    }
    return message;
  });

  return preparedChatHistory;
}

async function fetchChatMessages(chatHistory, selectedModel) {
  const response = await fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_message: chatHistory, model: selectedModel })
  });
  return response.body.getReader();
}

async function processStream(reader, callback) {
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += new TextDecoder("utf-8").decode(value);
    let endOfObjectIndex;
    while ((endOfObjectIndex = buffer.indexOf("}}")) !== -1) {
      const objectStr = buffer.slice(0, endOfObjectIndex + 2);
      buffer = buffer.slice(endOfObjectIndex + 2);
      try {
        const jsonMessage = JSON.parse(objectStr);
        callback(jsonMessage); // Process each JSON object
      } catch (e) {
        console.error("Error parsing JSON: ", e);
      }
    }
  }
}

function handleUIUpdate(startLoading = true) {
  const userMessageElement = document.getElementById('user_message');
  if (startLoading) {
    document.body.classList.add('loading');
    userMessageElement.classList.add('locked');
  } else {
    document.body.classList.remove('loading');
    userMessageElement.classList.remove('locked');
    userMessageElement.value = ''; // Clear the text field if successful
  }
}

function updateChatHistory(jsonMessage) {
  if (jsonMessage.error) {
    console.error("Bot Response Error:", jsonMessage.error);
    return;
  }

  const botMessageContent = jsonMessage.bot_message.choices[0].delta.content;
  const lastElementIndex = chatHistories[currentChatIndex].messages.length - 1;

  if (botMessageContent !== undefined) {
    chatHistories[currentChatIndex].messages[lastElementIndex].content += botMessageContent;
  }

  const finishReason = jsonMessage.bot_message.choices[0].finish_reason;
  if (finishReason) {
    saveChatList();
  }
}

async function updateChatTitle(selectedModel) {
  const newTitle = await generateTitle(chatHistories[currentChatIndex], selectedModel);
  chatHistories[currentChatIndex].title = newTitle;
  saveChatList(); 
  populateChatList(); 
  renderChatHistory(); 
}

async function sendMessage() {
  const userMessageElement = document.getElementById('user_message');
  const userMessageContent = userMessageElement.value;
  const selectedModel = document.getElementById('chat-model').value;
  const userMessage = { role: 'user', content: userMessageContent };
  var tempBotMessage = { role: 'assistant', model: selectedModel, content: '' };
  const isNewChat = chatHistories[currentChatIndex].messages.length === 0;

  chatHistories[currentChatIndex].messages.push(userMessage);
  chatHistories[currentChatIndex].messages.push(tempBotMessage);
  handleUIUpdate(); // Start loading UI

  const tempChatHistory = prepareChatHistory(chatHistories[currentChatIndex]);

  try {
    const reader = await fetchChatMessages(tempChatHistory.messages, selectedModel);
    await processStream(reader, jsonMessage => {
      updateChatHistory(jsonMessage);
      renderChatHistory();
    });
  } catch (error) {
    console.error(error);
    chatHistories[currentChatIndex].messages.pop(); // Remove the last user message on error
    renderChatHistory();
  } finally {
    handleUIUpdate(false); // Stop loading UI
  }

  if (isNewChat) {
    await updateChatTitle(selectedModel);
  }
}