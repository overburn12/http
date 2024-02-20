function toggleFileContent(headerElement) {
    const fileBody = headerElement.parentNode.querySelector('.file-body');
    if (fileBody.style.display === 'none' || fileBody.style.display === '') {
        fileBody.style.display = 'block';
    } else {
        fileBody.style.display = 'none';
    }
}
  
function handleFiles() {
    const files = document.getElementById('codeFiles').files;
    if (files.length === 0) {
        alert('Please select files to upload.');
        return;
    }
    // Iterate over each file, validate its size, read its content, and append it as a user message to chat history
    Array.from(files).forEach(async (file) => {
        const fileSize = file.size;
        const fileSizeInKB = fileSize / 1024; // convert to KB
        
        if (fileSizeInKB > 20) { // limit file size to 20KB
          alert('File size exceeds the limit (20KB).');
          clearFileInput();
          return;
        }
        
        const content = await readFileContent(file);
        const formattedContent = formatFileContentForChat(file.name, content);
        const userMessage = { role: 'user', content: formattedContent };
        chatHistories[currentChatIndex].messages.push(userMessage);
        saveChatList();
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
  
function clearFileInput() {
    document.getElementById('codeFiles').value = '';
}
  