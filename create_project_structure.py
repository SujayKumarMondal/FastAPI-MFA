import os

# Define the project structure
project_structure = {
    "backend": {
        "manage.py": "",
        "backend": {
            "__init__.py": "",
            "settings.py": "",
            "urls.py": "",
            "wsgi.py": ""
        },
        "auth_app": {
            "__init__.py": "",
            "models.py": "",
            "serializers.py": "",
            "views.py": "",
            "urls.py": "",
            "utils.py": "",
            "permissions.py": "",
            "tests.py": "",
            "migrations": {"__init__.py": ""}
        },
        "requirements.txt": "",
        ".env": ""
    },
    "frontend": {
        "package.json": "",
        "vite.config.js": "",
        "public": {"index.html": ""},
        "src": {
            "App.jsx": "",
            "main.jsx": "",
            "index.css": "",
            "api": {"api.js": ""},
            "pages": {
                "Register.jsx": "",
                "Login.jsx": "",
                "MFAVerify.jsx": "",
                "MFASetup.jsx": "",
                "Dashboard.jsx": ""
            },
            "components": {"ProtectedRoute.jsx": ""}
        }
    },
    ".gitignore": "",
    "README.md": ""
}

def create_files(base_path, structure):
    """Recursively create folders and files from a nested dictionary."""
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_files(path, content)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

if __name__ == "__main__":
    root_dir = input("Enter the full path for the root folder: ").strip()
    
    if not root_dir:
        print("Error: Please provide a valid folder path.")
    else:
        os.makedirs(root_dir, exist_ok=True)
        create_files(root_dir, project_structure)
        print(f"Project structure created successfully at: {root_dir}")
