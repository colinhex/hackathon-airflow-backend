from unibas.common.logic.parse_logic import ParsedContentUnion, parse
from unibas.common.model.resource_model import WebResource, WebContent
from unibas.common.logic.web_client import fetch_resource


def fetch_and_parse(resource: WebResource) -> ParsedContentUnion:
    content: WebContent = fetch_resource(resource)
    return parse(content)


if __name__ == '__main__':
    result = fetch_and_parse(WebResource(loc='https://www.bs.ch/sitemap.xml'))
    print(result.model_dump_json(indent=2, exclude='content'))