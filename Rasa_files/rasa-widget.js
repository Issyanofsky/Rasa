// rasa-widget.js
(function(){
    // --- Create toggle button ---
    const toggleBtn = document.createElement("button");
    toggleBtn.id = "rasa-toggle-btn";
    toggleBtn.title = "Open chat";
    toggleBtn.textContent = "Chat";
    document.body.appendChild(toggleBtn);

    // --- Styles ---
    const style = document.createElement("style");
    style.textContent = `
        #rasa-toggle-btn {
            position: fixed; bottom: 20px; right: 20px;
            width: 60px; height: 60px; border-radius: 50%;
            background:#0084ff; color:white; border:none;
            font-size:16px; cursor:pointer; z-index:9998;
            box-shadow:0 4px 15px rgba(0,0,0,0.3);
        }
        #rasa-toggle-btn:hover {background:#005bb5;}
        #rasa-widget {
            position: fixed; bottom: 90px; right: 20px;
            width: 350px; max-height:500px; display:none;
            flex-direction: column; font-family:Arial;
            background:#fff; border-radius:12px;
            box-shadow:0 4px 20px rgba(0,0,0,0.3); z-index:9999;
        }
        #rasa-widget header {background:#0084ff; color:white; padding:10px; font-weight:bold; display:flex; justify-content: space-between; align-items:center;}
        #rasa-widget header img {height:30px; width:30px; border-radius:50%; margin-right:8px;}
        #voice-button {
            margin-left: 10px;
            padding: 2px 6px;
            border-radius: 6px;
            border: none;
            background: white;
            color: #0084ff;
            font-weight: bold;
            cursor: pointer;
        }
        #voice-selector {
            display: none;
            margin-left: 10px;
            padding: 2px;
            border-radius:6px; border:none; font-size:0.9em;
        }
        #rasa-widget #chat-box {flex:1; padding:10px; overflow-y:auto; background:#f0f0f0;}
        #rasa-widget .message {margin:5px 0; padding:8px 12px; border-radius:18px; max-width:70%; word-wrap:break-word;}
        #rasa-widget .message.bot {background:#f1f0f0; margin-right:auto; display:flex; align-items:flex-start; flex-wrap:wrap;}
        #rasa-widget .message.user {background:#dcf8c6; margin-left:auto; justify-content:flex-end;}
        #rasa-widget .message.bot img {height:25px; width:25px; border-radius:50%; margin-right:8px;}
        #rasa-widget .bot-image {max-width:70%; border-radius:12px; margin:5px 0;}
        #rasa-widget #controls {display:flex; gap:5px; padding:10px; align-items:center;}
        #rasa-widget #controls input {flex:1; padding:8px; border-radius:12px; border:1px solid #ccc; outline:none;}
        #rasa-widget #controls button {padding:8px 12px; border:none; border-radius:12px; background:#0084ff; color:white; cursor:pointer;}
        #rasa-widget #controls button:hover {background:#005bb5;}
        #rasa-widget #mic-btn svg {width:20px; height:20px; fill:white;}
        #rasa-widget #thinking {font-style:italic; font-size:0.9em; color:#555; margin:5px;}
        /* Rasa buttons as chat bubbles */
        .rasa-button {
            background:#0084ff; color:white; border:none;
            border-radius:12px; padding:6px 12px; margin:3px 3px 3px 0;
            cursor:pointer; font-size:0.9em;
        }
        .rasa-button:hover {background:#005bb5;}
    `;
    document.head.appendChild(style);

    // --- Create widget container ---
    const container = document.createElement("div");
    container.id = "rasa-widget";
    container.innerHTML = `
        <header>
            <div style="display:flex; align-items:center;">
                <img src="bot.png" alt="Bot" />
                Assistant
                <button id="voice-button">...</button>
                <select id="voice-selector" title="Select voice"></select>
            </div>
        </header>
        <div id="chat-box"></div>
        <div id="controls">
            <input type="text" id="user-input" placeholder="Type a message..." />
            <button id="send-btn">Send</button>
            <button id="mic-btn" title="Speak">
                <svg viewBox="0 0 24 24"><path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 14 0h-2zm-5 8a7 7 0 0 0 7-7h-2a5 5 0 0 1-10 0H5a7 7 0 0 0 7 7zm0 2v2h-2v-2h2z"/></svg>
            </button>
        </div>
    `;
    document.body.appendChild(container);

    // --- Toggle widget ---
    toggleBtn.onclick = () => {
        container.style.display = container.style.display === "none" ? "flex" : "none";
    };

    const chatBox = container.querySelector("#chat-box");
    const input = container.querySelector("#user-input");
    const sendBtn = container.querySelector("#send-btn");
    const micBtn = container.querySelector("#mic-btn");
    const voiceSelector = container.querySelector("#voice-selector");
    const voiceButton = container.querySelector("#voice-button");

    const conversationId = "user_" + Math.random().toString(36).substring(2, 10);

    // --- Voice setup ---
    let voices = [];
    function populateVoices() {
        voices = window.speechSynthesis.getVoices();
        voiceSelector.innerHTML = '';
        voices.forEach((v,i)=> {
            const opt = document.createElement("option");
            opt.value = i;
            opt.textContent = `${v.name} (${v.lang})`;
            voiceSelector.appendChild(opt);
        });
        if(!voices.length) return setTimeout(populateVoices,200);
    }
    populateVoices();
    window.speechSynthesis.onvoiceschanged = populateVoices;

    function speak(text){
        if(!voices.length) voices = window.speechSynthesis.getVoices();
        if(!voices.length) return;
        const selected = voices[voiceSelector.value] || voices[0];
        const utter = new SpeechSynthesisUtterance(text);
        utter.voice = selected;
        utter.rate = 1; utter.pitch = 1;
        window.speechSynthesis.speak(utter);
    }

    // --- Voice selector toggle ---
    voiceButton.addEventListener("click", e=>{
        e.stopPropagation();
        voiceSelector.style.display = voiceSelector.style.display === "none" ? "inline-block" : "none";
    });

    voiceSelector.addEventListener("change", ()=>{
        voiceSelector.style.display = "none";
    });

    document.addEventListener("click", (e)=>{
        if(!voiceSelector.contains(e.target) && e.target!==voiceButton){
            voiceSelector.style.display = "none";
        }
    });

    // --- Display messages ---
    function displayMessage(text, sender){
        const div = document.createElement("div");
        div.className = "message " + sender;
        if(sender === "bot"){
            const img = document.createElement("img");
            img.src = "bot.png"; img.alt = "Bot";
            div.appendChild(img);
        }
        const span = document.createElement("span");
        span.textContent = text;
        div.appendChild(span);
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function displayImage(url){
        const imgDiv = document.createElement("div");
        imgDiv.className = "message bot";
        const img = document.createElement("img");
        img.src = url; img.alt = "Bot image"; img.className = "bot-image";
        imgDiv.appendChild(img);
        chatBox.appendChild(imgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // --- Display Rasa buttons ---
    function displayButtons(buttons){
        const btnDiv = document.createElement("div");
        btnDiv.className = "message bot";
        buttons.forEach(b=>{
            const btn = document.createElement("button");
            btn.className = "rasa-button";
            btn.textContent = b.title;
            btn.onclick = ()=> sendMessage(b.payload);
            btnDiv.appendChild(btn);
        });
        chatBox.appendChild(btnDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // --- Send message ---
    async function sendMessage(msg=null){
        if(msg===null){
            msg = input.value.trim();
            if(!msg) return;
        }
        displayMessage(msg,"user");
        input.value=""; input.disabled=true; sendBtn.disabled=true; micBtn.disabled=true;

        const thinking = document.createElement("div");
        thinking.id="thinking"; thinking.textContent="Bot is thinking...";
        chatBox.appendChild(thinking);
        chatBox.scrollTop = chatBox.scrollHeight;

        try{
            const res = await fetch("http://77.125.130.211:5005/webhooks/rest/webhook",{
                method:"POST",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({sender:conversationId, message:msg})
            });
            const data = await res.json();
            thinking.remove();
            data.forEach(m=>{
                if(m.text){ displayMessage(m.text,"bot"); speak(m.text); }
                if(m.image){ displayImage(m.image); }
                if(m.buttons){ displayButtons(m.buttons); }
            });
        }catch(err){
            thinking.remove();
            displayMessage("Error connecting to Rasa","bot");
            speak("Error connecting to Rasa");
        }

        input.disabled=false; sendBtn.disabled=false; micBtn.disabled=false; input.focus();
    }

    // --- Voice input ---
    function startListening(){
        if(!('webkitSpeechRecognition' in window)){
            alert("Speech recognition not supported. Use Chrome/Edge.");
            return;
        }
        const rec = new webkitSpeechRecognition();
        rec.lang='en-US';
        rec.interimResults=false;
        rec.maxAlternatives=1;
        rec.onstart = ()=>{ micBtn.querySelector("svg").style.fill="#00ff00"; };
        rec.onresult = e => sendMessage(e.results[0][0].transcript);
        rec.onerror = e => { displayMessage("Could not hear you","bot"); micBtn.querySelector("svg").style.fill="white"; input.focus(); };
        rec.onend = ()=>{ micBtn.querySelector("svg").style.fill="white"; };
        rec.start();
    }

    sendBtn.onclick = ()=>sendMessage();
    input.addEventListener("keydown", e=>{ if(e.key==="Enter") sendMessage(); });
    micBtn.onclick = ()=>startListening();

    // --- Initial greeting ---
    displayMessage("Hi, I am your assistant. You can type or speak to me.","bot");
    speak("Hi, I am your assistant. You can type or speak to me.");
})();
