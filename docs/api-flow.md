# API Flow — Scholar Lens

## URL Architecture

All URLs follow RESTful conventions using Django's URL routing system.

```
/                           Landing page
/accounts/                  Registration
/accounts/login/            Login
/accounts/logout/           Logout
/accounts/profile/          User profile
/accounts/profile/edit/     Edit profile
/accounts/password/change/  Change password

/papers/                    Paper list
/papers/upload/             Upload paper
/papers/<id>/               Paper detail
/papers/<id>/edit/          Edit paper
/papers/<id>/delete/        Delete paper
/papers/<id>/download/      Download PDF

/projects/                  Project list
/projects/create/           Create project
/projects/<id>/             Project detail
/projects/<id>/edit/        Edit project
/projects/<id>/add-member/  Add member
/projects/<id>/leave/       Leave project

/researchers/               Researcher directory
/researchers/<id>/          Researcher detail
/researchers/profile/edit/  Edit researcher profile
/researchers/interests/add/ Add interest
/researchers/skills/add/    Add skill

/collaboration/             Collaboration requests
/collaboration/send/<id>/   Send request
/collaboration/<id>/respond/ Accept/decline
/collaboration/<id>/cancel/  Cancel request
/collaboration/recommendations/ Researcher recommendations

/ai/<paper_id>/summary/     AI summary
/ai/<paper_id>/gaps/        Research gaps
/ai/<paper_id>/ask/         Ask paper (RAG)
/ai/<paper_id>/process/     Process paper

/evaluation/<paper_id>/     Evaluate paper
/evaluation/report/<id>/    Evaluation report
/evaluation/<paper_id>/similarity/ Similarity analysis

/search/                    Search papers

/dashboard/                 User dashboard
/dashboard/notifications/   Notifications
/dashboard/settings/        Settings

/admin/                     Django admin
```

## Request/Response Flows

### Authentication Flow
```
GET  /accounts/login/     → Display login form
POST /accounts/login/     → Validate credentials → Set session → Redirect to /dashboard/
GET  /accounts/logout/    → Clear session → Redirect to /
```

### Paper Upload Flow
```
GET  /papers/upload/      → Display upload form + author formset
POST /papers/upload/      → Validate form + file → Save paper → Save authors
                          → Redirect to /papers/<id>/
```

### AI Analysis Flow
```
GET  /ai/<id>/summary/    → Check for cached summary → Display if exists
POST /ai/<id>/summary/    → Trigger AI analysis → Store result → Display summary
```

### Evaluation Flow
```
GET  /evaluation/<id>/    → Check for existing report → Display or show 'Evaluate' button
POST /evaluation/<id>/    → Trigger evaluation → Generate scores → Redirect to report
GET  /evaluation/report/<id>/ → Display full evaluation report
```

## HTTP Methods

| Method | Usage |
|--------|-------|
| GET | Display pages, forms, search results |
| POST | Form submissions, AI triggers, state changes |

All POST requests require CSRF token.

## Authentication

- Session-based authentication using Django's auth system
- `@login_required` decorator on all protected views
- Ownership checks for edit/delete operations
- Role-based visibility for certain features
