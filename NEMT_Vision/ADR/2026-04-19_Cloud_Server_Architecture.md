# ADR-002: Cloud Server Architecture Decision

## Basic Information

| Attribute | Value |
|-----------|-------|
| **Date** | 2026-04-19 |
| **Decider** | CTO Agent |
| **Decision Type** | Architecture |
| **Status** | ✅ Accepted |

---

## Background

Need to establish cloud-based development infrastructure for NEMT Quant OS to address:
1. Local machine performance limitations
2. Need for consistent development environment
3. Better resource allocation for compute-intensive tasks (NLS calculations)

---

## Candidate Solutions

### Option A: Local Development Only

**Description**: Continue using local machine for all development

**Pros**:
- No additional infrastructure cost
- Simple setup

**Cons**:
- Performance limitations
- Inconsistent environments
- Single point of failure

### Option B: Cloud Development Server (Selected)

**Description**: Use cloud server (42.51.42.123) as primary development environment

**Pros**:
- Better CPU performance for NLS calculations
- Consistent environment
- Accessible from anywhere
- Better resource allocation

**Cons**:
- Additional cost
- Network dependency
- Initial setup complexity

### Option C: Hybrid Approach

**Description**: Use cloud for compute-heavy tasks, local for development

**Pros**:
- Best of both worlds
- Flexible resource allocation

**Cons**:
- More complex setup
- Need for synchronization

---

## Decision

**Selected**: Option B - Cloud Development Server

### Decision Rationale

1. Performance benchmark shows cloud server is 3.5x faster for compute tasks
2. Consistent environment reduces "works on my machine" issues
3. SSH access provides good security and flexibility
4. Initial setup complexity is worth long-term benefits

---

## Implementation

### Server Configuration

| Item | Specification |
|------|---------------|
| IP | 42.51.42.123 |
| User | root |
| Access | SSH with key-based auth |
| Purpose | Development, NLS computations, API services |

### Setup Completed

- [x] SSH connectivity established
- [x] Passwordless SSH setup
- [x] Essential tools installed (Python, Git)
- [x] Performance benchmarking completed

### Files Created

- `ssh_connect.py` - SSH connection utility
- `ssh_setup_server.py` - Server setup automation
- `ssh_passwordless_setup.py` - SSH key management
- `benchmark.py` - Performance benchmarking
- `run_cloud_benchmark.py` - Cloud benchmark runner

---

## Linked Principles

- **VISION.md**: Kitchen Theory - Establish solid infrastructure before features
- **TECH_PRINCIPLES.md**: Performance Principle - Optimize where it matters

---

## Consequences

### Positive Impacts

- 3.5x faster NLS calculations
- Consistent development environment
- Better resource utilization
- Geographic flexibility

### Negative Impacts

- Network dependency for development
- Additional cost (~$10/month estimated)
- Learning curve for remote development

### Mitigation

- Maintain local fallback for quick fixes
- Document remote development workflow
- Set up automated sync scripts

---

## Follow-up Actions

- [ ] Configure Cursor SSH remote access
- [ ] Set up automated code deployment
- [ ] Create remote development documentation
- [ ] Monitor server costs monthly

---

## Review Record

| Date | Reviewer | Opinion |
|------|----------|---------|
| 2026-04-19 | CTO | Accepted |

---

*This ADR is maintained by CTO Agent*
