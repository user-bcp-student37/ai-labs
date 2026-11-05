# Spec Delta

## Purpose

Define the observable login behavior for valid credentials and protect authentication from credential values that attempt to bypass verification.

## ADDED Requirements

### Requirement: Valid credentials preserve successful login
The login endpoint MUST continue to authenticate valid workshop credentials and return the established success response.

#### Scenario: Workshop user logs in successfully
- **WHEN** a client sends `student` and `Workshop123!` to `POST /auth/login`
- **THEN** the endpoint responds with HTTP 200, `user.username` equal to `student`, and a non-empty `token`

### Requirement: SQL injection attempts are rejected
The login endpoint MUST treat credential values that attempt to alter authentication as invalid and MUST NOT issue a token.

#### Scenario: Injection-like value is submitted as username
- **WHEN** a client submits `' OR '1'='1` as the username to `POST /auth/login`
- **THEN** the endpoint responds with HTTP 401 and the response does not contain a `token`

#### Scenario: Injection-like value is submitted as password
- **WHEN** a client submits `' OR '1'='1` as the password to `POST /auth/login`
- **THEN** the endpoint responds with HTTP 401 and the response does not contain a `token`
