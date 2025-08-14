// Utilities
function $(id) { return document.getElementById(id); }
function escapeHtml(s) { 
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;"); 
}

// Build table from TSV/text
function buildTableFromTSV(text) {
  if (!text) return "<em>No data</em>";
  const rows = text.replace(/\r/g, "").split("\n").filter(r => r !== "");
  if (!rows.length) return "<em>No data</em>";
  let html = "<table>";
  for (const row of rows) {
    html += "<tr>";
    const cols = row.split("\t");
    for (const c of cols) html += `<td>${escapeHtml(c)}</td>`;
    html += "</tr>";
  }
  html += "</table>";
  return html;
}

document.addEventListener("DOMContentLoaded", () => {
  const monthSel = $("month-select");
  const yearSel = $("year-select");
  const pasteBox = $("paste-box");
  const previewBox = $("preview-box");

  const fileInput = $("file-upload");
  const uploadBtn = $("upload-btn");
  const dropZone = $("drop-zone");
  const uploadStatus = $("upload-status");

  const sendBtn = $("send-btn");
  const sendStatus = $("send-status");

  // Preview on paste and input
  if (pasteBox) {
    pasteBox.addEventListener("paste", (e) => {
      e.preventDefault();
      const text = (e.clipboardData || window.clipboardData).getData("text");
      pasteBox.value = text;
      if (previewBox) previewBox.innerHTML = buildTableFromTSV(text);
    });
    pasteBox.addEventListener("input", () => {
      if (previewBox) previewBox.innerHTML = buildTableFromTSV(pasteBox.value);
    });
  }

  // Upload button -> open file chooser
  if (uploadBtn && fileInput) {
    uploadBtn.addEventListener("click", () => fileInput.click());
  }

  // Upload logic
  async function uploadFile(file) {
    if (!file) return;

    // validate size
    if (file.size > 10 * 1024 * 1024) {
      if (uploadStatus) { 
        uploadStatus.style.color = "red"; 
        uploadStatus.textContent = "File too large (max 10MB)"; 
      }
      return;
    }

    // validate extension
    const name = file.name.toLowerCase();
    if (!(/\.(xlsx|xls|csv)$/.test(name))) {
      if (uploadStatus) { 
        uploadStatus.style.color = "red"; 
        uploadStatus.textContent = "Invalid file type (.xlsx, .xls, .csv)"; 
      }
      return;
    }

    if (uploadStatus) { 
      uploadStatus.style.color = "#333"; 
      uploadStatus.textContent = `Uploading ${file.name}...`; 
    }

    const fd = new FormData();
    fd.append("file", file);

    try {
      const res = await fetch("/upload", { method: "POST", body: fd });
      const json = await res.json();
      if (res.ok && json.success) {
        if (uploadStatus) { 
          uploadStatus.style.color = "green"; 
          uploadStatus.textContent = `Uploaded: ${json.filename}`; 
        }
      } else {
        throw new Error(json.error || "Upload failed");
      }
    } catch (err) {
      console.error(err);
      if (uploadStatus) { 
        uploadStatus.style.color = "red"; 
        uploadStatus.textContent = "Upload failed (check server)"; 
      }
    }
  }

  // File input change
  if (fileInput) {
    fileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) uploadFile(e.target.files[0]);
    });
  }

  // Drag & drop
  if (dropZone) {
    dropZone.addEventListener("dragover", (e) => { 
      e.preventDefault(); 
      dropZone.classList.add("dragover"); 
    });
    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.classList.remove("dragover");
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
        uploadFile(e.dataTransfer.files[0]);
      }
    });
    // Click drop zone -> open file chooser
    dropZone.addEventListener("click", () => fileInput && fileInput.click());
  }

  // Send to admin
  if (sendBtn) {
    sendBtn.addEventListener("click", async () => {
      if (!sendStatus) return;

      const month = monthSel ? monthSel.value : "";
      const year = yearSel ? yearSel.value : "";
      const pasted = pasteBox ? pasteBox.value : "";

      if (!month || !year) {
        sendStatus.style.color = "red";
        sendStatus.textContent = "Please select month and year.";
        return;
      }
      if (!pasted && (!fileInput || !fileInput.files.length)) {
        sendStatus.style.color = "red";
        sendStatus.textContent = "Paste data or upload a file before sending.";
        return;
      }

      sendStatus.style.color = "#333";
      sendStatus.textContent = "Sending...";

      const fd = new FormData();
      fd.append("month", month);
      fd.append("year", year);
      fd.append("pasted_data", pasted);
      if (fileInput && fileInput.files[0]) fd.append("file", fileInput.files[0]);

      try {
        const res = await fetch("/submit", { method: "POST", body: fd });
        const json = await res.json();
        if (res.ok && json.success) {
          sendStatus.style.color = "green";
          sendStatus.textContent = "Sent to admin!";
        } else {
          throw new Error(json.error || "Server error");
        }
      } catch (err) {
        console.error(err);
        sendStatus.style.color = "red";
        sendStatus.textContent = "Failed to send (check server).";
      }
    });
  }

  // Initial render
  if (pasteBox && previewBox) {
    previewBox.innerHTML = buildTableFromTSV(pasteBox.value);
  }
});
