// Cloudflare Worker for Stella
// 권장 방식:
// Cloudflare Worker 설정에서 Secret/환경변수 이름을 OPENAI_API_KEY로 추가하세요.
//
// 임시 방식:
// 아래 FALLBACK_OPENAI_API_KEY에 직접 API Key를 넣어도 됩니다.
// 단, Worker 코드에 직접 넣으면 코드 접근 권한이 있는 사람에게 노출될 수 있습니다.

const FALLBACK_OPENAI_API_KEY = "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";
const DEFAULT_MODEL = "gpt-5.5";

const ALLOWED_MODELS = [
  "gpt-4.1-mini",
  "gpt-4.1",
  "gpt-4o-mini",
  "gpt-4o",
  "gpt-5-mini",
  "gpt-5.5"
];

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders() });
    }

    if (url.pathname !== "/api/stella") {
      return json({ error: "Not found" }, 404);
    }

    if (request.method !== "POST") {
      return json({ error: "Method not allowed" }, 405);
    }

    const apiKey = env.OPENAI_API_KEY || FALLBACK_OPENAI_API_KEY;

    if (!apiKey || apiKey === "PASTE_OPENAI_API_KEY_HERE") {
      return json({
        error: "OPENAI_API_KEY is not configured. Cloudflare Secret 또는 FALLBACK_OPENAI_API_KEY에 API Key를 넣어주세요."
      }, 500);
    }

    try {
      const body = await request.json();

      const system =
        body.system ||
        "당신은 Stella입니다. 한국어로 친절하고 간결하게 답변하세요.";

      const history = Array.isArray(body.history) ? body.history : [];
      const message = String(body.message || "").slice(0, 30000);

      if (!message.trim()) {
        return json({ error: "message is empty." }, 400);
      }

      const input = [
        { role: "system", content: system },
        ...history.slice(-12),
        { role: "user", content: message }
      ];

      const openaiResponse = await fetch("https://api.openai.com/v1/responses", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${apiKey}`
        },
        body: JSON.stringify({
          model: env.OPENAI_MODEL || DEFAULT_MODEL,
          input
        })
      });

      const raw = await openaiResponse.text();

      if (!openaiResponse.ok) {
        let error = raw;

        try {
          const parsed = JSON.parse(raw);
          error = parsed.error?.message || raw;
        } catch {}

        return json({ error }, openaiResponse.status);
      }

      const data = JSON.parse(raw);
      let text = data.output_text || "";

      if (!text && Array.isArray(data.output)) {
        const parts = [];

        for (const item of data.output) {
          for (const content of item.content || []) {
            if (content.type === "output_text" && content.text) {
              parts.push(content.text);
            }
          }
        }

        text = parts.join("\n");
      }

      return json({
        text: text || "응답 텍스트가 없습니다."
      });
    } catch (error) {
      return json({
        error: error.message || "Unknown error"
      }, 500);
    }
  }
};

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json; charset=utf-8"
  };
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: corsHeaders()
  });
}