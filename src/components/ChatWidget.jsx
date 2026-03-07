import { useState } from "react";

export function ChatWidget({ slug, history, onAppend, apiBase }) {
  const [open, setOpen] = useState(true);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendMessage(event) {
    event.preventDefault();
    if (!message.trim() || loading) {
      return;
    }

    const userMessage = { role: "user", content: message };
    onAppend(userMessage);
    setLoading(true);
    setMessage("");

    const response = await fetch(`${apiBase}/chat/${slug}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMessage.content }),
    });

    if (!response.ok || !response.body) {
      onAppend({ role: "assistant", content: "Chat request failed." });
      setLoading(false);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let assistantText = "";
    onAppend({ role: "assistant", content: "" });

    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        break;
      }
      assistantText += decoder.decode(value, { stream: true });
      onAppend({ role: "assistant", content: assistantText }, true);
    }

    setLoading(false);
  }

  return (
    <div className="fixed bottom-6 right-6 z-30 w-[min(380px,calc(100vw-2rem))]">
      <div className="overflow-hidden rounded-[28px] border border-white/10 bg-[#09100d]/95 shadow-glow backdrop-blur">
        <button
          type="button"
          onClick={() => setOpen((current) => !current)}
          className="flex w-full items-center justify-between px-5 py-4 text-left"
        >
          <div>
            <p className="font-heading text-lg text-white">Project Chat</p>
            <p className="text-sm text-white/45">Ask follow-up questions about the recommendations</p>
          </div>
          <span className="rounded-full bg-accent/15 px-3 py-1 text-xs uppercase tracking-[0.3em] text-accent">
            {open ? "Hide" : "Open"}
          </span>
        </button>

        {open && (
          <>
            <div className="max-h-80 space-y-3 overflow-y-auto border-t border-white/6 px-5 py-4">
              {history.length === 0 ? (
                <p className="text-sm text-white/40">Try: Which two upgrades give the fastest carbon payoff?</p>
              ) : (
                history.map((entry, index) => (
                  <div
                    key={`${entry.role}-${index}`}
                    className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm ${
                      entry.role === "user"
                        ? "ml-auto bg-accent text-bg"
                        : "bg-white/6 text-white/75"
                    }`}
                  >
                    {entry.content}
                  </div>
                ))
              )}
            </div>

            <form onSubmit={sendMessage} className="border-t border-white/6 px-4 py-4">
              <div className="flex gap-3">
                <input
                  value={message}
                  onChange={(event) => setMessage(event.target.value)}
                  placeholder="Ask Gemini about these results"
                  className="flex-1 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none transition focus:border-accent"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="rounded-2xl bg-accent px-4 py-3 text-sm font-medium text-bg disabled:opacity-60"
                >
                  {loading ? "..." : "Send"}
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

