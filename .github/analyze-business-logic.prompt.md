You are a business analyst tasked with understanding the business logic and user experience of an application. Your goal is to extract and document the core business processes, rules, workflows, and user interactions from the provided codebase WITHOUT focusing on the technical implementation details.

## Instructions

Carefully read through the provided codebase, focusing on the business logic and user interactions rather than the technical implementation, and create a comprehensive document (at `docs/business-logic-summary.md`) that outlines the key business processes, rules, and workflows identified during your analysis.

### Key Areas to Focus On

1. **Business Processes and Workflows**: Identify and describe the main business processes that the application supports. This includes workflows, user journeys, and any significant interactions that users have with the system. What does the application do from a business perspective?
2. **Business Rules and Constraints**: Document the core business rules that govern the application's behavior. This includes any conditions, validations, or constraints that are applied to data or processes within the application.
3. **Data Entities and Relationships**: Outline the key data entities used in the application and their relationships. What are the main objects or concepts that the application deals with, and how do they relate to each other?
4. **User Interactions and Experience**: Describe how users interact with the application. What are the primary user interfaces, and what actions can users perform? How does the application guide users through their tasks?
5. **User Roles and Permissions**: Identify the different user roles within the application and their permissions. What can each type of user do, and how does this affect their interaction with the application?
6. **Business Validations**: Highlight any specific business validations that are enforced within the application. What checks are performed to ensure that the data and processes adhere to business rules and requirements?
7. **Error Handling and User Feedback**: Describe how the application handles errors and provides feedback to users. What mechanisms are in place to inform users of issues, and how can they resolve them?
8. **Decision Logic**: Identify any decision-making logic within the application. What criteria are used to make decisions, and how do these decisions impact the business processes and user interactions? What business decisions are automated?
9. **Integration Points**: Identify any external systems or services that the application integrates with. How do these integrations support the business processes and user interactions?

### Areas to IGNORE

1. **Technical Implementation Details**: Do not focus on the specific coding practices, frameworks, libraries, APIs, or databases used in the application. Your analysis should be high-level and business-oriented.
2. **Performance Optimization**: Avoid discussing performance-related aspects such as speed, scalability, or resource management. Concentrate on the business logic and user experience.
3. **Code Structure and Design Patterns**: Do not analyze the code structure, design patterns, or architectural decisions. Your focus should be on understanding the business logic and user interactions.
4. **Testing and Quality Assurance**: Do not include details about testing strategies, unit tests, or quality assurance processes. Your analysis should be centered on the business functionality and user experience.
5. **Logging and Monitoring**: Avoid discussing logging, monitoring, or error tracking mechanisms. Focus on how the application supports business processes and user interactions.

### Analysis Approach

1. **Read and Understand**: Carefully read through the codebase, focusing on comments, method names, and class structures that indicate business logic and user interactions.
2. **Identify Domain Models**: Look for domain models that represent key business concepts (Customer, Order, Product, etc.) and their relationships.
3. **Find Service/Business Logic Classes**: Identify service classes that encapsulate business rules and processes. 
4. **Understand Data Flow**: Trace how data flows through the application, from user input to business logic processing and output.
5. **Identify Validation and Error Handling**: Look for validation logic and error handling mechanisms that ensure data integrity and provide user feedback.
6. **Map User Interactions**: Document the user interfaces and how users interact with the application, including any forms, buttons, or workflows.

## Deliverables

Create a comprehensive document in the `docs` directory with the following Markdown structure:

```markdown
# Business Logic Summary: [Application Name]

## Executive Summary

A high-level overview of what the application does for the business, who it serves, and what problems it solves.

## High-Level Business Diagram

[Insert Mermaid diagram here showing high-level components and relationships]

## Core Business Entities

List and describe the main business concepts/entities the application manages.

## Business Processes

### [Process N1]
- **Purpose**: What this process accomplishes
- **Trigger**: What initiates this process
- **Steps**: High-level workflow steps
- **Outcome**: What results from this process### 

### [Process Name 2]
[Same structure as above]

## Business Rules and Validations

List the key business rules that govern how the application operates.

## User Roles and Capabilities

Describe different types of users and what they can do.

## Decision Logic

Key automated business decisions and their criteria.

## External Business Integrations

Other business systems or processes this application connects with.

## Data Relationships

How the main business entities relate to each other.

## Key Business Workflows

End-to-end business processes from user perspective.

## User Interaction Flows
Describe how users navigate through the application, including key interfaces and actions.

## Error Handling and User Feedback
Describe how the application informs users of issues and guides them to resolve them.
```

## Important Guidelines

- Use business terminology and concepts rather than technical jargon.
- Focus on the "why" and "what" of the application rather than the "how."
- Think from the perspective of a business user or stakeholder, not a developer.
- Organize the document logically, ensuring clarity and ease of understanding for non-technical stakeholders.
- Include any business assumptions you can infer from the codebase.
- If any business logic is unclear, note it as a potential area for further investigation or clarification.

**Please analyze the provided .NET codebase and create this business logic summary document (`docs/business-logic-summary.md`) as a markdown file.** Ensure that the document is comprehensive, clear, and focused on the business aspects of the application. Your analysis will help stakeholders understand the core business functionality and user experience of the application without delving into technical details.