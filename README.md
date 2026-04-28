# SecureShop

SecureShop is a deliberately small microservices demo for a university DevSecOps workshop. It runs behind a single **Nginx** API gateway on port **80**; individual services are not published to the host by default.

## Architecture

| Path prefix            | Backend               | Port (internal) |
|------------------------|------------------------|-----------------|
| `/api/users/`          | user-service (Flask) | 8001            |
| `/api/products/`       | product-service        | 8002            |
| `/api/orders/`         | order-service          | 8003            |
| `/api/payments/`       | payment-service (Node) | 8004            |
| `/api/notifications/`  | notification-service   | 8005            |
| `/api/inventory/`      | inventory-service      | 8006            |

Each service uses its own **SQLite** file inside the container. **user-service** exposes `POST /login` and returns a JWT on success.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2

## Run the stack

From the repository root (`secureshop/`):

```bash
docker compose up --build
```

Wait until all containers are healthy, then call the gateway on **http://localhost** (port 80).

### Examples (through the gateway)

- Health: `GET http://localhost/api/users/health`
- Login: `POST http://localhost/api/users/login` with JSON body `{"username":"demo","password":"demo123"}`
- Products: `GET http://localhost/api/products/products`
- Product search (workshop route): `GET http://localhost/api/products/products/search?q=Widget`
- Orders: `GET http://localhost/api/orders/orders`
- Payments: `GET http://localhost/api/payments/payments`
- Notifications: `GET http://localhost/api/notifications/notifications`
- Inventory: `GET http://localhost/api/inventory/inventory`

Paths look duplicated (`/api/products/products`) because the gateway strips the `/api/<service>/` prefix and the Flask/Express apps serve resources under `/products`, `/orders`, etc.

## Stop

Press `Ctrl+C` in the terminal where Compose is running, or from another shell in the same directory:

```bash
docker compose down
```

## CI skeleton

GitHub Actions workflow: `.github/workflows/pipeline.yml`.

## SAST

This workshop repository includes two SAST tracks:

- `Bandit` for the Python services
- `Semgrep` for the full repository, including the Node.js services

### Run locally

Install the tools:

```bash
python -m pip install --user bandit semgrep
```

Run Bandit against the Python services:

```bash
python -m bandit -r ./user-service ./product-service ./order-service ./inventory-service
python -m bandit -r ./user-service ./product-service ./order-service ./inventory-service -f json -o bandit-results.json
python scripts/bandit_json_to_sarif.py bandit-results.json bandit-results.sarif
```

Run Semgrep against the repository:

```bash
semgrep --config=auto --sarif --output semgrep-results.sarif .
```

### GitHub Actions behavior

On every push and pull request to `main`, the workflow:

- runs `Bandit` on the Python services
- converts Bandit JSON output to SARIF
- runs `Semgrep` on the repository
- uploads both SARIF reports to GitHub Code Scanning so findings appear in the Security tab

## Workshop note

The codebase includes **intentionally weak patterns** for static analysis exercises (see in-repo comments tagged for tooling). Do not deploy this stack as-is to any real environment.
