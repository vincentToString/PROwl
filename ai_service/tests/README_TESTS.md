# Running Real API Tests

This directory contains tests for the AI service, including **expensive tests** that make real AWS Bedrock API calls.

## Test Categories

### 1. Regular Tests (Free)
These tests use mocks and don't make real API calls:
```bash
pytest ai_service/tests/ -v
```

### 2. Expensive Tests (COSTS MONEY!)

### Prerequisites

1. **Configure AWS credentials** in your `.env` file:
   ```bash
   AWS_ACCESS_KEY=AKIAXXXXXXXXXX
   AWS_SECRET_KEY=your-secret-key
   AWS_DEFAULT_REGION=us-east-2
   MODEL_ID=arn:aws:bedrock:us-east-2:your-account:inference-profile/us.meta.llama4-scout-17b-instruct-v1:0
   ```

2. **For RAG tests**, also configure:
   ```bash
   KNOWLEDGE_BASE_ID=your-kb-id-here
   ```

### Run All Expensive Tests
```bash
pytest ai_service/tests/test_real_api.py -v -s -m expensive
```

### Run Specific Tests

**Test regular Bedrock API (without RAG):**
```bash
pytest ai_service/tests/test_real_api.py::TestRealAPIIntegration::test_real_bedrock_with_prompt_template -v -s
```

**Test Bedrock RAG API (with Knowledge Base):**
```bash
pytest ai_service/tests/test_real_api.py::TestRealAPIIntegration::test_real_bedrock_rag_with_prompt -v -s
```

### Run Configuration Tests (Free)
These verify your config is properly set up without making API calls:
```bash
pytest ai_service/tests/test_real_api.py::TestRealAPIIntegration::test_config_ready_for_real_api -v -s
pytest ai_service/tests/test_real_api.py::TestRealAPIIntegration::test_prompt_template_exists -v -s
```