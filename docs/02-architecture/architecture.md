# Maya Portfolio Manager Architecture

## Overview

Maya Portfolio Manager is being rebuilt from a legacy Flask + SQLAlchemy application into a monorepo with:

- FastAPI backend
- React frontend
- MUI component library
- PostgreSQL as the primary database

The new architecture is intended to preserve proven operational behavior from the legacy system while creating a more maintainable, testable, and scalable foundation for lease portfolio management.

## Why FastAPI instead of Flask?

- Async support
- Better API-first design
- Automatic OpenAPI docs
- Easier scaling

## Why React + MUI?

- Component reusability
- Clean UI system
- Industry standard stack

## Why PostgreSQL?

- Better than SQLite for production
- Strong relational modeling
- Supports indexing and scaling