import os
from flask import Flask, request, jsonify, render_template_string
import agent

app = Flask(__name__)

HTML_VIEW = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AERY</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .chat-bg {
            background-color: #0b0f19;
            background-image: radial-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px);
            background-size: 24px 24px;
        }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }
    </style>
</head>
<body class="chat-bg text-slate-200 font-sans h-[100dvh] flex flex-col overflow-hidden relative select-none">

    <!-- Wallpaper Signature -->
    <div class="pointer-events-none fixed inset-0 flex items-center justify-center z-0">
        <span class="tracking-[0.25em] font-mono text-slate-500/20 select-none">
            <span class="text-xs lowercase">developer by, crimson</span><span class="text-base font-bold">O</span><span class="text-xs lowercase">moon</span>
        </span>
    </div>

    <!-- Top Navigation -->
    <header class="bg-slate-900/60 backdrop-blur-md px-6 py-4 flex justify-between items-center z-10 border-b border-slate-800/80 shrink-0">
        <div class="flex items-center space-x-2.5">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span class="text-sm font-semibold tracking-wider text-slate-100 font-mono">AERY</span>
        </div>

        <div class="flex items-center space-x-2">
            <span class="text-xs font-mono text-slate-400">NET</span>
            <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" id="netSwitch" class="sr-only peer" checked onchange="toggleNet(this.checked)">
                <div class="w-8 h-4 bg-slate-800 border border-slate-700 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-400 after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-slate-700 peer-checked:after:bg-slate-100"></div>
            </label>
        </div>
    </header>

    <!-- Chat Flow -->
    <main id="chatFlow" class="flex-1 p-4 md:p-6 overflow-y-auto space-y-4 z-10">
        <div class="flex justify-center w-full">
            <span class="text-slate-400 text-xs px-3 py-1 rounded-full bg-slate-900/40 border border-slate-800/50 backdrop-blur-sm">
                Session established with AERY
            </span>
        </div>
    </main>

    <!-- Bottom Command Deck -->
    <footer class="p-4 bg-slate-900/60 backdrop-blur-md border-t border-slate-800/80 z-10 shrink-0">
        <form onsubmit="handleSend(event)" class="max-w-4xl mx-auto flex space-x-2">
            <input 
                type="text" 
                id="userInput" 
                placeholder="Ask AERY anything..." 
                autocomplete="off"
                class="flex-1 bg-slate-800/60 border border-slate-700/60 text-slate-100 text-sm rounded-lg px-4 py-2.5 focus:outline-none focus:border-slate-500 transition placeholder-slate-500"
            >
            <button 
                type="submit"
                id="sendBtn"
                class="bg-slate-100 hover:bg-white text-slate-900 px-5 py-2.5 rounded-lg text-sm font-medium transition shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
                Send
            </button>
        </form>
    </footer>

    <script>
        const chatFlow = document.getElementById('chatFlow');
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');

        function appendMessage(sender, text, isAi = false) {
            const row = document.createElement('div');
            row.className = `flex flex-col ${isAi ? 'items-start mr-auto' : 'items-end ml-auto'} max-w-[85%] md:max-w-[70%]`;
            
            const bubble = document.createElement('div');
            bubble.className = isAi 
                ? 'rounded-xl px-4 py-2.5 bg-slate-800/70 border border-slate-700/50 text-slate-200 text-sm shadow-sm leading-relaxed whitespace-pre-wrap'
                : 'rounded-xl px-4 py-2.5 bg-slate-200 text-slate-900 text-sm font-medium shadow-sm leading-relaxed whitespace-pre-wrap';
            
            bubble.textContent = text;
            row.appendChild(bubble);
            chatFlow.appendChild(row);
            chatFlow.scrollTop = chatFlow.scrollHeight;
        }

        async function handleSend(e) {
            e.preventDefault();
            const text = userInput.value.trim();
            if (!text) return;

            userInput.value = '';
            userInput.disabled = true;
            sendBtn.disabled = true;

            appendMessage('You', text, false);

            const status = document.createElement('div');
            status.className = 'text-xs text-slate-500 font-mono pl-1';
            status.textContent = 'AERY is thinking...';
            chatFlow.appendChild(status);
            chatFlow.scrollTop = chatFlow.scrollHeight;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const payload = await res.json();
                status.remove();
                appendMessage('AERY', payload.reply || 'No response returned.', true);
            } catch (err) {
                status.remove();
                appendMessage('System', 'Failed to reach agent engine.', true);
            } finally {
                userInput.disabled = false;
                sendBtn.disabled = false;
                userInput.focus();
            }
        }

        async function toggleNet(enabled) {
            await fetch('/api/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled })
            });
        }
    </script>
</body>
</html>"""


@app.route('/')
def home():
    return render_template_string(HTML_VIEW)


@app.route('/api/toggle', methods=['POST'])
def toggle():
    state = request.json.get('enabled', True)
    if hasattr(agent, 'set_internet_toggle'):
        agent.set_internet_toggle(state)
    return jsonify({"status": "ok"})


@app.route('/api/chat', methods=['POST'])
def chat():
    prompt = request.json.get('message', '').strip()
    if not prompt:
        return jsonify({"reply": ""})

    # Dispatch to available agent entrypoint
    chat_handler = getattr(agent, 'chat_with_aery', 
                   getattr(agent, 'chat_with_alicia', 
                   getattr(agent, 'chat', None)))

    if not chat_handler:
        return jsonify({"reply": "Core engine handler not found in agent.py."})

    try:
        reply = chat_handler(prompt)
    except Exception as e:
        reply = f"Engine error: {e}"

    return jsonify({"reply": reply})


if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    print(f"[+] UI running on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
