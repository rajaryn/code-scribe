lucide.createIcons();

document.addEventListener("DOMContentLoaded", () => {
  const textarea = document.getElementById("chat-textarea");
  const micBtn = document.getElementById("mic-btn");
  const voiceInterface = document.getElementById("voice-interface");
  const visualizerContainer = document.getElementById("visualizer-bars");
  const timerDisplay = document.getElementById("recording-timer");
  const statusMsg = document.getElementById("status-msg");
  const sendBtn = document.getElementById("send-btn");

  let recognition;
  let isRecording = false;
  let timerInterval;
  let seconds = 0;

  // --- 1. SETUP VISUALIZER ---
  // Generate bars dynamically (similar to React's .map)
  const BAR_COUNT = 20;
  for (let i = 0; i < BAR_COUNT; i++) {
    const bar = document.createElement("div");
    bar.className = "visualizer-bar";
    // Randomize animation duration/delay for organic feel
    const duration = 0.4 + Math.random() * 0.4; // Between 0.4s and 0.8s
    const delay = Math.random() * 0.5;
    bar.style.animationDuration = `${duration}s`;
    bar.style.animationDelay = `-${delay}s`; // Negative delay starts animation immediately
    bar.style.height = "10%"; // Default low state
    visualizerContainer.appendChild(bar);
  }

  // --- 2. TIMER LOGIC ---
  const formatTime = (totalSeconds) => {
    const mins = Math.floor(totalSeconds / 60)
      .toString()
      .padStart(2, "0");
    const secs = (totalSeconds % 60).toString().padStart(2, "0");
    return `${mins}:${secs}`;
  };

  const startTimer = () => {
    seconds = 0;
    timerDisplay.innerText = "00:00";
    timerInterval = setInterval(() => {
      seconds++;
      timerDisplay.innerText = formatTime(seconds);
    }, 1000);
  };

  const stopTimer = () => {
    clearInterval(timerInterval);
    timerDisplay.innerText = "00:00";
  };

  // --- 3. AUTO RESIZE TEXTAREA ---
  const resizeTextarea = () => {
    textarea.style.height = "auto";
    textarea.style.height = textarea.scrollHeight + "px";

    if (textarea.value.trim().length > 0) {
      sendBtn.removeAttribute("disabled");
      sendBtn.classList.remove("opacity-0", "scale-75");
    } else {
      sendBtn.setAttribute("disabled", "true");
      sendBtn.classList.add("opacity-0", "scale-75");
    }
  };
  textarea.addEventListener("input", resizeTextarea);

  // --- 4. SPEECH RECOGNITION ---
  if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => {
      isRecording = true;
      micBtn.classList.add("recording");

      // UI Transition
      voiceInterface.classList.remove("hidden");
      voiceInterface.classList.add("flex");
      statusMsg.style.opacity = "1";

      startTimer();
    };

    recognition.onresult = (event) => {
      console.log(event);
      let finalTranscript = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        }
      }

      if (finalTranscript) {
        const currentText = textarea.value;
        const spacer =
          currentText.length > 0 && !currentText.endsWith(" ") ? " " : "";
        textarea.value = currentText + spacer + finalTranscript;
        resizeTextarea();
        textarea.scrollTop = textarea.scrollHeight;
      }
    };

    recognition.onend = () => {
      stopRecording();
    };

    recognition.onerror = (e) => {
      console.error("Mic Error:", e.error);
      stopRecording();
      statusMsg.innerText = "Error accessing microphone";
      setTimeout(() => {
        statusMsg.style.opacity = "0";
        statusMsg.innerText = "Listening...";
      }, 2000);
    };
  } else {
    micBtn.style.display = "none";
    console.warn("Speech API not supported");
  }

  // --- 5. CONTROL LOGIC ---
  const toggleMic = () => {
    if (!recognition) return;
    if (isRecording) {
      recognition.stop();
    } else {
      recognition.start();
    }
  };

  const stopRecording = () => {
    if (!isRecording) return;

    isRecording = false;
    micBtn.classList.remove("recording");

    // Hide Interface
    voiceInterface.classList.add("hidden");
    voiceInterface.classList.remove("flex");
    statusMsg.style.opacity = "0";

    stopTimer();
  };

  micBtn.addEventListener("click", toggleMic);

  setTimeout(toggleMic, 3000); // Auto-start recording after 2 seconds
});
