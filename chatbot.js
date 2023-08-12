const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');

userInput.addEventListener('keyup', function (event) {
    if (event.key === 'Enter') {
        sendMessage(userInput.value);
    }
});

function sendMessage(message) {
    const userMessage = `<div class="message user">${message}</div>`;
    const botMessage = `<div class="message bot">Loading...</div>`;
    chatBox.innerHTML += userMessage;
    chatBox.innerHTML += botMessage;

    // Simulate delay before receiving bot response
    setTimeout(() => {
        fetch('/get_response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 'user_input': message }),
        })
        .then(response => response.json())
        .then(data => {
            const botResponse = `<div class="message bot">${data.bot_response}</div>`;
            chatBox.innerHTML = chatBox.innerHTML.replace('Loading...', botResponse);
            chatBox.scrollTop = chatBox.scrollHeight;
        });
    }, 1000);

    userInput.value = '';
}
