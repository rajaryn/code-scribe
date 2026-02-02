# DevScribe: A Voice-First Agentic Development Environment

> 
> **"Moving from Character-Level Input to Intent-Level Input."** 
> 
> 

**DevScribe** is a "Hands-Free" AI-powered IDE designed to eliminate physical and cognitive barriers in software engineering. By utilizing a specialized multi-agent architecture, it allows developers—particularly those with motor impairments or RSI—to scaffold projects, write logic, and generate complex documentation purely via voice commands.

Unlike standard coding assistants that simply autocomplete text, DevScribe is an autonomous system that **plans, executes, and verifies** entire workflows locally on your machine.

---

## The Problem

We often say that "code is poetry," but the physical act of writing it is a high-friction process.

* **Physical Barriers:** Up to 76% of computer professionals in India report Work-Related Musculoskeletal Disorders (WRMSDs). When a developer loses the ability to type, they are often forced out of their role.

* **Setup Fatigue:** Modern development requires tedious boilerplate generation that drains cognitive energy.

* **Syntax Walls:** Writing scientific documentation in LaTeX is physically exhaustive and prone to syntax errors.


## System Architecture

DevScribe moves away from a monolithic "Chatbot" model toward a **Council of Specialists**—a pipeline of three to four specialized agents.

### 1. The Planner Agent (The Architect)

* **Role:** Converts high-level voice intent (e.g., "Create a Next.js dashboard") into a JSON-serialized project map.

* **Function:** It does not write code; it provisions the physical file structure and directories on the OS to establish the project skeleton.



### 2. The Coder Agent (The Lead Developer)

* **Role:** Handles the logic generation within the structure created by the Planner.
* **Function:** Populates files with functional logic, context-aware of specific extensions like `.cpp`, `.html`, or `.js`.


### 3. The LaTeX Enhancer (The Specialist)

* **Role:** A dedicated agent for scientific and academic documentation.
* **Function:** Uses a **Semantic Translation Layer** to convert spoken math (e.g., "integral from zero to infinity") into compile-ready LaTeX syntax using **Mathstral**.
* **Preview:** Features real-time rendering via MathJar 3.


### 4. The Verifier (The Gatekeeper)

* **Role:** Ensures security and stability in a hands-free environment.
* **Security:** Intercepts destructive shell commands (like `rm -rf`) before execution and requires explicit confirmation.
* **Self-Healing Loop:** Captures `stderr` logs from failed builds and feeds them back to the Coder agent for autonomous patching.

---

## Tech Stack (Local-First Philosophy)

DevScribe rejects cloud dependency in favor of a **Local-First** approach to ensure privacy, zero latency, and offline capability.

* **Backend:** Python (**FastAPI**) - Manages the file tree and orchestrates agents.
* **Frontend:** HTML5, CSS3, JavaScript (AJAX, MediaRecorder).
* **The Brain (Inference):** **Ollama** running locally.
* *Logic:* `Qwen 2.5 Coder`.
* *Math:* `Mathstral`.

* **The Ear (Transcription):**
* **Faster Whisper (int8 quantized):** Used for high-precision scientific notation.
* **Chrome Web Speech API:** Used for low-latency command triggers.
* **Rendering:** **Math Jar 3** for instant LaTeX visual feedback.

---

## Features

* **Voice-Driven Scaffolding:** Create complex folder structures and boilerplate instantly.
* **Voice-to-LaTeX:** Dictate complex matrices and equations without touching the keyboard.
* **Security Sandbox:** "Reflexive Guard" prevents accidental destructive commands.
* **Multi-Mode Preview:** Live preview for both Web (HTML) and Document (LaTeX/PDF) projects.

---

## Roadmap

* **Short-term:** Refinement of the "Self-Healing" feedback loop to loop up to 3 times for a clean build.
* **Mid-term:** Implementation of a UI "Status Shield" that visually glows when the Verifier is scanning code.
* **Long-term:** Full "Voice-First" IDE capable of handling large-scale refactoring and dependency auditing.

---

> DevScribe is not just a tool; it is an intervention. We are bridging the gap between intent and execution, ensuring that physical limitations no longer dictate a developer's potential. 
> 
---