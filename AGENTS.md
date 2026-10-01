# JobTrack — Project Overview

JobTrack is a LINE-based job application tracking system.

The main purpose of the project is to help users manage and track their job applications through LINE without manually maintaining a spreadsheet.

## Core Features

- Add job applications
- View job applications
- Update job applications
- Delete job applications
- Search and filter job applications
- View application summaries
- Export application data to XLSX
- Process natural language commands through an LLM
- Receive and respond to messages through the LINE Messaging API

## Core Principle

PostgreSQL is the source of truth for application data.

The LLM is responsible for understanding natural language and converting it into structured intent and data.

The backend is responsible for:

- Validating input
- Applying business rules
- Authorizing access
- Reading and writing database data
- Executing application logic
- Generating the final response

The LLM must not directly access or modify the database.

## Tech Stack

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

### Database

- PostgreSQL

### AI / LLM

- LLM API
- LLM is used for natural language understanding and structured intent extraction

### LINE

- LINE Messaging API
- LINE Webhook

### Export

- openpyxl
- XLSX

### Development & Testing

- Docker
- Docker Compose
- Pytest
- Postman
- Git
- GitHub

## Technology Rules

- Use the existing technology stack unless there is a clear reason to change it.
- Do not introduce new frameworks or libraries without explaining why they are needed.
- Prefer simple solutions over unnecessary complexity.
- Follow the existing project structure and coding patterns.

## Architecture & Data Flow

JobTrack uses a layered monolithic architecture with a LINE webhook as the external entry point.

```text
LINE User
   ↓
LINE Messaging API
   ↓
Webhook
   ↓
User Resolver
   ↓
LLM / NLP
   ↓
Business Logic
   ↓
Repository / Data Access
   ↓
PostgreSQL
```

## Layer Responsibilities

### API Layer

Responsible for:

- Receiving HTTP requests
- Validating request input
- Resolving dependencies
- Returning HTTP responses
- Handling HTTP-specific errors

The API layer should not contain complex business logic or database queries.

### Service / Business Logic Layer

Responsible for:

- Application business rules
- Processing user actions
- Coordinating multiple operations
- Deciding what operation should be performed

Business logic should not depend directly on LINE-specific details.

### Repository / Data Access Layer

Responsible for:

- Reading data from PostgreSQL
- Creating records
- Updating records
- Deleting records
- Executing database queries

Database queries should be kept in the repository layer where practical.

### LLM / NLP Layer

Responsible for:

- Understanding natural-language messages
- Extracting structured intent
- Extracting relevant data from user messages
- Determining which supported operation the user is requesting

The LLM must not:

- Access the database directly
- Execute SQL
- Modify database records directly
- Bypass backend validation or business rules

### User Identity

The LINE webhook receives a `line_user_id`.

The system should resolve the LINE user to the internal `user_id`.

Internal business logic and database queries should use `user_id` rather than passing `line_user_id` throughout the application.

Every operation involving job applications must be scoped to the current `user_id` to prevent users from accessing another user's data.

## Project Structure

The project is organized as a monorepo.

```text
line-job-application-tracker/
├── AGENTS.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── core/
│   ├── tests/
│   ├── alembic/
│   ├── .env
│   ├── .env.example
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

### Backend Directory Responsibilities

#### `backend/app/api/`

Contains FastAPI routers and HTTP endpoints.

Responsible for:

- Request handling
- Response handling
- Dependency injection
- HTTP-level validation and errors

Do not place complex business logic or raw database queries here.

#### `backend/app/models/`

Contains SQLAlchemy database models and database-related enums.

These models represent the PostgreSQL database structure.

#### `backend/app/schemas/`

Contains Pydantic schemas used for:

- Request validation
- Response serialization
- Data validation between application layers

#### `backend/app/services/`

Contains business logic and application use cases.

Use this layer when an operation requires business rules or coordination between multiple components.

#### `backend/app/repositories/`

Contains database access logic.

Repository functions should handle database queries and persistence operations.

#### `backend/app/core/`

Contains shared application infrastructure such as:

- Configuration
- Database connection
- Shared application settings

#### `backend/tests/`

Contains automated tests.

Tests should cover important business logic, API behavior, validation, and database-related behavior where appropriate.

## File Placement Rules

- Put HTTP endpoint logic in `api/`.
- Put business logic in `services/`.
- Put database queries in `repositories/`.
- Put database models in `models/`.
- Put Pydantic request/response schemas in `schemas/`.
- Put shared configuration and infrastructure in `core/`.
- Do not create unnecessary files or folders for small changes.
- Follow the existing structure before introducing a new architectural pattern.

## Database & Data Model Rules

PostgreSQL is the source of truth for all job application data.

SQLAlchemy is used for database access and Alembic is used for database migrations.

## Tables

### `users`

| Column         | Type     | Rules                 |
| -------------- | -------- | --------------------- |
| `id`           | UUID     | Primary key, required |
| `line_user_id` | String   | Unique, required      |
| `created_at`   | DateTime | Required              |
| `updated_at`   | DateTime | Required              |

### `job_applications`

| Column         | Type        | Rules                               |
| -------------- | ----------- | ----------------------------------- |
| `id`           | UUID        | Primary key, required               |
| `user_id`      | UUID        | Foreign key to `users.id`, required |
| `company`      | String      | Required                            |
| `position`     | String      | Required                            |
| `job_url`      | String/Text | Optional                            |
| `source`       | String      | Optional                            |
| `location`     | String      | Optional                            |
| `work_mode`    | Enum        | Optional                            |
| `date_applied` | Date        | Optional                            |
| `status`       | Enum        | Required                            |
| `salary`       | String      | Optional                            |
| `note`         | Text        | Optional                            |
| `created_at`   | DateTime    | Required                            |
| `updated_at`   | DateTime    | Required                            |

## Work Mode

Allowed values:

- `Remote`
- `Hybrid`
- `On-site`
- `Unknown`

## Application Status

Allowed values:

- `ยังไม่ได้สมัคร`
- `สมัครแล้ว`
- `กำลังคัดกรอง`
- `นัดสัมภาษณ์`
- `สัมภาษณ์แล้ว`
- `ผ่านการคัดเลือก`
- `ปฏิเสธแล้ว`
- `ไม่มีการตอบกลับ`

Do not add, remove, or rename status values without updating the data model and related application logic.

## Database Rules

### User Isolation

Every query involving `job_applications` must be scoped to the current `user_id`.

For example:

```python
select(JobApplication).where(
    JobApplication.id == application_id,
    JobApplication.user_id == user_id,
)
```

Never retrieve or modify an application using only its `id` when the operation belongs to a specific user.

### Date Handling

`date_applied` represents the date the user applied for the job.

If the user does not provide `date_applied` when creating an application, the backend should default it to the current date.

If the user explicitly provides a date, use the provided date.

### Timestamps

`created_at` and `updated_at` should use timezone-aware timestamps.

### IDs

Use UUIDs for primary keys.

Do not replace UUIDs with auto-incrementing integer IDs unless the data model is intentionally changed.

## Migration Rules

- Use Alembic for database schema changes.
- Do not manually modify the production database schema.
- When changing models, create the corresponding Alembic migration.
- Do not modify existing migrations that have already been applied unless there is a specific migration strategy requiring it.
- Review generated migrations before applying them.

## API & Coding Rules

### API Design

Use REST-style HTTP endpoints where appropriate.

Current application endpoints:

```text id="1byv9w"
POST   /applications
GET    /applications
GET    /applications/{application_id}
PATCH  /applications/{application_id}
DELETE /applications/{application_id}
GET    /applications/summary
GET    /applications/export
```

Follow the existing API design when adding new endpoints.

Do not change existing endpoint behavior unless the task explicitly requires it.

### Request Validation

Use Pydantic schemas for request validation.

Do not rely on manual validation inside every endpoint when Pydantic can handle the validation.

Invalid input should return an appropriate HTTP error response.

### Error Handling

Use appropriate HTTP status codes.

Common cases:

- `400` — Invalid request or business rule violation
- `404` — Resource not found
- `422` — Request validation error
- `500` — Unexpected server error

Do not expose database internals, stack traces, or sensitive information in API responses.

### Database Access

Endpoints should not contain complex SQL queries.

Prefer:

```text id="z4q7sh"
API
 ↓
Service
 ↓
Repository
 ↓
Database
```

For simple CRUD operations, the API may call the repository directly when a service layer provides no meaningful business logic.

Do not create unnecessary service or repository abstractions just for the sake of adding layers.

### Query Efficiency

Prefer database-side operations for aggregation and filtering.

For example, summary queries should use SQL operations such as:

- `COUNT`
- `GROUP BY`
- `WHERE`
- `ORDER BY`

Do not load all records into Python and perform large aggregations there when the database can perform the operation efficiently.

### User Scoping

Every application-related endpoint must identify the current user and ensure that all database operations are scoped to that user.

Never trust a client-provided `user_id` as authorization.

### Updates

For partial updates, use `PATCH`.

Only fields explicitly provided by the client should be updated.

Use Pydantic's `exclude_unset=True` when appropriate.

### Code Changes

When implementing a feature:

1. Understand the existing code first.
2. Reuse existing patterns where possible.
3. Make the smallest change necessary.
4. Do not rewrite unrelated code.
5. Do not change existing behavior without a clear reason.
6. Do not introduce new dependencies unless necessary.
7. Keep functions focused and readable.

Before modifying existing code, check whether the change could affect existing CRUD operations or other features.

## LLM / AI Rules

The LLM is used as a natural-language interface for JobTrack.

The LLM interprets the user's message and converts it into structured intent and data.

The backend remains responsible for validation, authorization, business rules, and database operations.

## LLM Responsibilities

The LLM may:

- Understand natural-language user messages
- Identify the user's intended operation
- Extract structured fields from messages
- Identify relevant application data
- Generate structured output according to the defined schema
- Generate natural-language responses based on backend-provided results

Example:

```text
User:
"สมัคร KBank ตำแหน่ง Backend Developer เมื่อวาน เงินเดือน 30,000"

LLM:
{
  "action": "create_application",
  "company": "KBank",
  "position": "Backend Developer",
  "date_applied": "...",
  "salary": "30000"
}
```

The exact output schema should follow the application's defined Pydantic models or structured-output schema.

## LLM Must Not

The LLM must never:

- Access PostgreSQL directly
- Execute SQL
- Modify database records directly
- Decide whether a user is authorized to access a record
- Bypass backend validation
- Generate or execute arbitrary backend code
- Be treated as the source of truth for application data

The backend must validate all structured data produced by the LLM before performing any database operation.

## Structured Intent

LLM output should represent an explicit supported action.

Examples of supported actions:

```text id="2h8x2p"
create_application
update_application
delete_application
get_applications
get_application
get_summary
export_applications
```

Do not allow arbitrary action names to directly trigger backend operations.

The backend should validate that the requested action is supported before executing it.

## Missing Information

If required information is missing, the system should not invent values.

For example, if the user says:

```text
"สมัครงานบริษัท KBank"
```

and `position` is required, the system should ask the user for the missing position instead of guessing it.

## Ambiguous Information

If the user's request is ambiguous and could result in an incorrect database operation, ask for clarification before modifying data.

Do not allow the LLM to silently guess critical information.

## Database Operations

The execution flow should be:

```text id="r9a7g1"
User Message
     ↓
LLM
     ↓
Structured Intent / Data
     ↓
Pydantic Validation
     ↓
Backend Business Logic
     ↓
Authorization / User Scoping
     ↓
Repository
     ↓
PostgreSQL
```

The LLM interprets the request.

The backend decides what is actually allowed to happen.

## Testing Rules

The project uses Pytest for automated testing.

When implementing a new feature, consider the tests that should verify its expected behavior.

## What Should Be Tested

Tests should cover important cases such as:

- Normal successful operations
- Invalid input
- Missing required fields
- Resource not found
- User data isolation
- Business rule violations
- Database-related behavior
- Edge cases relevant to the feature

## API Tests

API endpoints should be tested for:

- Expected HTTP status codes
- Request validation
- Response structure
- Successful operations
- Error cases
- User authorization and data isolation

## Database Tests

Database-related tests should verify that:

- Records are created correctly
- Records are updated correctly
- Records are deleted correctly
- Queries return only the current user's data
- Summary queries return correct results
- Filtering behaves as expected

## LLM Tests

LLM-related functionality should test structured outputs and important edge cases.

Tests should not depend entirely on live LLM responses when deterministic testing is possible.

Prefer mocking LLM responses for unit tests.

## Test Before Changing Existing Behavior

Before modifying existing functionality:

1. Check whether tests already cover the behavior.
2. Understand the expected behavior.
3. Make the smallest necessary change.
4. Run relevant tests after the change.

Do not remove or weaken existing tests simply to make new code pass.

## Test Commands

Run the relevant test suite with:

```bash
pytest
```

When working on a specific feature, prefer running the relevant tests first for faster feedback, then run the full test suite before completing the change.

## Git & Change Rules

Use Git to track all project changes.

The project uses feature-based branches.

Example:

```text
main
└── dev
    └── feat/application-crud
```

Branch names should describe the purpose of the change.

Examples:

```text
feat/application-summary
feat/line-webhook
feat/llm-intent
fix/application-update
refactor/repository
test/application-crud
```

## Commit Rules

Commits should describe the change clearly.

Examples:

```text
feat: add application summary
fix: prevent cross-user application access
test: add application CRUD tests
refactor: simplify application repository
```

Keep commits focused on a related change.

Avoid mixing unrelated changes in the same commit.

## AI-Generated Changes

Before making significant AI-generated changes:

1. Check the current Git status.
2. Make sure existing work is committed or otherwise safely backed up.
3. Clearly define the scope of the requested change.
4. Review the files that the AI plans to modify.

After the change:

1. Review the diff.
2. Check for unrelated modifications.
3. Run relevant tests.
4. Verify that existing functionality still works.
5. Commit the change only after review.

## Scope Control

AI coding agents must not:

- Modify unrelated features
- Rewrite working code without a clear reason
- Delete existing functionality without explicit instruction
- Change the technology stack without approval
- Add dependencies without explaining why they are needed
- Modify environment configuration unnecessarily
- Change database schema without considering the corresponding migration

When a task can be completed by modifying one or two existing files, do not unnecessarily restructure the project.

## Before Finishing a Task

The AI agent should report:

- What files were changed
- What was implemented
- Important design decisions
- Tests that were added or run
- Any remaining limitations or concerns

## AI Coding Agent Workflow

AI coding agents should follow a structured workflow when implementing changes.

### 1. Understand Before Coding

Before writing code:

- Read the relevant existing files.
- Understand the current architecture.
- Identify existing patterns that should be reused.
- Identify dependencies between the requested change and existing code.
- Confirm the scope of the task.

Do not immediately rewrite or create large amounts of code without understanding the existing implementation.

### 2. Explain the Approach

Before making a significant change, briefly explain:

- What will be changed
- Which files will be modified
- How the change fits into the existing architecture
- Any important design decisions
- Any assumptions being made

For small, straightforward changes, this explanation can be brief.

### 3. Implement Incrementally

Prefer small, focused changes.

Do not implement unrelated features as part of the same task.

Follow the existing project architecture and coding patterns.

Reuse existing functions, schemas, repositories, and utilities when appropriate.

### 4. Preserve Existing Behavior

When adding a feature:

- Do not break existing functionality.
- Do not modify unrelated CRUD behavior.
- Do not change API contracts without explicit instruction.
- Do not change database models unless required by the task.

If an existing implementation needs to change, explain why before making the change.

### 5. Review the Implementation

After coding, review the changes for:

- Correctness
- Security
- User data isolation
- Validation
- Error handling
- Database query efficiency
- Maintainability
- Unnecessary complexity
- Unrelated modifications

Pay particular attention to whether every database query is correctly scoped to `user_id`.

### 6. Run Tests

Run relevant tests after implementation.

If tests do not exist for the changed functionality, consider adding appropriate tests.

Do not claim that a feature works without verifying it when verification is possible.

### 7. Explain the Result

After completing the task, report:

- Files changed
- What was implemented
- How the implementation works
- Tests run and their results
- Any limitations
- Any follow-up work that may be needed

### 8. Teach Important Code

When implementing code that is important for a junior developer to understand, explain the key parts.

Focus on:

- Why the code is structured this way
- Important framework behavior
- Database query logic
- Security considerations
- Potential edge cases

Do not explain every obvious line of code unless specifically requested.

The goal is to help the developer understand and review AI-generated code rather than blindly accepting it.

## Security Rules

Security must be considered whenever code handles user identity, database access, authentication, external APIs, or sensitive configuration.

### User Data Isolation

Every user's job application data must be isolated from other users.

All application queries must be scoped to the authenticated or resolved `user_id`.

Never trust a `user_id` supplied directly by the client when determining authorization.

The backend must determine the current user from the application's trusted identity flow.

### LINE User Identity

`line_user_id` is an external identity provided by the LINE platform.

Do not expose internal database IDs or other users' identifiers through LINE messages or API responses unless explicitly required.

The LINE user must be resolved to the corresponding internal `user_id` before accessing application data.

### Database Security

Use SQLAlchemy parameterized queries or ORM operations.

Do not construct SQL queries by directly concatenating user-provided strings.

Never execute arbitrary SQL generated by an LLM or user input.

All database writes must pass through backend validation and business logic.

### Environment Variables

Secrets and credentials must not be committed to Git.

Examples include:

- Database passwords
- API keys
- LINE channel secrets
- LINE access tokens
- LLM API keys
- JWT secrets

Use environment variables for sensitive configuration.

`.env` should not be committed.

`.env.example` may contain variable names and safe example values, but must not contain real credentials.

### External APIs

External API responses should be treated as untrusted input.

Validate and handle external data before using it in application logic or database operations.

Do not expose external API credentials to the frontend.

### LLM Security

Treat LLM output as untrusted input.

The backend must validate structured LLM output before executing any action.

Never allow an LLM response to directly execute:

- SQL
- Shell commands
- Python code
- Arbitrary HTTP requests
- Database operations

Prompt injection or malicious instructions contained in user messages must not bypass backend authorization or validation.

### Error Messages

Do not expose:

- Database connection details
- SQL statements
- API keys
- Access tokens
- Stack traces
- Internal file paths
- Sensitive user data

to end users.

Detailed errors may be logged internally when appropriate.

### Logging

Do not log sensitive information unnecessarily.

Avoid logging:

- API keys
- Access tokens
- Passwords
- Database credentials
- Full private user data

Logs should contain enough information for debugging without exposing secrets.

## Documentation & Code Quality

Code should be understandable, maintainable, and consistent with the existing project.

### Code Style

- Follow the existing coding style.
- Prefer clear and descriptive names.
- Keep functions focused on a single responsibility.
- Avoid unnecessarily complex abstractions.
- Prefer readability over clever code.
- Keep duplicated code to a reasonable minimum.
- Do not optimize prematurely.

### Type Safety

Use Python type hints for functions, parameters, and return values where practical.

Prefer explicit types over untyped values when the type is meaningful.

Use Pydantic models for structured request and response data.

### Comments

Comments should explain why something is done when the reason is not obvious from the code.

Do not add comments that simply restate what the code already says.

Avoid excessive comments.

### Documentation

Update documentation when a change affects:

- API behavior
- Environment variables
- Database setup
- Project setup
- Deployment
- Important architecture decisions

The README should remain accurate enough for a new developer to understand how to run the project.

### Dependencies

Before adding a dependency:

- Check whether the existing project already provides the required functionality.
- Consider whether the dependency is necessary.
- Explain why it is needed.
- Avoid adding dependencies for trivial functionality.

Do not replace an existing library or framework without a clear reason.

### Configuration

Configuration should be centralized where practical.

Do not hardcode:

- API keys
- Passwords
- URLs that should be configurable
- Environment-specific settings

Use environment variables for environment-specific configuration.

### Maintainability

Prefer solutions that are:

- Simple
- Explicit
- Testable
- Easy for a junior developer to understand
- Consistent with the existing architecture

Do not introduce abstractions solely to make the code appear more sophisticated.

## MVP Scope & Out of Scope

The current goal is to build a simple, reliable MVP.

Prefer completing the required functionality before adding additional infrastructure or features.

## MVP Features

The MVP includes:

- LINE text-based interaction
- Create job applications
- View job applications
- View a single job application
- Update job applications
- Delete job applications
- Search and filter applications
- Application summary
- XLSX export
- Natural-language interaction through an LLM
- PostgreSQL persistence
- LINE webhook integration

## Future Features

These features may be considered later but are not part of the current MVP:

- Google Sheets integration
- Two-way synchronization with Google Sheets
- Application reminders
- Resume recommendations
- Advanced analytics
- Notification systems
- Additional messaging platforms
- Advanced AI agents

Do not implement future features unless explicitly requested.

## Out of Scope

Do not introduce the following unless there is a clear requirement:

- Microservices
- Message queues
- Redis
- Event-driven architecture
- Kubernetes
- Complex caching systems
- Separate authentication services
- Separate company management systems
- Status history tables
- Complex event-sourcing systems

The MVP should remain a layered monolith.

## Avoid Overengineering

When multiple solutions are possible, prefer the simplest solution that satisfies the current requirements.

Do not introduce infrastructure because it might be useful at a much larger scale.

Consider the actual requirements, expected traffic, operational complexity, and maintenance cost before adding infrastructure.

If a proposed change significantly increases system complexity, explain the trade-offs before implementing it.
