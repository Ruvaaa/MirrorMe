const input = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const chatbox = document.getElementById('chatbox');
const moodImage = document.getElementById('mood-image');

sendBtn.addEventListener('click', sendMessage);

input.addEventListener('keypress', function (e) {
  if (e.key === 'Enter') {
    sendMessage();
  }
});

function sendMessage() {
  const message = input.value.trim();
  if (message === '') return;

  appendMessage('You', message, 'user');

  input.value = '';

  fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: message })
  })
    .then(response => response.json())
    .then(data => {
      appendMessage('MirrorMe', data.response, 'bot');

      // 🎨 Update the mood board image
      if (moodImage) {
        moodImage.src = data.image_path;
      }
    })
    .catch(error => {
      console.error("Error fetching chatbot response:", error);
      appendMessage('MirrorMe', "Oops, something went wrong!", 'bot');
    });
}

function appendMessage(sender, message, type) {
  const msgEl = document.createElement('div');
  msgEl.classList.add('message', type);
  msgEl.innerHTML = `<strong>${sender}:</strong> ${message}`;
  chatbox.appendChild(msgEl);
  chatbox.scrollTop = chatbox.scrollHeight;
}
