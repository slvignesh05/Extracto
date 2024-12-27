import os
import requests
import re
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Hide your GitHub token in an environment variable for security
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}"
}

# Use session for better performance
session = requests.Session()
session.headers.update(HEADERS)

def get_repositories(org_name):
    """Fetch all repositories for the organization."""
    repos = []
    page = 1
    base_url = f"https://api.github.com/orgs/{org_name}/repos"

    while True:
        response = session.get(base_url, params={"per_page": 100, "page": page})
        if response.status_code != 200:
            return None, response.json()
        
        data = response.json()
        if not data:  # Break if no more data
            break

        repos.extend(data)
        page += 1

    return repos, None

def extract_domains(repos):
    """Extract unique domains from repository 'homepage' and 'description' fields."""
    unique_domains = {}
    for repo in repos:
        repo_url = repo.get("html_url", "")
        homepage = repo.get("homepage", "")
        description = repo.get("description", "")

        # Extract domains
        for field in [homepage, description]:
            if field:
                found_domains = re.findall(r"https?://(?:www\.)?([^\s/]+)", field)
                for domain in found_domains:
                    # Add only the first occurrence of each domain
                    if domain not in unique_domains:
                        unique_domains[domain] = repo_url

    # Convert the dictionary to a list of domain-repo mappings
    return [{"domain": domain, "repo_url": repo_url} for domain, repo_url in unique_domains.items()]


@app.route("/fetch_domains", methods=["POST"])
def fetch_domains():
    try:
        org_name = request.json.get("org_name")
        if not org_name:
            return jsonify({"error": "Organization name is required!"}), 400

        # Fetch repositories and domains logic
        repos, error = get_repositories(org_name)
        if error:
            return jsonify({"error": "Error fetching repositories"}), 500

        domains = extract_domains(repos)

        return jsonify(domains)
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True)
