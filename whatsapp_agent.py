import subprocess
import threading
import json
import time

class  WhatsAppAgent:
    def __init__(self, node_script='whatsapp-agent.js'):
        self.process = subprocess.Popen(
            ['node', node_script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',        # تعيين الترميز هنا
            errors='replace',        # استبدال الحروف غير القابلة للفك ترميزها
            bufsize=1
        )
        self.lock = threading.Lock()
        self.responses = []
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def _read_stdout(self):
        for line in self.process.stdout:
            line = line.strip()
            if line:
                with self.lock:
                    self.responses.append(line)

    def _read_stderr(self):
        for line in self.process.stderr:
            line = line.strip()
            if line:
                print(f"[Node stderr] {line}")

    def send_message(self, to_number, message, timeout=10):
        payload = json.dumps({"number": to_number, "message": message})
        with self.lock:
            self.responses.clear()

        try:
            self.process.stdin.write(payload + '\n')
            self.process.stdin.flush()

            start_time = time.time()
            while time.time() - start_time < timeout:
                with self.lock:
                    for resp in self.responses:
                        if "SENT" in resp:
                            return f"✅ WhatsApp message sent to {to_number}"
                        if "ERROR" in resp:
                            return f"❌ Failed to send message: {resp}"
                time.sleep(0.1)
            return "❌ Timeout waiting for response from Node.js"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def close(self):
        self.process.terminate()
        self.process.wait()
