document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 DevScribe: DOM fully loaded");

  // 1. Initial Icon Render
  if (window.lucide) {
    lucide.createIcons();
  }

  // UI Elements
  const textarea = document.getElementById("chat-textarea");
  const micBtn = document.getElementById("mic-btn");
  const voiceInterface = document.getElementById("voice-interface");
  const visualizerContainer = document.getElementById("visualizer-bars");
  const timerDisplay = document.getElementById("recording-timer");
  const statusMsg = document.getElementById("status-msg");
  const sendBtn = document.getElementById("send-btn");
  const mathModeBtn = document.getElementById("math-mode-btn");
  const inputWrapper = document.getElementById("input-wrapper");
  const projectGrid = document.getElementById("home-project-grid");

  let recognition;
  let isRecording = false;
  let isMathMode = false;
  let timerInterval;
  let seconds = 0;

  // --- 1. PROJECT PICKER LOGIC ---
  const loadProjectPicker = async () => {
    if (!projectGrid) return;

    // Using Absolute URL to prevent Catch-all route collisions
    const apiUrl = window.location.origin + "/api/list-projects";

    try {
      const res = await fetch(apiUrl);

      // Critical Check: Detect if server returned HTML (the common JSON SyntaxError source)
      const contentType = res.headers.get("content-type");
      if (contentType && contentType.includes("text/html")) {
        console.error(
          "🚨 API Collision: Server returned HTML. Check FastAPI route order.",
        );
        projectGrid.innerHTML = `
                    <div class="col-12 text-center text-secondary py-5">
                        <p>Unable to load workspace. (Route Collision Detected)</p>
                    </div>`;
        return;
      }

      const data = await res.json();
      const projectCount = document.getElementById("project-count");
      if (projectCount) projectCount.textContent = data.projects.length;

      if (data.projects.length === 0) {
        projectGrid.innerHTML = `
                    <div class="col-12 text-center text-secondary py-5">
                        <p class="opacity-50">No projects found. Describe something above to start.</p>
                    </div>`;
        return;
      }

      // Map and Render Project Cards
      projectGrid.innerHTML = data.projects
        .map(
          (proj) => `
                <div class="col-md-4 col-lg-3">
                    <a href="/${proj.name}" class="project-picker-card">
                        <div class="card-icon-wrapper ${proj.is_math ? "math-icon-bg" : "code-icon-bg"}">
                            <i data-lucide="${proj.is_math ? "sigma" : "code-2"}"></i>
                        </div>
                        <div class="card-content">
                            <div class="card-title text-truncate">${proj.display_name}</div>
                            <div class="card-date">${proj.last_modified}</div>
                        </div>
                    </a>
                </div>
            `,
        )
        .join("");

      lucide.createIcons();
    } catch (err) {
      console.error("❌ Failed to load picker:", err);
      projectGrid.innerHTML =
        '<div class="col-12 text-center text-danger py-5">Connection Error.</div>';
    }
  };

  // Initial Trigger
  loadProjectPicker();

  // --- 2. SETUP VISUALIZER ---
  const BAR_COUNT = 20;
  if (visualizerContainer) {
    visualizerContainer.innerHTML = "";
    for (let i = 0; i < BAR_COUNT; i++) {
      const bar = document.createElement("div");
      bar.className = "visualizer-bar";
      const duration = 0.4 + Math.random() * 0.4;
      const delay = Math.random() * 0.5;
      bar.style.animationDuration = `${duration}s`;
      bar.style.animationDelay = `-${delay}s`;
      bar.style.height = "10%";
      visualizerContainer.appendChild(bar);
    }
  }

  // --- 3. UTILITIES: TIMER & RESIZE ---
  const startTimer = () => {
    seconds = 0;
    timerInterval = setInterval(() => {
      seconds++;
      const mins = Math.floor(seconds / 60)
        .toString()
        .padStart(2, "0");
      const secs = (seconds % 60).toString().padStart(2, "0");
      timerDisplay.innerText = `${mins}:${secs}`;
    }, 1000);
  };

  const resizeTextarea = () => {
    textarea.style.height = "auto";
    textarea.style.height = textarea.scrollHeight + "px";
    sendBtn.disabled = textarea.value.trim().length === 0;
  };
  textarea.addEventListener("input", resizeTextarea);

  // --- 4. MATH MODE ---
  mathModeBtn.addEventListener("click", () => {
    isMathMode = !isMathMode;
    mathModeBtn.classList.toggle("active");
    textarea.placeholder = isMathMode
      ? "Describe formula..."
      : "Describe your app...";
  });

  // --- 5. SEND LOGIC ---
  const sendMessage = () => {
    const message = textarea.value.trim();
    if (!message) return;

    sendBtn.disabled = true;
    statusMsg.innerText = isMathMode ? "Processing LaTeX..." : "Building...";
    statusMsg.style.opacity = "1";

    const formData = new FormData();
    formData.append("message", message);
    formData.append("timestamp", new Date().toISOString());
    formData.append("is_math", isMathMode);

    $.ajax({
      url: window.location.origin + "/create-file-structure",
      type: "POST",
      data: formData,
      processData: false,
      contentType: false,
      success: function (res) {
        if (typeof res === "string" && res.trim().startsWith("<!DOCTYPE")) {
          window.location.reload();
          return;
        }

        const data = typeof res === "string" ? JSON.parse(res) : res;

        if (data.status === "success" && data.folder_name) {
          statusMsg.innerText = "Success! Redirecting...";
          window.location.replace(
            window.location.origin + "/" + data.folder_name,
          );
        } else {
          alert("Error creating project.");
          sendBtn.disabled = false;
        }
      },
      error: function (xhr) {
        console.error("❌ AJAX Error:", xhr.status);
        statusMsg.innerText = "Server Error!";
        sendBtn.disabled = false;
      },
    });
  };

  sendBtn.addEventListener("click", sendMessage);
  textarea.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // --- 6. SPEECH RECOGNITION ---
  try {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onstart = () => {
        isRecording = true;
        inputWrapper.classList.add("recording");
        voiceInterface.classList.add("active");
        startTimer();
      };

      recognition.onresult = (event) => {
        let finalTranscript = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal)
            finalTranscript += event.results[i][0].transcript;
        }
        if (finalTranscript) {
          textarea.value += (textarea.value ? " " : "") + finalTranscript;
          resizeTextarea();
        }
      };

      recognition.onend = () => {
        isRecording = false;
        inputWrapper.classList.remove("recording");
        voiceInterface.classList.remove("active");
        clearInterval(timerInterval);
      };

      micBtn.addEventListener("click", () => {
        isRecording ? recognition.stop() : recognition.start();
      });
    }
  } catch (e) {
    console.warn("🎙️ Speech Recognition setup failed:", e);
  }
});
