# Redrob Hackathon – Candidate Ranking System

**Team:** TECH_SHIV  
**Role:** Senior AI Engineer (Founding Team)  

This system ranks 100,000 candidates for a Senior AI Engineer role at Redrob.  
It uses **feature-based ranking** (career history, behavioral signals, location, honeypot detection) – no external APIs, runs in <5 minutes on CPU.

## How It Works

- **Career score** – product vs consulting experience, ranking keywords (embeddings, vector search, etc.), strict consulting rejection.
- **Behavioral score** – recency, recruiter response rate, interview completion, open to work, saved by recruiters, notice period.
- **Location score** – Pune/Noida, Tier‑1 cities, willingness to relocate.
- **Honeypot detection** – expert skills with zero years, impossible timelines, zero recruiter interaction, senior title with <2 years experience.

**Weights:** career 0.50, behavioral 0.45, location 0.05.  
**Tie‑breaker:** candidate_id (tiny fraction added to score).

## Prerequisites

- Python 3.11+ (CPU only, 8‑16 GB RAM)
- `pip` (Python package installer)

## Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/ShivkumarDiwan/redrob-one-shot.git
   cd redrob-one-shot
