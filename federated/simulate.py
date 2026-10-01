"""Run server + 3 hospital clients locally: python -m federated.simulate"""
import subprocess, sys, time
srv = subprocess.Popen([sys.executable, "-m", "federated.server"]); time.sleep(5)
cl = [subprocess.Popen([sys.executable, "-m", "federated.client", "--id", str(i)]) for i in range(3)]
for c in cl: c.wait()
srv.wait()
