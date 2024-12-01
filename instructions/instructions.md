# Test-Driven Development (TDD) Workflow Instructions

## Overview

This document outlines our TDD workflow for the Verba project, focusing on both frontend and backend testing practices.

## TDD Workflow

### 1. Write Test First
```bash
# Create test file before implementation
touch __tests__/[ComponentName].test.tsx  # For frontend
touch tests/test_[module_name].py         # For backend
```

### 2. Red-Green-Refactor Cycle

#### Red: Write Failing Test
```typescript
// Example: Frontend Component Test
describe('ComponentName', () => {
  test('should render with expected props', () => {
    const props = { /* required props */ };
    render(<ComponentName {...props} />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });
});
```

#### Green: Make Test Pass
- Implement minimal code to make test pass
- Commit working code:
```bash
git add .
git commit -m "feat: implement [ComponentName] with basic functionality"
```

#### Refactor: Improve Code
- Improve code structure while keeping tests green
- Commit refactored code:
```bash
git commit -m "refactor: improve [ComponentName] structure"
```

### 3. Testing Guidelines

#### Frontend Tests (React + Bun)

1. **Component Setup**
```typescript
import { describe, expect, test, vi } from "bun:test";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

describe('ComponentName', () => {
  // Mock props and functions
  const mockProps = {
    onSubmit: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });
});
```

2. **Testing Patterns**
- Test rendering:
```typescript
test('renders without crashing', () => {
  render(<Component {...mockProps} />);
  expect(screen.getByRole('button')).toBeInTheDocument();
});
```

- Test user interactions:
```typescript
test('handles user interaction', async () => {
  render(<Component {...mockProps} />);
  await userEvent.click(screen.getByRole('button'));
  expect(mockProps.onSubmit).toHaveBeenCalled();
});
```

#### Backend Tests (Python + pytest)

1. **Test Setup**
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_endpoint(client):
    response = client.get("/api/endpoint")
    assert response.status_code == 200
```

### 4. Git Commit Guidelines

Follow semantic commit messages:

- `feat:` New feature
- `fix:` Bug fix
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `docs:` Documentation updates

Example commits:
```bash
git commit -m "test: add SimpleFeedback component tests"
git commit -m "feat: implement SimpleFeedback component"
git commit -m "refactor: improve SimpleFeedback props handling"
```

### 5. Testing Best Practices

#### Frontend
- Use React Testing Library's queries in this order:
  1. getByRole
  2. getByLabelText
  3. getByPlaceholderText
  4. getByText
  5. getByDisplayValue
  6. getByTestId

- Test user interactions over implementation details
- Use `userEvent` over `fireEvent` when possible
- Mock API calls using Mock Service Worker (MSW)

#### Backend
- Use fixtures for test data
- Mock external services
- Test edge cases and error conditions
- Use parameterized tests for multiple scenarios

### 6. Continuous Integration

- All tests must pass before merging
- Run tests locally before pushing:
```bash
# Frontend
bun test

# Backend
pytest
```

### 7. Documentation

- Document test scenarios in test files
- Update README with new testing requirements
- Document any testing utilities or helpers

### 8. Troubleshooting

Common issues and solutions:

1. **Test Environment Setup**
```typescript
// frontend/test/setup.ts
import { afterEach, beforeAll } from "bun:test";
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/matchers';

beforeAll(() => {
  // Setup test environment
});

afterEach(() => {
  cleanup();
});
```

2. **Mock Implementation**
```typescript
const mockFunction = vi.fn().mockImplementation(() => {
  return Promise.resolve({ data: 'test' });
});
```

Remember: The key to successful TDD is writing tests first, making them fail, implementing the minimum code to make them pass, and then refactoring while keeping the tests green.
