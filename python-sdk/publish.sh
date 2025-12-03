#!/bin/bash

# Kuralit Python SDK Publishing Script
# This script automates the process of publishing the kuralit package to PyPI

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PACKAGE_NAME="kuralit"
VERSION_FILE="kuralit/version.py"
PYPROJECT_FILE="pyproject.toml"
TEST_PYPI_REPO="testpypi"
PYPI_REPO="pypi"
VENV_DIR=".venv"

# Detect and activate local venv if available
activate_venv() {
    if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
        # Activate venv
        source "$VENV_DIR/bin/activate"
        print_info "Using local virtual environment: $VENV_DIR"
        return 0
    fi
    return 1
}

# Get Python command (from venv if available, otherwise system)
get_python_cmd() {
    if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
        # Check if venv is already activated, if not activate it
        if [ -z "$VIRTUAL_ENV" ] || [ "$VIRTUAL_ENV" != "$(pwd)/$VENV_DIR" ]; then
            source "$VENV_DIR/bin/activate"
        fi
        echo "python"
    elif command_exists python3; then
        echo "python3"
    elif command_exists python; then
        echo "python"
    else
        print_error "Python not found. Please install Python 3.10+ or create a .venv"
        exit 1
    fi
}

# Functions
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Get current version
get_current_version() {
    if [ -f "$VERSION_FILE" ]; then
        # Use sed for macOS compatibility (BSD grep doesn't support -P)
        sed -n "s/.*__version__ = \"\([^\"]*\)\".*/\1/p" "$VERSION_FILE"
    else
        echo ""
    fi
}

# Update version in version.py
update_version_file() {
    local version=$1
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/__version__ = \".*\"/__version__ = \"$version\"/" "$VERSION_FILE"
    else
        # Linux
        sed -i "s/__version__ = \".*\"/__version__ = \"$version\"/" "$VERSION_FILE"
    fi
}

# Update version in pyproject.toml
update_pyproject_version() {
    local version=$1
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/^version = \".*\"/version = \"$version\"/" "$PYPROJECT_FILE"
    else
        # Linux
        sed -i "s/^version = \".*\"/version = \"$version\"/" "$PYPROJECT_FILE"
    fi
}

# Clean build artifacts
clean_build() {
    print_info "Cleaning build artifacts..."
    rm -rf dist/ build/ *.egg-info kuralit.egg-info
    print_success "Build artifacts cleaned"
}

# Build package
build_package() {
    print_info "Building package..."
    
    # Activate venv if available
    activate_venv || true
    
    # Get Python command
    PYTHON_CMD=$(get_python_cmd)
    
    # Check if uv is available
    if ! command_exists uv; then
        print_error "uv not found. Please install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    
    # Check if build package is installed
    if ! uv pip show build >/dev/null 2>&1; then
        print_warning "build package not found. Installing..."
        uv pip install --upgrade build wheel
    fi
    
    $PYTHON_CMD -m build --sdist --wheel
    print_success "Package built successfully"
}

# Check package contents
check_package() {
    print_info "Checking package contents..."
    
    # Check if dist directory exists and has files
    if [ ! -d "dist" ]; then
        print_error "dist/ directory not found"
        exit 1
    fi
    
    # Check for wheel and source distribution files
    WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -1)
    TAR_FILE=$(ls dist/*.tar.gz 2>/dev/null | head -1)
    
    if [ -z "$WHEEL_FILE" ] && [ -z "$TAR_FILE" ]; then
        print_error "No distribution files found in dist/"
        exit 1
    fi
    
    if [ -n "$WHEEL_FILE" ]; then
        print_success "Wheel found: $(basename "$WHEEL_FILE")"
    fi
    
    if [ -n "$TAR_FILE" ]; then
        print_success "Source distribution found: $(basename "$TAR_FILE")"
    fi
    
    # Count files in wheel if it exists
    if [ -n "$WHEEL_FILE" ]; then
        activate_venv || true
        PYTHON_CMD=$(get_python_cmd)
        FILE_COUNT=$($PYTHON_CMD -m zipfile -l "$WHEEL_FILE" 2>/dev/null | grep -c "^kuralit/" || echo "0")
        print_success "Wheel contains $FILE_COUNT Python files"
        
        # Check for LICENSE and README
        if $PYTHON_CMD -m zipfile -l "$WHEEL_FILE" 2>/dev/null | grep -q "LICENSE"; then
            print_success "LICENSE file included"
        else
            print_warning "LICENSE file not found in package"
        fi
        
        # README is included in METADATA, check for it there
        if $PYTHON_CMD -m zipfile -l "$WHEEL_FILE" 2>/dev/null | grep -q "METADATA"; then
            if unzip -p "$WHEEL_FILE" kuralit-*.dist-info/METADATA 2>/dev/null | grep -q "Description-Content-Type: text/markdown"; then
                print_success "README.md included (in package metadata)"
            else
                print_warning "README.md may not be properly configured"
            fi
        fi
    fi
}

# Upload to repository
upload_to_pypi() {
    local repo=$1
    local repo_name=$2
    
    print_info "Uploading to $repo_name..."
    
    # Activate venv if available
    activate_venv || true
    PYTHON_CMD=$(get_python_cmd)
    
    # Check if uv is available
    if ! command_exists uv; then
        print_error "uv not found. Please install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    
    if ! command_exists twine; then
        print_warning "twine not found. Installing..."
        uv pip install --upgrade twine
    fi
    
    # Check for credentials
    if [ -z "$TWINE_USERNAME" ] || [ -z "$TWINE_PASSWORD" ]; then
        print_error "TWINE_USERNAME and TWINE_PASSWORD environment variables not set"
        print_info "Set them with:"
        echo "  export TWINE_USERNAME=__token__"
        echo "  export TWINE_PASSWORD=pypi-your-token-here"
        exit 1
    fi
    
    if [ "$repo" = "$TEST_PYPI_REPO" ]; then
        twine upload --repository "$repo" dist/*
    else
        twine upload dist/*
    fi
    
    print_success "Uploaded to $repo_name"
}

# Test installation
test_installation() {
    local repo_url=$1
    local repo_name=$2
    
    print_info "Testing installation from $repo_name..."
    
    # Create temporary virtual environment for testing
    TEMP_DIR=$(mktemp -d)
    activate_venv || true
    PYTHON_CMD=$(get_python_cmd)
    $PYTHON_CMD -m venv "$TEMP_DIR/venv"
    source "$TEMP_DIR/venv/bin/activate"
    
    if [ -n "$repo_url" ]; then
        pip install --index-url "$repo_url" --extra-index-url https://pypi.org/simple/ "$PACKAGE_NAME"
    else
        pip install "$PACKAGE_NAME"
    fi
    
    # Test import
    python -c "from $PACKAGE_NAME import __version__, Agent, Toolkit, Function; print(f'Version: {__version__}')" || {
        print_error "Import test failed"
        deactivate
        rm -rf "$TEMP_DIR"
        exit 1
    }
    
    print_success "Installation test passed"
    
    deactivate
    rm -rf "$TEMP_DIR"
}

# Main menu
show_menu() {
    echo ""
    echo "Kuralit Publishing Script"
    echo "========================"
    echo ""
    CURRENT_VERSION=$(get_current_version)
    echo "Current version: $CURRENT_VERSION"
    echo ""
    echo "Options:"
    echo "  1) Bump version"
    echo "  2) Build package"
    echo "  3) Test on TestPyPI"
    echo "  4) Publish to PyPI"
    echo "  5) Full workflow (bump → build → test → publish)"
    echo "  6) Exit"
    echo ""
    read -p "Select option [1-6]: " choice
    echo "$choice"
}

# Bump version
bump_version() {
    print_header "Bump Version"
    
    CURRENT_VERSION=$(get_current_version)
    echo "Current version: $CURRENT_VERSION"
    read -p "Enter new version (e.g., 0.2.0): " NEW_VERSION
    
    if [ -z "$NEW_VERSION" ]; then
        print_error "Version cannot be empty"
        exit 1
    fi
    
    # Validate version format (basic check)
    if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+)?$ ]]; then
        print_warning "Version format may be invalid (expected: X.Y.Z or X.Y.Z-suffix)"
        read -p "Continue anyway? [y/N]: " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    print_info "Updating version to $NEW_VERSION..."
    update_version_file "$NEW_VERSION"
    update_pyproject_version "$NEW_VERSION"
    print_success "Version updated to $NEW_VERSION"
    
    # Show git commands
    echo ""
    print_info "Next steps (optional):"
    echo "  git add $VERSION_FILE $PYPROJECT_FILE"
    echo "  git commit -m \"Bump version to $NEW_VERSION\""
    echo "  git tag v$NEW_VERSION"
    echo "  git push origin main --tags"
}

# Build workflow
build_workflow() {
    print_header "Build Package"
    clean_build
    build_package
    check_package
    echo ""
    print_success "Build complete! Files in dist/:"
    ls -lh dist/
}

# TestPyPI workflow
testpypi_workflow() {
    print_header "Test on TestPyPI"
    
    if [ ! -d "dist" ] || [ -z "$(ls -A dist/*.whl dist/*.tar.gz 2>/dev/null)" ]; then
        print_warning "No build files found. Building now..."
        build_workflow
    fi
    
    upload_to_pypi "$TEST_PYPI_REPO" "TestPyPI"
    echo ""
    print_info "Testing installation from TestPyPI..."
    test_installation "https://test.pypi.org/simple/" "TestPyPI"
    echo ""
    print_success "TestPyPI upload and installation test completed!"
    print_info "View package at: https://test.pypi.org/project/$PACKAGE_NAME/"
}

# PyPI workflow
pypi_workflow() {
    print_header "Publish to PyPI"
    
    CURRENT_VERSION=$(get_current_version)
    print_warning "You are about to publish version $CURRENT_VERSION to PyPI"
    print_warning "This action cannot be undone!"
    read -p "Are you sure? [y/N]: " confirm
    
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        print_info "Publishing cancelled"
        exit 0
    fi
    
    if [ ! -d "dist" ] || [ -z "$(ls -A dist/*.whl dist/*.tar.gz 2>/dev/null)" ]; then
        print_warning "No build files found. Building now..."
        build_workflow
    fi
    
    upload_to_pypi "$PYPI_REPO" "PyPI"
    echo ""
    print_info "Testing installation from PyPI..."
    sleep 5  # Wait a moment for PyPI to process
    test_installation "" "PyPI"
    echo ""
    print_success "Published to PyPI!"
    print_info "View package at: https://pypi.org/project/$PACKAGE_NAME/"
}

# Full workflow
full_workflow() {
    print_header "Full Publishing Workflow"
    
    # Step 1: Bump version
    bump_version
    echo ""
    
    # Step 2: Build
    read -p "Build package now? [Y/n]: " confirm
    if [[ ! "$confirm" =~ ^[Nn]$ ]]; then
        build_workflow
        echo ""
    fi
    
    # Step 3: Test on TestPyPI
    read -p "Test on TestPyPI first? [Y/n]: " confirm
    if [[ ! "$confirm" =~ ^[Nn]$ ]]; then
        testpypi_workflow
        echo ""
        read -p "TestPyPI test passed. Publish to production PyPI? [y/N]: " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            print_info "Stopping here. You can publish later with option 4."
            exit 0
        fi
    fi
    
    # Step 4: Publish to PyPI
    pypi_workflow
}

# Main
main() {
    # Check if we're in the right directory
    if [ ! -f "$VERSION_FILE" ] || [ ! -f "$PYPROJECT_FILE" ]; then
        print_error "Must run from project root directory"
        print_info "Looking for: $VERSION_FILE and $PYPROJECT_FILE"
        exit 1
    fi
    
    # Activate venv early if available
    if activate_venv; then
        # Venv activated, will use its Python
        :
    fi
    
    # Check for arguments
    if [ $# -eq 0 ]; then
        # Interactive mode
        while true; do
            choice=$(show_menu)
            case $choice in
                1)
                    bump_version
                    ;;
                2)
                    build_workflow
                    ;;
                3)
                    testpypi_workflow
                    ;;
                4)
                    pypi_workflow
                    ;;
                5)
                    full_workflow
                    ;;
                6)
                    print_info "Exiting..."
                    exit 0
                    ;;
                *)
                    print_error "Invalid option"
                    ;;
            esac
            echo ""
            read -p "Press Enter to continue..."
        done
    else
        # Command line mode
        case "$1" in
            bump)
                if [ -z "$2" ]; then
                    print_error "Usage: $0 bump <version>"
                    exit 1
                fi
                update_version_file "$2"
                update_pyproject_version "$2"
                print_success "Version bumped to $2"
                ;;
            build)
                build_workflow
                ;;
            test)
                testpypi_workflow
                ;;
            publish)
                pypi_workflow
                ;;
            full)
                full_workflow
                ;;
            *)
                echo "Usage: $0 [bump <version>|build|test|publish|full]"
                echo ""
                echo "Commands:"
                echo "  bump <version>  - Bump version number"
                echo "  build           - Build package"
                echo "  test            - Test on TestPyPI"
                echo "  publish         - Publish to PyPI"
                echo "  full            - Run full workflow"
                echo ""
                echo "Or run without arguments for interactive mode"
                exit 1
                ;;
        esac
    fi
}

# Run main
main "$@"

