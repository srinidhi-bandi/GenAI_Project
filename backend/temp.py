# app.py
from flask import Flask, request, jsonify, render_template_string
from ollama import Client
import re

app = Flask(__name__)

client = Client(host="http://localhost:11434")
MODEL = "llama3.2"  

LABELS = ["toxic", "hate speech", "harassment", "violent threat", "safe"]

def extract_label(text):
    if not text:
        return "unknown"
    t = text.lower()
    for label in LABELS:
        if re.search(rf"\b{re.escape(label)}\b", t):
            return label
    return "unknown"


HTML_PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Toxicity Detector</title>

  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">

  <style>
    /* Apply Poppins font everywhere */
    body, h2, input, button, p, label {
      font-family: 'Poppins', sans-serif;
    }
    body {
      padding: 2rem;
      background: #0D0D0D;
      color: #E8E8E8;
      font-size: 18px;
    }

    .card {
      background: #141414;
      padding: 2rem;
      border-radius: 16px;
      width: 600px;
      max-width: 95%;
      margin: auto;
      box-shadow: 0 8px 30px rgba(0,0,0,0.6);
      text-align: center;
    }

    h2 {
      text-align: center;
      margin-bottom: 1.5rem;
      color: #00E5FF;
      font-size: 28px;
      font-weight: 700;
    }

    input {
  width: 100%;           /* Full width inside card */
  box-sizing: border-box; /* Include padding & border in width */
  padding: 0.8rem;
  border-radius: 8px;
  border: 2px solid #333;
  background: #0D0D0D;
  color: #fff;
  font-size: 16px;
  margin-bottom: 1rem;
  font-family: 'Poppins', sans-serif;
}

    


    button {
      width: 100%;
      padding: 10px 20px;
      font-size: 18px;
      cursor: pointer;
      font-weight: 700;
      border-radius: 8px;
      color: #00E5FF;
      background-color: transparent;
      border: 2px solid #00E5FF;
      transition: 0.3s ease;
      margin-top: 10px;
    }

    button:hover {
      background-color: #00E5FF;
      color: #0D0D0D;
    }

    p#result {
      margin-top: 1.5rem;
      font-size: 18px;
      padding: 0.8rem;
      border-radius: 8px;
      background: #0B0B0B;
      border: 1px solid #222;
    }
  </style>
</head>
<body>
  <div class="card">
  <h2>Toxicity Detector</h2>

  <label for="text">Enter text</label>
  <input 
      id="text" 
      type="text" 
      placeholder="Type something..." 
      autocomplete="off" 
      autocorrect="off" 
      autocapitalize="off" 
      spellcheck="false"
  />

  <button id="detectBtn">Detect</button>

  <p id="result">Waiting for input...</p>
</div>


  <script>
    const btn = document.getElementById("detectBtn");
    const input = document.getElementById("text");
    const result = document.getElementById("result");

    async function detect() {
      const text = input.value.trim();
      if (!text) {
        result.textContent = "Please enter some text.";
        return;
      }
      result.textContent = "Detecting...";

      try {
        const resp = await fetch("/detect", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text })
        });

        const data = await resp.json();

        if (resp.ok) {
          result.textContent = "Label: " + data.label;
        } else {
          result.textContent = "Error: " + (data.error || "Unknown error");
        }

      } catch (err) {
        result.textContent = "Network error: " + err.message;
      }
    }

    btn.addEventListener("click", detect);
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") detect(); });
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/detect", methods=["POST"])
def detect():
    data = request.get_json(force=True)
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    prompt = f"""
Classify the following text into one category:
[toxic, hate speech, harassment, violent threat, safe].

Text: "{text}"

Return only the category name.
"""

    try:
        resp = client.generate(model=MODEL, prompt=prompt)
        raw = resp.get("response", "").strip()
        label = extract_label(raw)
        return jsonify({"label": label})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
