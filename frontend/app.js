document.getElementById("send").onclick = async () => {
  const msg = document.getElementById("msg").value;

  const res = await fetch("http://127.0.0.1:8000/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: msg }),
  });

  const data = await res.json();
  document.getElementById("answer").textContent = data.answer;
};
