const vscode = require('vscode');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

/**
 * ACP Phase 3: Enhanced UX & Observability
 * Implements: Inline Completions, Streaming Chat, and AND-TRACE Headers.
 */

let modelCache = [];
let sidebarProvider;

class SovereignSidebarProvider {
    constructor(extensionUri) {
        this._extensionUri = extensionUri;
    }

    resolveWebviewView(webviewView) {
        this._view = webviewView;
        webviewView.webview.options = { enableScripts: true };
        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);
    }

    updateStatus(agent, status, log = null) {
        console.log(`[ACP-SIDEBAR] Update: ${agent} | ${status} | ${log}`);
        if (this._view) {
            this._view.webview.postMessage({ command: 'update', agent, status, log });
            // If log starts with Snapshot created, refresh history
            if (log && log.includes('Snapshot created')) {
                this.updateHistory();
            }
        }
    }

    updateHistory() {
        if (!vscode.workspace.workspaceFolders) return;
        const workspacePath = vscode.workspace.workspaceFolders[0].uri.fsPath;
        try {
            const history = execSync('git log -5 --grep="ACP-SNAPSHOT" --format="%h|%s|%ar"', { cwd: workspacePath }).toString();
            if (this._view) {
                this._view.webview.postMessage({ command: 'updateHistory', history });
            }
        } catch (e) {
            console.error('Failed to fetch snapshot history:', e);
        }
    }

    _getHtmlForWebview(webview) {
        return `<!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: 'Segoe UI', sans-serif; background: #0b0e14; color: #e1e4e8; padding: 15px; }
                .status-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; margin-bottom: 20px; }
                .agent-name { font-size: 1.2em; font-weight: bold; color: #58a6ff; margin-bottom: 5px; }
                .status-badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; background: #238636; color: white; }
                .status-badge.thinking { background: #9e6a03; }
                .status-badge.idle { background: #484f58; }
                .log-section { font-family: 'Consolas', monospace; font-size: 0.9em; color: #8b949e; border-top: 1px solid #30363d; padding-top: 10px; margin-top: 10px; max-height: 150px; overflow-y: auto; }
                .log-entry { margin-bottom: 4px; border-left: 2px solid #58a6ff; padding-left: 8px; }
                
                .rollback-module { border-top: 1px solid #30363d; padding-top: 15px; margin-top: 20px; }
                .snapshot-item { font-size: 0.85em; background: #0d1117; padding: 5px; margin-bottom: 5px; border-radius: 4px; border: 1px solid #21262d; }
                .panic-btn { width: 100%; padding: 10px; background: #da3633; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 10px; }
                .panic-btn:hover { background: #f85149; }
                
                .pulse { animation: pulse-animation 2s infinite; }
                @keyframes pulse-animation { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
            </style>
        </head>
        <body>
            <h3>Sovereign Control</h3>
            <div class="status-card">
                <div id="agent" class="agent-name">SYNAPSE</div>
                <div id="status" class="status-badge idle">IDLE</div>
                <div id="logs" class="log-section">
                    <div class="log-entry">Control Plane Online</div>
                </div>
            </div>

            <div class="rollback-module">
                <h4>Recent Snapshots</h4>
                <div id="history"></div>
                <button class="panic-btn" onclick="rollback()">🚨 PANIC: ROLLBACK</button>
            </div>
            
            <script>
                const vscode = acquireVsCodeApi();
                const agentEl = document.getElementById('agent');
                const statusEl = document.getElementById('status');
                const logsEl = document.getElementById('logs');
                const historyEl = document.getElementById('history');

                function rollback() {
                    vscode.postMessage({ command: 'panicRollback' });
                }

                window.addEventListener('message', event => {
                    const { command, agent, status, log, history } = event.data;
                    if (command === 'update') {
                        agentEl.innerText = agent;
                        statusEl.innerText = status;
                        statusEl.className = 'status-badge ' + status.toLowerCase();
                        if (status === 'THINKING' || status === 'EXECUTING') statusEl.classList.add('pulse');
                        
                        if (log) {
                            const entry = document.createElement('div');
                            entry.className = 'log-entry';
                            entry.innerText = '[' + new Date().toLocaleTimeString() + '] ' + log;
                            logsEl.prepend(entry);
                        }
                    } else if (command === 'updateHistory') {
                        historyEl.innerHTML = '';
                        if (!history) return;
                        history.trim().split('\\n').forEach(line => {
                            if (!line) return;
                            const [hash, msg, time] = line.split('|');
                            const item = document.createElement('div');
                            item.className = 'snapshot-item';
                            item.innerHTML = '<b>' + hash + '</b>: ' + msg.substring(13, 25) + '... <br><small>' + time + '</small>';
                            historyEl.appendChild(item);
                        });
                    }
                });
            </script>
        </body>
        </html>`;
    }
}

function activate(context) {
    console.log('Antigravity Control Plane (ACP) Extension Active');

    sidebarProvider = new SovereignSidebarProvider(context.extensionUri);
    const sidebarReg = vscode.window.registerWebviewViewProvider('acpSidebar', sidebarProvider);

    // 1. Dynamic Model Discovery
    fetchModels();

    // 2. Inline Completion Provider (antigravity-fast)
    const completionProvider = vscode.languages.registerInlineCompletionItemProvider(
        { pattern: '**' },
        {
            provideInlineCompletionItems: async (document, position, context, token) => {
                // 300ms Debounce logic
                await new Promise(resolve => setTimeout(resolve, 300));
                if (token.isCancellationRequested) return;

                const textBefore = document.getText(
                    new vscode.Range(new vscode.Position(Math.max(0, position.line - 5), 0), position)
                );

                try {
                    const response = await callACPProxy('antigravity-fast', textBefore);
                    return [new vscode.InlineCompletionItem(response)];
                } catch (err) {
                    console.error('ACP Completion Error:', err);
                    return [];
                }
            }
        }
    );

    // 3. Streaming Chat Command (antigravity-smart)
    const chatCommand = vscode.commands.registerCommand('ask.antigravity', async () => {
        const panel = vscode.window.createWebviewPanel(
            'acpChat',
            'Antigravity Chat',
            vscode.ViewColumn.Two,
            { enableScripts: true }
        );

        panel.webview.html = getChatHtml();

        panel.webview.onDidReceiveMessage(async (message) => {
            if (message.command === 'sendPrompt') {
                await handleStreamingChat(message.text, panel);
            }
        });

        sidebarProvider._view.webview.onDidReceiveMessage(async (message) => {
            if (message.command === 'panicRollback') {
                await vscode.commands.executeCommand('panic.rollback');
            }
        });
    });

    const rollbackCommand = vscode.commands.registerCommand('panic.rollback', async () => {
        const choice = await vscode.window.showWarningMessage('Are you sure you want to rollback to the last snapshot? This will reset the workspace.', 'ROLLBACK', 'Cancel');
        if (choice === 'ROLLBACK') {
            const workspacePath = vscode.workspace.workspaceFolders[0].uri.fsPath;
            try {
                execSync('git reset --hard HEAD~1', { cwd: workspacePath });
                vscode.window.showInformationMessage('Rollback Successful.');
                sidebarProvider.updateStatus('SYNAPSE', 'IDLE', 'PANIC: Rollback Successful');
                sidebarProvider.updateHistory();
            } catch (err) {
                vscode.window.showErrorMessage(`Rollback Failed: ${err.message}`);
            }
        }
    });

    context.subscriptions.push(completionProvider, chatCommand, sidebarReg, rollbackCommand);
}

/**
 * Standardized Tracing (AND-TRACE)
 * Injects tracing headers for PostgreSQL logging.
 */
async function callACPProxy(modelAlias, prompt, stream = false) {
    const traceId = `trace-${Math.random().toString(36).substring(2, 11)}`;
    const sessionId = vscode.env.sessionId;

    return new Promise((resolve, reject) => {
        const reqData = JSON.stringify({
            model: modelAlias,
            messages: [{ role: 'user', content: prompt }],
            stream: stream
        });

        const options = {
            hostname: 'localhost',
            port: 8000,
            path: '/v1/chat/completions',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer sk-antigravity-admin', // Master Key
                'X-AND-TRACE': traceId,
                'X-AND-SESSION': sessionId
            }
        };

        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => { data += chunk; });
            res.on('end', () => {
                try {
                    const json = JSON.parse(data);
                    resolve(json.choices[0].message.content);
                } catch (e) { reject(e); }
            });
        });

        req.on('error', reject);
        req.write(reqData);
        req.end();
    });
}

/**
 * Implements Streaming UI updates for the Webview
 */
async function handleStreamingChat(prompt, panel) {
    // Identify Agent based on content or role (Simple heuristic for now)
    const activeAgent = prompt.toLowerCase().includes('plan') ? 'LEXICONNA' : 'SYNAPSE';
    sidebarProvider.updateStatus(activeAgent, 'THINKING', `User: ${prompt.substring(0, 20)}...`);

    const traceId = `trace-chat-${Date.now()}`;
    const options = {
        hostname: 'localhost',
        port: 8000,
        path: '/v1/chat/completions',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer sk-antigravity-admin',
            'X-AND-TRACE': traceId,
            'X-AND-SESSION': vscode.env.sessionId
        }
    };

    const tools = [
        {
            type: "function",
            function: {
                name: "write_file",
                description: "Writes content to a specific file path in the workspace.",
                parameters: {
                    type: "object",
                    properties: {
                        path: { type: "string", description: "Relative path to file" },
                        content: { type: "string", description: "The content to write" }
                    },
                    required: ["path", "content"]
                }
            }
        },
        {
            type: "function",
            function: {
                name: "read_file",
                description: "Reads the content of a file from the workspace.",
                parameters: {
                    type: "object",
                    properties: {
                        path: { type: "string", description: "Relative path to the file to read" }
                    },
                    required: ["path"]
                }
            }
        },
        {
            type: "function",
            function: {
                name: "workspace_snapshot",
                description: "Creates a Git checkpoint before any destructive actions.",
                parameters: {
                    type: "object",
                    properties: {
                        traceId: { type: "string", description: "The current AND-TRACE ID" }
                    },
                    required: ["traceId"]
                }
            }
        }
    ];

    const req = http.request(options, (res) => {
        res.on('data', async (chunk) => {
            const lines = chunk.toString().split('\n');
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        const message = data.choices[0];
                        
                        // Handle standard content streaming
                        if (message.delta && message.delta.content) {
                            panel.webview.postMessage({ command: 'contentChunk', text: message.delta.content });
                        }

                        // Handle Tool Calls (Dynamic Injection Success Path)
                        if (message.delta && message.delta.tool_calls) {
                            const toolCall = message.delta.tool_calls[0];
                            if (toolCall.function) {
                                panel.webview.postMessage({ command: 'contentChunk', text: `\n[ACP-ACTION]: Triggering ${toolCall.function.name}...\n` });
                                const result = await executeTool(toolCall);
                                panel.webview.postMessage({ command: 'contentChunk', text: `\n[ACP-RESULT]: ${result}\n` });
                            }
                        }
                    } catch (e) { /* End of stream */ }
                }
            }
        });
    });

    req.write(JSON.stringify({
        model: 'antigravity-smart',
        messages: [{ role: 'user', content: prompt }],
        tools: tools,
        stream: true
    }));
    req.end();

    req.on('close', () => {
        sidebarProvider.updateStatus('SYNAPSE', 'IDLE');
    });
}

/**
 * Execution Core for Phase 4: Autonomous Workspace Management
 */
async function executeTool(toolCall) {
    const { name, arguments: argsString } = toolCall.function;
    const args = JSON.parse(argsString);
    
    // Safety check: only allow operations within the workspace
    if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
        return "Error: No workspace folder open.";
    }
    
    const workspacePath = vscode.workspace.workspaceFolders[0].uri.fsPath;
    const targetPath = path.join(workspacePath, args.path);

    // Basic security: prevent path traversal
    if (!targetPath.startsWith(workspacePath)) {
        return `Error: Security Violation. Execution blocked for path: ${args.path}`;
    }

    try {
        sidebarProvider.updateStatus('SYNAPSE', 'EXECUTING', `Tool: ${name}`);
        if (name === 'write_file') {
            fs.writeFileSync(targetPath, args.content, 'utf8');
            sidebarProvider.updateStatus('SYNAPSE', 'EXECUTING', `Success: Wrote ${args.path}`);
            return `Successfully wrote to ${args.path}`;
        } else if (name === 'read_file') {
            if (!fs.existsSync(targetPath)) {
                sidebarProvider.updateStatus('SYNAPSE', 'EXECUTING', `Error: ${args.path} not found`);
                return `Error: File not found at ${args.path}`;
            }
            const content = fs.readFileSync(targetPath, 'utf8');
            sidebarProvider.updateStatus('SYNAPSE', 'EXECUTING', `Success: Read ${args.path}`);
            return content;
        } else if (name === 'workspace_snapshot') {
            return await createSnapshot(args.traceId);
        }
    } catch (err) {
        sidebarProvider.updateStatus('SYNAPSE', 'EXECUTING', `Error: ${err.message}`);
        return `Error executing ${name}: ${err.message}`;
    }
}

/**
 * SSP Core: Automated Pre-Action Snapshot
 */
async function createSnapshot(traceId) {
    if (!vscode.workspace.workspaceFolders) return "Error: No workspace open.";
    const workspacePath = vscode.workspace.workspaceFolders[0].uri.fsPath;
    
    try {
        sidebarProvider.updateStatus('SYNAPSE', 'EXECUTING', `Creating Snapshot...`);
        execSync('git add .', { cwd: workspacePath });
        execSync(`git commit -m "ACP-SNAPSHOT: ${traceId}" --allow-empty`, { cwd: workspacePath });
        const commitHash = execSync('git rev-parse --short HEAD', { cwd: workspacePath }).toString().trim();
        sidebarProvider.updateStatus('SYNAPSE', 'EXECUTING', `Snapshot created: ${commitHash}`);
        return `Snapshot created: ACP-SNAPSHOT: ${traceId} (Hash: ${commitHash})`;
    } catch (err) {
        return `Snapshot skipped (likely no changes or git not init): ${err.message}`;
    }
}

async function fetchModels() {
    try {
        const response = await new Promise((resolve, reject) => {
            http.get('http://localhost:8000/v1/models', (res) => {
                let data = '';
                res.on('data', d => data += d);
                res.on('end', () => resolve(JSON.parse(data)));
            }).on('error', reject);
        });
        modelCache = response.data.map(m => m.id);
        console.log('ACP Discovered Models:', modelCache);
    } catch (err) {
        console.error('ACP Discovery Failed:', err);
    }
}

function getChatHtml() {
    return `<!DOCTYPE html>
    <html>
    <body style="padding: 20px; font-family: sans-serif;">
        <h3>Antigravity Smart Chat</h3>
        <div id="chat" style="background: #1e1e1e; padding: 10px; min-height: 200px; margin-bottom: 10px; border-radius: 4px;"></div>
        <input type="text" id="input" style="width: 80%; background: #333; color: white; border: none; padding: 5px;" placeholder="Enter prompt...">
        <button onclick="send()" style="padding: 5px 10px; cursor: pointer;">Send</button>

        <script>
            const vscode = acquireVsCodeApi();
            const chatDiv = document.getElementById('chat');
            const input = document.getElementById('input');

            function send() {
                const text = input.value;
                chatDiv.innerHTML += '<p><b>You:</b> ' + text + '</p>';
                vscode.postMessage({ command: 'sendPrompt', text: text });
                input.value = '';
            }

            window.addEventListener('message', event => {
                if (event.data.command === 'contentChunk') {
                    chatDiv.innerHTML += event.data.text;
                }
            });
        </script>
    </body>
    </html>`;
}

function deactivate() {}

module.exports = { activate, deactivate };
