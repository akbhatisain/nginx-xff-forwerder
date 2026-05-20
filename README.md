# DevOps Test Assignment — Safe Public Entry Points for X-Forwarded-For

This repository contains a Docker Compose test environment with three nginx reverse proxies and one HTTP application.

The implementation is intentionally designed so that **each nginx can be used as a public entry point** and **each one sanitizes any client-provided `X-Forwarded-For`**.

## Goal

Demonstrate that:
- a request can arrive at any nginx instance;
- the application receives a trusted client IP in `X-Forwarded-For`;
- forged client `X-Forwarded-For` values are ignored;
- testing is documented with `curl`.

## Why this version is better for the assignment

The original interpretation with chained nginx instances is useful for showing append behavior, but it leaves a gap when requests can enter through any nginx.

This version treats **every exposed nginx as a trust boundary**. That matches the assignment wording more safely: no matter which nginx receives the request first, it resets `X-Forwarded-For` to the actual peer address.

## Architecture

```text
client -> nginx1 -> app
client -> nginx2 -> app
client -> nginx3 -> app
```

Ports exposed on the host:
- `8081` -> nginx1
- `8082` -> nginx2
- `8083` -> nginx3

## Security model

Every public nginx uses:

```nginx
proxy_set_header X-Forwarded-For $remote_addr;
```

That means:
- any incoming client-supplied `X-Forwarded-For` is discarded;
- the application receives only the real client address seen by the nginx entry point;
- the solution is safe regardless of which nginx receives the request.

## Repository layout

```text
.
├── docker-compose.yml
├── README.md
├── app/
│   ├── Dockerfile
│   └── app.py
└── nginx/
    ├── nginx1.conf
    ├── nginx2.conf
    └── nginx3.conf
```

## Run

Start the environment:

```bash
docker compose up --build -d
```

Check that all containers are running:

```bash
docker ps
```

Stop the environment:

```bash
docker compose down
```

## How to test

### 1. Basic request through nginx1

```bash
curl -s http://localhost:8081/ | jq
```

What to check:
- `via_node` should be `nginx1`
- `x_forwarded_for` should contain the real client IP
- `x_real_ip` should contain the same real client IP

### 2. Basic request through nginx2

```bash
curl -s http://localhost:8082/ | jq
```

What to check:
- `via_node` should be `nginx2`
- `x_forwarded_for` should contain the real client IP
- `x_real_ip` should contain the same real client IP

### 3. Basic request through nginx3

```bash
curl -s http://localhost:8083/ | jq
```

What to check:
- `via_node` should be `nginx3`
- `x_forwarded_for` should contain the real client IP
- `x_real_ip` should contain the same real client IP

### 4. Spoofing test through nginx1

```bash
curl -s -H 'X-Forwarded-For: 1.2.3.4' http://localhost:8081/ | jq
```

What to check:
- `x_forwarded_for` must **not** be `1.2.3.4`
- `x_real_ip` must show the actual client IP
- `via_node` should still be `nginx1`

### 5. Spoofing test through nginx2

```bash
curl -s -H 'X-Forwarded-For: 9.9.9.9' http://localhost:8082/ | jq
```

What to check:
- `x_forwarded_for` must **not** be `9.9.9.9`
- `x_real_ip` must show the actual client IP
- `via_node` should still be `nginx2`

### 6. Spoofing test through nginx3

```bash
curl -s -H 'X-Forwarded-For: 8.8.8.8' http://localhost:8083/ | jq
```

What to check:
- `x_forwarded_for` must **not** be `8.8.8.8`
- `x_real_ip` must show the actual client IP
- `via_node` should still be `nginx3`

### 7. Show raw HTTP response headers

```bash
curl -i http://localhost:8081/
```

This can be used to show the full HTTP exchange during testing.

### 8. Watch logs during testing

```bash
docker compose logs -f
```

This helps confirm the containers are running and responding while curl tests are executed.

## Full test protocol

Run all required tests in sequence:

```bash
curl -s http://localhost:8081/ | jq
curl -s http://localhost:8082/ | jq
curl -s http://localhost:8083/ | jq
curl -s -H 'X-Forwarded-For: 1.2.3.4' http://localhost:8081/ | jq
curl -s -H 'X-Forwarded-For: 9.9.9.9' http://localhost:8082/ | jq
curl -s -H 'X-Forwarded-For: 8.8.8.8' http://localhost:8083/ | jq
```

Expected outcome:
- requests are successfully processed through all three nginx entry points;
- the application identifies the nginx node via `via_node`;
- the application receives the actual client IP in `x_forwarded_for` and `x_real_ip`;
- fake client-supplied `X-Forwarded-For` values are ignored.

## Example response

```json
{
  "remote_addr": "172.20.0.2",
  "x_forwarded_for": "172.20.0.1",
  "x_real_ip": "172.20.0.1",
  "via_node": "nginx1"
}
```

Exact addresses depend on Docker network allocation.

## Important note for interview discussion

If the reviewers ask specifically for a multi-hop trusted chain where internal proxies append their addresses, the classic pattern is:

```nginx
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```

But that pattern is only safe when the first public-facing proxy has already sanitized the header. In this solution, the focus is on satisfying the stricter requirement that requests may arrive at **any** nginx.

## Time spent

Approximate implementation time: 1 to 2 hours.

## Git commands

```bash
git init
git add .
git commit -m "Add safe public-entry nginx X-Forwarded-For test bench"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```