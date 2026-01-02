# Test Management API

The Test Management API provides endpoints for managing test suites, scenarios, and executions. This API allows you to organize, run, and track voice AI conversation tests.

## Overview

The Test Management API is organized into three main resource types:

- **Test Suites**: Collections of related test scenarios
- **Test Scenarios**: Individual test cases with goals and configurations
- **Test Executions**: Records of test runs with results and statistics

All endpoints require a PostgreSQL database connection. Requests to these endpoints will return `501 Not Implemented` if PostgreSQL is not configured.

## Base URL

All test management endpoints are prefixed with `/api/v1/tests`.

## Test Suites

Test suites are collections of related test scenarios. They help organize tests into logical groups.

### Create Test Suite

Create a new test suite.

**Endpoint:** `POST /api/v1/tests/suites`

**Request Body:**

```json
{
  "name": "Regression Suite",
  "description": "Daily regression tests"
}
```

**Response:** `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Regression Suite",
  "description": "Daily regression tests",
  "status": "pending",
  "created_at": "2024-01-15T10:00:00Z"
}
```

### List Test Suites

Get a list of all test suites.

**Endpoint:** `GET /api/v1/tests/suites`

**Response:** `200 OK`

```json
{
  "count": 2,
  "suites": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Regression Suite",
      "description": "Daily regression tests",
      "status": "pending",
      "created_at": "2024-01-15T10:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Smoke Tests",
      "description": "Quick smoke tests",
      "status": "completed",
      "created_at": "2024-01-15T09:00:00Z"
    }
  ]
}
```

### Get Test Suite

Get detailed information about a specific test suite.

**Endpoint:** `GET /api/v1/tests/suites/{suite_id}`

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Regression Suite",
  "description": "Daily regression tests",
  "status": "pending",
  "created_at": "2024-01-15T10:00:00Z"
}
```

### Update Test Suite

Update an existing test suite.

**Endpoint:** `PUT /api/v1/tests/suites/{suite_id}`

**Request Body:**

```json
{
  "name": "Updated Suite Name",
  "description": "Updated description",
  "status": "running"
}
```

**Response:** `200 OK`

### Delete Test Suite

Delete a test suite. This will also delete all associated test scenarios.

**Endpoint:** `DELETE /api/v1/tests/suites/{suite_id}`

**Response:** `204 No Content`

## Test Scenarios

Test scenarios define individual test cases with specific goals and configurations.

### Create Test Scenario

Create a new test scenario within a test suite.

**Endpoint:** `POST /api/v1/tests/scenarios`

**Request Body:**

```json
{
  "suite_id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Order Status Check",
  "goal": "User checks order status",
  "persona_json": {
    "role": "customer",
    "tone": "polite"
  },
  "max_turns": 10,
  "timeout": 300
}
```

**Response:** `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "suite_id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Order Status Check",
  "goal": "User checks order status",
  "persona_json": {
    "role": "customer",
    "tone": "polite"
  },
  "max_turns": 10,
  "timeout": 300
}
```

### List Test Scenarios

Get a list of test scenarios with optional filtering by suite.

**Endpoint:** `GET /api/v1/tests/scenarios?suite_id={suite_id}`

**Query Parameters:**

- `suite_id` (optional): Filter scenarios by test suite ID

**Response:** `200 OK`

```json
{
  "count": 2,
  "scenarios": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "suite_id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Order Status Check",
      "goal": "User checks order status",
      "persona_json": {},
      "max_turns": 10,
      "timeout": 300
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "suite_id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Payment Processing",
      "goal": "User processes payment",
      "persona_json": {},
      "max_turns": 15,
      "timeout": 600
    }
  ]
}
```

### Get Test Scenario

Get detailed information about a specific test scenario.

**Endpoint:** `GET /api/v1/tests/scenarios/{scenario_id}`

**Response:** `200 OK`

### Update Test Scenario

Update an existing test scenario.

**Endpoint:** `PUT /api/v1/tests/scenarios/{scenario_id}`

**Request Body:**

```json
{
  "name": "Updated Scenario Name",
  "goal": "Updated goal",
  "persona_json": {
    "role": "admin"
  },
  "max_turns": 15,
  "timeout": 600
}
```

**Response:** `200 OK`

### Delete Test Scenario

Delete a test scenario.

**Endpoint:** `DELETE /api/v1/tests/scenarios/{scenario_id}`

**Response:** `204 No Content`

## Test Executions

Test executions represent runs of test scenarios with results and statistics.

### Run Tests

Trigger execution of test scenarios. You can run all scenarios in a suite or specific scenarios.

**Endpoint:** `POST /api/v1/tests/run`

**Request Body:**

```json
{
  "suite_id": "550e8400-e29b-41d4-a716-446655440001",
  "scenarios": ["550e8400-e29b-41d4-a716-446655440000"],
  "max_workers": 10
}
```

**Request Fields:**

- `suite_id` (optional): Run all scenarios in this suite
- `scenarios` (optional): List of specific scenario IDs to run
- `max_workers` (required): Maximum number of parallel workers (1-100)

**Note:** Either `suite_id` or `scenarios` must be provided.

**Response:** `201 Created`

```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "scenarios_count": 2,
  "estimated_duration": 300
}
```

### Get Test Summary

Get test summary statistics with optional filtering by suite.

**Endpoint:** `GET /api/v1/tests/summary?suite_id={suite_id}`

**Query Parameters:**

- `suite_id` (optional): Filter statistics by test suite ID

**Response:** `200 OK`

```json
{
  "total": 50,
  "passed": 40,
  "failed": 10,
  "pass_rate": 0.8,
  "avg_duration_ms": 45000,
  "avg_latency_ms": 850
}
```

**Response Fields:**

- `total`: Total number of completed test executions
- `passed`: Number of passed tests
- `failed`: Number of failed tests
- `pass_rate`: Pass rate as a decimal (0.0 to 1.0)
- `avg_duration_ms`: Average test duration in milliseconds
- `avg_latency_ms`: Average latency in milliseconds

### Get Execution Status

Get the status and details of a specific test execution.

**Endpoint:** `GET /api/v1/tests/executions/{execution_id}`

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "scenario_id": "550e8400-e29b-41d4-a716-446655440001",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440002",
  "status": "completed",
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:05:00Z",
  "result_json": {
    "passed": true,
    "score": 0.95
  }
}
```

**Response Fields:**

- `id`: Execution UUID
- `scenario_id`: Associated test scenario UUID
- `conversation_id`: Associated conversation UUID (if any)
- `status`: Execution status (`pending`, `running`, `completed`, `failed`)
- `started_at`: Start timestamp (ISO 8601)
- `completed_at`: Completion timestamp (ISO 8601)
- `result_json`: Execution results as JSON

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request

Invalid request format or missing required fields.

```json
{
  "error": "bad_request",
  "message": "Invalid request",
  "detail": "Either suite_id or scenarios must be provided"
}
```

### 404 Not Found

Resource not found.

```json
{
  "error": "not_found",
  "message": "Resource not found",
  "detail": "Test suite '550e8400-e29b-41d4-a716-446655440000' not found"
}
```

### 501 Not Implemented

PostgreSQL database not configured.

```json
{
  "error": "not_implemented",
  "message": "Test API requires PostgreSQL database",
  "detail": null
}
```

## Usage Examples

### Create a Test Suite and Scenarios

```bash
# Create a test suite
curl -X POST http://localhost:8000/api/v1/tests/suites \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Regression Suite",
    "description": "Daily regression tests"
  }'

# Create a test scenario
curl -X POST http://localhost:8000/api/v1/tests/scenarios \
  -H "Content-Type: application/json" \
  -d '{
    "suite_id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Order Status Check",
    "goal": "User checks order status",
    "max_turns": 10,
    "timeout": 300
  }'
```

### Run Tests

```bash
# Run all scenarios in a suite
curl -X POST http://localhost:8000/api/v1/tests/run \
  -H "Content-Type: application/json" \
  -d '{
    "suite_id": "550e8400-e29b-41d4-a716-446655440001",
    "max_workers": 10
  }'

# Run specific scenarios
curl -X POST http://localhost:8000/api/v1/tests/run \
  -H "Content-Type: application/json" \
  -d '{
    "scenarios": [
      "550e8400-e29b-41d4-a716-446655440000",
      "550e8400-e29b-41d4-a716-446655440002"
    ],
    "max_workers": 10
  }'
```

### Get Test Summary

```bash
# Get overall summary
curl http://localhost:8000/api/v1/tests/summary

# Get summary for a specific suite
curl "http://localhost:8000/api/v1/tests/summary?suite_id=550e8400-e29b-41d4-a716-446655440001"
```

### Check Execution Status

```bash
curl http://localhost:8000/api/v1/tests/executions/550e8400-e29b-41d4-a716-446655440000
```

## Field Descriptions

### Test Suite Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Unique identifier for the test suite |
| `name` | string | Test suite name |
| `description` | string \| null | Test suite description |
| `status` | string | Suite status (`pending`, `running`, `completed`) |
| `created_at` | string (ISO 8601) \| null | Creation timestamp |

### Test Scenario Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Unique identifier for the test scenario |
| `suite_id` | string (UUID) | Parent test suite UUID |
| `name` | string | Test scenario name |
| `goal` | string | Test scenario goal/objective |
| `persona_json` | object | Persona configuration (JSON) |
| `max_turns` | integer \| null | Maximum number of conversation turns |
| `timeout` | integer \| null | Timeout in seconds |

### Test Execution Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Unique identifier for the execution |
| `scenario_id` | string (UUID) | Associated test scenario UUID |
| `conversation_id` | string (UUID) \| null | Associated conversation UUID |
| `status` | string | Execution status |
| `started_at` | string (ISO 8601) \| null | Start timestamp |
| `completed_at` | string (ISO 8601) \| null | Completion timestamp |
| `result_json` | object | Execution results (JSON) |
