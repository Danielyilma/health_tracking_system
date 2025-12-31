# Health Tracking System - Distributed System Mini-Project

A microservices-based distributed system for health tracking, demonstrating service decomposition, RESTful communication, and event-driven architecture.

## Architecture Overview

The system allows users to register, log in, and submit health data (steps, weight, etc.). It distributes this data to ancillary services asynchronously.

### Components

| Service | Responsibility | Port (Host) | DB |
| :--- | :--- | :--- | :--- |
| **API Gateway** | Entry point, routes requests to internal services | `8000` | N/A |
| **Auth Service** | User registration & JWT issuance | Internal | `auth_db` |
| **Health Service** | Stores health records, publishes events | Internal | `health_db` |
| **Notification Service** | Consumes events, simulates push notifications | N/A | N/A |
| **Analytics Service** | Consumes events, aggregates stats (avg steps) | Internal | `analytics_db` |

### Communication Patterns
- **Synchronous (REST)**: Client -> Gateway -> Auth/Health Services.
- **Asynchronous (Pub/Sub)**: Health Service -> RabbitMQ -> Notification/Analytics Services.

## Tech Stack
- **Backend**: Python (FastAPI)
- **Database**: PostgreSQL (Multiple logical databases)
- **Broker**: RabbitMQ
- **Infrastructure**: Docker & Docker Compose

## Getting Started

### Prerequisites
- Docker & Docker Compose installed.

### Setup
1.  Clone this repository.
2.  Navigate to the project root:
    ```bash
    cd HealthTrackingSystem
    ```
3.  Check the `.env` file (defaults are provided for local dev).

### Running the System
Start all services in detached mode:

```bash
docker-compose up -d --build
```

### Verification
1.  **Check Services**: `docker-compose ps`
2.  **API Health**: Visit `http://localhost:8000/health` (Gateway)
3.  **Logs**: Follow logs to see event processing:
    ```bash
    docker-compose logs -f notification_service analytics_service
    ```

### Example Usage (curl)

1.  **Register**:
    ```bash
    curl -X POST "http://localhost:8000/auth/register" -H "Content-Type: application/json" -d '{"username": "alice", "password": "password123"}'
    ```

2.  **Login** (Get Token):
    ```bash
    curl -X POST "http://localhost:8000/auth/login" -d "username=alice&password=password123"
    ```
    *Copy the `access_token` from the response.*

3.  **Submit Health Data**:
    ```bash
    curl -X POST "http://localhost:8000/health-data" \
      -H "Content-Type: application/json" \
      -d '{"username": "alice", "steps": 5000, "sleep_hours": 7.5, "weight": 70.0}'
    ```
    *You should see logs in Notification and Analytics services reacting to this.*

4.  **View Analytics**:
    Check the database or logs. The Analytics service updates the average steps in its own DB.

## Development Notes
- Databases are initialized via `init_db.sql`.
- Services wait for RabbitMQ/Postgres to be healthy before starting.
