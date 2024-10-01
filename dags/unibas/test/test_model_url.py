import unittest
from hashlib import md5

from pydantic import AnyUrl

from unibas.common.model.model_parsed import UrlArche, UrlGraph, UrlParseResult


class TestUrlArche(unittest.TestCase):

    def test_url_arche_key_generates_correctly(self):
        arche = UrlArche(origin=AnyUrl('http://example.com'), target=AnyUrl('http://example.org'))
        self.assertEqual(arche.key, md5(bytes(f'{AnyUrl("http://example.com")}:{AnyUrl("http://example.org")}', 'utf-8')).hexdigest())

    def test_url_arche_merge_adds_weights(self):
        arche1 = UrlArche(origin=AnyUrl('http://example.com'), target=AnyUrl('http://example.org'), weight=1.0)
        arche2 = UrlArche(origin=AnyUrl('http://example.com'), target=AnyUrl('http://example.org'), weight=2.0)
        arche1.merge(arche2)
        self.assertEqual(arche1.weight, 3.0)

    def test_url_arche_merge_handles_none_weight(self):
        arche1 = UrlArche(origin=AnyUrl('http://example.com'), target=AnyUrl('http://example.org'))
        arche2 = UrlArche(origin=AnyUrl('http://example.com'), target=AnyUrl('http://example.org'), weight=2.0)
        arche1.merge(arche2)
        self.assertEqual(arche1.weight, 2.0)


class TestUrlGraph(unittest.TestCase):

    def test_url_graph_add_arche_adds_nodes_and_arches(self):
        graph = UrlGraph(name='test')
        arche = UrlArche(origin=AnyUrl('http://example.com'), target=AnyUrl('http://example.org'), weight=1.0)
        graph.add_arche(arche)
        self.assertIn(arche.origin, graph.nodes)
        self.assertIn(arche.target, graph.nodes)
        self.assertIn(arche.key, graph.arches)

    def test_url_graph_merge_combines_graphs(self):
        graph1 = UrlGraph(name='test')
        graph2 = UrlGraph(name='test')
        arche1 = UrlArche(origin=AnyUrl('http://example.com'), target=AnyUrl('http://example.org'), weight=1.0)
        arche2 = UrlArche(origin=AnyUrl('http://example.org'), target=AnyUrl('http://example.net'), weight=2.0)
        graph1.add_arche(arche1)
        graph2.add_arche(arche2)
        graph1.merge(graph2)
        self.assertIn(arche1.key, graph1.arches)
        self.assertIn(arche2.key, graph1.arches)

    def test_url_graph_merge_all_combines_multiple_graphs(self):
        graph1 = UrlGraph(name='test')
        graph2 = UrlGraph(name='test')
        graph3 = UrlGraph(name='test')
        arche1 = UrlArche(origin=AnyUrl('http://example.com'), target=AnyUrl('http://example.org'), weight=1.0)
        arche2 = UrlArche(origin=AnyUrl('http://example.org'), target=AnyUrl('http://example.net'), weight=2.0)
        arche3 = UrlArche(origin=AnyUrl('http://example.net'), target=AnyUrl('http://example.com'), weight=3.0)
        graph1.add_arche(arche1)
        graph2.add_arche(arche2)
        graph3.add_arche(arche3)
        graphs = [graph1, graph2, graph3]
        merged_graph = UrlGraph.merge_all(graphs)

        self.assertIn(arche1.key, merged_graph.arches)
        self.assertIn(arche2.key, merged_graph.arches)
        self.assertIn(arche3.key, merged_graph.arches)

    def test_get_outgoing_arches(self):
        graph = UrlGraph(name='test')
        arche1 = UrlArche(origin=AnyUrl('http://example.com'), target=AnyUrl('http://example.org'), weight=1.0)
        arche2 = UrlArche(origin=AnyUrl('http://example.com'), target=AnyUrl('http://example.net'), weight=2.0)
        graph.add_arche(arche1)
        graph.add_arche(arche2)
        outgoing_arches = graph.get_outgoing_arches(AnyUrl('http://example.com'))
        self.assertEqual(len(outgoing_arches), 2)
        self.assertIn(arche1, outgoing_arches)
        self.assertIn(arche2, outgoing_arches)

    def test_get_incoming_arches(self):
        graph = UrlGraph(name='test')
        arche1 = UrlArche(origin=AnyUrl('http://example.org'), target=AnyUrl('http://example.com'), weight=1.0)
        arche2 = UrlArche(origin=AnyUrl('http://example.net'), target=AnyUrl('http://example.com'), weight=2.0)
        graph.add_arche(arche1)
        graph.add_arche(arche2)
        incoming_arches = graph.get_incoming_arches(AnyUrl('http://example.com'))
        self.assertEqual(len(incoming_arches), 2)
        self.assertIn(arche1, incoming_arches)
        self.assertIn(arche2, incoming_arches)

    def test_get_all_arches_for(self):
        graph = UrlGraph(name='test')
        arche1 = UrlArche(origin=AnyUrl('http://example.com'), target=AnyUrl('http://example.org'), weight=1.0)
        arche2 = UrlArche(origin=AnyUrl('http://example.net'), target=AnyUrl('http://example.com'), weight=2.0)
        graph.add_arche(arche1)
        graph.add_arche(arche2)
        all_arches = graph.get_all_arches_for(AnyUrl('http://example.com'))
        self.assertEqual(len(all_arches), 2)
        self.assertIn(arche1, all_arches)
        self.assertIn(arche2, all_arches)


class TestUrlParseResult(unittest.TestCase):

    def test_url_parse_result_is_empty_returns_true_for_empty(self):
        result = UrlParseResult(origin=AnyUrl('http://example.com'))
        self.assertTrue(result.is_empty())

    def test_url_parse_result_is_empty_returns_false_for_non_empty(self):
        result = UrlParseResult(origin=AnyUrl('http://example.com'), urls=[(AnyUrl('http://example.org'), 1)])
        self.assertFalse(result.is_empty())

    def test_url_parse_result_get_urls_returns_correct_urls(self):
        result = UrlParseResult(origin=AnyUrl('http://example.com'), urls=[(AnyUrl('http://example.org'), 1)])
        self.assertEqual(result.get_urls(), [AnyUrl('http://example.org')])

    def test_url_parse_result_get_urls_with_freq_returns_correct_urls_with_freq(self):
        result = UrlParseResult(origin=AnyUrl('http://example.com'), urls=[(AnyUrl('http://example.org'), 1)])
        self.assertEqual(result.get_urls_with_freq(), [(AnyUrl('http://example.org'), 1)])

    def test_url_parse_result_get_origin_returns_correct_origin(self):
        result = UrlParseResult(origin=AnyUrl('http://example.com'))
        self.assertEqual(result.get_origin(), AnyUrl('http://example.com'))

    def test_url_parse_result_get_urls_from_same_host_from_origin(self):
        result = UrlParseResult(origin=AnyUrl('http://example.com'), urls=[(AnyUrl('http://example.com/page'), 1), (AnyUrl('http://example.org'), 1)])
        self.assertEqual(result.get_urls_from_same_host_from_origin(), [AnyUrl('http://example.com/page')])

    def test_url_parse_result_get_urls_from_different_host_from_origin(self):
        result = UrlParseResult(origin=AnyUrl('http://example.com'), urls=[(AnyUrl('http://example.com/page'), 1), (AnyUrl('http://example.org'), 1)])
        self.assertEqual(result.get_urls_from_different_host_from_origin(), [AnyUrl('http://example.org')])

    def test_url_parse_result_get_graph_data_returns_correct_graph(self):
        result = UrlParseResult(origin=AnyUrl('http://example.com'), urls=[(AnyUrl('http://example.org'), 1)])
        graph = result.get_graph_data(graph_name='test')
        self.assertIn(AnyUrl('http://example.com'), graph.nodes)
        self.assertIn(AnyUrl('http://example.org'), graph.nodes)
        self.assertIn(UrlArche(origin=AnyUrl('http://example.com'), target=AnyUrl('http://example.org'), weight=1.0).key, graph.arches)


if __name__ == '__main__':
    unittest.main()