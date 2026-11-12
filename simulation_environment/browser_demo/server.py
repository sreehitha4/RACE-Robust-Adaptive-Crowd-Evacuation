"""Optional local browser preview; not a replacement for teammate Sinan's React app."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
from simulation import CrowdSimulation, SimulationConfig
from simulation.service import SimulationService

ROOT = Path(__file__).resolve().parents[1]
config = SimulationConfig.from_json(ROOT / 'config.json')
sim = CrowdSimulation(config, project_root=ROOT)
service = SimulationService(sim)
class Handler(BaseHTTPRequestHandler):
    def _send(self, data, content_type='application/json'):
        body = data if isinstance(data, bytes) else data.encode()
        self.send_response(200); self.send_header('Content-Type', content_type); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path == '/': self._send((Path(__file__).parent/'index.html').read_bytes(), 'text/html; charset=utf-8')
        elif self.path == '/state':
            if sim.status == 'running': service.advance(2)
            self._send(json.dumps(service.state()))
        else: self.send_error(404)
    def do_POST(self):
        if self.path == '/start': service.start()
        elif self.path == '/pause': service.pause()
        elif self.path == '/reset': service.reset()
        else: self.send_error(404); return
        self._send(json.dumps(service.state()))
    def log_message(self, *_): pass
if __name__ == '__main__':
    print('RACE preview: http://127.0.0.1:8765')
    ThreadingHTTPServer(('127.0.0.1',8765), Handler).serve_forever()
