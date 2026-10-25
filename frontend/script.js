// প্রতিটি ব্রাউজার সেশনের জন্য ইউনিক আইডি
const sessionId = "web_" + Math.random().toString(36).substring(2, 10);

const chatForm = document.getElementById("chatForm");
const userInput = document.getElementById("userInput");
const chatBody = document.getElementById("chatBody");
const sendBtn = document.getElementById("sendBtn");

// মেসেজ UI-তে যোগ করার ফাংশন
function addMessage(text, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender === "user" ? "user-message" : "bot-message");
    
    const bubble = document.createElement("div");
    bubble.classList.add("bubble");
    bubble.textContent = text;
    
    messageDiv.appendChild(bubble);
    chatBody.appendChild(messageDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
    
    return messageDiv;
}

// টাইপিং ইন্ডিকেটর দেখানো/মুছে ফেলা
function showTyping() {
    const typingDiv = document.createElement("div");
    typingDiv.classList.add("message", "bot-message");
    typingDiv.id = "typingIndicator";
    typingDiv.innerHTML = `
        <div class="bubble typing">
            <span></span><span></span><span></span>
        </div>
    `;
    chatBody.appendChild(typingDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function removeTyping() {
    const typing = document.getElementById("typingIndicator");
    if (typing) typing.remove();
}

// ফর্ম সাবমিট হ্যান্ডলার
chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const message = userInput.value.trim();
    if (!message) return;
    
    // ইউজারের মেসেজ দেখাও
    addMessage(message, "user");
    userInput.value = "";
    
    // বাটন ডিসেবল + টাইপিং ইন্ডিকেটর
    sendBtn.disabled = true;
    showTyping();
    
    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: sessionId,
                message: message
            })
        });
        
        const data = await response.json();
        removeTyping();
        
        if (response.ok) {
            addMessage(data.reply, "bot");
        } else {
            // ৫০৩ বা অন্য এরর হলে
            addMessage(data.detail || "Something went wrong. Please try again.", "bot");
        }
    } catch (error) {
        removeTyping();
        addMessage("Network error. Please check your connection.", "bot");
        console.error(error);
    } finally {
        sendBtn.disabled = false;
        userInput.focus();
    }
});