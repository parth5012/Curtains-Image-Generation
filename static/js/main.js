/* ═══════════════════════════════════════════════════════
   CurtainViz – main.js  (Frontend Logic)
   ═══════════════════════════════════════════════════════ */

(function () {
  "use strict";

  // ── State ──────────────────────────────────────────────
  const state = {
    fileKey: null,
    previewSrc: null,
    previewMime: null,
    selections: {
      curtain_type: "Panel",
      fabric: "Linen",
      rod_type: "standard",
      color: "white",
    },
  };

  // ── DOM refs ───────────────────────────────────────────
  const uploadZone      = document.getElementById("upload-zone");
  const fileInput       = document.getElementById("file-input");
  const uploadInner     = document.getElementById("upload-inner");
  const previewWrapper  = document.getElementById("preview-wrapper");
  const previewImg      = document.getElementById("preview-img");
  const changeBtn       = document.getElementById("change-btn");
  const generateBtn     = document.getElementById("generate-btn");
  const resultArea      = document.getElementById("result-area");
  const beforeImg       = document.getElementById("before-img");
  const afterImg        = document.getElementById("after-img");
  const downloadBtn     = document.getElementById("download-btn");
  const loadingOverlay  = document.getElementById("loading-overlay");
  const errorToast      = document.getElementById("error-toast");
  const toastMsg        = document.getElementById("toast-msg");
  const toastClose      = document.getElementById("toast-close");

  // Summary labels
  const sumCurtain  = document.getElementById("sum-curtain");
  const sumFabric   = document.getElementById("sum-fabric");
  const sumRod      = document.getElementById("sum-rod");
  const sumColor    = document.getElementById("sum-color");
  const colorLabel  = document.getElementById("color-label-text");

  // ── Option Cards / Swatches ────────────────────────────
  document.querySelectorAll(".option-card").forEach((card) => {
    card.addEventListener("click", () => {
      const group = card.dataset.group;
      const value = card.dataset.value;

      // Deselect siblings in the same group
      document.querySelectorAll(`[data-group="${group}"]`).forEach((el) => {
        el.classList.remove("active");
      });
      card.classList.add("active");

      state.selections[group] = value;
      updateSummary();
    });
  });

  document.querySelectorAll(".color-swatch").forEach((swatch) => {
    swatch.addEventListener("click", () => {
      document.querySelectorAll(".color-swatch").forEach((el) => el.classList.remove("active"));
      swatch.classList.add("active");
      state.selections.color = swatch.dataset.value;
      colorLabel.textContent = capitalize(swatch.dataset.value);
      updateSummary();
    });
  });

  function updateSummary() {
    sumCurtain.textContent = state.selections.curtain_type;
    sumFabric.textContent  = state.selections.fabric;
    sumRod.textContent     = capitalize(state.selections.rod_type);
    sumColor.textContent   = capitalize(state.selections.color);
  }

  function capitalize(str) {
    return str
      .split(" ")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ");
  }

  // ── Upload Zone ────────────────────────────────────────
  uploadZone.addEventListener("click", (e) => {
    if (e.target === changeBtn) return;
    fileInput.click();
  });

  changeBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    resetUpload();
    fileInput.click();
  });

  uploadZone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fileInput.click();
    }
  });

  // Drag-and-drop
  uploadZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadZone.classList.add("drag-over");
  });
  uploadZone.addEventListener("dragleave", () => uploadZone.classList.remove("drag-over"));
  uploadZone.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadZone.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) handleFile(fileInput.files[0]);
  });

  function handleFile(file) {
    const allowed = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
    if (!allowed.includes(file.type)) {
      showError("Unsupported file type. Please upload a JPG, PNG, or WEBP image.");
      return;
    }

    // Show local preview immediately
    const reader = new FileReader();
    reader.onload = (ev) => {
      previewImg.src       = ev.target.result;
      state.previewSrc     = ev.target.result;
      uploadInner.classList.add("hidden");
      previewWrapper.classList.remove("hidden");
    };
    reader.readAsDataURL(file);

    // Upload to server
    const formData = new FormData();
    formData.append("image", file);

    fetch("/upload", { method: "POST", body: formData })
      .then((r) => r.json())
      .then((data) => {
        if (data.error) {
          showError(data.error);
          resetUpload();
          return;
        }
        state.fileKey    = data.file_key;
        state.previewMime = data.mime;
      })
      .catch(() => {
        showError("Failed to upload image. Please try again.");
        resetUpload();
      });
  }

  function resetUpload() {
    state.fileKey   = null;
    state.previewSrc = null;
    previewImg.src  = "";
    fileInput.value = "";
    previewWrapper.classList.add("hidden");
    uploadInner.classList.remove("hidden");
    resultArea.classList.add("hidden");
  }

  // ── Generate ───────────────────────────────────────────
  generateBtn.addEventListener("click", async () => {
    if (!state.fileKey) {
      showError("Please upload a window photo first.");
      return;
    }

    setLoading(true);
    resultArea.classList.add("hidden");

    try {
      const response = await fetch("/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_key:     state.fileKey,
          curtain_type: state.selections.curtain_type,
          fabric:       state.selections.fabric,
          rod_type:     state.selections.rod_type,
          color:        state.selections.color,
        }),
      });

      const data = await response.json();

      if (data.error) {
        showError(data.error);
        return;
      }

      // Show before/after
      beforeImg.src = state.previewSrc;
      afterImg.src  = data.image;
      resultArea.classList.remove("hidden");

      // Scroll into view
      resultArea.scrollIntoView({ behavior: "smooth", block: "nearest" });

      // Store for download
      downloadBtn._imageSrc  = data.image;
      downloadBtn._imageMime = data.mime;
    } catch (err) {
      showError("A network error occurred. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  });

  // ── Download ───────────────────────────────────────────
  downloadBtn.addEventListener("click", () => {
    const src = downloadBtn._imageSrc;
    if (!src) return;

    const ext = (downloadBtn._imageMime || "image/png").split("/")[1];
    const a   = document.createElement("a");
    a.href     = src;
    a.download = `curtainviz-result.${ext}`;
    a.click();
  });

  // ── Loading ────────────────────────────────────────────
  function setLoading(active) {
    generateBtn.disabled = active;
    if (active) {
      loadingOverlay.classList.remove("hidden");
    } else {
      loadingOverlay.classList.add("hidden");
    }
  }

  // ── Error Toast ────────────────────────────────────────
  function showError(msg) {
    toastMsg.textContent = msg;
    errorToast.classList.remove("hidden");

    // Auto-hide after 6 seconds
    clearTimeout(showError._timer);
    showError._timer = setTimeout(hideError, 6000);
  }

  function hideError() {
    errorToast.classList.add("hidden");
  }

  toastClose.addEventListener("click", hideError);

})();
