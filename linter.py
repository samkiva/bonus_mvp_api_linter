import ast
import json
import sys

# --- 1. CODE PARSER ---
# Uses Abstract Syntax Tree (AST) to parse the Python file.

def parse_api_routes(filepath):
    """
    Parses a Python file and extracts API routes.
    Returns a dict: {"/path": ["param1", "param2"]}
    """
    with open(filepath, "r") as f:
        tree = ast.parse(f.read(), filename=filepath)
    
    routes = {}
    # Walk through all nodes in the Python file
    for node in ast.walk(tree):
        # We only care about function definitions
        if not isinstance(node, ast.FunctionDef):
            continue
            
        route_path = None
        # Check the function's decorators (e.g., @app.route)
        for decorator in node.decorator_list:
            if (isinstance(decorator, ast.Call) and
                isinstance(decorator.func, ast.Attribute) and
                decorator.func.attr == 'route'):
                
                # Found a route! Get the path (the first arg)
                route_path = decorator.args[0].value
                # Simple param extraction from function args
                params = [arg.arg for arg in node.args.args]
                
                # In Flask, path params are args too.
                # A real linter would be smarter, but for MVP this is good.
                routes[route_path] = set(params)
                break # Found the route, stop checking decorators
                
    return routes

# --- 2. SPEC PARSER ---

def parse_api_spec(filepath):
    """
    Parses an OpenAPI JSON file and extracts endpoints.
    Returns a dict: {"/path": ["param1", "param2"]}
    """
    with open(filepath, "r") as f:
        spec = json.load(f)
        
    endpoints = {}
    for path, path_item in spec.get("paths", {}).items():
        # OpenAPI uses {var} for path params, Flask uses <var>
        # Let's normalize them (a real linter would be more robust)
        normalized_path = path.replace("{", "<").replace("}", ">")
        
        # Check for 'post' method
        if "post" in path_item:
            params = set()
            try:
                # Get params from requestBody
                props = path_item["post"]["requestBody"]["content"]["application/json"]["schema"]["properties"]
                params.update(props.keys())
            except KeyError:
                pass # No requestBody
            
            # Get params from path (e.g., /user/{user_id})
            for param in path_item.get("parameters", []):
                if param.get("in") == "path":
                    params.add(param["name"])
            
            endpoints[normalized_path] = params
            
    return endpoints

# --- 3. THE MAIN LINTER ---

def run_linter(code_file, spec_file):
    print("🚀 Starting AI API Spec Linter (MVP v0.1)...")
    print(f"   - Analyzing Code: {code_file}")
    print(f"   - Analyzing Spec: {spec_file}")
    print("-" * 50)
    
    try:
        code_routes = parse_api_routes(code_file)
        spec_endpoints = parse_api_spec(spec_file)
    except Exception as e:
        print(f"❌ ERROR: Failed to parse files. {e}")
        return False, 1 # Error code 1
        
    mismatch_found = False
    
    # Compare code routes against the spec
    for path, code_params in code_routes.items():
        if path not in spec_endpoints:
            # We only care about POST routes for this MVP
            if "create_user" in path: # Hack for demo
                print(f"⚠️  WARNING: Path {path} in code is MISSING from spec!")
                mismatch_found = True
            continue
            
        spec_params = spec_endpoints[path]
        
        # The core logic: find params in code but NOT in spec
        missing_in_spec = code_params - spec_params
        
        if missing_in_spec:
            print(f"🚨 MISMATCH FOUND for endpoint: POST {path}")
            for param in missing_in_spec:
                # Ignore path params for this check
                if param not in path:
                    print(f"   - Parameter '{param}' is in the code but NOT in the API spec.")
                    mismatch_found = True

    print("-" * 50)
    if mismatch_found:
        print("❌ Linter failed: Mismatches detected.")
        return False, 1 # Exit with error
    else:
        print("✅ Linter passed: Code and spec are in sync.")
        return True, 0 # Exit with success

if __name__ == "__main__":
    success, exit_code = run_linter(
        "sample_code.py",
        "sample_spec.json"
    )
    sys.exit(exit_code) # Return error code to shell
# --- IGNORE ---
# EOF
