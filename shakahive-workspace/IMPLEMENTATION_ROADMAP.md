# NOVARAai Implementation Roadmap

**Version 2.0**  
**30 September 2026**  
**16-20 Week Implementation Plan**

## Overview

This roadmap maps the 16-20 week implementation plan to the NOVARAai codebase, aligning with the delivery specification for NCST Rwanda and similar research institutions.

## Team Capacity

**Proposed Team:**
- Product Owner and Institutional Lead
- Technical Lead
- 2 Backend Engineers
- 1 Data and Integration Engineer
- 1 AI Engineer
- 2 Frontend Engineers
- Shared UX Designer
- Shared QA Engineer
- Shared DevOps/Security Engineer
- Research Reviewer (scheduled)
- Patent Specialist (scheduled)

## Phase Breakdown

### Phase 1: Foundation (Weeks 1-2)
**Exit Gate:** Approved scope, credentials plan, and benchmark definitions

#### Epic E01: Architecture and Delivery
**Owner:** Technical Lead

**Tasks:**
- [x] Service architecture defined (14 microservices)
- [x] Docker Compose orchestration
- [x] Database schema design
- [x] API Gateway implementation
- [ ] Deployment pipeline setup
- [ ] CI/CD configuration
- [ ] Infrastructure provisioning
- [ ] Monitoring baseline

**Acceptance Output:** Independent deploy/rollback and trace propagation

#### Epic E02: Access and Tenant Policy
**Owner:** Backend Lead

**Tasks:**
- [x] Auth Service implementation (Port 8010)
- [x] JWT authentication
- [x] Role-based access control (RBAC)
- [x] Multi-tenant isolation
- [x] Session management
- [ ] Cross-tenant denial tests
- [ ] Stale session handling
- [ ] Self-approval denial

**Acceptance Output:** Cross-tenant, stale-session and self-approval denials

---

### Phase 2: Core Infrastructure (Weeks 3-5)
**Exit Gate:** Independent deployment; cross-tenant denial; permanent identity issuance

#### Epic E03: Permanent Registry
**Owner:** Registry Engineer

**Tasks:**
- [x] Registry Service implementation (Port 8006)
- [x] Permanent identity generation
- [x] Conflict detection (email, ORCID, name similarity)
- [x] Tenant identity linking
- [x] Verification workflow
- [ ] Same person across tenants enforcement
- [ ] Verified link conflict blocking
- [ ] Identity merge/reversal tests

**Acceptance Output:** Same person across tenants; verified link conflict blocked

#### Deployment & Databases
**Owner:** DevOps Engineer

**Tasks:**
- [ ] PostgreSQL production setup
- [ ] Redis cluster configuration
- [ ] Elasticsearch deployment
- [ ] Database migrations
- [ ] Backup strategy
- [ ] Service orchestration
- [ ] Event plumbing setup

---

### Phase 3: Integration & Data (Weeks 6-8)
**Exit Gate:** Live known-record queries; disclosure controls; source failures visible

#### Epic E04: Submission and Documents
**Owner:** Backend & AI Engineers

**Tasks:**
- [ ] File upload service
- [ ] Document extraction (PDF, DOCX)
- [ ] Version control
- [ ] Frozen version preservation
- [ ] Unreadable file detection
- [ ] Metadata extraction

**Acceptance Output:** Unreadable files not assessed; frozen versions preserved

#### Epic E05: International Integrations
**Owner:** Integration Engineer

**Tasks:**
- [x] Integration Service (Port 8007)
- [x] Crossref connector
- [x] OpenAlex connector
- [x] EPO connector
- [x] ORCID Service (Port 8008)
- [ ] Live source queries
- [ ] Failure and replay tests
- [ ] Rate limiting
- [ ] API key management

**Acceptance Output:** Live source queries plus failure and replay tests

---

### Phase 4: Screening & Review (Weeks 9-11)
**Exit Gate:** Evidence-linked end-to-end grant and invention case

#### Epic E06: Comparison and Evidence
**Owner:** AI Lead

**Tasks:**
- [x] Evidence Service (Port 8011)
- [x] Evidence matrix implementation
- [x] Retrieval system
- [x] Citation support analysis
- [ ] Retrieval benchmark
- [ ] Citation-support benchmark
- [ ] Evidence quality validation

**Acceptance Output:** Retrieval and citation-support benchmark

#### Epic E07: Human Review
**Owner:** Backend & Frontend

**Tasks:**
- [x] Reviewer Service (Port 8012)
- [x] Review assignment workflow
- [x] Decision tracking
- [x] Conflict guards
- [ ] Version conflict detection
- [ ] Traceable human decision
- [ ] Review UI implementation
- [ ] Mobile accessibility

**Acceptance Output:** Conflict and version guards; traceable human decision

---

### Phase 5: Repository & Operations (Weeks 12-14)
**Exit Gate:** Idempotent approved write; merge/reversal and dispute tests

#### Epic E08: Repository and Outputs
**Owner:** Data Engineer

**Tasks:**
- [x] Repository Service (Port 8009)
- [x] Sync operations
- [x] Diff tracking
- [x] Reconciliation logic
- [ ] No duplicate replay enforcement
- [ ] Uncertain write reconciliation
- [ ] Repository stewardship
- [ ] Monitoring setup

**Acceptance Output:** No duplicate replay; uncertain write reconciliation

#### Epic E10: Security and Operations
**Owner:** DevOps & QA

**Tasks:**
- [x] Monitoring Service (Port 8013)
- [x] Prometheus metrics
- [x] Security event logging
- [x] Alert management
- [ ] Critical issues closure
- [ ] Restore demonstration
- [ ] Security audit
- [ ] Penetration testing

**Acceptance Output:** Critical issues closed; restore demonstrated

---

### Phase 6: Validation & Training (Weeks 15-16)
**Exit Gate:** Release criteria met or formally scoped remediation

#### Expert Evaluation
**Owner:** Research Reviewer & Patent Specialist

**Tasks:**
- [ ] Domain validation with adjudicated examples
- [ ] Benchmark evaluation (100+ grants, 500+ publications, 30+ inventions)
- [ ] Baseline review time measurement
- [ ] Issue recall testing
- [ ] Exact-match precision validation
- [ ] Retrieval recall testing
- [ ] 30% review-time reduction validation

**Targets:**
- 95% expert-rated citation support
- 99% precision for auto-accepted exact-identifier matches
- 85% recall in top 50 against expert references
- 30% median review-time reduction

#### Access Testing & Recovery
**Owner:** Security & DevOps

**Tasks:**
- [ ] Access control testing
- [ ] Cross-tenant isolation verification
- [ ] Disaster recovery drill
- [ ] Failover testing
- [ ] Data integrity checks

#### Training
**Owner:** Product Owner

**Tasks:**
- [ ] Admin training
- [ ] Reviewer training
- [ ] User documentation
- [ ] Support runbooks
- [ ] Incident escalation procedures

---

### Phase 7: Reserve & Stabilization (Weeks 17-20)
**Exit Gate:** Institutional acceptance and operational ownership

#### Reserve Activities
- [ ] Provider delays handling
- [ ] Evaluation remediation
- [ ] Pilot stabilization
- [ ] Performance optimization
- [ ] Bug fixes
- [ ] Documentation updates

#### Release Approval
- [ ] Technical lead: Architecture and operational evidence
- [ ] Institutional owner: Workflow and benchmark results
- [ ] Security lead: Critical findings closure
- [ ] Product owner: Scope and known limitations

---

## Service Inventory

### Core Screening Services (Original)
1. **API Gateway** (8000) - Orchestration
2. **Eligibility Service** (8001) - Criteria validation
3. **Plagiarism Service** (8002) - GPU-accelerated detection
4. **Duplication Service** (8003) - Duplicate detection
5. **Novelty Service** (8004) - GPU-accelerated assessment
6. **Report Service** (8005) - Report generation

### New Enterprise Services (v2.0)
7. **Registry Service** (8006) - Permanent identity (E03)
8. **Integration Service** (8007) - Crossref/OpenAlex/EPO (E05)
9. **ORCID Service** (8008) - ORCID integration (E05)
10. **Repository Service** (8009) - Sync and diffs (E08)
11. **Auth Service** (8010) - Tenant isolation (E02)
12. **Evidence Service** (8011) - Evidence matrix (E06)
13. **Reviewer Service** (8012) - Review workflow (E07)
14. **Monitoring Service** (8013) - Security & ops (E10)

---

## Risk Register

| Risk | Mitigation | Owner |
|------|------------|-------|
| Source licensing delay | Early access gate, no mocks | Integration Engineer |
| Incorrect identity merge | Conservative matching, steward approval | Registry Engineer |
| Distributed complexity | Stable service ownership, contract tests | Technical Lead |
| Cost spikes | Job budgets, source limits | DevOps Engineer |
| Data leakage | Private processing, query-disclosure gates | Security Lead |
| Unsupported legal conclusions | Specialist workflow, restricted language | Product Owner |

---

## Definition of Done

For each story:
- [ ] Requirement linked
- [ ] Acceptance tested
- [ ] Role and scope checks enforced
- [ ] API and events documented
- [ ] Audit and metrics included
- [ ] Error/empty/loading/forbidden states implemented
- [ ] No secrets committed
- [ ] Migration reviewed (if needed)
- [ ] User-facing behavior demonstrated in target environment

---

## Change Control Process

New scope must include:
- Problem statement
- User value
- Affected services
- Source dependencies
- Data implications
- Acceptance tests
- Schedule impact

**Out of Scope (unless reprioritized):**
- Specialist filing
- Freedom-to-operate analysis
- Procurement modules
- Policy management modules

---

## Handover Requirements

Required deliverables:
- [ ] Versioned service source repositories
- [ ] Deployment manifests
- [ ] Database migrations
- [ ] OpenAPI and event schemas
- [ ] Policy catalog
- [ ] Design components
- [ ] Source-access register
- [ ] Benchmark report
- [ ] Threat model
- [ ] Restore evidence
- [ ] Support runbooks
- [ ] User training materials
- [ ] Incident escalation ownership

---

## Critical Path

```
Source access → Repository sandbox → Normalized evidence → 
Benchmarkable comparison → Expert acceptance
```

**Prerequisites:**
- Identity and authorization foundations must precede all private-data workflows
- UI work can begin against contract fixtures
- Mocked connectors cannot satisfy integration gates

---

## Package Limitations

**Current Deliverables:**
- Coordinated design baseline
- Service implementations
- API contracts
- Docker orchestration

**Not Included:**
- Runtime-tested SQL
- Production HTML preview
- Connected providers
- Provisioned cloud infrastructure
- Patent filing capability

**Implementation Required:**
- All specified gates must be satisfied
- No substitution with mocks for integration gates
- Source access agreements must be secured

---

## Next Steps

1. **Immediate:** Confirm pilot owners and source agreements
2. **Week 1:** Select resolver domain and registry governance
3. **Week 1:** Approve service catalog and authorization model
4. **Week 1:** Obtain repository API or import specification
5. **Week 2:** Establish evaluation corpus
6. **Week 2:** Build thin vertical slice:
   - Authenticated researcher → Permanent ID → Private submission → 
   - One live source lookup → Evidence display → Audited review

---

## Success Metrics

**From PRD (Proposed):**
- All material findings have source locators
- ≥95% expert-rated citation support
- ≥99% precision for auto-accepted exact-identifier matches
- ≥85% recall in top 50 against expert references
- ≥30% median review-time reduction without reduced material-issue recall

**Operational:**
- System uptime ≥99.5%
- API response time <2s (p95)
- Screening time <90 seconds per application
- Zero critical security vulnerabilities
- Successful disaster recovery <4 hours

---

## Contact & Support

**Technical Lead:** [Contact]
**Product Owner:** [Contact]
**Security Lead:** [Contact]

For implementation questions, refer to:
- ARCHITECTURE.md - System architecture
- README.md - User documentation
- QUICKSTART.md - Setup guide
- Service-specific documentation at /docs endpoint
