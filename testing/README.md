# 🧪 Tests for AI Agents

This directory contains unit tests for the core agents in the application:

- `ChatAgent`
- `EmailAgent`
- `SummarizationAgent`
- `TimelineAgent`
- `ImageMergeAgent`

---

## 🚀 How to Run Unit Tests

### 1. 📦 Install Dependencies

Make sure your virtual environment is activated, then install the test and lint tools:

```bash
pip install pytest pytest-cov black


#RUN ALL TESTS
pytest tests/


#RUN SPECIFIC TESTS
pytest tests/test_emailagent.py

#RUN AND SEE COVERAGE OUTPUT IN TERMINAL
pytest --cov=agents tests/


#GENERATE DETAILED HTML REPORT
pytest --cov=agents --cov-report=html tests/

#OPTIONAL RESULTS IN BROWSER
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux



