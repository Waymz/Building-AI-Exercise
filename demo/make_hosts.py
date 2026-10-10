# Generates hosts.csv: invented hosts with the TCP ports a sweep found open.
# No real network data. Each role has typical ports, plus noise (ports
# missing because a firewall blocked them, or extra ports from odd software).
import numpy as np

PORTS = [22, 23, 53, 80, 88, 135, 139, 161, 389, 443, 445, 515, 554,
         631, 1433, 3306, 3389, 5432, 5900, 8000, 8080, 9100]

# probability that each typical port is open, per role
ROLES = {
    "windows-server": {135: .95, 139: .8, 445: .95, 3389: .9, 80: .3, 443: .4, 1433: .3},
    "domain-controller": {53: .95, 88: .95, 135: .95, 389: .95, 445: .95, 3389: .8, 139: .7},
    "linux-server": {22: .95, 80: .5, 443: .5, 3306: .3, 5432: .3, 8080: .2},
    "printer": {80: .9, 443: .5, 161: .7, 515: .7, 631: .8, 9100: .95, 23: .2},
    "ip-camera": {80: .9, 554: .95, 443: .4, 8000: .6, 23: .3},
    "network-device": {22: .9, 23: .3, 80: .4, 443: .7, 161: .9},
    "workstation": {135: .9, 139: .6, 445: .8, 3389: .3, 5900: .2},
}
NOISE = 0.03          # chance any other port is open anyway
PER_ROLE = 40

rng = np.random.default_rng(42)
rows = []
for role, typical in ROLES.items():
    for _ in range(PER_ROLE):
        open_ports = [p for p in PORTS if rng.random() < typical.get(p, NOISE)]
        rows.append((role, open_ports))

order = rng.permutation(len(rows))
with open("hosts.csv", "w") as f:
    f.write("host,role," + ",".join(f"p{p}" for p in PORTS) + "\n")
    for n, i in enumerate(order):
        role, open_ports = rows[i]
        bits = ["1" if p in open_ports else "0" for p in PORTS]
        f.write(f"host{n+1:03d},{role}," + ",".join(bits) + "\n")
print(f"wrote {len(rows)} hosts, {len(PORTS)} ports")
