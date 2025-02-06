import urllib, urllib.request, re
import anthropic
from config import ANTHROPIC_API_KEY
import base64
import httpx

client = anthropic.Anthropic(
	api_key=ANTHROPIC_API_KEY,
)

# Base URL
base_url = "http://export.arxiv.org/api"

# Endpoint
endpoint = "query"

# Parameters
params = {
	"search_query": 'ti:"electron thermal conductivity"',
	"sortBy": "submittedDate",
	"sortOrder": "ascending",
	"max_results": "1",
}

# Encode the parameters
encoded_params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)

# Construct the final URL
url = f"{base_url}/{endpoint}?{encoded_params}"

# Make the request to arxiv
data = urllib.request.urlopen(url)

decodedData = data.read().decode('utf-8')

# We extract data enclosed inside <entry> tags
entry_pattern = re.compile(r"<entry>(.*?)<\/entry>", re.DOTALL)
entries = entry_pattern.findall(decodedData)

data_list = []

# We match id, title, summary and links
field_pattern = re.compile(r'<id>(.*?)<\/id>|<title>(.*?)<\/title>|<summary>(.*?)<\/summary>|<link title="pdf" href="(.*?)" rel="related" type="application\/pdf"\/>', re.DOTALL)

for entry in entries:
	results = {
		"id": None,
		"title": None,
		"summary": None,
		"link": None
	}

	matches = field_pattern.findall(entry)

	for match in matches:
		if match[0]:
			results["id"] = match[0]
		if match[1]:
			results["title"] = match[1]
		if match[2]:
			results["summary"] = match[2]
		if match[3]:
			results["link"] = match[3]

	data_list.append(results)

for i, entry_data in enumerate(data_list, start=1):
	pdf_data = base64.standard_b64encode(httpx.get(entry_data['link']).content).decode("utf-8")

	print(f"Entry {i}:")
	print(f"  ID: {entry_data['id']}")
	print(f"  Title: {entry_data['title']}")
	print(f"  Summary: {entry_data['summary']}")
	print(f"  Link: {entry_data['link']}")

	message = client.messages.create(
		model="claude-3-5-sonnet-20241022",
		max_tokens=1024,
		messages=[
			{
				"role": "user",
				"content": [
					{
						"type": "document",
						"source": {
							"type": "base64",
							"media_type": "application/pdf",
							"data": pdf_data
						}
					},
					{
						"type": "text",
						"text": "What are the key findings in this document?"
					}
				]
			}
		],
	)
	print(f"  Claude: {message.choices[0].message}")
	print("=" * 50)