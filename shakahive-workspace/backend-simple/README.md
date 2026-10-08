# NOVARAai - Simplified Backend with Real AI

A working prototype with actual AI capabilities for NRIF grant screening.

## Features

### Real AI Modules
1. **Eligibility Checker** - Validates against real NRIF criteria:
   - Budget limits ($100K - $5M)
   - Institution type validation
   - Research focus assessment
   - Commercial content detection

2. **Plagiarism Detector** - Uses text similarity algorithms:
   - Sequence matching for overall similarity
   - Phrase-level matching (5+ word sequences)
   - Reference database of existing proposals
   - Severity classification (high/medium/low)

3. **Duplication Checker** - Fuzzy matching against existing applications:
   - Multiple similarity metrics (sequence, fuzzy, title)
   - Combined scoring algorithm
   - Duplicate detection threshold (70%)
   - Top match reporting

4. **Novelty Assessor** - Innovation scoring:
   - Technical novelty detection
   - Methodological innovation assessment
   - Application potential evaluation
   - Market impact analysis
   - Research domain detection

## Quick Start

### Windows
```batch
start.bat
```

### Manual Start
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
```

The server will start on http://localhost:8000

## API Endpoints

### Applications
- `GET /applications` - Get all applications
- `POST /applications` - Create new application
- `GET /applications/{id}` - Get specific application
- `DELETE /applications/{id}` - Delete application
- `PUT /applications/{id}/status` - Update status

### Screening
- `POST /screen/{id}` - Run AI screening on application
- `GET /screenings` - Get all screening results

### Authentication
- `POST /auth-service/login` - Login (accepts any credentials for prototype)

## Database

Uses SQLite for persistence (automatically created on startup):
- `applications` table - Stores grant applications
- `screening_results` table - Stores AI screening results

## Testing

1. Start the backend: `python main.py`
2. Start the frontend: `cd ../frontend && npm run dev`
3. Go to http://localhost:3000
4. Login with any credentials
5. Create an application
6. Click "Screen" to run AI analysis

## AI Scoring

The overall score is calculated as:
- Eligibility: 30% weight
- Plagiarism: 30% weight
- Duplication: 20% weight (inverted)
- Novelty: 20% weight

Status determination:
- Score >= 70 + eligibility passed = Approved
- Score >= 50 = Pending Review
- Score < 50 = Rejected
