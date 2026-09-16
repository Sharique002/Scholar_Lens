# Database Schema — Scholar Lens

## Entity Relationship Overview

```
User (Django Auth)
 ├── 1:1 ── UserProfile (accounts)
 ├── 1:1 ── ResearcherProfile (researchers)
 ├── 1:N ── ResearchPaper (papers)
 ├── 1:N ── ResearchProject (as leader) (projects)
 ├── N:M ── ResearchProject (as member via ProjectMember) (projects)
 ├── 1:N ── CollaborationRequest (as sender/receiver) (collaboration)
 ├── 1:N ── ChatMessage (ai_engine)
 └── 1:N ── ResearchActivity (dashboard)

ResearchPaper
 ├── 1:N ── PaperAuthor
 ├── 1:N ── PaperChunk
 │           └── 1:1 ── PaperEmbedding
 ├── 1:N ── AIAnalysis
 ├── 1:N ── ResearchGap
 ├── 1:N ── EvaluationReport
 │           └── 1:N ── ResearchScore
 └── 1:N ── ChatMessage

ResearcherProfile
 ├── N:M ── ResearchInterest
 └── N:M ── Skill

ResearchProject
 └── 1:N ── ProjectMember
```

## Models by App

### accounts
| Field | Type | Description |
|-------|------|-------------|
| **UserProfile** | | |
| user | OneToOneField(User) | Django auth user |
| role | CharField | STUDENT, FACULTY, ADMIN |
| bio | TextField | User biography |
| avatar | ImageField | Profile picture |
| institution | CharField | University/organization |
| phone | CharField | Contact phone |
| website | URLField | Personal website |

### researchers
| Field | Type | Description |
|-------|------|-------------|
| **ResearcherProfile** | | |
| user | OneToOneField(User) | Extended user profile |
| headline | CharField | Professional headline |
| expertise_summary | TextField | Summary of expertise |
| google_scholar_url | URLField | Google Scholar link |
| orcid_id | CharField | ORCID identifier |
| years_experience | PositiveIntegerField | Years in research |
| interests | ManyToManyField(ResearchInterest) | Research interests |
| skills | ManyToManyField(Skill) | Technical skills |
| is_available_for_collaboration | BooleanField | Open to collaborate |
| **ResearchInterest** | | |
| name | CharField(unique) | Interest name |
| category | CharField | Interest category |
| **Skill** | | |
| name | CharField(unique) | Skill name |
| category | CharField | PROGRAMMING, FRAMEWORK, etc. |

### papers
| Field | Type | Description |
|-------|------|-------------|
| **ResearchPaper** | | |
| title | CharField | Paper title |
| abstract | TextField | Paper abstract |
| research_area | CharField | AI_ML, NLP, etc. |
| keywords | CharField | Comma-separated keywords |
| status | CharField | UPLOADED → EVALUATED |
| pdf_file | FileField | Uploaded PDF |
| extracted_text | TextField | Extracted full text |
| page_count | IntegerField | Number of pages |
| word_count | IntegerField | Word count |
| uploader | ForeignKey(User) | Who uploaded |
| **PaperAuthor** | | |
| paper | ForeignKey(ResearchPaper) | Parent paper |
| name | CharField | Author name |
| email | EmailField | Author email |
| affiliation | CharField | Author institution |
| order | PositiveIntegerField | Display order |
| **PaperChunk** | | |
| paper | ForeignKey(ResearchPaper) | Parent paper |
| chunk_index | IntegerField | Position in document |
| page_number | IntegerField | PDF page number origin |
| section | CharField | Detected section header (Methodology, etc.) |
| start_offset | IntegerField | Character start offset |
| end_offset | IntegerField | Character end offset |
| content | TextField | Chunk text content |
| token_count | IntegerField | Estimated tokens |
| **PaperEmbedding** | | |
| chunk | OneToOneField(PaperChunk) | Related chunk |
| embedding | JSONField | Vector embedding |
| model_name | CharField | Model used |

### ai_engine
| Field | Type | Description |
|-------|------|-------------|
| **AIAnalysis** | | |
| paper | ForeignKey(ResearchPaper) | Analyzed paper |
| analysis_type | CharField | SUMMARY, GAPS, etc. |
| result | JSONField | Analysis output |
| model_name | CharField | AI model used |
| **ResearchGap** | | |
| paper | ForeignKey(ResearchPaper) | Parent paper |
| title | CharField | Gap title |
| description | TextField | Detailed description |
| severity | CharField | HIGH, MEDIUM, LOW |
| suggestions | TextField | Recommended direction |
| **ChatMessage** | | |
| paper | ForeignKey(ResearchPaper) | Paper context |
| user | ForeignKey(User) | Asking user |
| question | TextField | User question |
| answer | TextField | Grounded AI answer |
| sources | JSONField | List of cited chunk objects with page/section |

### evaluation
| Field | Type | Description |
|-------|------|-------------|
| **EvaluationReport** | | |
| evaluation_id | UUIDField | Unique provenance identifier |
| paper | ForeignKey(ResearchPaper) | Evaluated paper |
| overall_score | FloatField | 0-100 weighted score |
| summary | TextField | Overall assessment verdict |
| strengths | JSONField | Key strengths list |
| weaknesses | JSONField | Improvement areas list |
| concerns | JSONField | Methodological concerns list |
| recommendations | JSONField | Improvement suggestions |
| provider | CharField | OpenAI / Heuristic rule engine |
| model_version | CharField | Model version used |
| prompt_version | CharField | Canonical prompt version (v2.0) |
| scoring_framework_version | CharField | Framework ID (v2-7dim-100pt) |
| paper_version | IntegerField | Sequential version run index |
| confidence | CharField | High, Medium, Low |
| limitations | TextField | Scope and analytical boundaries |
| disclaimer | TextField | Legal disclaimer |
| **ResearchScore** | | |
| report | ForeignKey(EvaluationReport) | Parent report |
| dimension | CharField | Canonical 7: NOVELTY, RESEARCH_GAP, METHODOLOGY, CONTRIBUTION, EVIDENCE_QUALITY, TECHNICAL_STRENGTH, CLARITY |
| score | FloatField | 0-100 dimension score |
| weight | FloatField | Canonical dimension weight |
| explanation | TextField | Detailed assessment explanation |
| supporting_evidence | JSONField | Citations with section, page, snippet |
| confidence | CharField | High, Medium, Low |
| limitations | TextField | Specific dimension limitations |

### projects
| Field | Type | Description |
|-------|------|-------------|
| **ResearchProject** | | |
| title | CharField | Project title |
| description | TextField | Project description |
| leader | ForeignKey(User) | Project leader |
| research_area | CharField | Research domain |
| status | CharField | PLANNING → COMPLETED |
| start_date | DateField | Project start |
| end_date | DateField | Project end |
| is_public | BooleanField | Visibility |
| **ProjectMember** | | |
| project | ForeignKey(ResearchProject) | Parent project |
| user | ForeignKey(User) | Team member |
| role | CharField | LEADER, RESEARCHER, etc. |

### collaboration
| Field | Type | Description |
|-------|------|-------------|
| **CollaborationRequest** | | |
| sender | ForeignKey(User) | Request initiator |
| receiver | ForeignKey(User) | Request target |
| message | TextField | Request message |
| status | CharField | PENDING, ACCEPTED, etc. |
| project | ForeignKey(ResearchProject) | Optional project |

### dashboard
| Field | Type | Description |
|-------|------|-------------|
| **ResearchActivity** | | |
| user | ForeignKey(User) | Activity user |
| activity_type | CharField | PAPER_UPLOAD, AI_ANALYSIS, etc. |
| description | TextField | Activity description |
| related_paper | ForeignKey(ResearchPaper) | Related paper |

## Indexes

- `ResearchPaper`: title, research_area, status, created_at
- `CollaborationRequest`: status, sender, receiver
- `ResearchActivity`: user, created_at
- `PaperChunk`: unique_together(paper, chunk_index)
- `ResearchScore`: unique_together(report, dimension)
- `ProjectMember`: unique_together(project, user)
