const API_URL = "http://127.0.0.1:8000/api/chat";

const sendBtn = document.getElementById("send");
if (sendBtn) {
  sendBtn.addEventListener("click", async () => {
    const msgInput = document.getElementById("msg");
    const answerBox = document.getElementById("answer");
    if (!msgInput || !answerBox) return;

    const question = msgInput.value.trim();
    if (!question) {
      answerBox.textContent = "Introdueix una pregunta abans d'enviar-la.";
      msgInput.focus();
      return;
    }

    const originalBtnText = sendBtn.textContent;
    sendBtn.disabled = true;
    sendBtn.textContent = "Enviant…";
    answerBox.textContent = "Enviant la consulta al motor d'IA…";

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question }),
      });

      if (!res.ok) {
        const errorBody = await res.json().catch(() => ({}));
        const detail = errorBody?.detail || "No s'ha pogut obtenir resposta de l'IA.";
        throw new Error(detail);
      }
      const data = await res.json();
      answerBox.textContent = data?.answer?.trim() || "La IA no ha retornat resposta.";
    } catch (error) {
      console.error("Error consultant la IA:", error);
      answerBox.textContent =
        error?.message ||
        "Hi ha hagut un problema en consultar l'IA. Torna-ho a intentar en uns segons.";
    } finally {
      sendBtn.disabled = false;
      sendBtn.textContent = originalBtnText;
    }
  });
}

document.querySelectorAll(".prompt-template").forEach((btn) => {
  btn.addEventListener("click", () => {
    const msgInput = document.getElementById("msg");
    if (!msgInput) return;
    const prompt = btn.dataset.promptTemplate || "";
    msgInput.value = prompt;
    msgInput.focus();
  });
});

const setupMapModalAutoLoad = (modalId, iframeId) => {
  const modalEl = document.getElementById(modalId);
  const iframeEl = document.getElementById(iframeId);
  if (!modalEl || !iframeEl) return;

  modalEl.addEventListener("shown.bs.modal", () => {
    if (iframeEl.dataset.loaded === "true") return;
    iframeEl.src = iframeEl.dataset.mapSrc;
    iframeEl.dataset.loaded = "true";
  });
};

setupMapModalAutoLoad("signalModal", "iframe-signal");
setupMapModalAutoLoad("healthModal", "iframe-health");
setupMapModalAutoLoad("clientsModal", "iframe-clients");
