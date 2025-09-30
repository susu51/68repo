# 🔄 Kuryecini v1.0.0 Rollback Plan

## Quick Rollback Commands

### Emergency Rollback (Immediate)
```bash
# Backend (Render)
curl -X POST "https://api.render.com/v1/services/YOUR_SERVICE_ID/deploys" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"MANUAL","commitId":"PREVIOUS_WORKING_COMMIT"}'

# Frontend (Vercel)  
vercel --prod --prebuilt build-backup/
# OR via dashboard: Deployments → Previous deployment → "Promote to Production"
```

### Git Rollback (For Code Issues)
```bash
# Create hotfix branch from previous tag
git checkout v0.9.9  # Previous stable version
git checkout -b hotfix/v1.0.1

# OR revert problematic commits
git revert HEAD~n  # n = number of commits to revert
git push origin main
```

---

## Rollback Scenarios & Procedures

### Scenario 1: Complete Deployment Failure
**Symptoms**: Site completely down, health checks failing
**Action**: Immediate rollback
**Timeline**: 5 minutes

```bash
1. Rollback backend to last known good commit
2. Rollback frontend to last known good deployment  
3. Verify health endpoints
4. Monitor error rates for 15 minutes
5. If stable, investigate root cause
```

### Scenario 2: Critical Bug in Production
**Symptoms**: App functional but critical bug affecting users
**Action**: Conditional rollback or hotfix
**Timeline**: 30 minutes decision window

```bash
1. Assess bug severity and user impact
2. If high impact: immediate rollback
3. If medium impact: prepare hotfix in parallel
4. Deploy hotfix OR rollback within 30 minutes
```

### Scenario 3: Performance Degradation
**Symptoms**: Slow response times, high error rates
**Action**: Investigate then rollback if needed
**Timeline**: 15 minutes investigation

```bash
1. Check monitoring dashboards
2. Review deployment logs
3. If performance doesn't recover in 15 min: rollback
4. Investigate root cause post-rollback
```

### Scenario 4: Database Migration Issues
**Symptoms**: Data consistency problems, migration failures
**Action**: Backend rollback + DB restore
**Timeline**: 60 minutes

```bash
1. Stop all write operations
2. Rollback backend to pre-migration version
3. Restore database from backup (if needed)
4. Verify data integrity
5. Resume operations
```

---

## Pre-Rollback Checklist

### Before Rolling Back
- [ ] Document the issue (screenshots, logs, error messages)
- [ ] Notify team via Slack/alerts
- [ ] Check if issue affects all users or subset
- [ ] Verify rollback target is stable
- [ ] Backup current state if possible

### During Rollback
- [ ] Follow rollback procedure for scenario type
- [ ] Monitor health endpoints during rollback
- [ ] Test critical functionality after rollback
- [ ] Verify user experience is restored

### Post-Rollback
- [ ] Update status page (if applicable)
- [ ] Notify users if necessary
- [ ] Begin root cause analysis
- [ ] Plan fix for next deployment

---

## Rollback Targets

### Git Commits & Tags
```
v1.0.0      - Current production release (problematic)
v0.9.9      - Previous stable release (rollback target)
v0.9.8      - Emergency fallback (if v0.9.9 has issues)
main@HEAD~5 - Pre-release commit (development)
```

### Environment Configurations
```bash
# Backup environment variables
cp .env.production .env.production.backup.$(date +%Y%m%d_%H%M%S)

# Rollback environments available
- .env.production.v0.9.9    # Previous version env
- .env.production.stable    # Known good configuration
- .env.production.minimal   # Minimal feature set
```

---

## Service-Specific Rollback Procedures

### Frontend (Vercel) Rollback
```bash
# Method 1: Via CLI
vercel deploy --prod build-backup/

# Method 2: Via Dashboard
1. Go to Vercel project dashboard
2. Navigate to "Deployments"
3. Find last successful deployment
4. Click "..." → "Promote to Production"

# Method 3: Via API
curl -X POST "https://api.vercel.com/v8/projects/PROJECT_ID/deployments/DEPLOYMENT_ID/promote" \
  -H "Authorization: Bearer TOKEN"
```

### Backend (Render) Rollback
```bash
# Method 1: Via Dashboard
1. Go to Render service dashboard
2. Navigate to "Deploys"
3. Find last successful deploy
4. Click "Redeploy"

# Method 2: Via API
curl -X POST "https://api.render.com/v1/services/SERVICE_ID/deploys" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"type":"MANUAL","commitId":"COMMIT_SHA"}'

# Method 3: Git revert + push
git revert HEAD
git push origin main  # Triggers automatic redeploy
```

### Database Rollback
```bash
# MongoDB Atlas Point-in-Time Recovery
1. Go to Atlas dashboard
2. Select cluster → Backup
3. Choose restore point before deployment
4. Create new cluster or restore to existing
5. Update MONGO_URL environment variable
```

---

## Health Check Verification

### Post-Rollback Health Checks
```bash
# Backend health
curl -f https://your-backend/api/healthz
curl -f https://your-backend/api/menus

# Frontend accessibility
curl -f https://your-frontend/
curl -f https://your-frontend/some/deep/route

# Database connectivity
# (Test via backend health check detailed endpoint)
curl https://your-backend/health/detailed
```

### Performance Verification
```bash
# Response time check
time curl -s https://your-frontend/ > /dev/null
time curl -s https://your-backend/api/healthz > /dev/null

# Error rate monitoring
# Monitor Sentry/logs for error patterns
tail -f /var/log/kuryecini/production.log | grep ERROR
```

---

## Communication Templates

### Internal Alert (Slack/Teams)
```
🚨 PRODUCTION ROLLBACK IN PROGRESS
Issue: [Brief description]
Affected: [Users/Features affected]
Rollback Target: v0.9.9
ETA: 5-15 minutes
Status: In progress / Complete
Next: Root cause analysis
```

### User Communication (Status Page)
```
⚠️ Service Temporarily Restored
We've temporarily restored a previous version of our service while we investigate and fix a recent issue. All core functionality is available. We'll update you once the fix is deployed.

Updated: [Timestamp]
Status: Investigating / Monitoring / Resolved
```

### Post-Incident Report Template
```
# Incident Report: [Date] - [Brief Description]

## Timeline
- HH:MM - Issue first detected
- HH:MM - Rollback initiated  
- HH:MM - Service restored
- HH:MM - Root cause identified

## Impact
- Duration: X minutes
- Users affected: ~X%
- Revenue impact: $X (estimated)

## Root Cause
[Technical explanation]

## Resolution
- Immediate: Rollback to v0.9.9
- Permanent: [Fix implemented in v1.0.1]

## Prevention
- [Actions to prevent recurrence]
- [Process improvements]
```

---

## Hotfix Process

### Creating Hotfix Branch
```bash
# Create hotfix from last stable tag
git checkout v0.9.9
git checkout -b hotfix/v1.0.1

# Make minimal fix
git commit -m "fix: critical issue description"

# Tag hotfix
git tag v1.0.1
git push origin hotfix/v1.0.1 --tags
```

### Hotfix Deployment
```bash
# Deploy hotfix (same process as regular deployment)
# Test thoroughly in staging first
# Deploy to production
# Monitor for 30 minutes

# Merge back to main after verification
git checkout main
git merge hotfix/v1.0.1
git push origin main
```

---

## Contact Information

### Emergency Contacts
- **DevOps Lead**: [Contact info]
- **Product Owner**: [Contact info] 
- **Technical Lead**: [Contact info]

### Service Providers
- **Vercel Support**: https://vercel.com/support
- **Render Support**: https://render.com/support
- **MongoDB Atlas**: https://cloud.mongodb.com/support

### Monitoring & Alerting
- **Sentry**: https://sentry.io/projects/
- **Uptime Monitoring**: [Service URL]
- **Error Tracking**: [Dashboard URL]

---

**Remember**: The goal of rollback is to restore service quickly. Root cause analysis and proper fix come after service restoration.