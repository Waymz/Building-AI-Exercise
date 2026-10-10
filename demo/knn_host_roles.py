# Guess what an unidentified host is from the TCP ports it has open,
# using k-nearest neighbors (Building AI, chapter 3), and show the evidence.
import numpy as np

K = 5
MIN_AGREEMENT = 0.6   # below this share of neighbor votes, answer "unknown"

# read the data: column 0 = host name, 1 = role, the rest = 0/1 per port
header = open("hosts.csv").readline().strip().split(",")
ports = [int(h[1:]) for h in header[2:]]
names = np.genfromtxt("hosts.csv", delimiter=",", skip_header=1, usecols=0, dtype=str)
roles = np.genfromtxt("hosts.csv", delimiter=",", skip_header=1, usecols=1, dtype=str)
X = np.genfromtxt("hosts.csv", delimiter=",", skip_header=1)[:, 2:]

# hold out the last 25% as test data the classifier never sees while "training"
split = int(len(X) * 0.75)
X_train, X_test = X[:split], X[split:]
y_train, y_test = roles[:split], roles[split:]
names_test = names[split:]


def distance(a, b):
    # Manhattan distance on 0/1 vectors = number of ports that differ
    return np.sum(np.abs(a - b))


def classify(x):
    d = np.array([distance(x, t) for t in X_train])
    nearest = np.argsort(d)[:K]
    votes = {}
    for i in nearest:
        votes[y_train[i]] = votes.get(y_train[i], 0) + 1
    best = max(votes, key=votes.get)
    agreement = votes[best] / K
    if agreement < MIN_AGREEMENT:
        best = "unknown"
    return best, agreement, nearest


correct = answered = 0
for x, truth, name in zip(X_test, y_test, names_test):
    guess, agreement, nearest = classify(x)
    if guess != "unknown":
        answered += 1
        correct += guess == truth

# accuracy on the hosts it was willing to answer, and how often it abstained
print(f"test hosts: {len(X_test)}  answered: {answered}  "
      f"abstained: {len(X_test) - answered}  accuracy when answering: {correct / answered:.0%}")

# one worked example, with the evidence a technician would see
x = X_test[0]
guess, agreement, nearest = classify(x)
print(f"\n{names_test[0]} open ports: {[p for p, b in zip(ports, x) if b]}")
print(f"guess: {guess} ({agreement:.0%} of {K} neighbors agree; truth: {y_test[0]})")
for i in nearest:
    print(f"  {roles[:split][i]:18} differs on {int(distance(x, X_train[i]))} ports, "
          f"open: {[p for p, b in zip(ports, X_train[i]) if b]}")
