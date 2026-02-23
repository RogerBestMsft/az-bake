You are a senior software architect tasked with understanding the technical architecture and implementation details of an application. Your goal is to extract and document the technical structure, patterns, dependencies, and architectural decisions from the provided codebase to enable future refactoring activities which could include changing dependent technologies, enhancing maintainability, improving test coverage, or refactoring components into separate services.

## Instructions

Carefully analyze the provided codebase, focusing on the technical implementation, architecture patterns, and structural decisions, and create a comprehensive document (at `docs/technical-architecture.md`) that outlines the technical architecture and provides actionable insights for future refactoring efforts.

### Key Areas to Focus On

1. **Application Architecture Pattern**: Identify the overall architectural pattern being used (MVC, Clean Architecture, Onion Architecture, etc.). How is the application structured and layered?
2. **Project Structure and Dependencies**: Document the solution structure, project dependencies, and how different projects/assemblies relate to each other. What is the dependency graph?
3. **Data Access Layer**: Analyze how data is accessed and managed. What ORM is used? How are database connections handled? What are the data access patterns? What are the key entities and their relationships?
4. **Service Layer Architecture**: Identify service classes, their responsibilities, and how they interact. What patterns are used for dependency injection and service registration?
5. **External Dependencies and Integrations**: Document third-party libraries, NuGet packages, external APIs, and integration patterns. How are external systems accessed?
6. **Configuration Management**: How is configuration handled? What configuration sources are used (appsettings, environment variables, etc.)?
7. **Cross-Cutting Concerns**: How are logging, error handling, security, caching, and other cross-cutting concerns implemented?
8. **Communication Patterns**: How do different parts of the application communicate? Are there internal APIs, message queues, or event-driven patterns?
9. **Authentication and Authorization**: What security frameworks and patterns are implemented? How are users authenticated and authorized?
10. **Background Processing**: Are there background services, scheduled jobs, or async processing patterns? How are they implemented?
11. **Testing Architecture**: What testing strategies are in place? How is the code structured to support testing?
12. **Deployment and Infrastructure**: What deployment patterns are evident from the code? Are there containerization, cloud-specific implementations, or infrastructure as code patterns?

### Technical Analysis Focus

1. **Code Organization**: Analyze namespaces, folder structures, and how code is organized across projects. Look for:
   - Controllers with many dependencies (potential service boundary indicators)
   - Shared utility classes (candidates for shared libraries)
   - Large service classes (potential for further decomposition)
   - Circular dependencies between projects

2. **Design Patterns**: Identify design patterns used throughout the codebase (Repository, Factory, Strategy, etc.). Pay attention to:
   - Repository patterns that could become service APIs
   - Factory patterns that might indicate service creation boundaries
   - Observer/Event patterns that suggest async communication opportunities

3. **Dependency Injection**: Document the DI container usage and service lifetimes. Look for:
   - Singleton services that might need to be distributed
   - Scoped services and their transaction boundaries
   - Services with many constructor dependencies (high coupling indicators)

4. **Database Schema and Migrations**: Understand data models and how schema changes are managed. Examine:
   - Entity relationships that cross logical boundaries
   - Tables with high coupling (many foreign keys)
   - Aggregate roots that could define service boundaries
   - Migration patterns and versioning strategies

5. **API Design**: Analyze REST API structure, routing patterns, and serialization approaches. Look for:
   - Controller groupings that suggest natural service boundaries
   - DTOs that could become inter-service contracts
   - API versioning strategies
   - Endpoint dependencies and call patterns

6. **Security Implementation**: Analyze authentication, authorization, input validation, and security headers. Look for:
   - Middleware that handles security concerns
   - Authorization policies either in configuration or code
   - Claims-based authorization patterns
   - Input validation strategies and their impact on business logic

7. **Performance Considerations**: Identify caching strategies, async patterns, and performance optimizations
8. **Error Handling Strategies**: Document exception handling patterns and error propagation

### Refactoring Analysis

1. **Service Boundaries**: Identify logical boundaries that could become separate services. Look for:
   - Domain aggregates and bounded contexts
   - Controllers/services that rarely interact with others
   - Features that have distinct deployment or scaling requirements
   - Business capabilities that could operate independently

2. **Shared Dependencies**: Document components that would need to be shared across services
3. **Data Coupling**: Analyze database dependencies and how data could be partitioned using specific strategies:
   - **Database-per-Service**: Identify tables that naturally group together
   - **Shared Database Anti-pattern**: Document current shared data concerns
   - **Data Synchronization**: Identify master-detail relationships requiring eventual consistency
   - **Reference Data**: Catalog lookup tables and configuration data sharing needs

4. **Communication Requirements**: Identify what would need to become inter-service communication
5. **Transaction Boundaries**: Understand current transaction scopes and distributed transaction needs. Analyze:
   - Current `TransactionScope` usage and boundaries
   - Database transactions that span multiple business contexts
   - Operations that would require distributed transactions (2PC/Saga patterns)
   - Eventual consistency opportunities vs. strong consistency requirements
   - Compensation patterns for handling distributed transaction failures

## Deliverables

Create a comprehensive document in the `docs` directory with the following Markdown structure:

```markdown
# Technical Architecture Analysis: [Application Name]

## Executive Summary

High-level overview of the technical architecture, main technologies used, and architectural patterns employed.

## Technology Stack

### Core Technologies
- Language(s) and version(s)
- Database(s)
- Web Framework
- Key Libraries and Frameworks

### External Dependencies
- Third-party NuGet packages
- External APIs
- Infrastructure dependencies

## Architecture Overview

### High-Level Architecture Diagram
[Insert Mermaid diagram showing main architectural components and their relationships]

### Architecture Pattern
Description of the overall architectural approach (layered, clean architecture, etc.)

## Project Structure

### Solution Organization
- Project breakdown and responsibilities
- Inter-project dependencies
- Assembly boundaries

### Dependency Graph
[Insert Mermaid diagram showing project dependencies]

## Data Architecture

### Data Access Patterns
- ORM/Data access technology
- Repository patterns
- Database connection management
- Entity models and relationships

### Database Design
- Schema overview
- Migration strategies
- Data partitioning considerations

## Service Architecture

### Service Layer Organization
- Service classes and their responsibilities
- Dependency injection patterns
- Service class dependencies and layering
- Service lifetimes and scoping

### Business Logic Distribution
- Where business rules are implemented
- Service boundaries and interactions

## Cross-Cutting Concerns

### Logging and Monitoring
- Logging framework and patterns
- Monitoring and telemetry

### Security Implementation
- Authentication mechanisms
- Authorization patterns
- Security middleware and policies

### Error Handling
- Exception handling strategies
- Error propagation patterns

### Configuration Management
- Configuration sources and patterns
- Environment-specific settings

## Communication Patterns

### Internal Communication
- How components communicate within the application
- Event handling patterns
- Message passing mechanisms

### External Communication
- API design and patterns
- External service integration
- Communication protocols used

## Performance and Scalability

### Caching Strategies
- Caching layers and implementations
- Cache invalidation patterns

### Asynchronous Processing
- Async/await patterns
- Background processing
- Queue-based processing

## Testing Architecture

### Test Organization
- Unit test structure and patterns
- Integration test approaches
- Test isolation strategies

## Refactoring Analysis

### Service Boundary Recommendations

#### Potential Service 1: [Name]
- **Responsibilities**: Core functions this service would handle
- **Data Dependencies**: Database tables/entities it would own
- **External Dependencies**: Third-party integrations it would manage
- **Internal APIs**: Endpoints it would expose to other services

#### Potential Service 2: [Name]
[Same structure as above]

### Shared Components
- Libraries that would need to be shared across services
- Common data models and DTOs
- Shared utilities and helpers

### Data Partitioning Strategy

#### Database Decomposition Approaches
- **Vertical Partitioning**: Tables that can be cleanly separated by domain/service
- **Horizontal Partitioning**: Large tables that could be sharded across services
- **Functional Decomposition**: Separating read/write operations and CQRS opportunities

#### Specific Partitioning Strategies
- **Database-per-Service**: Complete isolation with service-owned schemas
- **Shared Database with Service Schemas**: Logical separation within same database
- **Data Lake/Event Sourcing**: Event-driven data architecture opportunities

#### Data Consistency Patterns
- **Strong Consistency**: Operations requiring immediate consistency (identify current ACID boundaries)
- **Eventual Consistency**: Operations that can tolerate delayed updates
- **Saga Pattern**: Multi-step business processes requiring coordination
- **Event Sourcing**: Audit trails and state reconstruction requirements

#### Shared Data Concerns
- Reference data and lookup tables
- User/identity information sharing
- Configuration and feature flags
- Audit and logging data

### Inter-Service Communication Requirements
- APIs needed between services
- Async messaging requirements
- Event-driven architecture opportunities

### Migration Complexity Assessment
- High-risk refactoring areas
- Dependencies that complicate separation
- Recommended migration sequence

### Infrastructure Considerations

#### Containerization and Orchestration
- Current containerization patterns (Docker, container images)
- Kubernetes/orchestration readiness assessment
- Container registry and image management strategies
- Resource allocation and scaling patterns

#### Service Mesh and Communication
- API Gateway requirements and patterns
- Service-to-service authentication (mTLS, JWT, etc.)
- Circuit breaker and retry policy implementations
- Load balancing and traffic routing needs

#### Deployment and DevOps
- CI/CD pipeline modifications for microservices
- Database migration strategies in distributed deployments
- Blue-green vs. rolling deployment considerations
- Feature flag and canary release patterns

#### Monitoring and Observability
- Distributed tracing requirements (correlation IDs, trace context)
- Centralized logging aggregation needs
- Service health checks and monitoring endpoints
- Performance monitoring across service boundaries

#### Configuration and Secrets Management
- Centralized vs. distributed configuration approaches
- Secret management and rotation strategies
- Environment-specific configuration distribution
- Service discovery and registration patterns

## Technical Debt and Improvement Opportunities

### Code Quality Issues
- Areas needing refactoring for better separation
- Tightly coupled components
- Violations of architectural principles

### Performance Bottlenecks
- Areas that could benefit from service separation
- Resource contention issues
- Scalability limitations

## Recommendations

### Immediate Improvements
- Quick wins for better architecture
- Preparation steps for service extraction

### Long-term Refactoring Strategy
- Recommended order for service extraction
- Risk mitigation strategies
- Testing approaches during migration
```

## Important Guidelines

- Focus on technical implementation details and architectural decisions
- Use technical terminology appropriate for software architects and senior developers
- Provide specific code examples and patterns where relevant
- Think from the perspective of someone who needs to refactor this into microservices
- Include diagrams using Mermaid syntax where helpful for visualization
- Identify potential challenges and risks in refactoring efforts
- Consider both current architecture and future scalability needs
- Document assumptions about technical decisions where code intent is unclear
- Prioritize actionable insights that can guide refactoring decisions

**Please analyze the provided .NET codebase and create this technical architecture analysis document (`docs/technical-architecture.md`) as a markdown file.** Ensure that the document provides comprehensive technical insights with specific attention to service boundaries, data partitioning, and inter-service communication requirements.