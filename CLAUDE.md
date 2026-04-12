# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lifetime Calendar — a "Your Life in Weeks" visualizer. Users set their birthdate and life expectancy; the app renders every week of their life as a grid cell (lived/current/future), with per-week notes and a live countdown timer.

## Rules

- @.claude/rules/architecture.md — backend, frontend structure and key files
- @.claude/rules/commands.md — how to run and build each server
- @.claude/rules/api.md — all backend REST endpoints
- @.claude/rules/environment.md — environment variables

## Context7

When writing code that uses any library or framework, use Context7 MCP to fetch current documentation before implementing. Run `resolve-library-id` then `query-docs` to get accurate API usage, method signatures, and patterns.

## Memory

- @.claude/MEMORY.md — accumulated project notes, decisions, and context
