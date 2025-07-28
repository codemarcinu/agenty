# Analiza załączonych logów testów
with open("paste.txt", encoding="utf-8") as f:
    test_logs = f.read()

# Znajdź wszystkie błędy FAILED i ERROR
import re

failed_tests = re.findall(r"FAILED ([^-]+) - (.+)", test_logs)
error_tests = re.findall(r"ERROR ([^-]+) - (.+)", test_logs)


error_patterns = {}
for test, error in failed_tests + error_tests:
    # Wyodrębnienie głównego typu błędu
    if "Multiple classes found for path" in error:
        error_type = "SQLAlchemy Multiple Classes"
    elif "One or more mappers failed to initialize" in error:
        error_type = "SQLAlchemy Mapper Initialization"
    elif "Unsupported agent type" in error:
        error_type = "Unsupported Agent Type"
    elif "AttributeError" in error:
        error_type = "AttributeError"
    elif "AssertionError" in error:
        error_type = "AssertionError"
    elif "async def functions are not natively supported" in error:
        error_type = "Async Function Support"
    elif "NameError" in error:
        error_type = "NameError"
    else:
        error_type = "Other"

    error_patterns[error_type] = error_patterns.get(error_type, 0) + 1

for error_type, count in sorted(
    error_patterns.items(), key=lambda x: x[1], reverse=True
):
    pass

sqlalchemy_errors = [
    error
    for test, error in failed_tests + error_tests
    if "Multiple classes found for path" in error
]
if sqlalchemy_errors:
    pass

agent_errors = [
    error
    for test, error in failed_tests + error_tests
    if "Unsupported agent type" in error
]
if agent_errors:
    pass

attr_errors = [
    error for test, error in failed_tests + error_tests if "AttributeError" in error
]
if attr_errors:
    pass
