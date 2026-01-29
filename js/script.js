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
  const BAR_COUNT = 20;
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
      // sendBtn.setAttribute("disabled", "true");
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

    voiceInterface.classList.add("hidden");
    voiceInterface.classList.remove("flex");
    statusMsg.style.opacity = "0";

    stopTimer();
  };

  // --- 6. SEND MESSAGE FUNCTION ---
  const sendMessage = () => {
    const message = textarea.value.trim();
    
    if (!message) return;

    // Stop recording if active
    if (isRecording && recognition) {
      recognition.stop();
    }

    // Disable send button and show loading state
    sendBtn.setAttribute("disabled", "true");
    sendBtn.classList.add("opacity-0", "scale-75");
    
    // Show loading status message
    statusMsg.innerText = "Creating project structure...";
    statusMsg.style.opacity = "1";

    // Send data via AJAX
    $.ajax({
      url: "/create-file-structure", 
      type: "POST",
      data: {
        message: message,
        timestamp: new Date().toISOString()
      },
      dataType: "json",
      success: function(response) {
        console.log("Message sent successfully:", response);
        
        // Clear textarea
        textarea.value = "";
        resizeTextarea();
        
        // Check if project was created successfully
        if (response.status === "success" && response.folder_name) {
          // Update status with success message
          statusMsg.innerText = `Project '${response.folder_name}' created! Redirecting...`;
          
          // Redirect after a short delay
          setTimeout(() => {
            window.location.href = `/${response.folder_name}`;
          }, 1500);
        } else {
          // Show error message if creation failed
          statusMsg.innerText = response.message || "Project creation failed";
          setTimeout(() => {
            statusMsg.style.opacity = "0";
            statusMsg.innerText = "Listening...";
            
            // Re-enable send button
            if (textarea.value.trim().length > 0) {
              sendBtn.removeAttribute("disabled");
              sendBtn.classList.remove("opacity-0", "scale-75");
            }
          }, 2000);
        }
      },
      error: function(xhr, status, error) {
        console.error("Error sending message:", error);
        
        // Show error message
        statusMsg.innerText = "Failed to send message";
        setTimeout(() => {
          statusMsg.style.opacity = "0";
          statusMsg.innerText = "Listening...";
        }, 2000);
        
        // Re-enable send button
        if (textarea.value.trim().length > 0) {
          sendBtn.removeAttribute("disabled");
          sendBtn.classList.remove("opacity-0", "scale-75");
        }
      }
    });
  };

  // --- 7. EVENT LISTENERS ---
  micBtn.addEventListener("click", toggleMic);
  sendBtn.addEventListener("click", sendMessage);

  // Allow Enter key to send (Shift+Enter for new line)
  textarea.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (textarea.value.trim().length > 0) {
        sendMessage();
      }
    }
  });

  setTimeout(toggleMic, 3000);
});