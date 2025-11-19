## **Project Overview**

This project is a **speech-to-text prototype** built with the **OpenAI API** (`gpt-4o-transcribe` / `whisper-1`).
It can **transcribe multi-language audio** while **keeping each word in its original language or script** (code-switching).
The output is **plain text only** — no JSON, no subtitles, and no punctuation correction.

It was designed as a **proof of concept (PoC)** for client demos.


## **Main Components**

### **1. ASR Layer (Speech → Text)**

* Uses **OpenAI models** for transcription.
* Works with streaming or batch audio.
* Supports a **custom lexicon** (list of domain-specific terms) to help recognize important words like drug names or brand names.
* Produces raw text with high accuracy.


### **2. Post-Processing Layer**

* **Keeps original language/script** of each word.
* **Handles numerals** (e.g., “10 mg”) consistently.
* **Uses the lexicon** to fix misspellings and protect critical words.
*  **output styles** is plain text paragraph


### **3. Feedback & Learning**

* Reviewers can quickly edit transcripts and see differences.
* The system learns from edits — adding new terms or corrections to the lexicon.
* Monitors performance metrics like accuracy, edit rate, and latency.
* Allows versioning and quick rollback of any change.


### **4. Data Layer**

* Supports **WAV, MP3, and M4A** audio files.
* Keeps a **JSON-based lexicon** for each task or flow.

