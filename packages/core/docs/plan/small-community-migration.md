# Small Community Migration Plan: Docker → UV

## Current Situation
- **User base**: ~50 active users (206 monthly downloads)
- **Old version**: v0.3.x (Docker-based, published as `comfydock`)
- **New version**: v1.0.0 (UV-based, complete rewrite)
- **Breaking change**: Everything - completely different paradigm

## Migration Strategy: "Clean Break with Clear Communication"

### Phase 1: Warning Release (1 day effort)
**Timeline: 1 week before v1.0.0**

#### 1.1 Push v0.3.4 with startup warning
```python
# In old CLI main() function
click.secho("="*60, fg="yellow")
click.secho("⚠️  ComfyDock v1.0 Coming: COMPLETE REWRITE", fg="yellow", bold=True)
click.secho("  - Moving from Docker to UV package management", fg="yellow")
pip install comfydock==0.3.4", fg="cyan")
click.secho("  - Migration guide: github.com/ComfyDock/v1-migration", fg="cyan")
click.secho("="*60, fg="yellow")
time.sleep(3)  # Ensure visibility
```

#### 1.2 Disable auto-update suggestions
- Remove or comment out update check
- Prevent accidental upgrades to incompatible version

### Phase 2: Release v1.0.0 (4 hours effort)
**Timeline: Week 2**

#### 2.1 Add old installation detection
```python
# In new CLI main()
def check_docker_installation():
    old_config = Path.home() / ".comfydock" / "environments.json"
    if old_config.exists():
        click.secho("\n⚠️  Detected old Docker-based ComfyDock", fg="red")
        click.secho("\nThis is ComfyDock v1.0 (UV-based) - NOT compatible with Docker version", fg="yellow")
        click.secho("\nYour options:", fg="white")
        click.secho("1. Keep using old version: pip install comfydock==0.3.4", fg="cyan")
        click.secho("2. Install both versions: See migration guide", fg="cyan")
        click.secho("3. Start fresh with v1.0: Continue (old setup unchanged)\n", fg="green")

        if not click.confirm("Continue with v1.0?", default=False):
            click.secho("\nInstall old version: pip install comfydock==0.3.4", fg="cyan")
            sys.exit(0)
```

#### 2.2 Update PyPI package
- Push as v1.0.0 to same `comfydock` package
- Update description to clearly state "UV-based (v1.0+) - Breaking change from v0.3"

### Phase 3: Communication (2 hours effort)

#### 3.1 GitHub Release Notes
```markdown
# ⚠️ ComfyDock v1.0.0 - COMPLETE REWRITE

**BREAKING CHANGE**: Moved from Docker to UV package management.

## For Existing Users (v0.3.x)
**Your Docker environments will NOT work with v1.0**

Stay on old version:
```bash
pip install comfydock==0.3.4
```

Or try v1.0 in a separate installation (won't affect old setup).

## For New Users
Just install v1.0 - it's much better!

## What Changed?
- Docker → UV package management
- Faster, lighter, more reliable
- No Docker required
- Git-based version control
- Better dependency resolution

## Migration
Currently manual - we'll add tools based on user feedback.
Join Discord for help: [link]
```

#### 3.2 Simple Migration Guide
Create `docs/migration-from-docker.md`:
```markdown
# Migrating from Docker-based ComfyDock

## Option 1: Keep Both Versions
```bash
# Install old version with suffix
pipx install comfydock==0.3.4 --suffix=-docker

# Install new version
pipx install comfydock

# Use both:
comfydock-docker up  # Old Docker version
comfydock init       # New UV version
```

## Option 2: Manual Migration
1. Note your Docker environment setup
2. Install v1.0: `pip install comfydock`
3. Create new UV environment: `comfydock create my-env`
4. Manually add nodes: `comfydock node add [node-name]`
5. Test and adjust

## Getting Help
- Discord: [link]
- GitHub Issues: [link]
```

### Phase 4: Support (Ongoing)

#### 4.1 Monitor feedback channels
- GitHub issues
- Discord (if applicable)
- Direct messages

#### 4.2 Common issues template
```markdown
## FAQ

**Q: I updated and everything broke!**
A: Downgrade to v0.3.4: `pip install comfydock==0.3.4`

**Q: Can I run both versions?**
A: Yes, use pipx or uv tools with different names

**Q: Will you add automatic migration?**
A: Based on demand - manual for now
```

## Implementation Checklist

### Pre-Release (Week -1)
- [ ] Update old CLI with warning (v0.3.4)
- [ ] Test warning appears correctly
- [ ] Prepare GitHub release notes
- [ ] Write basic migration guide

### Release Day
- [ ] Publish v1.0.0 to PyPI
- [ ] Create GitHub release with breaking change warning
- [ ] Post in Discord/communication channels
- [ ] Monitor for immediate issues

### Post-Release (Week +1)
- [ ] Respond to user questions
- [ ] Document common issues
- [ ] Consider migration tools if many users struggle

## Success Metrics
- Less than 10 users with major issues
- Clear understanding of how to stay on old version
- No accidental upgrades breaking workflows
- Positive feedback on v1.0 improvements

## Time Investment
- **Total: ~8 hours**
  - Warning release: 1 hour
  - v1.0 detection code: 2 hours
  - Documentation: 2 hours
  - Release process: 1 hour
  - User support: 2 hours

## Future Considerations

### If Demand Exists (>10 requests)
Consider adding:
- Basic migration scanner for Docker containers
- Automated node list extraction
- Environment template generation

### If No Issues (<5 complaints)
- Deprecate v0.3.x officially after 3 months
- Remove old version warnings after 6 months
- Focus entirely on v1.x development

## Key Principle
**Break things clearly and honestly** rather than trying to maintain compatibility. Your small user base will appreciate:
1. Clear communication about breaking changes
2. Easy way to stay on old version
3. Better product in v1.0

The goal is not seamless migration but clear communication and a path forward for those who want it.