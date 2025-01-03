# Test-Driven Development (TDD) Workflow Instructions

This document outlines our **TDD workflow** for the **Verba** project, incorporating **feature branches** for new features and emphasizing **frontend** and **backend** testing practices.

---

## 1. Feature Branch & Test-First Approach

1. **Create a Feature Branch**  
   ```bash
   git checkout main
   git pull
   git checkout -b feat/my-new-feature

	2.	Write Failing Test
	•	Create a test file before writing the actual feature code:

# Frontend
touch __tests__/MyFeature.test.tsx

# Backend
touch tests/test_my_feature.py


	3.	Commit Tests

git add .
git commit -m "test: add failing test for MyFeature"

2. Red-Green-Refactor Cycle
	1.	Red (Failing Test)
	•	Write the minimal test case to define expected behavior.
	•	Example (Frontend):

describe('MyFeature', () => {
  test('should render with expected props', () => {
    // Test will fail because the component doesn't exist yet
    render(<MyFeature someProp="test" />)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })
})


	2.	Green (Make Test Pass)
	•	Implement the minimal code for the new feature or function:

export function MyFeature({ someProp }: { someProp: string }) {
  return <button>{someProp}</button>
}


	•	Confirm test passes locally:

bun test  # Frontend
pytest    # Backend


	•	Commit working code:

git add .
git commit -m "feat: implement MyFeature to pass initial tests"


	3.	Refactor
	•	Improve code structure while keeping tests green:

git commit -m "refactor: improve MyFeature structure"

3. Merging to Main
	1.	Push Feature Branch

git push -u origin feat/my-new-feature


	2.	Open Pull Request
	•	Ensure all tests pass in CI.
	•	Team members review code.
	3.	Merge to Main
	•	Once approved and CI is green, merge.
	•	This ensures main always has fully tested, stable code.

4. Testing Guidelines

4.1 Frontend Tests (React + Bun)
	1.	Component Setup

import { describe, expect, test, vi } from "bun:test"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"

describe('MyFeature', () => {
  const mockProps = { onSubmit: vi.fn() }

  beforeEach(() => {
    vi.clearAllMocks()
  })
})


	2.	Testing Patterns
	•	Render Test

test('renders without crashing', () => {
  render(<MyFeature {...mockProps} />)
  expect(screen.getByRole('button')).toBeInTheDocument()
})


	•	User Interaction

test('handles user click', async () => {
  render(<MyFeature {...mockProps} />)
  await userEvent.click(screen.getByRole('button'))
  expect(mockProps.onSubmit).toHaveBeenCalled()
})



4.2 Backend Tests (Python + pytest)
	1.	Test Setup

import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_endpoint(client):
    response = client.get("/api/endpoint")
    assert response.status_code == 200


	2.	Edge Cases & Mocks
	•	Use fixtures for test data.
	•	Mock external services (e.g., S3, Stripe, etc.).
	•	Parameterized tests for multiple scenarios.

5. Git Commit Guidelines
	•	Semantic Commits
	•	feat: New feature
	•	fix: Bug fix
	•	test: Adding or updating tests
	•	refactor: Code refactoring
	•	docs: Documentation updates
	•	Example Commits

git commit -m "test: add MyFeature component tests"
git commit -m "feat: implement MyFeature component"
git commit -m "refactor: refactor MyFeature logic"

6. Testing Best Practices

Frontend
	•	React Testing Library Queries (preferred order):
	1.	getByRole
	2.	getByLabelText
	3.	getByPlaceholderText
	4.	getByText
	5.	getByDisplayValue
	6.	getByTestId
	•	User Interactions over implementation details.
	•	Mock network/API calls (e.g., Mock Service Worker).

Backend
	•	Fixtures for test data setup.
	•	Mock external calls/services.
	•	Cover edge cases & handle exceptions properly.

7. Continuous Integration
	•	All tests must pass before merging to main.
	•	Local Test:

# Frontend
bun test

# Backend
pytest

8. Documentation
	•	Document test scenarios in each test file.
	•	Update README with any new testing or setup requirements.

9. Troubleshooting
	1.	Test Environment Setup

// frontend/test/setup.ts
import { afterEach, beforeAll } from "bun:test"
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/matchers'

beforeAll(() => {
  // Global test setup
})

afterEach(() => {
  cleanup()
})


	2.	Mock Implementations

const mockFunction = vi.fn(() => Promise.resolve({ data: 'test' }))

10. Key Takeaways
	1.	Create a feature branch for new functionality.
	2.	Write tests first (Red-Green-Refactor).
	3.	Commit regularly with semantic commit messages.
	4.	Merge back to main only when all tests pass.
	5.	Keep tests clean, focused, and maintainable.
