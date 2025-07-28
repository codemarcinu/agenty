# 🔧 Scripts Documentation - FoodSave AI

## Overview

This directory contains automation scripts for maintaining and updating project documentation. These scripts help ensure consistency, quality, and up-to-date information across all documentation files.

## Available Scripts

### 1. `generate_toc.sh` - Table of Contents Generator

Automatically generates and updates Table of Contents (TOC) for the entire project.

#### Features
- Generates main project TOC in `docs/TOC.md`
- Creates mini-TOC for individual markdown files
- Checks TOC consistency and broken links
- Supports different generation modes

#### Usage
```bash
# Generate everything (main TOC + mini-TOC for all files)
./scripts/generate_toc.sh --all

# Generate only main project TOC
./scripts/generate_toc.sh --main

# Generate mini-TOC for documentation files only
./scripts/generate_toc.sh --docs

# Check TOC consistency without generating
./scripts/generate_toc.sh --check

# Show help
./scripts/generate_toc.sh --help
```

#### Options
- `--main`: Generate main project TOC only
- `--docs`: Generate mini-TOC for documentation files only
- `--all`: Generate both main TOC and all mini-TOC (default)
- `--check`: Check TOC consistency without generating
- `--help`: Show help message

### 2. `update_documentation.sh` - Comprehensive Documentation Update

Updates dates, statuses, links, and performs comprehensive documentation maintenance.

#### Features
- Updates "Last Updated" dates in all markdown files
- Updates copyright years
- Checks and reports test status
- Validates markdown syntax
- Checks for broken links
- Generates documentation summary
- Integrates with TOC generation

#### Usage
```bash
# Full update (dates, status, links, validation, summary)
./scripts/update_documentation.sh --full

# Quick update (dates and basic checks only)
./scripts/update_documentation.sh --quick

# Check consistency without updating
./scripts/update_documentation.sh --check-only

# Show help
./scripts/update_documentation.sh --help
```

#### Options
- `--full`: Full update (dates, status, links, validation, summary)
- `--quick`: Quick update (dates and basic checks only)
- `--check-only`: Check consistency without updating
- `--help`: Show help message

## Workflow Integration

### Pre-commit Hook
Add to your `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Update documentation before commit
./scripts/update_documentation.sh --quick
./scripts/generate_toc.sh --check
```

### CI/CD Pipeline
Add to your CI/CD pipeline:
```yaml
# Example for GitHub Actions
- name: Update Documentation
  run: |
    ./scripts/update_documentation.sh --full
    ./scripts/generate_toc.sh --all
```

### Scheduled Updates
Add to crontab for weekly updates:
```bash
# Update documentation every Sunday at 2 AM
0 2 * * 0 cd /path/to/project && ./scripts/update_documentation.sh --full
```

## Output Files

### Generated Files
- `docs/TOC.md` - Main project Table of Contents
- `docs/DOCUMENTATION_SUMMARY.md` - Documentation statistics and summary
- Mini-TOC sections in individual markdown files

### Log Files
Scripts provide colored output with:
- ✅ Green: Success messages
- ⚠️ Yellow: Warnings
- ❌ Red: Errors
- 🔵 Blue: Headers

## Configuration

### Environment Variables
Scripts automatically detect:
- `PROJECT_ROOT`: Project root directory
- `CURRENT_DATE`: Current date in YYYY-MM-DD format
- `CURRENT_YEAR`: Current year

### Customization
You can customize script behavior by modifying:
- File patterns in `find` commands
- Date formats
- Link validation rules
- Markdown syntax checks

## Best Practices

### When to Use
- **Before commits**: Run `--quick` to update dates
- **Before releases**: Run `--full` for complete update
- **Weekly maintenance**: Run `--full` to keep documentation current
- **After major changes**: Run `--check-only` to verify consistency

### File Organization
- Keep scripts in `scripts/` directory
- Make scripts executable: `chmod +x scripts/*.sh`
- Document script usage in this README
- Version control all scripts

### Error Handling
- Scripts exit on first error (`set -e`)
- Check return codes in CI/CD pipelines
- Review warnings and errors in output
- Fix issues before committing

## Troubleshooting

### Common Issues

#### Permission Denied
```bash
chmod +x scripts/*.sh
```

#### Broken Links
```bash
# Check for broken links
./scripts/update_documentation.sh --check-only
```

#### Large Files Without TOC
```bash
# Generate mini-TOC for all files
./scripts/generate_toc.sh --docs
```

#### Date Update Issues
```bash
# Check which files need date updates
grep -r "Last Updated: 2025-06-28"
```

### Debug Mode
Add `set -x` to scripts for debug output:
```bash
#!/bin/bash
set -x  # Debug mode
set -e  # Exit on error
```

## Contributing

### Adding New Scripts
1. Create script in `scripts/` directory
2. Make it executable: `chmod +x scripts/new_script.sh`
3. Add documentation to this README
4. Test with various scenarios
5. Update this README with usage examples

### Script Standards
- Use consistent naming: `verb_noun.sh`
- Include help text with `--help` option
- Use colored output for status messages
- Handle errors gracefully
- Document all functions and options

## Examples

### Daily Development Workflow
```bash
# Quick documentation update
./scripts/update_documentation.sh --quick

# Check TOC consistency
./scripts/generate_toc.sh --check

# If issues found, regenerate TOC
./scripts/generate_toc.sh --all
```

### Release Preparation
```bash
# Full documentation update
./scripts/update_documentation.sh --full

# Verify everything is consistent
./scripts/generate_toc.sh --check

# Commit documentation updates
git add docs/
git commit -m "Update documentation for release"
```

### CI/CD Integration
```bash
# In your CI pipeline
./scripts/update_documentation.sh --full
./scripts/generate_toc.sh --all

# Check for any issues
if [ $? -ne 0 ]; then
    echo "Documentation update failed"
    exit 1
fi
```

---

*Last Updated: 2025-06-28*  
*Generated by: update_documentation.sh* 