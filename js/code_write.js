// 1. Initial Icon Load
const refreshIcons = () => lucide.createIcons();
refreshIcons();

const voiceInput = document.getElementById("voice-input");
const micBtn = document.getElementById("mic-btn");
const sendBtn = document.getElementById("send-btn");
const codeEditor = document.getElementById("code-editor");
const fileName = document.getElementById("current-file-name");
const folderTree = document.getElementById("folder-tree");
const loadingSpinner = document.getElementById("loading-spinner");
const projectTitleText = document.getElementById("project-title-text");
const mathIndicator = document.getElementById("math-mode-indicator");
const lineNumbers = document.getElementById("line-numbers");
const previewBtn = document.getElementById("preview-btn");
const previewModalOverlay = document.getElementById("preview-modal-overlay");
const previewIframe = document.getElementById("preview-iframe");
const projectSwitcher = document.getElementById("project-switcher");

let isRecording = false,
  currentProjectName = "",
  currentFilePath = "";

// --- NEW: PROJECT SWITCHER LOGIC ---

async function initializeProjectSwitcher() {
  if (!projectSwitcher) return;

  try {
    // Fetch all generated folders from the backend
    const res = await fetch("/api/list-projects");
    const data = await res.json();

    // Clear existing options except the placeholder
    projectSwitcher.innerHTML =
      '<option value="" disabled>Select project...</option>';

    data.projects.forEach((project) => {
      const option = document.createElement("option");
      option.value = project.name;
      option.textContent = project.display_name;

      // Auto-select the project we are currently viewing
      if (project.name === currentProjectName) {
        option.selected = true;
        projectTitleText.textContent = project.display_name;
        // Update math indicator based on metadata from API
        mathIndicator.style.display = project.is_math ? "inline-block" : "none";
      }
      projectSwitcher.appendChild(option);
    });

    // Handle redirection on change
    projectSwitcher.addEventListener("change", (e) => {
      const selectedFolder = e.target.value;
      if (selectedFolder) {
        window.location.href = `/${selectedFolder}`;
      }
    });
  } catch (err) {
    console.error("❌ Failed to load project list:", err);
  }
}

// --- EDITOR UTILITIES ---

function updateLineNumbers() {
  const lines = codeEditor.value.split("\n");
  lineNumbers.innerHTML = lines.map((_, i) => i + 1).join("<br>");
}

function getProjectNameFromURL() {
  return (
    window.location.pathname
      .split("/")
      .filter((s) => s)
      .pop() || ""
  );
}

// --- FILE OPERATIONS ---

async function loadFolderStructure() {
  currentProjectName = getProjectNameFromURL();
  if (!currentProjectName) return;

  // Initialize the switcher metadata first
  initializeProjectSwitcher();

  loadingSpinner.style.display = "block";
  folderTree.style.display = "none";

  try {
    const res = await fetch(`/api/folder-structure/${currentProjectName}`);
    const data = await res.json();
    if (res.ok) {
      folderTree.innerHTML = buildTreeHTML(data.structure);
      refreshIcons();
      attachTreeEventListeners();

      // Default load for math projects
      if (currentProjectName.startsWith("math_project_")) {
        voiceInput.placeholder = "Refine your formula...";
        loadFileContent("main.tex");
      }
    }
  } catch (e) {
    console.error(e);
  } finally {
    loadingSpinner.style.display = "none";
    folderTree.style.display = "block";
  }
}

function buildTreeHTML(items) {
  return items
    .map((item) => {
      const icon = item.type === "folder" ? "folder" : "file-code";
      let html = `<div class="tree-item ${item.type}" data-path="${item.path}">
                  <i data-lucide="${icon}" class="tree-icon"></i><span>${item.name}</span>
                </div>`;
      if (item.children)
        html += `<div class="tree-children">${buildTreeHTML(item.children)}</div>`;
      return html;
    })
    .join("");
}

async function loadFileContent(path) {
  try {
    const res = await fetch(`/api/file-content/${currentProjectName}/${path}`);
    const data = await res.json();
    if (res.ok) {
      codeEditor.value = data.content;
      fileName.textContent = path;
      currentFilePath = path;
      updateLineNumbers();
    }
  } catch (e) {
    console.error(e);
  }
}

function attachTreeEventListeners() {
  document.querySelectorAll(".tree-item.file").forEach((item) => {
    item.addEventListener("click", function () {
      document
        .querySelectorAll(".tree-item")
        .forEach((i) => i.classList.remove("active"));
      this.classList.add("active");
      loadFileContent(this.getAttribute("data-path"));
    });
  });
}

async function saveFileContent() {
  if (!currentFilePath) return;
  await fetch(`/api/save-file/${currentProjectName}/${currentFilePath}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content: codeEditor.value }),
  });
}

// --- VOICE & WHISPER LOGIC ---

let mediaRecorder;
let audioChunks = [];

micBtn.addEventListener("click", async () => {
  if (!isRecording) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];

      mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
        voiceInput.placeholder = "Transcribing math...";

        const response = await fetch("/api/whisper-latex", {
          method: "POST",
          body: audioBlob,
        });

        const data = await response.json();

        if (data.text) {
          const start = codeEditor.selectionStart;
          const end = codeEditor.selectionEnd;
          const text = codeEditor.value;
          const before = text.substring(0, start);
          const after = text.substring(end);

          codeEditor.value = before + data.text + after;
          codeEditor.selectionStart = codeEditor.selectionEnd =
            start + data.text.length;

          updateLineNumbers();
          await saveFileContent();
        }
        voiceInput.placeholder = "Describe changes...";
      };

      mediaRecorder.start();
      isRecording = true;
      micBtn.classList.add("recording");
    } catch (err) {
      console.error("Mic access denied:", err);
    }
  } else {
    mediaRecorder.stop();
    isRecording = false;
    micBtn.classList.remove("recording");
  }
});

// --- UI EVENT LISTENERS ---

voiceInput.addEventListener("input", () => {
  sendBtn.disabled = voiceInput.value.trim().length === 0;
});

sendBtn.addEventListener("click", async () => {
  const msg = voiceInput.value;
  if (!msg) return;

  sendBtn.disabled = true;
  const res = await fetch("/api/write-code", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: msg,
      current_file_path: currentFilePath,
      folder_structure: "",
    }),
  });
  const data = await res.json();
  if (data.status === "success") {
    await loadFolderStructure();
    if (currentFilePath) loadFileContent(currentFilePath);
  }
  voiceInput.value = "";
});

previewBtn.addEventListener("click", async () => {
  await saveFileContent();

  if (currentProjectName.startsWith("math_project_")) {
    const previewUrl = `/render-latex/${currentProjectName}/${currentFilePath || "main.tex"}`;
    window.open(previewUrl, "_blank");
  } else {
    previewIframe.src = `/preview_static/${currentProjectName}/`;
    previewModalOverlay.style.display = "flex";
  }
});

document.getElementById("modal-close-btn").onclick = () =>
  (previewModalOverlay.style.display = "none");
document.getElementById("save-btn").onclick = saveFileContent;
codeEditor.oninput = updateLineNumbers;

window.onload = loadFolderStructure;
