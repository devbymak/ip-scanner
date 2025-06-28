# HTTP IP Scanner for CDN Ranges (Cloudflare & Fastly)

🚀 **A multi-threaded IP scanner that sends HTTP requests to random IPs from popular CDN ranges.**  
This tool helps you discover responsive IPs that can be used in V2Ray or other proxy setups to achieve faster, more stable connections.

---

## ✨ Features

- 📡 Generates random IPs inside predefined Cloudflare and Fastly IP ranges (both are always used together).
- ⚡ Uses HTTP GET requests to quickly test responsiveness (ignores HTTP status codes).
- 🚀 Multi-threaded scanning for high performance.
- 📊 Displays a live progress bar with `tqdm`.
- 📝 Automatically saves responsive IPs with their response times into a timestamped CSV file.

---

## ❓ Why Not Use Ping?

We intentionally avoid ICMP ping. Under Iran’s firewall, ping often yields **false positives** — an IP might show a very low latency with ping but give extremely poor speeds (or fail altogether) when used with XHTTP or WebSocket in V2Ray.

This scanner tests actual HTTP requests, giving a more realistic picture of usable IP performance.

---

## ⚙️ Installation

Requires Python 3.7+.

Install dependencies:

```bash
pip3 install -r requirements.txt
````

---

## 🚀 Usage

Run the script:

```bash
python3 main.py
```

You will be prompted to:

* Which network to test? **[fastly/cloudflare]**: 
* Enter the **number of random IPs** to test (e.g. `5000`)
* Set the **number of parallel worker threads** (recommend: CPU cores × 2)
* Set the **HTTP timeout in seconds** (e.g. `3`)

Example interactive session:

```
Which network to test? [fastly/cloudflare]: fastly
Enter number of IPs to check: 100
Enter number of worker threads [recommended 8]: 2
Enter timeout in seconds [default 1]: 22
```

It will show a progress bar and save results to a file like:

```
results_2025-06-28_16-15-42.csv
```

---

## 📂 Output

CSV file with:

| IP Address | Response Time (seconds) |
| ---------- | ----------------------- |
| 104.16.0.1 | 0.35                    |
| 172.64.1.2 | 0.27                    |
| ...        | ...                     |

You can use these responsive IPs in your V2Ray or Xray configuration for faster connections.

---

## ⚠️ Disclaimer

* This script does **not** inspect HTTP status codes — it only checks for timeout vs. no timeout.
* Use responsibly. Designed for research and optimizing your own proxy setups.

---

## 📜 License

MIT License.

---
