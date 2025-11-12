"""
Generate PDF documentation from OpenAPI spec
Usage: python generate_api_docs_pdf.py
"""
import requests
import json
from datetime import datetime

def generate_markdown_from_openapi(openapi_url="http://localhost:8000/openapi.json"):
    """Convert OpenAPI JSON to Markdown format"""

    print("Fetching OpenAPI specification...")
    response = requests.get(openapi_url)
    spec = response.json()

    markdown = []

    # Title and Info
    markdown.append(f"# {spec['info']['title']}")
    markdown.append(f"\n**Version**: {spec['info']['version']}")
    markdown.append(f"\n**Description**: {spec['info']['description']}")
    markdown.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    markdown.append("\n---\n")

    # Table of Contents
    markdown.append("## Table of Contents\n")
    tags = {}
    for path, methods in spec['paths'].items():
        for method, details in methods.items():
            if method in ['get', 'post', 'put', 'patch', 'delete']:
                tag = details.get('tags', ['Other'])[0]
                if tag not in tags:
                    tags[tag] = []
                tags[tag].append(f"{method.upper()} {path}")

    for tag in sorted(tags.keys()):
        markdown.append(f"- [{tag}](#{tag.lower().replace(' ', '-')})")

    markdown.append("\n---\n")

    # Endpoints by Tag
    for tag in sorted(tags.keys()):
        markdown.append(f"\n## {tag}\n")

        for path, methods in sorted(spec['paths'].items()):
            for method, details in methods.items():
                if method not in ['get', 'post', 'put', 'patch', 'delete']:
                    continue

                if details.get('tags', ['Other'])[0] != tag:
                    continue

                # Endpoint header
                markdown.append(f"\n### {method.upper()} `{path}`\n")

                # Summary and description
                if 'summary' in details:
                    markdown.append(f"**{details['summary']}**\n")
                if 'description' in details:
                    markdown.append(f"{details['description']}\n")

                # Parameters
                if 'parameters' in details:
                    markdown.append("\n**Parameters:**\n")
                    markdown.append("| Name | In | Type | Required | Description |")
                    markdown.append("|------|-----|------|----------|-------------|")
                    for param in details['parameters']:
                        required = "Yes" if param.get('required', False) else "No"
                        param_type = param.get('schema', {}).get('type', 'string')
                        description = param.get('description', '-')
                        markdown.append(f"| {param['name']} | {param['in']} | {param_type} | {required} | {description} |")
                    markdown.append("")

                # Request Body
                if 'requestBody' in details:
                    markdown.append("\n**Request Body:**\n")
                    content = details['requestBody'].get('content', {})
                    if 'application/json' in content:
                        schema_ref = content['application/json'].get('schema', {})
                        markdown.append(f"```json")
                        markdown.append(json.dumps(schema_ref, indent=2))
                        markdown.append("```\n")

                # Responses
                if 'responses' in details:
                    markdown.append("\n**Responses:**\n")
                    for status_code, response in details['responses'].items():
                        description = response.get('description', 'No description')
                        markdown.append(f"- **{status_code}**: {description}")
                    markdown.append("")

                markdown.append("\n---\n")

    # Schemas
    if 'components' in spec and 'schemas' in spec['components']:
        markdown.append("\n## Data Models\n")
        for schema_name, schema_def in sorted(spec['components']['schemas'].items()):
            markdown.append(f"\n### {schema_name}\n")
            if 'description' in schema_def:
                markdown.append(f"{schema_def['description']}\n")

            if 'properties' in schema_def:
                markdown.append("\n**Properties:**\n")
                markdown.append("| Field | Type | Required | Description |")
                markdown.append("|-------|------|----------|-------------|")
                required_fields = schema_def.get('required', [])
                for prop_name, prop_def in schema_def['properties'].items():
                    prop_type = prop_def.get('type', 'object')
                    is_required = "Yes" if prop_name in required_fields else "No"
                    description = prop_def.get('description', '-')
                    markdown.append(f"| {prop_name} | {prop_type} | {is_required} | {description} |")
                markdown.append("")

    return "\n".join(markdown)


def save_markdown(content, filename="API_Documentation.md"):
    """Save markdown content to file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Markdown documentation saved to: {filename}")


def convert_markdown_to_pdf_instructions():
    """Print instructions for converting markdown to PDF"""
    print("\n" + "="*60)
    print("To convert the Markdown file to PDF, you have several options:")
    print("="*60)
    print("\n1. Using Pandoc (Recommended):")
    print("   Install: https://pandoc.org/installing.html")
    print("   Command: pandoc API_Documentation.md -o API_Documentation.pdf")
    print("\n2. Using Grip + wkhtmltopdf:")
    print("   pip install grip")
    print("   grip API_Documentation.md --export API_Documentation.html")
    print("   wkhtmltopdf API_Documentation.html API_Documentation.pdf")
    print("\n3. Using VS Code:")
    print("   Install 'Markdown PDF' extension")
    print("   Right-click on .md file -> 'Markdown PDF: Export (pdf)'")
    print("\n4. Using Online Converter:")
    print("   Visit: https://www.markdowntopdf.com/")
    print("   Upload API_Documentation.md and download PDF")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        # Generate markdown from OpenAPI spec
        markdown_content = generate_markdown_from_openapi()

        # Save to file
        save_markdown(markdown_content)

        # Print conversion instructions
        convert_markdown_to_pdf_instructions()

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to http://localhost:8000")
        print("Make sure the API server is running!")
    except Exception as e:
        print(f"Error: {e}")
