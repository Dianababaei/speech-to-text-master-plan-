# Manual Feedback Workflow Documentation

## Table of Contents

1. [Workflow Overview](#workflow-overview)
2. [Step 1: User Submits Correction](#step-1-user-submits-correction)
3. [Step 2: Admin Reviews Feedback](#step-2-admin-reviews-feedback)
4. [Step 3: Admin Approves/Rejects](#step-3-admin-approvesrejects)
5. [Step 4: Admin Updates Lexicon](#step-4-admin-updates-lexicon)
6. [Best Practices](#best-practices)
7. [Edge Cases & Troubleshooting](#edge-cases--troubleshooting)
8. [Approval Decision Tree](#approval-decision-tree)
9. [Related Documentation](#related-documentation)

---

## Workflow Overview

The manual feedback workflow enables continuous improvement of transcription quality through user corrections and admin-curated lexicon updates. This creates a feedback loop where real-world corrections systematically improve domain-specific terminology.

### Feedback Loop Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Feedback Loop Workflow                        │
└─────────────────────────────────────────────────────────────────┘

1. TRANSCRIPTION                2. USER REVIEW              3. SUBMIT FEEDBACK
   ┌──────────┐                    ┌──────────┐                ┌──────────┐
   │  Audio   │──transcribe───────>│ Review   │──correction──>│ Feedback │
   │   File   │    (OpenAI)        │  Result  │     API       │   DB     │
   └──────────┘                    └──────────┘                └──────────┘
       │                                                             │
       │                                                             │
       └─────────────────────────────────────────────────────────────┤
                                                                     │
4. ADMIN REVIEW                 5. APPROVE/REJECT          6. UPDATE LEXICON
   ┌──────────┐                    ┌──────────┐                ┌──────────┐
   │  Filter  │────query────────>  │  Review  │──approve────>  │ Lexicon  │
   │ Feedback │     (API)          │ & Decide │     (API)      │  Terms   │
   └──────────┘                    └──────────┘                └──────────┘
       │                                │                            │
       │                                │reject                      │
       │                                ↓                            │
       │                          [Archive/Log]                      │
       │                                                             │
       └─────────────────────────────────────────────────────────────┘
                                      │
                                      ↓
                            [Improved Transcriptions]
```

### Roles

**End Users (Submit Corrections)**
- Review transcription results after job completion
- Identify incorrect transcriptions
- Submit corrections via API
- Provide context notes when helpful

**Administrators (Review and Apply)**
- Review submitted feedback regularly
- Filter and prioritize corrections
- Approve valuable corrections
- Reject invalid or low-quality feedback
- Update lexicons with approved terms
- Monitor transcription quality metrics

### Key Principles

1. **User-driven improvement**: Real corrections from actual use cases
2. **Admin curation**: Quality control prevents lexicon pollution
3. **Systematic learning**: Approved corrections become permanent improvements
4. **Transparency**: Full audit trail of feedback and lexicon changes
5. **Batch efficiency**: Process multiple similar corrections together

---

## Step 1: User Submits Correction

After reviewing a completed transcription, users submit corrections when they identify errors. This creates a feedback record that admins can review and potentially incorporate into the lexicon.

### When to Submit Feedback

Submit feedback when you notice:
- **Transcription errors**: Words or phrases incorrectly transcribed
- **Domain-specific terms**: Medical, legal, or technical terms misrecognized
- **Consistent mistakes**: Errors that appear repeatedly
- **Critical corrections**: Important terms that affect meaning

**Don't submit for**:
- Minor punctuation preferences (system outputs plain text)
- Stylistic changes (formatting, capitalization preferences)
- Expected variations in speech (filler words, accents)

### API Endpoint

```
POST /jobs/{job_id}/feedback
```

### Request Structure

**Path Parameters:**
- `job_id` (string, UUID): The job identifier from the transcription request

**Headers:**
- `X-API-Key` (string): Your API authentication key
- `Content-Type`: `application/json`

**Request Body:**

```json
{
  "original_text": "The patient has atreal fibrillation",
  "corrected_text": "The patient has atrial fibrillation",
  "feedback_type": "correction",
  "review_notes": "Common medical term - 'atrial' was misrecognized as 'atreal'",
  "review_time_seconds": 45
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `original_text` | string | Yes | The exact incorrect text from transcription |
| `corrected_text` | string | Yes | Your corrected version of the text |
| `feedback_type` | string | No | Type of feedback: `correction`, `validation`, `quality_issue` (default: `correction`) |
| `review_notes` | string | No | Additional context or explanation |
| `review_time_seconds` | integer | No | Time spent reviewing (for analytics) |

### Response

**Success (201 Created):**

```json
{
  "feedback_id": 42,
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "original_text": "The patient has atreal fibrillation",
  "corrected_text": "The patient has atrial fibrillation",
  "feedback_type": "correction",
  "accuracy_score": 0.96,
  "edit_distance": 1,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**

- **400 Bad Request**: Invalid request body or missing required fields
- **401 Unauthorized**: Missing or invalid API key
- **404 Not Found**: Job ID doesn't exist or doesn't belong to your API key
- **422 Unprocessable Entity**: Invalid data format

### cURL Example

```bash
curl -X POST "https://api.example.com/jobs/123e4567-e89b-12d3-a456-426614174000/feedback" \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "original_text": "The patient has atreal fibrillation",
    "corrected_text": "The patient has atrial fibrillation",
    "feedback_type": "correction",
    "review_notes": "Medical term correction"
  }'
```

### Python Example

```python
import requests
import json

# Configuration
API_KEY = "your-api-key-here"
BASE_URL = "https://api.example.com"
job_id = "123e4567-e89b-12d3-a456-426614174000"

# Prepare feedback
feedback_data = {
    "original_text": "The patient has atreal fibrillation",
    "corrected_text": "The patient has atrial fibrillation",
    "feedback_type": "correction",
    "review_notes": "Medical term correction"
}

# Submit feedback
response = requests.post(
    f"{BASE_URL}/jobs/{job_id}/feedback",
    headers={
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    },
    json=feedback_data
)

if response.status_code == 201:
    feedback = response.json()
    print(f"Feedback submitted successfully!")
    print(f"Feedback ID: {feedback['feedback_id']}")
    print(f"Status: {feedback['status']}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

### Python Client Class

```python
from typing import Optional
import requests

class FeedbackClient:
    """Client for submitting feedback to the transcription API."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.example.com"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        })
    
    def submit_feedback(
        self,
        job_id: str,
        original_text: str,
        corrected_text: str,
        feedback_type: str = "correction",
        review_notes: Optional[str] = None,
        review_time_seconds: Optional[int] = None
    ) -> dict:
        """
        Submit feedback for a transcription job.
        
        Args:
            job_id: UUID of the transcription job
            original_text: Incorrect text from transcription
            corrected_text: Your corrected version
            feedback_type: Type of feedback (correction, validation, quality_issue)
            review_notes: Additional context or explanation
            review_time_seconds: Time spent reviewing
            
        Returns:
            dict: Feedback response with ID and status
            
        Raises:
            requests.HTTPError: If the API request fails
        """
        payload = {
            "original_text": original_text,
            "corrected_text": corrected_text,
            "feedback_type": feedback_type
        }
        
        if review_notes:
            payload["review_notes"] = review_notes
        if review_time_seconds:
            payload["review_time_seconds"] = review_time_seconds
        
        response = self.session.post(
            f"{self.base_url}/jobs/{job_id}/feedback",
            json=payload
        )
        response.raise_for_status()
        return response.json()

# Usage
client = FeedbackClient(api_key="your-api-key")
result = client.submit_feedback(
    job_id="123e4567-e89b-12d3-a456-426614174000",
    original_text="atreal fibrillation",
    corrected_text="atrial fibrillation",
    review_notes="Common cardiology term"
)
print(f"Submitted feedback #{result['feedback_id']}")
```

---

## Step 2: Admin Reviews Feedback

Administrators regularly review submitted feedback to identify valuable corrections that should be incorporated into lexicons. The API provides powerful filtering to help prioritize review efforts.

### API Endpoint

```
GET /feedback
```

### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `status` | string | Filter by status: `pending`, `approved`, `rejected` | `status=pending` |
| `feedback_type` | string | Filter by type: `correction`, `validation`, `quality_issue` | `feedback_type=correction` |
| `lexicon_id` | string | Filter by associated lexicon | `lexicon_id=radiology` |
| `reviewer` | string | Filter by reviewer username | `reviewer=admin1` |
| `min_accuracy_score` | float | Minimum accuracy score (0-1) | `min_accuracy_score=0.8` |
| `max_accuracy_score` | float | Maximum accuracy score (0-1) | `max_accuracy_score=0.95` |
| `from_date` | string | Filter from date (ISO 8601) | `from_date=2024-01-01T00:00:00Z` |
| `to_date` | string | Filter to date (ISO 8601) | `to_date=2024-01-31T23:59:59Z` |
| `is_processed` | boolean | Filter by processing status | `is_processed=false` |
| `page` | integer | Page number (1-indexed) | `page=1` |
| `limit` | integer | Items per page (max 100) | `limit=50` |
| `sort_by` | string | Sort field: `created_at`, `accuracy_score`, `edit_distance` | `sort_by=created_at` |
| `sort_order` | string | Sort order: `asc`, `desc` | `sort_order=desc` |

### Response Structure

**Success (200 OK):**

```json
{
  "items": [
    {
      "feedback_id": 42,
      "job_id": "123e4567-e89b-12d3-a456-426614174000",
      "status": "pending",
      "original_text": "The patient has atreal fibrillation",
      "corrected_text": "The patient has atrial fibrillation",
      "diff_data": {
        "changes": [
          {"position": 17, "old": "atreal", "new": "atrial"}
        ]
      },
      "edit_distance": 1,
      "accuracy_score": 0.96,
      "feedback_type": "correction",
      "reviewer": null,
      "review_notes": "Medical term correction",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "is_processed": false
    },
    {
      "feedback_id": 43,
      "job_id": "223e4567-e89b-12d3-a456-426614174001",
      "status": "pending",
      "original_text": "prescribe acetamenophen",
      "corrected_text": "prescribe acetaminophen",
      "diff_data": {
        "changes": [
          {"position": 10, "old": "acetamenophen", "new": "acetaminophen"}
        ]
      },
      "edit_distance": 1,
      "accuracy_score": 0.95,
      "feedback_type": "correction",
      "reviewer": null,
      "review_notes": "Drug name spelling",
      "created_at": "2024-01-15T11:00:00Z",
      "updated_at": "2024-01-15T11:00:00Z",
      "is_processed": false
    }
  ],
  "total": 2,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

### Interpreting Feedback Records

**Key Fields:**

- **original_text**: What the transcription produced (incorrect)
- **corrected_text**: What it should have been (user's correction)
- **diff_data**: Structured diff showing specific changes
- **edit_distance**: Levenshtein distance (lower = more similar)
- **accuracy_score**: Calculated accuracy (0-1, higher = better)
- **is_processed**: Whether this has been used for lexicon updates

**Quality Indicators:**

- **Low edit_distance (1-3)**: Likely typo or single-word correction
- **High accuracy_score (>0.9)**: Mostly correct, small fixes
- **Low accuracy_score (<0.7)**: Significant errors, review carefully
- **Detailed review_notes**: User provided context, higher quality

### Filtering Strategies

#### Strategy 1: Unreviewed High-Priority Corrections

Find pending corrections with good accuracy scores (easy wins):

```bash
GET /feedback?status=pending&feedback_type=correction&min_accuracy_score=0.9&sort_by=created_at&sort_order=desc
```

#### Strategy 2: Domain-Specific Review

Review corrections for specific lexicon:

```bash
GET /feedback?lexicon_id=radiology&status=pending&is_processed=false
```

#### Strategy 3: Identify Patterns

Find corrections with similar issues (low accuracy):

```bash
GET /feedback?status=pending&max_accuracy_score=0.8&sort_by=accuracy_score&sort_order=asc
```

#### Strategy 4: Recent Submissions

Review today's feedback:

```bash
GET /feedback?from_date=2024-01-15T00:00:00Z&status=pending
```

### cURL Examples

**Get all pending feedback:**

```bash
curl -X GET "https://api.example.com/feedback?status=pending" \
  -H "X-API-Key: your-api-key-here"
```

**Filter by lexicon and date range:**

```bash
curl -X GET "https://api.example.com/feedback?lexicon_id=cardiology&from_date=2024-01-01T00:00:00Z&to_date=2024-01-31T23:59:59Z&status=pending" \
  -H "X-API-Key: your-api-key-here"
```

**Get high-quality corrections:**

```bash
curl -X GET "https://api.example.com/feedback?min_accuracy_score=0.9&feedback_type=correction&status=pending&limit=20" \
  -H "X-API-Key: your-api-key-here"
```

### Python Examples

**Basic filtering:**

```python
import requests

API_KEY = "your-api-key-here"
BASE_URL = "https://api.example.com"

# Get pending feedback
response = requests.get(
    f"{BASE_URL}/feedback",
    headers={"X-API-Key": API_KEY},
    params={
        "status": "pending",
        "feedback_type": "correction",
        "limit": 50
    }
)

feedback_list = response.json()
print(f"Found {feedback_list['total']} pending corrections")

for item in feedback_list['items']:
    print(f"\nFeedback #{item['feedback_id']}")
    print(f"  Original: {item['original_text']}")
    print(f"  Corrected: {item['corrected_text']}")
    print(f"  Accuracy: {item['accuracy_score']:.2%}")
```

**Advanced filtering with date range:**

```python
from datetime import datetime, timedelta

# Get feedback from the last 7 days
week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"

response = requests.get(
    f"{BASE_URL}/feedback",
    headers={"X-API-Key": API_KEY},
    params={
        "from_date": week_ago,
        "status": "pending",
        "min_accuracy_score": 0.85,
        "sort_by": "created_at",
        "sort_order": "desc"
    }
)

feedback = response.json()
print(f"Recent high-quality feedback: {len(feedback['items'])} items")
```

**Pagination example:**

```python
def fetch_all_pending_feedback(api_key: str, base_url: str):
    """Fetch all pending feedback using pagination."""
    all_feedback = []
    page = 1
    
    while True:
        response = requests.get(
            f"{base_url}/feedback",
            headers={"X-API-Key": api_key},
            params={
                "status": "pending",
                "page": page,
                "limit": 100
            }
        )
        response.raise_for_status()
        data = response.json()
        
        all_feedback.extend(data['items'])
        
        # Check if we've fetched all pages
        if page >= data['pages']:
            break
        
        page += 1
    
    return all_feedback

pending = fetch_all_pending_feedback(API_KEY, BASE_URL)
print(f"Total pending feedback: {len(pending)}")
```

### Prioritization Strategies

**1. Frequency-based**: Identify corrections that appear multiple times

```python
from collections import Counter

# Group corrections by normalized term
corrections = Counter()
for item in feedback_list['items']:
    # Extract corrected term (simplified)
    corrected = item['corrected_text'].split()
    original = item['original_text'].split()
    for c, o in zip(corrected, original):
        if c != o:
            corrections[f"{o} → {c}"] += 1

# Show most common corrections
print("Most common corrections:")
for correction, count in corrections.most_common(10):
    print(f"  {correction}: {count} times")
```

**2. Recency-based**: Focus on recent feedback while issues are fresh

**3. Domain-specific**: Process medical terms before general vocabulary

**4. Impact-based**: Prioritize terms that affect critical meaning

---

## Step 3: Admin Approves/Rejects

After reviewing feedback, administrators approve valuable corrections or reject invalid ones. This controls lexicon quality and provides clear audit trails.

### API Endpoint

```
PATCH /feedback/{feedback_id}
```

### Request Structure

**Path Parameters:**
- `feedback_id` (integer): The feedback record identifier

**Headers:**
- `X-API-Key` (string): Your API authentication key
- `Content-Type`: `application/json`

**Request Body:**

```json
{
  "status": "approved",
  "reviewer": "admin_username",
  "admin_notes": "Valid medical term correction. Adding to radiology lexicon."
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | Yes | New status: `approved` or `rejected` |
| `reviewer` | string | No | Admin username for audit trail |
| `admin_notes` | string | No | Reason for decision |

### Status Transition Rules

```
pending ──approve──> approved   (can be used for lexicon updates)
pending ──reject───> rejected   (archived, not used for learning)

✗ approved ──×──> rejected     (not allowed - maintain consistency)
✗ rejected ──×──> approved     (not allowed - create new feedback if needed)
```

**Status Meanings:**

- **pending**: Newly submitted, awaiting admin review
- **approved**: Validated by admin, ready for lexicon incorporation
- **rejected**: Invalid, low-quality, or not applicable

### When to Approve

Approve feedback that:
- ✅ Contains genuine transcription errors
- ✅ Identifies domain-specific terminology
- ✅ Provides valuable corrections for lexicon
- ✅ Has clear before/after text
- ✅ Includes helpful context notes
- ✅ Represents systematic issues worth fixing

### When to Reject

Reject feedback that:
- ❌ Contains stylistic preferences, not errors
- ❌ Suggests incorrect corrections
- ❌ Duplicates existing lexicon entries
- ❌ Lacks clear correction information
- ❌ Represents one-time unique scenarios
- ❌ Contains offensive or inappropriate content

### Response

**Success (200 OK):**

```json
{
  "feedback_id": 42,
  "status": "approved",
  "reviewer": "admin_username",
  "admin_notes": "Valid medical term correction. Adding to radiology lexicon.",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

**Error Responses:**

- **400 Bad Request**: Invalid status transition
- **401 Unauthorized**: Missing or invalid API key
- **404 Not Found**: Feedback ID doesn't exist
- **422 Unprocessable Entity**: Invalid data format

### cURL Examples

**Approve feedback:**

```bash
curl -X PATCH "https://api.example.com/feedback/42" \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved",
    "reviewer": "admin1",
    "admin_notes": "Valid correction for common medical term"
  }'
```

**Reject feedback:**

```bash
curl -X PATCH "https://api.example.com/feedback/43" \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "rejected",
    "reviewer": "admin1",
    "admin_notes": "Stylistic preference, not a transcription error"
  }'
```

### Python Examples

**Approve single feedback:**

```python
import requests

API_KEY = "your-api-key-here"
BASE_URL = "https://api.example.com"

feedback_id = 42

response = requests.patch(
    f"{BASE_URL}/feedback/{feedback_id}",
    headers={
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    },
    json={
        "status": "approved",
        "reviewer": "admin1",
        "admin_notes": "Valid correction"
    }
)

if response.status_code == 200:
    print(f"Feedback #{feedback_id} approved successfully")
else:
    print(f"Error: {response.json()}")
```

**Batch approval workflow:**

```python
def approve_feedback(
    feedback_id: int,
    api_key: str,
    base_url: str,
    reviewer: str,
    notes: str = None
) -> bool:
    """Approve a feedback item."""
    response = requests.patch(
        f"{base_url}/feedback/{feedback_id}",
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        },
        json={
            "status": "approved",
            "reviewer": reviewer,
            "admin_notes": notes or "Approved for lexicon update"
        }
    )
    return response.status_code == 200

def reject_feedback(
    feedback_id: int,
    api_key: str,
    base_url: str,
    reviewer: str,
    reason: str
) -> bool:
    """Reject a feedback item."""
    response = requests.patch(
        f"{base_url}/feedback/{feedback_id}",
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        },
        json={
            "status": "rejected",
            "reviewer": reviewer,
            "admin_notes": reason
        }
    )
    return response.status_code == 200

# Example: Process a batch of feedback
pending_feedback = [
    {"id": 42, "good": True, "note": "Medical term"},
    {"id": 43, "good": False, "note": "Stylistic only"},
    {"id": 44, "good": True, "note": "Drug name"}
]

for item in pending_feedback:
    if item["good"]:
        success = approve_feedback(
            item["id"], API_KEY, BASE_URL, "admin1", item["note"]
        )
    else:
        success = reject_feedback(
            item["id"], API_KEY, BASE_URL, "admin1", item["note"]
        )
    
    status = "✓" if success else "✗"
    action = "approved" if item["good"] else "rejected"
    print(f"{status} Feedback #{item['id']} {action}")
```

**Interactive review script:**

```python
def interactive_review(api_key: str, base_url: str):
    """Interactive script for reviewing feedback."""
    # Fetch pending feedback
    response = requests.get(
        f"{base_url}/feedback",
        headers={"X-API-Key": api_key},
        params={"status": "pending", "limit": 10}
    )
    
    feedback_items = response.json()['items']
    
    if not feedback_items:
        print("No pending feedback to review")
        return
    
    print(f"\n{'='*60}")
    print(f"FEEDBACK REVIEW - {len(feedback_items)} items pending")
    print(f"{'='*60}\n")
    
    for item in feedback_items:
        print(f"\n{'─'*60}")
        print(f"Feedback ID: {item['feedback_id']}")
        print(f"Accuracy Score: {item['accuracy_score']:.2%}")
        print(f"Edit Distance: {item['edit_distance']}")
        print(f"\nOriginal:  {item['original_text']}")
        print(f"Corrected: {item['corrected_text']}")
        
        if item['review_notes']:
            print(f"\nUser Notes: {item['review_notes']}")
        
        print(f"\n{'─'*60}")
        decision = input("Decision [a]pprove / [r]eject / [s]kip: ").lower()
        
        if decision == 'a':
            notes = input("Admin notes (optional): ")
            if approve_feedback(item['feedback_id'], api_key, base_url, "admin1", notes):
                print("✓ Approved")
        elif decision == 'r':
            reason = input("Rejection reason: ")
            if reject_feedback(item['feedback_id'], api_key, base_url, "admin1", reason):
                print("✓ Rejected")
        else:
            print("○ Skipped")

# Run interactive review
interactive_review(API_KEY, BASE_URL)
```

---

## Step 4: Admin Updates Lexicon

After approving feedback, administrators add the corrected terms to the appropriate lexicon. This ensures future transcriptions benefit from the corrections.

### API Endpoint

```
POST /lexicons/{lexicon_id}/terms
```

### Request Structure

**Path Parameters:**
- `lexicon_id` (string): Lexicon identifier (e.g., `radiology`, `cardiology`, `general`)

**Headers:**
- `X-API-Key` (string): Your API authentication key
- `Content-Type`: `application/json`

**Request Body:**

```json
{
  "term": "atreal fibrillation",
  "replacement": "atrial fibrillation",
  "source": "feedback",
  "metadata": {
    "feedback_id": 42,
    "added_by": "admin1",
    "reason": "Common transcription error"
  }
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `term` | string | Yes | The incorrect term to match (case-insensitive) |
| `replacement` | string | Yes | The correct term to substitute |
| `source` | string | No | Source of term: `feedback`, `manual`, `imported` |
| `metadata` | object | No | Additional context (feedback_id, notes, etc.) |

### Response

**Success (201 Created):**

```json
{
  "id": 150,
  "lexicon_id": "radiology",
  "term": "atreal fibrillation",
  "normalized_term": "atreal fibrillation",
  "replacement": "atrial fibrillation",
  "source": "feedback",
  "is_active": true,
  "metadata": {
    "feedback_id": 42,
    "added_by": "admin1",
    "reason": "Common transcription error"
  },
  "created_at": "2024-01-15T14:35:00Z",
  "updated_at": "2024-01-15T14:35:00Z"
}
```

**Error Responses:**

- **400 Bad Request**: Invalid request body
- **401 Unauthorized**: Missing or invalid API key
- **409 Conflict**: Term already exists in lexicon
- **422 Unprocessable Entity**: Invalid lexicon_id format

### Translating Feedback to Lexicon Entries

#### Strategy 1: Direct Term Extraction

For simple single-word corrections:

```python
# Feedback: "atreal" → "atrial"
lexicon_term = {
    "term": "atreal",
    "replacement": "atrial"
}
```

#### Strategy 2: Phrase Extraction

For multi-word corrections:

```python
# Feedback: "atreal fibrillation" → "atrial fibrillation"
lexicon_term = {
    "term": "atreal fibrillation",
    "replacement": "atrial fibrillation"
}
```

#### Strategy 3: Pattern Consolidation

When multiple feedback items correct the same error:

```python
# Multiple feedback: "acetamenophen", "acetaminofen" → "acetaminophen"
# Create single lexicon entry with most common misspelling
lexicon_term = {
    "term": "acetamenophen",
    "replacement": "acetaminophen",
    "metadata": {
        "alternative_spellings": ["acetaminofen", "acetaminophin"],
        "frequency": 5
    }
}
```

### Lexicon Selection Guidelines

Choose the appropriate lexicon based on domain:

| Lexicon ID | Use For | Examples |
|------------|---------|----------|
| `radiology` | Medical imaging terms | MRI, CT scan, radiograph |
| `cardiology` | Heart and cardiovascular | atrial fibrillation, ECG, angina |
| `pharmacy` | Drugs and medications | acetaminophen, lisinopril, metformin |
| `general` | Common terms across domains | patient, doctor, diagnosis |

### cURL Examples

**Add term from approved feedback:**

```bash
curl -X POST "https://api.example.com/lexicons/cardiology/terms" \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "term": "atreal fibrillation",
    "replacement": "atrial fibrillation",
    "source": "feedback",
    "metadata": {
      "feedback_id": 42,
      "added_by": "admin1"
    }
  }'
```

**Add multiple variations:**

```bash
# Add primary term
curl -X POST "https://api.example.com/lexicons/pharmacy/terms" \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "term": "acetamenophen",
    "replacement": "acetaminophen",
    "source": "feedback"
  }'

# Add alternative spelling
curl -X POST "https://api.example.com/lexicons/pharmacy/terms" \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "term": "acetaminofen",
    "replacement": "acetaminophen",
    "source": "feedback"
  }'
```

### Python Examples

**Add single term:**

```python
import requests

API_KEY = "your-api-key-here"
BASE_URL = "https://api.example.com"

def add_lexicon_term(
    lexicon_id: str,
    term: str,
    replacement: str,
    api_key: str,
    base_url: str,
    feedback_id: int = None,
    added_by: str = None
) -> dict:
    """Add a term to a lexicon from approved feedback."""
    payload = {
        "term": term,
        "replacement": replacement,
        "source": "feedback"
    }
    
    if feedback_id or added_by:
        payload["metadata"] = {}
        if feedback_id:
            payload["metadata"]["feedback_id"] = feedback_id
        if added_by:
            payload["metadata"]["added_by"] = added_by
    
    response = requests.post(
        f"{base_url}/lexicons/{lexicon_id}/terms",
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        },
        json=payload
    )
    response.raise_for_status()
    return response.json()

# Add term from feedback
term = add_lexicon_term(
    lexicon_id="cardiology",
    term="atreal fibrillation",
    replacement="atrial fibrillation",
    api_key=API_KEY,
    base_url=BASE_URL,
    feedback_id=42,
    added_by="admin1"
)

print(f"Added term #{term['id']} to lexicon")
```

**Automated workflow: Feedback → Lexicon:**

```python
def process_approved_feedback_to_lexicon(
    api_key: str,
    base_url: str,
    default_lexicon: str = "general"
):
    """
    Automated workflow to process approved feedback into lexicon.
    
    1. Fetch approved feedback that hasn't been processed
    2. Extract terms from corrections
    3. Add terms to appropriate lexicon
    4. Mark feedback as processed
    """
    # Step 1: Fetch unprocessed approved feedback
    response = requests.get(
        f"{base_url}/feedback",
        headers={"X-API-Key": api_key},
        params={
            "status": "approved",
            "is_processed": False,
            "limit": 50
        }
    )
    feedback_items = response.json()['items']
    
    print(f"Processing {len(feedback_items)} approved feedback items...\n")
    
    for item in feedback_items:
        try:
            # Step 2: Extract correction
            # Simple extraction - in production, use more sophisticated parsing
            original_words = item['original_text'].lower().split()
            corrected_words = item['corrected_text'].lower().split()
            
            # Find differences
            for orig, corr in zip(original_words, corrected_words):
                if orig != corr:
                    # Step 3: Add to lexicon
                    term_data = {
                        "term": orig,
                        "replacement": corr,
                        "source": "feedback",
                        "metadata": {
                            "feedback_id": item['feedback_id'],
                            "original_phrase": item['original_text'],
                            "corrected_phrase": item['corrected_text']
                        }
                    }
                    
                    # Determine lexicon (use metadata or default)
                    lexicon_id = item.get('metadata', {}).get('lexicon_id', default_lexicon)
                    
                    try:
                        add_response = requests.post(
                            f"{base_url}/lexicons/{lexicon_id}/terms",
                            headers={
                                "X-API-Key": api_key,
                                "Content-Type": "application/json"
                            },
                            json=term_data
                        )
                        
                        if add_response.status_code == 201:
                            term = add_response.json()
                            print(f"✓ Added: '{orig}' → '{corr}' to {lexicon_id} lexicon")
                        elif add_response.status_code == 409:
                            print(f"○ Skipped: '{orig}' → '{corr}' (already exists)")
                        else:
                            print(f"✗ Error adding term: {add_response.status_code}")
                    
                    except requests.RequestException as e:
                        print(f"✗ Request failed: {e}")
                        continue
            
            # Step 4: Mark as processed
            # This would require a PATCH endpoint to update is_processed flag
            # PATCH /feedback/{feedback_id} with {"is_processed": true}
            
        except Exception as e:
            print(f"✗ Error processing feedback #{item['feedback_id']}: {e}")

# Run the automated workflow
process_approved_feedback_to_lexicon(API_KEY, BASE_URL, "general")
```

**Batch processing with consolidation:**

```python
from collections import defaultdict

def consolidate_and_add_terms(
    api_key: str,
    base_url: str,
    lexicon_id: str
):
    """
    Consolidate similar corrections and add to lexicon.
    
    Groups corrections by the corrected term to identify patterns.
    """
    # Fetch approved unprocessed feedback
    response = requests.get(
        f"{base_url}/feedback",
        headers={"X-API-Key": api_key},
        params={
            "status": "approved",
            "is_processed": False
        }
    )
    feedback_items = response.json()['items']
    
    # Group by corrected term
    corrections = defaultdict(list)
    
    for item in feedback_items:
        # Extract corrections (simplified)
        original_words = item['original_text'].lower().split()
        corrected_words = item['corrected_text'].lower().split()
        
        for orig, corr in zip(original_words, corrected_words):
            if orig != corr:
                corrections[corr].append({
                    "term": orig,
                    "feedback_id": item['feedback_id'],
                    "count": 1
                })
    
    # Add consolidated terms
    print(f"Found {len(corrections)} unique corrections\n")
    
    for replacement, variants in corrections.items():
        # Count occurrences
        term_counts = defaultdict(int)
        for variant in variants:
            term_counts[variant['term']] += variant['count']
        
        # Use most common misspelling as primary term
        most_common_term = max(term_counts, key=term_counts.get)
        count = term_counts[most_common_term]
        
        print(f"'{most_common_term}' → '{replacement}' (seen {count} times)")
        
        # Add to lexicon
        term_data = {
            "term": most_common_term,
            "replacement": replacement,
            "source": "feedback",
            "metadata": {
                "frequency": count,
                "alternative_spellings": [t for t in term_counts.keys() if t != most_common_term]
            }
        }
        
        try:
            response = requests.post(
                f"{base_url}/lexicons/{lexicon_id}/terms",
                headers={
                    "X-API-Key": api_key,
                    "Content-Type": "application/json"
                },
                json=term_data
            )
            
            if response.status_code == 201:
                print(f"  ✓ Added to lexicon\n")
            elif response.status_code == 409:
                print(f"  ○ Already exists\n")
        
        except requests.RequestException as e:
            print(f"  ✗ Failed: {e}\n")

# Run consolidation
consolidate_and_add_terms(API_KEY, BASE_URL, "medical")
```

### Best Practices for Lexicon Updates

**1. Maintain Quality:**
- Only add terms from approved feedback
- Verify corrections are genuinely better
- Avoid adding rare one-off variations

**2. Handle Duplicates:**
- Check if term already exists before adding
- Use metadata to track multiple sources
- Update frequency counts for existing terms

**3. Use Metadata:**
- Track feedback_id for audit trail
- Record who added the term and when
- Note the reason or context

**4. Organize by Domain:**
- Use appropriate lexicon for each term
- Keep medical terms separate from general vocabulary
- Consider creating specialized sub-lexicons

**5. Monitor Impact:**
- Track before/after transcription quality
- Identify which lexicon additions help most
- Remove terms that don't improve accuracy

---

## Best Practices

### Batch Review Workflows

**Daily Review Routine:**

```python
def daily_review_workflow(api_key: str, base_url: str):
    """Daily workflow for processing feedback."""
    
    # 1. Check pending count
    response = requests.get(
        f"{base_url}/feedback",
        headers={"X-API-Key": api_key},
        params={"status": "pending", "limit": 1}
    )
    total_pending = response.json()['total']
    print(f"📊 Pending feedback: {total_pending}")
    
    if total_pending == 0:
        print("✓ No pending feedback to review")
        return
    
    # 2. Review high-confidence items first (quick wins)
    print("\n🎯 Reviewing high-confidence corrections...")
    response = requests.get(
        f"{base_url}/feedback",
        headers={"X-API-Key": api_key},
        params={
            "status": "pending",
            "min_accuracy_score": 0.9,
            "feedback_type": "correction",
            "limit": 20
        }
    )
    high_confidence = response.json()['items']
    print(f"Found {len(high_confidence)} high-confidence items")
    
    # Process these (approve most, review edge cases)
    # ... approval logic ...
    
    # 3. Review domain-specific feedback
    for lexicon in ["radiology", "cardiology", "pharmacy"]:
        print(f"\n🏥 Reviewing {lexicon} feedback...")
        response = requests.get(
            f"{base_url}/feedback",
            headers={"X-API-Key": api_key},
            params={
                "status": "pending",
                "lexicon_id": lexicon,
                "limit": 10
            }
        )
        lexicon_feedback = response.json()['items']
        print(f"Found {len(lexicon_feedback)} items for {lexicon}")
        # ... review logic ...
    
    # 4. Update lexicons with approved items
    print("\n📝 Updating lexicons with approved feedback...")
    process_approved_feedback_to_lexicon(api_key, base_url)
    
    # 5. Summary
    print("\n✅ Daily review complete")

# Run daily
daily_review_workflow(API_KEY, BASE_URL)
```

### Identifying Patterns in Corrections

**Pattern Analysis:**

```python
def analyze_correction_patterns(api_key: str, base_url: str):
    """Analyze patterns in feedback to identify systematic issues."""
    
    # Fetch recent approved feedback
    response = requests.get(
        f"{base_url}/feedback",
        headers={"X-API-Key": api_key},
        params={
            "status": "approved",
            "limit": 500,
            "sort_by": "created_at",
            "sort_order": "desc"
        }
    )
    
    feedback_items = response.json()['items']
    
    # Pattern 1: Most common corrections
    from collections import Counter
    corrections = Counter()
    
    for item in feedback_items:
        orig = item['original_text'].lower()
        corr = item['corrected_text'].lower()
        if orig != corr:
            corrections[f"{orig} → {corr}"] += 1
    
    print("🔍 Most Common Corrections:")
    for correction, count in corrections.most_common(10):
        print(f"  {count:3d}× {correction}")
    
    # Pattern 2: Accuracy score distribution
    accuracy_scores = [item['accuracy_score'] for item in feedback_items]
    avg_accuracy = sum(accuracy_scores) / len(accuracy_scores)
    
    print(f"\n📊 Accuracy Statistics:")
    print(f"  Average: {avg_accuracy:.2%}")
    print(f"  Min: {min(accuracy_scores):.2%}")
    print(f"  Max: {max(accuracy_scores):.2%}")
    
    # Pattern 3: Feedback by type
    type_counts = Counter(item['feedback_type'] for item in feedback_items)
    print(f"\n📝 Feedback Types:")
    for ftype, count in type_counts.items():
        print(f"  {ftype}: {count}")
    
    # Pattern 4: Edit distance distribution
    edit_distances = [item['edit_distance'] for item in feedback_items]
    print(f"\n✏️  Edit Distance:")
    print(f"  Average: {sum(edit_distances) / len(edit_distances):.1f}")
    print(f"  Most common: {Counter(edit_distances).most_common(5)}")

analyze_correction_patterns(API_KEY, BASE_URL)
```

### When to Create vs Update Terms

**Decision Matrix:**

| Scenario | Action | Reason |
|----------|--------|--------|
| Term doesn't exist in lexicon | **CREATE** | New correction to learn |
| Term exists with different replacement | **UPDATE** | Better correction found |
| Term exists with same replacement | **SKIP** | Already handled |
| Similar term exists (variant spelling) | **CREATE** | Handle both spellings |
| Term is highly domain-specific | **CREATE** in specialized lexicon | Better organization |
| Term is general/common | **CREATE** in general lexicon | Broad applicability |

**Implementation:**

```python
def smart_term_add_or_update(
    lexicon_id: str,
    term: str,
    replacement: str,
    api_key: str,
    base_url: str
) -> str:
    """
    Intelligently add or update a term based on existence.
    
    Returns: "created", "updated", "skipped", or "error"
    """
    # Check if term exists
    response = requests.get(
        f"{base_url}/lexicons/{lexicon_id}/terms",
        headers={"X-API-Key": api_key},
        params={"search": term, "limit": 100}
    )
    
    existing_terms = response.json()['items']
    
    # Find exact match (case-insensitive)
    existing = None
    for t in existing_terms:
        if t['term'].lower() == term.lower():
            existing = t
            break
    
    if not existing:
        # CREATE new term
        try:
            response = requests.post(
                f"{base_url}/lexicons/{lexicon_id}/terms",
                headers={
                    "X-API-Key": api_key,
                    "Content-Type": "application/json"
                },
                json={"term": term, "replacement": replacement}
            )
            if response.status_code == 201:
                return "created"
        except:
            return "error"
    
    elif existing['replacement'] != replacement:
        # UPDATE if replacement is different
        try:
            response = requests.put(
                f"{base_url}/lexicons/{lexicon_id}/terms/{existing['id']}",
                headers={
                    "X-API-Key": api_key,
                    "Content-Type": "application/json"
                },
                json={"term": term, "replacement": replacement}
            )
            if response.status_code == 200:
                return "updated"
        except:
            return "error"
    
    else:
        # SKIP - already correct
        return "skipped"
    
    return "error"

# Usage
result = smart_term_add_or_update(
    "cardiology", "atreal", "atrial", API_KEY, BASE_URL
)
print(f"Term was {result}")
```

### Handling Conflicting Corrections

**Scenario:** Multiple users submit different corrections for the same term.

**Resolution Strategies:**

**1. Frequency-based:**
```python
def resolve_by_frequency(conflicting_corrections: list) -> str:
    """Choose the most common correction."""
    from collections import Counter
    corrections = Counter(c['corrected_text'] for c in conflicting_corrections)
    return corrections.most_common(1)[0][0]
```

**2. Recency-based:**
```python
def resolve_by_recency(conflicting_corrections: list) -> str:
    """Choose the most recent correction."""
    sorted_by_date = sorted(
        conflicting_corrections,
        key=lambda x: x['created_at'],
        reverse=True
    )
    return sorted_by_date[0]['corrected_text']
```

**3. Accuracy-based:**
```python
def resolve_by_accuracy(conflicting_corrections: list) -> str:
    """Choose correction with highest accuracy score."""
    best = max(conflicting_corrections, key=lambda x: x['accuracy_score'])
    return best['corrected_text']
```

**4. Expert review:**
```python
def flag_for_expert_review(conflicting_corrections: list):
    """Flag conflicts for manual expert review."""
    print(f"⚠️  Conflicting corrections found:")
    for i, corr in enumerate(conflicting_corrections, 1):
        print(f"  {i}. '{corr['corrected_text']}' "
              f"(accuracy: {corr['accuracy_score']:.2%}, "
              f"submitted: {corr['created_at']})")
    
    choice = input("Select correction [1-N] or [s]kip: ")
    if choice.lower() != 's':
        return conflicting_corrections[int(choice) - 1]['corrected_text']
    return None
```

### Periodic Lexicon Maintenance

**Monthly Maintenance Checklist:**

```python
def monthly_lexicon_maintenance(api_key: str, base_url: str):
    """Comprehensive monthly lexicon maintenance."""
    
    print("🔧 Monthly Lexicon Maintenance\n")
    
    # 1. Identify unused terms
    print("1️⃣ Identifying unused terms...")
    # Terms with low frequency or no recent usage
    # (requires usage tracking in metadata)
    
    # 2. Review low-impact terms
    print("2️⃣ Reviewing low-impact terms...")
    # Terms that rarely match in transcriptions
    
    # 3. Consolidate duplicates
    print("3️⃣ Checking for duplicates...")
    for lexicon in ["radiology", "cardiology", "pharmacy", "general"]:
        response = requests.get(
            f"{base_url}/lexicons/{lexicon}/terms",
            headers={"X-API-Key": api_key},
            params={"limit": 1000}
        )
        terms = response.json()['items']
        
        # Find near-duplicates
        seen_replacements = {}
        for term in terms:
            replacement = term['replacement'].lower()
            if replacement in seen_replacements:
                print(f"  ⚠️  Duplicate in {lexicon}: "
                      f"'{term['term']}' and '{seen_replacements[replacement]['term']}' "
                      f"both → '{replacement}'")
            else:
                seen_replacements[replacement] = term
    
    # 4. Update term metadata
    print("4️⃣ Updating term metadata...")
    # Add usage statistics, last matched date, etc.
    
    # 5. Generate quality report
    print("5️⃣ Generating quality report...")
    # Report on feedback trends, common errors, improvement metrics
    
    print("\n✅ Maintenance complete")

# Run monthly
monthly_lexicon_maintenance(API_KEY, BASE_URL)
```

---

## Edge Cases & Troubleshooting

### Common Edge Cases

#### 1. Feedback for Non-Existent Job

**Error:**
```json
{
  "detail": "Job not found",
  "status_code": 404
}
```

**Resolution:**
- Verify job_id is correct (UUID format)
- Ensure job belongs to your API key
- Check job status is "completed" before submitting feedback

#### 2. Duplicate Feedback Submissions

**Scenario:** User submits same correction multiple times

**Prevention:**
```python
def check_existing_feedback(job_id: str, api_key: str, base_url: str) -> bool:
    """Check if feedback already exists for this job."""
    response = requests.get(
        f"{base_url}/feedback",
        headers={"X-API-Key": api_key},
        params={"job_id": job_id}
    )
    return response.json()['total'] > 0

# Use before submitting
if not check_existing_feedback(job_id, API_KEY, BASE_URL):
    # Submit feedback
    pass
else:
    print("Feedback already exists for this job")
```

#### 3. Empty or Invalid Corrections

**Invalid submissions:**
- original_text == corrected_text (no change)
- Empty strings
- Only whitespace differences

**Validation:**
```python
def validate_correction(original: str, corrected: str) -> tuple[bool, str]:
    """Validate correction before submission."""
    # Check not empty
    if not original or not corrected:
        return False, "Text cannot be empty"
    
    # Check not identical
    if original.strip() == corrected.strip():
        return False, "Corrected text is identical to original"
    
    # Check reasonable length
    if len(original) > 5000 or len(corrected) > 5000:
        return False, "Text too long (max 5000 characters)"
    
    # Check not just whitespace changes
    if original.replace(" ", "") == corrected.replace(" ", ""):
        return False, "Only whitespace differences detected"
    
    return True, "Valid"

# Validate before submitting
is_valid, message = validate_correction(original, corrected)
if not is_valid:
    print(f"Invalid correction: {message}")
```

#### 4. Lexicon Term Already Exists

**Error when adding term:**
```json
{
  "detail": "Term already exists in this lexicon",
  "status_code": 409
}
```

**Resolution:**
```python
def handle_duplicate_term(lexicon_id: str, term: str, replacement: str, 
                         api_key: str, base_url: str):
    """Handle duplicate term gracefully."""
    try:
        # Try to add
        response = requests.post(
            f"{base_url}/lexicons/{lexicon_id}/terms",
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            json={"term": term, "replacement": replacement}
        )
        response.raise_for_status()
        print("✓ Term added successfully")
    
    except requests.HTTPError as e:
        if e.response.status_code == 409:
            # Term exists - check if update needed
            print("○ Term already exists")
            
            # Fetch existing term
            response = requests.get(
                f"{base_url}/lexicons/{lexicon_id}/terms",
                headers={"X-API-Key": api_key},
                params={"search": term}
            )
            existing = response.json()['items'][0]
            
            if existing['replacement'] != replacement:
                print(f"  Existing: '{existing['replacement']}'")
                print(f"  New:      '{replacement}'")
                update = input("  Update? [y/n]: ")
                
                if update.lower() == 'y':
                    # Update the term
                    requests.put(
                        f"{base_url}/lexicons/{lexicon_id}/terms/{existing['id']}",
                        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
                        json={"term": term, "replacement": replacement}
                    )
                    print("✓ Term updated")
        else:
            print(f"✗ Error: {e}")
```

#### 5. Feedback for Wrong Lexicon

**Scenario:** User submits medical term correction, but job used general lexicon

**Prevention:**
```python
def get_job_lexicon(job_id: str, api_key: str, base_url: str) -> str:
    """Get the lexicon used for a specific job."""
    response = requests.get(
        f"{base_url}/jobs/{job_id}",
        headers={"X-API-Key": api_key}
    )
    job = response.json()
    return job.get('metadata', {}).get('lexicon_id', 'general')

# Include in feedback submission
lexicon_id = get_job_lexicon(job_id, API_KEY, BASE_URL)
feedback_data['metadata'] = {'lexicon_id': lexicon_id}
```

#### 6. Invalid Status Transitions

**Error:**
```json
{
  "detail": "Cannot change status from approved to rejected",
  "status_code": 400
}
```

**Valid transitions:**
- pending → approved ✓
- pending → rejected ✓
- approved → rejected ✗
- rejected → approved ✗

**Prevention:**
```python
def check_valid_transition(current_status: str, new_status: str) -> bool:
    """Check if status transition is valid."""
    valid_transitions = {
        "pending": ["approved", "rejected"],
        "approved": [],
        "rejected": []
    }
    return new_status in valid_transitions.get(current_status, [])

# Before updating
if not check_valid_transition(feedback['status'], "rejected"):
    print("Invalid status transition")
```

### Troubleshooting Guide

#### Issue: "No pending feedback found"

**Possible Causes:**
1. All feedback has been reviewed
2. Filters are too restrictive
3. Wrong lexicon_id specified

**Solutions:**
```python
# Check total feedback across all statuses
response = requests.get(
    f"{BASE_URL}/feedback",
    headers={"X-API-Key": API_KEY},
    params={"limit": 1}
)
total = response.json()['total']
print(f"Total feedback in system: {total}")

# Check by status
for status in ["pending", "approved", "rejected"]:
    response = requests.get(
        f"{BASE_URL}/feedback",
        headers={"X-API-Key": API_KEY},
        params={"status": status, "limit": 1}
    )
    count = response.json()['total']
    print(f"{status.capitalize()}: {count}")
```

#### Issue: "Feedback submission fails with 404"

**Possible Causes:**
1. Job doesn't exist
2. Job doesn't belong to your API key
3. Job hasn't completed yet

**Solutions:**
```python
# Verify job exists and is complete
response = requests.get(
    f"{BASE_URL}/jobs/{job_id}",
    headers={"X-API-Key": API_KEY}
)

if response.status_code == 404:
    print("Job not found or unauthorized")
elif response.status_code == 200:
    job = response.json()
    print(f"Job status: {job['status']}")
    
    if job['status'] != 'completed':
        print(f"Cannot submit feedback - job not completed yet")
```

#### Issue: "Lexicon updates don't improve transcriptions"

**Possible Causes:**
1. Wrong lexicon selected for job
2. Terms too specific/rare
3. Term normalization issues
4. Case sensitivity problems

**Solutions:**
1. Verify correct lexicon is specified in transcription request:
   ```bash
   curl -X POST "/transcribe" \
     -H "X-Lexicon-ID: radiology" \
     -F "audio=@file.mp3"
   ```

2. Check term normalization:
   ```python
   # Terms are normalized (lowercased) for matching
   # "Atrial" in term matches "atrial", "ATRIAL", "Atrial" in transcription
   ```

3. Review lexicon term statistics:
   ```python
   response = requests.get(
       f"{BASE_URL}/lexicons/radiology/terms",
       headers={"X-API-Key": API_KEY}
   )
   terms = response.json()['items']
   
   # Check if terms are being used
   for term in terms:
       print(f"{term['term']:30s} → {term['replacement']}")
   ```

#### Issue: "High feedback volume, can't keep up"

**Solutions:**

1. **Prioritize high-impact corrections:**
   ```python
   # Focus on corrections with multiple occurrences
   response = requests.get(
       f"{BASE_URL}/feedback",
       headers={"X-API-Key": API_KEY},
       params={
           "status": "pending",
           "min_accuracy_score": 0.85,
           "limit": 50
       }
   )
   ```

2. **Automate approval for high-confidence items:**
   ```python
   def auto_approve_high_confidence(api_key: str, base_url: str):
       """Auto-approve feedback with very high confidence."""
       response = requests.get(
           f"{base_url}/feedback",
           headers={"X-API-Key": api_key},
           params={
               "status": "pending",
               "min_accuracy_score": 0.95,
               "edit_distance": 1,  # Only single-character changes
               "limit": 100
           }
       )
       
       high_conf = response.json()['items']
       
       for item in high_conf:
           # Auto-approve
           requests.patch(
               f"{base_url}/feedback/{item['feedback_id']}",
               headers={"X-API-Key": api_key, "Content-Type": "application/json"},
               json={
                   "status": "approved",
                   "reviewer": "auto_approve_bot",
                   "admin_notes": "Auto-approved: high confidence correction"
               }
           )
       
       print(f"Auto-approved {len(high_conf)} high-confidence corrections")
   ```

3. **Batch review by pattern:**
   ```python
   # Group similar corrections together
   def group_by_pattern(feedback_items: list) -> dict:
       """Group feedback by correction pattern."""
       groups = defaultdict(list)
       
       for item in feedback_items:
           # Extract the main correction (simplified)
           orig_words = set(item['original_text'].lower().split())
           corr_words = set(item['corrected_text'].lower().split())
           diff = corr_words - orig_words
           
           if diff:
               key = next(iter(diff))  # Use first different word as key
               groups[key].append(item)
       
       return groups
   
   # Review all similar corrections at once
   groups = group_by_pattern(feedback_items)
   for pattern, items in groups.items():
       print(f"\nPattern: '{pattern}' ({len(items)} occurrences)")
       # Batch approve/reject
   ```

#### Issue: "Feedback metrics don't match expectations"

**Diagnostic queries:**

```python
def feedback_diagnostics(api_key: str, base_url: str):
    """Run diagnostic queries on feedback data."""
    
    print("🔍 Feedback Diagnostics\n")
    
    # 1. Status distribution
    print("1️⃣ Status Distribution:")
    for status in ["pending", "approved", "rejected"]:
        response = requests.get(
            f"{base_url}/feedback",
            headers={"X-API-Key": api_key},
            params={"status": status, "limit": 1}
        )
        count = response.json()['total']
        print(f"   {status.capitalize():10s}: {count:4d}")
    
    # 2. Accuracy distribution
    print("\n2️⃣ Accuracy Score Distribution:")
    response = requests.get(
        f"{base_url}/feedback",
        headers={"X-API-Key": api_key},
        params={"limit": 1000}
    )
    items = response.json()['items']
    
    accuracy_ranges = {
        "0.0-0.5": 0,
        "0.5-0.7": 0,
        "0.7-0.9": 0,
        "0.9-1.0": 0
    }
    
    for item in items:
        score = item['accuracy_score']
        if score < 0.5:
            accuracy_ranges["0.0-0.5"] += 1
        elif score < 0.7:
            accuracy_ranges["0.5-0.7"] += 1
        elif score < 0.9:
            accuracy_ranges["0.7-0.9"] += 1
        else:
            accuracy_ranges["0.9-1.0"] += 1
    
    for range_label, count in accuracy_ranges.items():
        print(f"   {range_label}: {count:4d}")
    
    # 3. Processing status
    print("\n3️⃣ Processing Status:")
    processed = sum(1 for item in items if item['is_processed'])
    unprocessed = len(items) - processed
    print(f"   Processed:   {processed:4d}")
    print(f"   Unprocessed: {unprocessed:4d}")
    
    # 4. Feedback by type
    print("\n4️⃣ Feedback Types:")
    type_counts = Counter(item['feedback_type'] for item in items)
    for ftype, count in type_counts.items():
        print(f"   {ftype:15s}: {count:4d}")

feedback_diagnostics(API_KEY, BASE_URL)
```

---

## Approval Decision Tree

Use this decision tree to guide your approval/rejection decisions:

```
┌─────────────────────────────────────────────────────────┐
│           Feedback Review Decision Tree                 │
└─────────────────────────────────────────────────────────┘

START: Review Feedback Item
    │
    ├─> Is the correction FACTUALLY CORRECT?
    │   │
    │   ├─> NO ──> REJECT (incorrect correction)
    │   │          Note: "Suggested correction is incorrect"
    │   │
    │   └─> YES
    │       │
    │       ├─> Is it a GENUINE TRANSCRIPTION ERROR?
    │       │   │
    │       │   ├─> NO (stylistic/punctuation only)
    │       │   │   └─> REJECT
    │       │   │       Note: "Stylistic change, not an error"
    │       │   │
    │       │   └─> YES
    │       │       │
    │       │       ├─> Is the term DOMAIN-SPECIFIC?
    │       │       │   │
    │       │       │   ├─> YES (medical/legal/technical)
    │       │       │   │   │
    │       │       │   │   ├─> Already in lexicon?
    │       │       │   │   │   │
    │       │       │   │   │   ├─> YES ──> REJECT
    │       │       │   │   │   │           Note: "Already in lexicon"
    │       │       │   │   │   │
    │       │       │   │   │   └─> NO ──> APPROVE ✓
    │       │       │   │   │               Note: "Valid term for lexicon"
    │       │       │   │   │               Action: Add to appropriate lexicon
    │       │       │   │   │
    │       │       │   │   └─> Is it COMMON/RECURRING?
    │       │       │   │       │
    │       │       │   │       ├─> YES ──> APPROVE ✓
    │       │       │   │       │           Note: "Common error worth fixing"
    │       │       │   │       │
    │       │       │   │       └─> NO ──> REJECT
    │       │       │   │                   Note: "Too rare to justify lexicon entry"
    │       │       │   │
    │       │       │   └─> NO (general term)
    │       │       │       │
    │       │       │       └─> Is accuracy score > 0.9?
    │       │       │           │
    │       │       │           ├─> YES ──> APPROVE ✓
    │       │       │           │           Note: "High-quality correction"
    │       │       │           │
    │       │       │           └─> NO
    │       │       │               │
    │       │       │               └─> Manual review needed
    │       │       │                   ├─> Clear improvement ──> APPROVE ✓
    │       │       │                   └─> Unclear/debatable ──> REJECT
    │       │       │
    │       │       └─> Does it have CONTEXT NOTES?
    │       │           │
    │       │           ├─> YES ──> Higher confidence in review
    │       │           └─> NO ──> Review more carefully
    │       │
    │       └─> Is edit_distance reasonable (<= 3)?
    │           │
    │           ├─> YES ──> Likely typo or minor correction
    │           └─> NO ──> May be major rewrite, review carefully

OUTCOMES:
  ✓ APPROVE → Add to lexicon → Improve future transcriptions
  ✗ REJECT → Archive feedback → No lexicon changes
```

### Quick Reference Checklist

**Approve if:**
- ✅ Corrects genuine transcription error
- ✅ Domain-specific term not in lexicon
- ✅ Common/recurring mistake
- ✅ High accuracy score (>0.9)
- ✅ Clear before/after text
- ✅ Helpful context provided

**Reject if:**
- ❌ Stylistic preference only
- ❌ Incorrect suggested correction
- ❌ Already in lexicon
- ❌ Too rare to justify entry
- ❌ Unclear or confusing correction
- ❌ No meaningful improvement

---

## Related Documentation

### API Documentation

- **OpenAPI Specification**: `http://localhost:8000/docs` (Swagger UI)
- **ReDoc**: `http://localhost:8000/redoc` (Alternative API docs)
- **API Reference**: [API_REFERENCE.md](./API_REFERENCE.md) (if available)

### Lexicon Documentation

- **Lexicon CRUD Endpoints**: [LEXICON_API_IMPLEMENTATION.md](../LEXICON_API_IMPLEMENTATION.md)
- **Lexicon Service README**: [app/services/LEXICON_SERVICE_README.md](../app/services/LEXICON_SERVICE_README.md)
- **Lexicon Endpoints**: [LEXICON_ENDPOINTS_README.md](../LEXICON_ENDPOINTS_README.md)

### Database Schema

- **Migration Files**: `alembic/versions/001_initial_schema.py`
- **Feedback Table Schema**:
  ```sql
  CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    original_text TEXT NOT NULL,
    corrected_text TEXT NOT NULL,
    diff_data JSONB,
    edit_distance INTEGER,
    accuracy_score FLOAT,
    review_time_seconds INTEGER,
    reviewer VARCHAR(100),
    review_notes TEXT,
    extracted_terms JSONB,
    feedback_type VARCHAR(50),
    is_processed BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE
  );
  ```

### Authentication

- **API Key Setup**: [setup_api_key.py](../setup_api_key.py)
- **Authentication Guide**: Check main README.md for API key generation

### Example Code

- **Python Examples**: `examples/` directory
- **Integration Tests**: `tests/` directory

### Support

For issues or questions:
1. Check troubleshooting section above
2. Review error messages in API responses
3. Check server logs for detailed error information
4. Consult related documentation linked above

---

## Summary

The manual feedback workflow creates a virtuous cycle:

1. **Users identify errors** → Submit corrections via API
2. **Admins review feedback** → Filter and prioritize valuable corrections
3. **Admins approve/reject** → Quality control ensures lexicon integrity
4. **Admins update lexicons** → Approved corrections become permanent improvements
5. **Future transcriptions improve** → System learns from real-world usage

**Key Success Factors:**

- Regular review cadence (daily or weekly)
- Clear approval criteria (domain-specific, recurring, high-quality)
- Systematic lexicon organization (by domain)
- Pattern analysis (identify common issues)
- Quality maintenance (periodic lexicon cleanup)

By following this workflow, you'll continuously improve transcription accuracy for your specific domains and use cases.
