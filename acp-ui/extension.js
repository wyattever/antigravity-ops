const vscode = require('vscode');
const axios = require('axios');

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    // Audit: Prove activation in the notification area
    vscode.window.showInformationMessage('[ACP] Internal Radar v2.0 Activated');
    
    const provider = new ACPViewProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(ACPViewProvider.viewType, provider)
    );
}

class ACPViewProvider {
    static viewType = 'acp.sidePanel';

    constructor(extensionUri) {
        this._extensionUri = extensionUri;
    }

    resolveWebviewView(webviewView, context, _token) {
        this._view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };
        
        // Handshake Delay: Give Docker/LiteLLM time to finish boot/migrations
        setTimeout(() => {
            webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);
        }, 2000);

        webviewView.webview.onDidReceiveMessage(async (data) => {
            if (data.command === 'sendChat') {
                // HARD AUDIT: Show a popup to prove this function is executing
                vscode.window.showInformationMessage(`[ACP] Intercepting: ${data.text.substring(0, 15)}...`);
                await this._handleChat(data.text);
            }
        });
    }

    async _handleChat(text) {
        if (!this._view) return;

        this._view.webview.postMessage({ command: 'addUserMessage', text });

        try {
            // FORCE NUMERIC IP AND PORT
            const gatewayUrl = "http://127.0.0.1:8000/v1/chat/completions";
            
            // Console logs for Output window
            console.log(`[ACP-UI] >>> SENDING TO: ${gatewayUrl}`);

            const response = await axios.post(gatewayUrl, {
                model: "antigravity-smart", // Using the model name found in your curl test
                messages: [{ role: "user", content: text }]
            }, {
                headers: { 
                    'Authorization': 'Bearer sk-1234',
                    'X-Trace-ID': 'LEXC-VERIFY-999',
                    'Content-Type': 'application/json'
                },
                timeout: 8000 
            });

            console.log(`[ACP-UI] <<< RECEIVED: ${response.status}`);
            const reply = response.data.choices[0].message.content;
            this._view.webview.postMessage({ command: 'addAgentMessage', text: reply });

        } catch (error) {
            const errorMsg = error.response ? `Gateway ${error.response.status}` : error.message;
            console.error(`[ACP-UI] !!! ERROR: ${errorMsg}`);
            
            // Show error in a popup so the user can't miss it
            vscode.window.showErrorMessage(`[ACP] Routing Failed: ${errorMsg}`);
            
            this._view.webview.postMessage({ 
                command: 'addAgentMessage', 
                text: `ROUTING ERROR: ${errorMsg}. Please check Output > Extension Host logs.` 
            });
        }
    }

    _getHtmlForWebview(webview) {
        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <style>
                    :root {
                        --md-sys-color-primary: #0B57D0;
                        --md-sys-color-background: #F8F9FA;
                        --md-sys-color-surface: #FFFFFF;
                        --md-sys-color-on-surface: #1F1F1F;
                        --md-sys-color-outline: #E0E0E0;
                    }
                    body { font-family: sans-serif; background: var(--md-sys-color-background); color: var(--md-sys-color-on-surface); display: flex; flex-direction: column; height: 100vh; margin: 0; overflow: hidden; }
                    #header { padding: 16px; background: #FFF; border-bottom: 2px solid var(--md-sys-color-primary); display: flex; justify-content: space-between; }
                    #header span { font-size: 10px; font-weight: 900; letter-spacing: 0.1em; color: var(--md-sys-color-primary); }
                    #messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
                    .msg { font-size: 13px; line-height: 1.5; max-width: 85%; padding: 10px 14px; border-radius: 12px; }
                    .user { align-self: flex-end; border: 1px solid var(--md-sys-color-outline); background: rgba(255,255,255,0.8); }
                    .agent { align-self: flex-start; background: #FFF; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
                    #input-area { padding: 16px; background: #FFF; border-top: 1px solid var(--md-sys-color-outline); }
                    #pill { background: #F0F4F9; border-radius: 24px; padding: 4px 12px; display: flex; border: 1px solid #E0E0E0; }
                    input { flex: 1; background: transparent; border: none; outline: none; padding: 8px; font-size: 13px; }
                    button { background: var(--md-sys-color-primary); color: white; border: none; border-radius: 50%; width: 28px; height: 28px; cursor: pointer; }
                </style>
            </head>
            <body>
                <div id="header">
                    <span>INTERNAL RADAR v2.0</span>
                    <span style="color: #9E9E9E">TRC: 999</span>
                </div>
                <div id="messages"></div>
                <div id="input-area">
                    <div id="pill">
                        <input type="text" id="chatInput" placeholder="Verify Route...">
                        <button id="sendBtn">&#8593;</button>
                    </div>
                </div>
                <script>
                    const vscode = acquireVsCodeApi();
                    const messages = document.getElementById('messages');
                    const input = document.getElementById('chatInput');
                    const btn = document.getElementById('sendBtn');

                    btn.onclick = () => {
                        const text = input.value;
                        if (text) {
                            vscode.postMessage({ command: 'sendChat', text });
                            input.value = '';
                        }
                    };
                    input.onkeypress = (e) => { if(e.key === 'Enter') btn.onclick(); };
                    window.addEventListener('message', event => {
                        const data = event.data;
                        const div = document.createElement('div');
                        div.className = 'msg ' + (data.command === 'addUserMessage' ? 'user' : 'agent');
                        div.innerText = data.text;
                        messages.appendChild(div);
                        messages.scrollTop = messages.scrollHeight;
                    });
                </script>
            </body>
            </html>`;
    }
}
module.exports = { activate };
