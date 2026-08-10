# ADR 0001: Start with a clean-room implementation

- **Status:** accepted
- **Date:** 2026-08-10

## Context

The project was motivated in part by an audit of `ChenLiu-1996/figures4papers`. No explicit root license was identified during that audit.

## Decision

Build a new implementation from behavioral requirements and published ideas. Do not copy upstream code, assets, data, or documentation. Keep migrated examples empty until rights are verified or the examples are independently recreated.

## Consequences

- Initial development is slower but legally and academically safer.
- Similar functionality must be supported by original tests and synthetic fixtures.
- Attribution remains mandatory even when no protected expression is copied.
- A future license grant can enable a separately reviewed migration; it does not silently change this decision.
