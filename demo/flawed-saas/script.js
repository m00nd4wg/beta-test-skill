const start = document.querySelector("#start");
const status = document.querySelector("#status");

console.error("Demo seeded issue: analytics key missing");

fetch("/missing-demo-endpoint.json").catch(() => {
  // This failed request is intentional so the evidence runner has something to record.
});

start.addEventListener("click", () => {
  // Intentionally bad UX: no immediate loading state.
  window.setTimeout(() => {
    status.textContent = "Almost there. This intentionally slow state should have appeared sooner.";
  }, 3800);
});

