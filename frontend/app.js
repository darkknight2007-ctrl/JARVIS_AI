/* =========================================================
   JARVIS — app.js  |  WebSocket client + UI logic
   ========================================================= */

const WS_URL = "ws://localhost:8000/ws";
const API_URL = "http://localhost:8000";

let ws = null;
let isStreaming = false;
let messageCount = 0;
let currentBubble = null;   // streaming target element
let currentRawText = "";    // accumulates streamed chars

// ── Connect WebSocket ──────────────────────────────────────
function connect() {
  setStatus("connecting");
  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    setStatus("connected");
    fetchModels();
  };

  ws.onclose = () => {
    setStatus("disconnected");
    // auto-reconnect after 3 s
    setTimeout(connect, 3000);
  };

  ws.onerror = () => setStatus("disconnected");

  ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    handleServerEvent(data);
  };
}

async function fetchModels() {
  try {
    const res = await fetch(`${API_URL}/api/models`);
    const data = await res.json();
    const select = document.getElementById("model-select");
    
    // Clear and populate
    select.innerHTML = "";
    data.models.forEach(modelName => {
      const option = document.createElement("option");
      option.value = modelName;
      option.textContent = modelName;
      if (modelName === data.active) {
        option.selected = true;
      }
      select.appendChild(option);
    });
  } catch (e) {
    console.error("Failed to load models:", e);
    document.getElementById("model-select").innerHTML = `<option>Error Loading Models</option>`;
  }
}

async function switchModel(newModel) {
  const select = document.getElementById("model-select");
  select.disabled = true;
  const originalColor = select.style.color;
  select.style.color = "var(--orange)"; // visual loading indicator
  
  try {
    const res = await fetch(`${API_URL}/api/model`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: newModel })
    });
    const data = await res.json();
    if(data.status === "success") {
       select.style.color = "var(--green)";
       setTimeout(() => select.style.color = originalColor, 1500);
    } else {
       throw new Error(data.error);
    }
  } catch (e) {
    console.error("Error switching model:", e);
    alert("Failed to switch model: " + e.message);
    select.style.color = "var(--red)";
  } finally {
    select.disabled = false;
  }
}

// ── Handle incoming server events ─────────────────────────
function handleServerEvent(data) {
  switch (data.type) {

    case "tool_start":
      showToolBar(`🔧 Using: ${friendlyToolName(data.tool)}…`);
      appendToolEvent("start", data.tool, data.input);
      break;

    case "tool_end":
      showToolBar(`✅ Done: ${friendlyToolName(data.tool)}`);
      appendToolEvent("end", data.tool, data.output);
      break;

    case "token":
      if (!currentBubble) startAssistantBubble();
      currentRawText += data.content;
      renderStreaming(currentRawText);
      scrollToBottom();
      break;

    case "error":
      if (!currentBubble) startAssistantBubble();
      currentRawText += `\n\n⚠️ ${data.content}`;
      renderStreaming(currentRawText);
      finishStreaming();
      break;

    case "done":
      finishStreaming();
      break;
  }
}

// ── Send message ───────────────────────────────────────────
function sendMessage() {
  const input = document.getElementById("msg-input");
  const text = input.value.trim();
  if (!text || isStreaming || !ws || ws.readyState !== WebSocket.OPEN) return;

  // Hide welcome card on first message
  const welcome = document.getElementById("welcome-card");
  if (welcome) welcome.remove();

  appendUserMessage(text);
  input.value = "";
  autoResize(input);

  isStreaming = true;
  currentBubble = null;
  currentRawText = "";
  document.getElementById("send-btn").disabled = true;

  ws.send(JSON.stringify({ message: text }));
}

// ── Keyboard handler ───────────────────────────────────────
function handleKey(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

// ── Auto-resize textarea ───────────────────────────────────
function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 160) + "px";
}

// ── Insert a quick prompt ──────────────────────────────────
function insertPrompt(text) {
  const input = document.getElementById("msg-input");
  input.value = text;
  input.focus();
  autoResize(input);
}

// ── Clear conversation ─────────────────────────────────────
function clearConversation() {
  fetch(`${API_URL}/clear`, { method: "POST" }).catch(() => {});
  const msgs = document.getElementById("messages");
  msgs.innerHTML = `
    <div class="welcome-card" id="welcome-card">
      <div class="welcome-icon">🤖</div>
      <h2>Good day, sir. JARVIS online.</h2>
      <p>Your private AI assistant for web development — running entirely on your Mac.</p>
      <div class="welcome-tags">
        <span>📁 Files</span><span>⚡ Terminal</span>
        <span>🔒 Local</span><span>💻 Web Dev</span>
      </div>
      <p class="tip">Try: <em>"Create a modern portfolio site"</em></p>
    </div>`;
  messageCount = 0;
  updateMsgCount();
}

// ── Append user message ────────────────────────────────────
function appendUserMessage(text) {
  messageCount++;
  updateMsgCount();
  const msgs = document.getElementById("messages");
  const row = document.createElement("div");
  row.className = "msg user";
  row.innerHTML = `
    <div class="msg-avatar">👤</div>
    <div class="msg-content">
      <div class="msg-bubble">${escapeHtml(text)}</div>
      <div class="msg-time">${timeNow()}</div>
    </div>`;
  msgs.appendChild(row);
  scrollToBottom();
}

// ── Start an assistant bubble (streaming) ─────────────────
function startAssistantBubble() {
  messageCount++;
  updateMsgCount();
  const bubbleId = "bubble-" + Date.now();
  const msgs = document.getElementById("messages");
  const row = document.createElement("div");
  row.className = "msg assistant";
  row.innerHTML = `
    <div class="msg-avatar">J</div>
    <div class="msg-content">
      <div class="msg-bubble markdown-body" id="${bubbleId}"><span class="cursor"></span></div>
      <div class="msg-time">${timeNow()}</div>
    </div>`;
  msgs.appendChild(row);
  currentBubble = document.getElementById(bubbleId);
  scrollToBottom();
}

// ── Append tool event inside current assistant bubble ──────
function appendToolEvent(kind, tool, detail) {
  if (!currentBubble) startAssistantBubble();
  const icon = kind === "start" ? "🔧" : "✅";
  const label = kind === "start"
    ? `Using <strong>${friendlyToolName(tool)}</strong>`
    : `Completed <strong>${friendlyToolName(tool)}</strong>`;
  const el = document.createElement("div");
  el.className = "tool-event";
  el.innerHTML = `<span class="tool-icon">${icon}</span><span>${label}</span>`;
  // Insert before cursor / after last tool event
  currentBubble.insertBefore(el, currentBubble.querySelector(".cursor"));
}

// ── Render streaming markdown ──────────────────────────────
function renderStreaming(raw) {
  if (!currentBubble) return;
  const rendered = parseMarkdown(raw);
  currentBubble.innerHTML = rendered + '<span class="cursor"></span>';
}

// ── Finalize the streaming bubble ─────────────────────────
function finishStreaming() {
  hideToolBar();
  if (currentBubble && currentRawText) {
    currentBubble.innerHTML = parseMarkdown(currentRawText);
    addCopyButtons(currentBubble);
  }
  currentBubble = null;
  currentRawText = "";
  isStreaming = false;
  document.getElementById("send-btn").disabled = false;
  scrollToBottom();

  // Re-run syntax highlighting
  document.querySelectorAll("pre code").forEach(el => {
    if (!el.dataset.highlighted) hljs.highlightElement(el);
  });
}

// ── Display complete assistant message ─────────────────────
function showAssistantMessage(content) {
  messageCount++;
  updateMsgCount();
  const bubbleId = "bubble-" + Date.now();
  const msgs = document.getElementById("messages");
  const row = document.createElement("div");
  row.className = "msg assistant";
  row.innerHTML = `
    <div class="msg-avatar">J</div>
    <div class="msg-content">
      <div class="msg-text">${parseMarkdown(content)}</div>
    </div>
  `;
  msgs.appendChild(row);
  scrollToBottom();

  // Re-run syntax highlighting
  document.querySelectorAll("pre code").forEach(el => {
    if (!el.dataset.highlighted) hljs.highlightElement(el);
  });
}

// ── Markdown rendering ─────────────────────────────────────
function parseMarkdown(text) {
  // Convert <think> tags into markdown blockquotes before parsing
  text = text.replace(/<think>/g, "\n> **🧠 JARVIS Thought Process:**\n> ");
  text = text.replace(/<\/think>/g, "\n\n");
  
  if (typeof marked === "undefined") return escapeHtml(text).replace(/\n/g, "<br>");

  marked.setOptions({
    highlight: (code, lang) => {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(code, { language: lang, ignoreIllegals: true }).value;
      }
      return hljs.highlightAuto(code).value;
    },
    breaks: true,
    gfm: true,
  });

  // Wrap code blocks with a header (language + copy button)
  let html = marked.parse(text);
  html = html.replace(/<pre><code class="language-(\w+)">/g, (_, lang) =>
    `<pre><div class="code-header"><span class="code-lang">${lang}</span>` +
    `<button class="copy-btn" onclick="copyCode(this)">Copy</button></div>` +
    `<code class="language-${lang}">`
  );
  html = html.replace(/<pre><code>/g,
    `<pre><div class="code-header"><span class="code-lang">code</span>` +
    `<button class="copy-btn" onclick="copyCode(this)">Copy</button></div><code>`
  );
  return html;
}

// ── Add copy buttons to already-rendered code blocks ──────
function addCopyButtons(container) {
  container.querySelectorAll("pre").forEach(pre => {
    if (pre.querySelector(".code-header")) return; // already has one
    const code = pre.querySelector("code");
    if (!code) return;
    const header = document.createElement("div");
    header.className = "code-header";
    header.innerHTML = `<span class="code-lang">code</span><button class="copy-btn" onclick="copyCode(this)">Copy</button>`;
    pre.insertBefore(header, code);
  });
}

function copyCode(btn) {
  const code = btn.closest("pre").querySelector("code");
  if (!code) return;
  navigator.clipboard.writeText(code.innerText).then(() => {
    btn.textContent = "Copied!";
    setTimeout(() => (btn.textContent = "Copy"), 1800);
  });
}

// ── Tool bar helpers ───────────────────────────────────────
function showToolBar(msg) {
  const bar = document.getElementById("tool-bar");
  document.getElementById("tool-bar-text").textContent = msg;
  bar.classList.add("show");
}
function hideToolBar() {
  document.getElementById("tool-bar").classList.remove("show");
}

// ── Status indicator ───────────────────────────────────────
function setStatus(state) {
  const dot  = document.getElementById("status-dot");
  const text = document.getElementById("status-text");
  dot.className = `status-dot ${state}`;
  const labels = { connected: "Online", disconnected: "Offline", connecting: "Connecting…" };
  text.textContent = labels[state] || state;
}

// ── Helpers ────────────────────────────────────────────────
function scrollToBottom() {
  const msgs = document.getElementById("messages");
  msgs.scrollTop = msgs.scrollHeight;
}

function updateMsgCount() {
  document.getElementById("msg-count").textContent =
    `${messageCount} message${messageCount !== 1 ? "s" : ""}`;
}

function timeNow() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function escapeHtml(str) {
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
            .replace(/"/g,"&quot;").replace(/'/g,"&#39;");
}

function friendlyToolName(name) {
  const map = {
    read_file: "Read File",
    write_file: "Write File",
    list_directory: "List Directory",
    create_directory: "Create Directory",
    run_terminal_command: "Terminal",
  };
  return map[name] || name;
}

// ── Particle background ────────────────────────────────────
function initCanvas() {
  const canvas = document.getElementById("bg-canvas");
  const ctx = canvas.getContext("2d");
  let W = canvas.width  = window.innerWidth;
  let H = canvas.height = window.innerHeight;

  const DOTS = 60;
  const dots = Array.from({ length: DOTS }, () => ({
    x: Math.random() * W, y: Math.random() * H,
    vx: (Math.random() - .5) * .3, vy: (Math.random() - .5) * .3,
    r: Math.random() * 1.5 + .5,
  }));

  function draw() {
    ctx.clearRect(0, 0, W, H);
    // Draw connecting lines
    for (let i = 0; i < DOTS; i++) {
      for (let j = i + 1; j < DOTS; j++) {
        const dx = dots[i].x - dots[j].x;
        const dy = dots[i].y - dots[j].y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < 120) {
          const rgb = getComputedStyle(document.body).getPropertyValue('--particle-rgb').trim() || '0, 212, 255';
          ctx.beginPath();
          ctx.strokeStyle = `rgba(${rgb}, ${.25 * (1 - dist/120)})`;
          ctx.lineWidth = .5;
          ctx.moveTo(dots[i].x, dots[i].y);
          ctx.lineTo(dots[j].x, dots[j].y);
          ctx.stroke();
        }
      }
    }
    // Draw dots
    dots.forEach(d => {
      const rgb = getComputedStyle(document.body).getPropertyValue('--particle-rgb').trim() || '0, 212, 255';
      ctx.beginPath();
      ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${rgb}, 0.5)`;
      ctx.fill();
      d.x += d.vx; d.y += d.vy;
      if (d.x < 0 || d.x > W) d.vx *= -1;
      if (d.y < 0 || d.y > H) d.vy *= -1;
    });
    requestAnimationFrame(draw);
  }
  draw();

  window.addEventListener("resize", () => {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  });
}

// ── Init ───────────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
  loadTheme();
  connect();
  initCanvas();
  fetchFileTree();
  document.getElementById("msg-input").focus();
});

// ── Theme Engine ──────────────────────────────────────────
function switchTheme(themeName) {
  document.body.setAttribute('data-theme', themeName);
  localStorage.setItem('jarvis-theme', themeName);
}

function loadTheme() {
  const savedTheme = localStorage.getItem('jarvis-theme') || 'default';
  document.body.setAttribute('data-theme', savedTheme);
  const select = document.getElementById("theme-select");
  if (select) select.value = savedTheme;
}

// ── File Explorer ──────────────────────────────────────────
async function fetchFileTree() {
  const container = document.getElementById("file-tree-container");
  container.innerHTML = '<span class="loader" style="transform:scale(0.5); display:inline-block"></span>';
  try {
    const res = await fetch(`${API_URL}/api/files`);
    if (!res.ok) throw new Error("Failed to load files");
    const data = await res.json();
    container.innerHTML = "";
    
    // Create root UL securely
    const ul = document.createElement("ul");
    ul.className = "file-tree";
    data.tree.forEach(node => ul.appendChild(createTreeNode(node)));
    container.appendChild(ul);
  } catch (err) {
    container.innerHTML = `<span style="color:var(--red); font-size:12px;">Error loading files</span>`;
  }
}

function createTreeNode(node) {
  const li = document.createElement("li");
  const isDir = node.type === "folder";
  
  const nodeDiv = document.createElement("div");
  nodeDiv.className = `tree-node ${isDir ? "tree-folder" : "tree-file"}`;
  
  const icon = document.createElement("span");
  icon.textContent = isDir ? "📁" : "📄";
  
  const label = document.createElement("span");
  label.textContent = node.name;
  
  nodeDiv.appendChild(icon);
  nodeDiv.appendChild(label);
  
  if (isDir) {
    // Hidden children container
    const childrenUl = document.createElement("ul");
    childrenUl.className = "tree-children";
    if (node.children) {
      node.children.forEach(child => childrenUl.appendChild(createTreeNode(child)));
    }
    
    li.appendChild(nodeDiv);
    li.appendChild(childrenUl);
    
    // Toggle functionality
    nodeDiv.onclick = () => {
      const isOpen = childrenUl.classList.contains("open");
      if (isOpen) {
        childrenUl.classList.remove("open");
        icon.textContent = "📁";
      } else {
        childrenUl.classList.add("open");
        icon.textContent = "📂";
      }
    };
  } else {
    li.appendChild(nodeDiv);
    // Paste file path into chat when clicked
    nodeDiv.onclick = () => {
      insertPrompt(`Examine the file at: ${node.path}`);
    };
  }
  
  return li;
}

// ── Vision / Image Upload ───────────────────────────────────
async function handleImageUpload(files) {
  if (!files || files.length === 0) return;

  const file = files[0];
  const maxSize = 10 * 1024 * 1024; // 10MB limit

  if (file.size > maxSize) {
    alert("Image too large. Please select an image under 10MB.");
    return;
  }

  // Show loading state
  const uploadBtn = document.querySelector("label[for='image-upload']");
  const originalText = uploadBtn.textContent;
  uploadBtn.textContent = "📤 Uploading...";
  uploadBtn.style.opacity = "0.7";

  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("question", "What's in this image?");

    const response = await fetch(`${API_URL}/api/upload-image`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (response.ok) {
      // If analysis was done server-side, show the result
      if (data.analysis && !data.analysis.includes("Vision model integration is in progress")) {
        showAssistantMessage(data.analysis);
      } else {
        // Insert prompt to analyze the image
        insertPrompt(`Analyze this image: ${data.file_path}`);
        // Auto-send the message
        setTimeout(() => {
          document.getElementById("send-btn").click();
        }, 500);
      }
    } else {
      alert(`Upload failed: ${data.error || "Unknown error"}`);
    }

  } catch (error) {
    console.error("Upload error:", error);
    alert("Failed to upload image. Please try again.");
  } finally {
    // Reset button state
    uploadBtn.textContent = originalText;
    uploadBtn.style.opacity = "1";
    // Clear file input
    document.getElementById("image-upload").value = "";
  }
}

// ── Git Integration ────────────────────────────────────────
async function runGitCommand(command) {
  try {
    let endpoint;

    switch (command) {
      case 'status':
        endpoint = '/api/git/status';
        break;
      case 'push':
        endpoint = '/api/git/push';
        break;
      default:
        return;
    }

    let response;
    if (command === 'push') {
      response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ directory: '.' })
      });
    } else {
      response = await fetch(`${API_URL}${endpoint}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const data = await response.json();

    if (response.ok) {
      showAssistantMessage(`Git ${command} result:\n\n${data.output}`);
    } else {
      alert(`Git ${command} failed: ${data.error}`);
    }

  } catch (error) {
    console.error("Git command error:", error);
    alert("Failed to execute git command. Please try again.");
  }
}

function promptGitCommit() {
  const message = prompt("Enter commit message:");
  if (message) {
    executeGitCommit(message);
  }
}

async function executeGitCommit(message) {
  try {
    const response = await fetch(`${API_URL}/api/git/commit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });

    const data = await response.json();

    if (response.ok) {
      showAssistantMessage(`Git commit result:\n\n${data.output}`);
    } else {
      alert(`Git commit failed: ${data.error}`);
    }

  } catch (error) {
    console.error("Git commit error:", error);
    alert("Failed to execute git commit. Please try again.");
  }
}
