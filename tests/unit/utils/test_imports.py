#!/usr/bin/env python3
"""
Test script to verify all imports in the project are working correctly.
"""

import sys
import importlib
import traceback
from pathlib import Path
from typing import List, Tuple

def find_python_files(directory: str) -> List[Path]:
    """Find all Python files in the project."""
    project_path = Path(directory)
    python_files = []
    
    # Find all .py files, excluding some directories
    exclude_dirs = {
        '__pycache__', '.git', 'venv', 'node_modules', 
        '.pytest_cache', 'htmlcov', 'dist', 'build'
    }
    
    for py_file in project_path.rglob("*.py"):
        # Skip files in excluded directories
        if any(part in exclude_dirs for part in py_file.parts):
            continue
        # Skip test files for now
        if 'test_' in py_file.name or py_file.name.startswith('test_'):
            continue
        python_files.append(py_file)
    
    return python_files

def extract_imports_from_file(file_path: Path) -> List[str]:
    """Extract import statements from a Python file."""
    imports = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line.startswith('from ') or line.startswith('import '):
                # Skip relative imports for now
                if line.startswith('from .') or line.startswith('from ..'):
                    continue
                imports.append((line, line_num))
                
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return imports

def test_module_import(module_path: str) -> Tuple[bool, str]:
    """Test if a module can be imported."""
    try:
        # Convert file path to module path
        if module_path.startswith('src/'):
            module_path = module_path[4:]  # Remove 'src/' prefix
        
        module_path = module_path.replace('/', '.').replace('.py', '')
        
        # Skip if it's not a backend module
        if not module_path.startswith('backend'):
            return True, "Skipped (not backend module)"
            
        importlib.import_module(module_path)
        return True, "OK"
    except Exception as e:
        return False, str(e)

def test_import_statement(import_stmt: str, file_path: Path) -> Tuple[bool, str]:
    """Test a specific import statement."""
    try:
        # Clean up the import statement
        import_stmt = import_stmt.strip()
        
        # Execute the import statement
        exec(import_stmt, {})
        return True, "OK"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)}"

def main():
    """Main test function."""
    print("🔍 Testing all imports in the project...\n")
    
    # Add src to Python path
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))
    
    # Find all Python files
    python_files = find_python_files("src")
    print(f"Found {len(python_files)} Python files to test\n")
    
    # Test 1: Module imports
    print("=" * 60)
    print("TEST 1: Testing module imports")
    print("=" * 60)
    
    module_results = []
    for py_file in python_files:
        try:
            relative_path = str(py_file.relative_to(project_root))
        except ValueError:
            # Handle case where file is not in project_root
            relative_path = str(py_file)
        success, message = test_module_import(relative_path)
        module_results.append((relative_path, success, message))
        
        status = "✅" if success else "❌"
        print(f"{status} {relative_path}: {message}")
    
    # Test 2: Individual import statements
    print("\n" + "=" * 60)
    print("TEST 2: Testing individual import statements")
    print("=" * 60)
    
    import_results = []
    total_imports = 0
    failed_imports = 0
    
    for py_file in python_files:
        imports = extract_imports_from_file(py_file)
        if not imports:
            continue
            
        try:
            file_display = str(py_file.relative_to(project_root))
        except ValueError:
            file_display = str(py_file)
        print(f"\n📁 {file_display}:")
        
        for import_stmt, line_num in imports:
            total_imports += 1
            success, message = test_import_statement(import_stmt, py_file)
            import_results.append((str(py_file), import_stmt, line_num, success, message))
            
            if not success:
                failed_imports += 1
                
            status = "✅" if success else "❌"
            print(f"  Line {line_num:3d}: {status} {import_stmt}")
            if not success:
                print(f"           Error: {message}")
    
    # Test 3: Specific critical modules
    print("\n" + "=" * 60)
    print("TEST 3: Testing critical refactored modules")
    print("=" * 60)
    
    critical_modules = [
        "backend.agents.conversation.query_classifiers",
        "backend.agents.conversation.anti_hallucination_validators", 
        "backend.agents.conversation.context_processors",
        "backend.agents.conversation.response_generators",
        "backend.agents.conversation.pantry_tools",
        "backend.agents.chef.recipe_validators",
        "backend.agents.chef.recipe_generators",
        "backend.agents.chef.prompt_builders",
    ]
    
    critical_results = []
    for module in critical_modules:
        try:
            imported_module = importlib.import_module(module)
            # Test if we can access main classes
            if 'query_classifiers' in module:
                _ = imported_module.QueryClassifier
            elif 'recipe_validators' in module:
                _ = imported_module.AntiHallucinationValidator
            elif 'context_processors' in module:
                _ = imported_module.ContextProcessor
            # Add more specific tests as needed
            
            critical_results.append((module, True, "OK"))
            print(f"✅ {module}: OK")
        except Exception as e:
            critical_results.append((module, False, str(e)))
            print(f"❌ {module}: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    # Module import summary
    successful_modules = sum(1 for _, success, _ in module_results if success)
    total_modules = len(module_results)
    print(f"📦 Module imports: {successful_modules}/{total_modules} successful")
    
    # Import statement summary
    successful_imports = total_imports - failed_imports
    print(f"📥 Import statements: {successful_imports}/{total_imports} successful")
    
    # Critical modules summary
    successful_critical = sum(1 for _, success, _ in critical_results if success)
    total_critical = len(critical_results)
    print(f"🎯 Critical modules: {successful_critical}/{total_critical} successful")
    
    # Overall status
    overall_success = (
        successful_modules == total_modules and 
        failed_imports == 0 and 
        successful_critical == total_critical
    )
    
    if overall_success:
        print("\n🎉 ALL IMPORTS ARE WORKING CORRECTLY!")
        return 0
    else:
        print("\n⚠️  SOME IMPORTS HAVE ISSUES - CHECK DETAILS ABOVE")
        
        # Show failed modules
        if successful_modules < total_modules:
            print("\n❌ Failed module imports:")
            for path, success, message in module_results:
                if not success:
                    print(f"   • {path}: {message}")
        
        # Show failed import statements
        if failed_imports > 0:
            print(f"\n❌ Failed import statements ({failed_imports} total):")
            shown_count = 0
            for file_path, import_stmt, line_num, success, message in import_results:
                if not success and shown_count < 10:  # Show max 10 examples
                    print(f"   • {file_path}:{line_num} - {import_stmt}")
                    print(f"     {message}")
                    shown_count += 1
            if failed_imports > 10:
                print(f"   ... and {failed_imports - 10} more")
        
        # Show failed critical modules
        if successful_critical < total_critical:
            print("\n❌ Failed critical modules:")
            for module, success, message in critical_results:
                if not success:
                    print(f"   • {module}: {message}")
        
        return 1

if __name__ == "__main__":
    exit(main())