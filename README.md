# Evidence-First Migration Planner

*Final project for the Building AI course (University of Helsinki and MinnaLearn).*

## Summary

An assistant that helps IT teams plan a move from old servers to new infrastructure (Hyper-V, Proxmox
or Azure). A small collector maps a company's network: devices, servers, virtual machines and who talks
to whom. AI then fills the gaps in that map and drafts a migration plan in which **every recommendation
points to the evidence behind it**, so an engineer can check it instead of trusting it.

## Background

Before a company moves its servers, someone has to answer three questions: what do we have, what
depends on what, and what should move together? In small and mid-sized businesses the honest answer is
usually "we're not sure." Documentation is stale, the person who built the network has left, and a
forgotten dependency (a license server, a database an old app still calls) is what turns a weekend
cutover into a Monday outage.

This is a common problem, not a rare one. Managed service providers (MSPs) do these assessments for
client after client, mostly by hand with spreadsheets, interviews and screenshots, and the quality
depends on who did the work.

My motivation: I have spent more than 25 years in networking and IT infrastructure, as a network
engineer, a technical account manager running incident response, and an IT manager. I have done these
migrations and I have been on the incident bridge when one went wrong. I am building a network
assessment tool as a personal project, and this course showed me where AI can honestly help it and
where it should stay out of the way.

## How is it used?

1. A technician runs a read-only collector inside the client's network. It discovers switches,
   firewalls, servers and VMs, and records network traffic summaries (which host talks to which host
   on which port).
2. The platform builds an inventory and a dependency map, then proposes move groups and migration
   waves.
3. The engineer reviews each recommendation. Every claim links to its source: "these two servers
   should move together *because* 4,812 connections on TCP 1433 were seen between them over 7 days."
4. The MSP turns the reviewed plan into a quote and a runbook for the client.

**Who is affected, and how they see it:**

| Who | What they want | Risk to them |
|---|---|---|
| MSP technician | Less manual discovery, fewer surprises | Over-trusting a confident wrong guess |
| MSP engineer / vCIO | A plan they can defend to the client | Accountability stays with them, not the tool |
| Client's IT staff | An accurate picture of their own network | Network data leaving their building |
| Client's employees | Their apps keep working after the move | Downtime caused by a missed dependency |
| Client's owner | A fair price and a safe plan | The tool used to upsell work they don't need |

That last row matters: an assessment tool built by the people who sell the migration has a conflict
of interest. Showing the evidence for every recommendation is the main defense.

## Data sources and AI methods

**Data** (all collected read-only from the client's own network):

- TCP port sweep: which hosts are alive and which ports they answer on.
- SNMP, LLDP/CDP and vendor APIs: devices, ports, links, VLANs.
- NetFlow / IPFIX / sFlow: traffic between hosts (who, to whom, which port, how much).
- Hypervisor APIs (vCenter, Hyper-V, Proxmox): VM size and 14 days of CPU, RAM and disk use.

Data quality is the hard part. Some hosts refuse logins, firewalls hide ports, and traffic seen in one
week can miss a job that runs once a month. The design treats every gap as something to report, not
something to paper over.

**Where AI helps, using methods from this course:**

| Problem | Method | Why it fits |
|---|---|---|
| "What is this unknown host?" Hosts we can't log in to only show open ports. | **k-nearest neighbors** with **Manhattan distance** on 0/1 port vectors (demo below). **Naive Bayes** is a natural alternative: each open port is a piece of evidence that shifts the odds of each role. | The labels come for free: hosts we *can* log in to tell us their real role, so each network trains its own classifier. The neighbors are the evidence. |
| "Will this server still fit after the move?" | **Linear regression** (least squares) on 14 days of utilization to project growth. | Simple, explainable, and easy to check against a rule of thumb. |
| "Which past finding or runbook step matches this situation?" | **TF-IDF** similarity between a new finding and a library of earlier findings and fixes. | Retrieves real, written text to cite instead of inventing advice. |
| "Write the plan in plain English." | A large language model, constrained to **cite a fact ID for every claim** and forbidden from producing numbers. Sizes, counts and costs come from rules, not the model. | Saves writing time without letting the model make up facts. |

**What I deliberately did not use AI for:** grouping servers into move groups. Traffic between servers
already *is* the dependency graph; rules over it are more predictable and easier to defend than a
learned model.

### Demo: guessing a host's role from its open ports

The [`demo/`](demo/) folder has a working k-NN classifier in plain Python and NumPy.

- `make_hosts.py` generates `hosts.csv`: 280 **invented** hosts in 7 roles (Windows server, domain
  controller, Linux server, printer, IP camera, network device, workstation), each with the ports a
  sweep found open across 22 common ports. Noise is added: typical ports sometimes blocked, odd ports
  sometimes open.
- `knn_host_roles.py` holds out 25% as test data, classifies each test host by majority vote of its
  5 nearest neighbors, answers "unknown" when fewer than 60% of neighbors agree, and prints the
  neighbors as evidence.

```
$ python3 make_hosts.py
wrote 280 hosts, 22 ports
$ python3 knn_host_roles.py
test hosts: 70  answered: 70  abstained: 0  accuracy when answering: 96%

host211 open ports: [22, 88, 3306, 5900]
guess: linux-server (60% of 5 neighbors agree; truth: linux-server)
  linux-server       differs on 2 ports, open: [22, 3306]
  linux-server       differs on 3 ports, open: [22]
  linux-server       differs on 3 ports, open: [22, 3306, 5432]
  network-device     differs on 3 ports, open: [22, 88, 161]
  network-device     differs on 3 ports, open: [22, 161, 5900]
```

**Read that 96% with suspicion.** I wrote the rules that generated the data, so the roles are cleaner
than real networks. Real hosts run several roles at once, and a firewall can hide nearly everything.
The worked example shows the more honest picture: only 3 of 5 neighbors agreed, which is exactly the
kind of guess a technician should double-check.

## Challenges

- **It does not replace the engineer.** It proposes; a person decides and is accountable.
- **No labeled history yet.** Predicting which migrations will go badly (for example with logistic
  regression) needs outcomes from real past projects, which don't exist yet.
- **Traffic data has blind spots.** Flow records show which hosts talk, not which program is talking,
  and a short collection window misses monthly or quarterly jobs.
- **Privacy and trust.** Network maps are sensitive. Data has to be sanitized, stored per client and
  deleted on request, and the client should be able to see exactly what was collected.
- **Language models can be confidently wrong.** Requiring a cited source for every sentence reduces
  this but does not eliminate it; a cited fact can still be misread.
- **The demo uses invented data.** Results on real networks will be worse until it is tested on them.

## What next

- Test the host classifier on real (sanitized) networks and compare k-NN with naive Bayes.
- Add banner and TLS-certificate text as features, using TF-IDF, so "port 443 open" becomes
  "port 443 open with a printer's web page."
- Collect migration outcomes over time so a risk model can learn which servers cause trouble.
- Let the engineer's corrections feed back into the classifier, so each wrong guess makes the next
  one better.

## Acknowledgments

- University of Helsinki and MinnaLearn for *Elements of AI*, *Ethics of AI* and *Building AI*. The
  k-NN, Manhattan distance, TF-IDF, regression and naive Bayes methods here come from those courses.
- [NumPy](https://numpy.org/), used by the demo.
- The open standards that make discovery possible: SNMP, LLDP, NetFlow and IPFIX, and sFlow.
- The MSP technical account managers and vCIO who described how assessments are really done today.
- The demo and this write-up were developed with help from Claude (Anthropic) as a coding and
  writing assistant.

## License

Copyright (c) 2026 James Lyle. All rights reserved. This repository is public for viewing as a course
submission only; see [LICENSE](LICENSE). No part of it may be copied, modified or reused without
written permission.
