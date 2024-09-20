from typing import Set, Dict, Tuple

from pymongo import UpdateOne


class UrlGraph:
    url_edges: Set[Tuple[str, int, str]] = set()  # (origin_url, count, target_url)
    url_nodes: Dict[str, Tuple[str, str, int, int]] = dict()  # {url: (last_mod, content_type, incoming, outgoing)}

    def collect(self, url: str, last_mod: str, content_type: str, references: Dict[str, int]) -> None:
        """
        Collects and processes a URL's outgoing references and metadata.

        :param url: The URL being collected.
        :param last_mod: The last modification date of the URL.
        :param content_type: The content type of the URL.
        :param references: A dictionary of referenced URLs as keys and how often they appear as values.
        """
        # Ensure the node for this URL is in the nodes dictionary
        if url not in self.url_nodes:
            self.url_nodes[url] = (last_mod, content_type, 0, len(references))
        else:
            # Update the outgoing links count
            last_mod_existing, content_type_existing, incoming, outgoing = self.url_nodes[url]
            self.url_nodes[url] = (last_mod, content_type, incoming, outgoing + len(references))

        # Process all the references (outgoing links)
        for target_url, count in references.items():
            # Add the edge from the current URL to the target
            self.url_edges.add((url, count, target_url))

            # If the target URL doesn't exist in nodes, initialize it
            if target_url not in self.url_nodes:
                self.url_nodes[target_url] = ("", "", 1, 0)  # incoming connection starts at 1, outgoing at 0
            else:
                # Update the incoming links count for the target URL
                last_mod_target, content_type_target, incoming, outgoing = self.url_nodes[target_url]
                self.url_nodes[target_url] = (last_mod_target, content_type_target, incoming + 1, outgoing)

    def get_mongo_merge_query_parameters(self):
        """
        Returns a list of MongoDB UpdateOne operations needed to merge the graph
        with existing data in MongoDB.
        Each operation will update the nodes and edges of the graph.
        """
        operations = []

        # Update nodes
        for url, (last_mod, content_type, incoming, outgoing) in self.url_nodes.items():
            operations.append(
                UpdateOne(
                    {"url": url},
                    {
                        "$set": {
                            "last_mod": last_mod,
                            "content_type": content_type
                        },
                        "$inc": {
                            "incoming": incoming,
                            "outgoing": outgoing
                        }
                    },
                    upsert=True  # If the node doesn't exist, create it
                )
            )

        # Update edges
        for origin, count, target in self.url_edges:
            operations.append(
                UpdateOne(
                    {"origin": origin, "target": target},
                    {
                        "$inc": {
                            "count": count  # Increment the count of this edge
                        }
                    },
                    upsert=True  # If the edge doesn't exist, create it
                )
            )

        return operations

