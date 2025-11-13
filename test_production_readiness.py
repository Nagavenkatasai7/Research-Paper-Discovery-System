"""
Production Readiness Test Suite
Comprehensive testing following industry best practices
"""

import sys
sys.path.append('.')

import time
import traceback
from typing import Dict, List
from paper_content_extractor import PaperContentExtractor
from api_clients import SemanticScholarClient
from grok_client import GrokClient
import config


class ProductionTest:
    """Base class for production tests"""

    def __init__(self):
        self.results = []
        self.failures = []

    def test(self, name: str, func, *args, **kwargs):
        """Run a test and record results"""
        print(f"\n{'='*80}")
        print(f"TEST: {name}")
        print(f"{'='*80}")

        start = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start

            print(f"✅ PASSED in {duration:.2f}s")
            self.results.append({
                'name': name,
                'status': 'PASSED',
                'duration': duration,
                'result': result
            })
            return result
        except Exception as e:
            duration = time.time() - start
            print(f"❌ FAILED in {duration:.2f}s")
            print(f"Error: {str(e)}")
            traceback.print_exc()

            self.failures.append({
                'name': name,
                'status': 'FAILED',
                'duration': duration,
                'error': str(e)
            })
            return None

    def report(self):
        """Generate test report"""
        print(f"\n\n{'='*80}")
        print("PRODUCTION READINESS TEST REPORT")
        print(f"{'='*80}\n")

        total = len(self.results) + len(self.failures)
        passed = len(self.results)
        failed = len(self.failures)

        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"❌ Failed: {failed} ({failed/total*100:.1f}%)")

        if self.failures:
            print(f"\n{'='*80}")
            print("FAILED TESTS")
            print(f"{'='*80}\n")
            for f in self.failures:
                print(f"❌ {f['name']}")
                print(f"   Error: {f['error']}\n")

        # Performance summary
        if self.results:
            print(f"\n{'='*80}")
            print("PERFORMANCE SUMMARY")
            print(f"{'='*80}\n")

            durations = [r['duration'] for r in self.results]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)

            print(f"Average: {avg_duration:.2f}s")
            print(f"Max: {max_duration:.2f}s")
            print(f"Min: {min_duration:.2f}s")

        print(f"\n{'='*80}")
        if failed == 0:
            print("✅ ALL TESTS PASSED - PRODUCTION READY")
        elif failed / total < 0.1:
            print("⚠️ MOSTLY READY - FEW FAILURES TO ADDRESS")
        else:
            print("❌ NOT PRODUCTION READY - SIGNIFICANT FAILURES")
        print(f"{'='*80}\n")

        return failed == 0


class APITests(ProductionTest):
    """Test all API integrations"""

    def test_semantic_scholar_search(self):
        """Test Semantic Scholar search API"""
        client = SemanticScholarClient(api_key=config.SEMANTIC_SCHOLAR_API_KEY)
        results = client.search_papers("machine learning", limit=5)

        assert len(results) > 0, "No results returned"
        assert results[0].get('title'), "Missing title"
        assert results[0].get('abstract') or results[0].get('tldr'), "Missing content"

        print(f"   Found {len(results)} papers")
        print(f"   First: {results[0]['title'][:60]}...")
        print(f"   Has TLDR: {'✅' if results[0].get('tldr') else '❌'}")

        return results

    def test_semantic_scholar_rate_limiting(self):
        """Test rate limiting doesn't crash"""
        client = SemanticScholarClient(api_key=config.SEMANTIC_SCHOLAR_API_KEY)

        # Make 5 quick requests
        for i in range(5):
            results = client.search_papers(f"test query {i}", limit=2)
            print(f"   Request {i+1}: {len(results)} results")

        return True

    def test_grok_api_connection(self):
        """Test Grok API connectivity"""
        client = GrokClient(
            api_key=config.GROK_SETTINGS['api_key'],
            model="grok-4-fast-reasoning",
            validate=False
        )

        response = client.generate(
            prompt="Say 'test successful' if you can read this",
            max_tokens=10,
            temperature=0
        )

        assert response, "No response from Grok"
        assert len(response) > 0, "Empty response"

        print(f"   Response: {response[:100]}")
        return response


class ContentExtractionTests(ProductionTest):
    """Test metadata-first content extraction"""

    def test_metadata_extraction_success_rate(self):
        """Critical: Test 95%+ success rate"""
        client = SemanticScholarClient(api_key=config.SEMANTIC_SCHOLAR_API_KEY)
        extractor = PaperContentExtractor()

        # Get 20 test papers
        papers = client.search_papers("quantum computing", limit=20)

        successes = 0
        metadata_successes = 0

        for i, paper in enumerate(papers):
            try:
                result = extractor.extract_content(paper, f"test_{i}")
                if result['success']:
                    successes += 1
                    if result['has_tldr'] or result['has_abstract']:
                        metadata_successes += 1
            except Exception as e:
                print(f"   Paper {i} failed: {e}")

        success_rate = successes / len(papers)
        metadata_rate = metadata_successes / len(papers)

        print(f"   Total papers: {len(papers)}")
        print(f"   Successes: {successes}")
        print(f"   Success rate: {success_rate:.1%}")
        print(f"   Metadata rate: {metadata_rate:.1%}")

        assert success_rate >= 0.90, f"Success rate {success_rate:.1%} below 90%"
        assert metadata_rate >= 0.80, f"Metadata rate {metadata_rate:.1%} below 80%"

        return success_rate

    def test_extraction_quality_levels(self):
        """Test quality classification"""
        client = SemanticScholarClient(api_key=config.SEMANTIC_SCHOLAR_API_KEY)
        extractor = PaperContentExtractor()

        papers = client.search_papers("machine learning", limit=10)

        quality_counts = {'excellent': 0, 'good': 0, 'fair': 0, 'minimal': 0}

        for i, paper in enumerate(papers):
            result = extractor.extract_content(paper, f"quality_test_{i}")
            if result['success']:
                quality = result.get('quality', 'unknown')
                quality_counts[quality] = quality_counts.get(quality, 0) + 1

        print(f"   Quality distribution:")
        for q, count in quality_counts.items():
            print(f"   - {q}: {count}")

        # At least 50% should be excellent or good
        good_quality = quality_counts['excellent'] + quality_counts['good']
        assert good_quality / len(papers) >= 0.5, "Too few high-quality extractions"

        return quality_counts

    def test_extraction_speed(self):
        """Test extraction is instant (<0.5s)"""
        client = SemanticScholarClient(api_key=config.SEMANTIC_SCHOLAR_API_KEY)
        extractor = PaperContentExtractor()

        papers = client.search_papers("neural networks", limit=5)

        times = []
        for i, paper in enumerate(papers):
            start = time.time()
            result = extractor.extract_content(paper, f"speed_test_{i}")
            duration = time.time() - start
            times.append(duration)
            print(f"   Paper {i+1}: {duration:.3f}s")

        avg_time = sum(times) / len(times)
        max_time = max(times)

        print(f"   Average: {avg_time:.3f}s")
        print(f"   Max: {max_time:.3f}s")

        assert avg_time < 0.5, f"Average {avg_time:.3f}s too slow"
        assert max_time < 1.0, f"Max {max_time:.3f}s too slow"

        return avg_time


class ChatTests(ProductionTest):
    """Test chat functionality"""

    def test_chat_response_speed(self):
        """Test chat responds in <5 seconds"""
        client = SemanticScholarClient(api_key=config.SEMANTIC_SCHOLAR_API_KEY)
        papers = client.search_papers("quantum computing", limit=1)
        paper = papers[0]

        # Build context
        title = paper.get('title', 'Unknown Title')
        tldr = paper.get('tldr', None)
        abstract = paper.get('abstract', 'No abstract available')

        context_parts = [f"Title: {title}"]
        if tldr:
            context_parts.append(f"\nTL;DR: {tldr}")
        if abstract and abstract != 'No abstract available':
            context_parts.append(f"\nAbstract: {abstract}")

        context = '\n'.join(context_parts)

        # Test question
        question = "What is the main contribution of this paper?"
        prompt = f"""You are a research assistant. Answer based on the information provided.

Paper Information:
{context}

Question: {question}

Answer (2-3 sentences):"""

        # Time the response
        grok_client = GrokClient(
            api_key=config.GROK_SETTINGS['api_key'],
            model="grok-4-fast-reasoning",
            validate=False
        )

        start = time.time()
        answer = grok_client.generate(
            prompt=prompt,
            max_tokens=200,
            temperature=0.3
        )
        duration = time.time() - start

        print(f"   Question: {question}")
        print(f"   Answer: {answer[:100]}...")
        print(f"   Response time: {duration:.2f}s")

        assert duration < 10, f"Response took {duration:.2f}s (> 10s limit)"
        assert len(answer) > 20, "Answer too short"

        return duration

    def test_multiple_questions(self):
        """Test answering multiple questions"""
        client = SemanticScholarClient(api_key=config.SEMANTIC_SCHOLAR_API_KEY)
        papers = client.search_papers("machine learning", limit=1)
        paper = papers[0]

        # Build context
        context = f"Title: {paper['title']}\nAbstract: {paper.get('abstract', 'N/A')}"

        questions = [
            "What is this paper about?",
            "What are the key findings?",
            "What are potential limitations?"
        ]

        grok_client = GrokClient(
            api_key=config.GROK_SETTINGS['api_key'],
            model="grok-4-fast-reasoning",
            validate=False
        )

        times = []
        for i, question in enumerate(questions):
            prompt = f"Context: {context}\n\nQuestion: {question}\n\nAnswer:"

            start = time.time()
            answer = grok_client.generate(prompt=prompt, max_tokens=150, temperature=0.3)
            duration = time.time() - start
            times.append(duration)

            print(f"   Q{i+1} ({duration:.2f}s): {question}")
            print(f"   A{i+1}: {answer[:80]}...")

        avg_time = sum(times) / len(times)
        print(f"   Average response time: {avg_time:.2f}s")

        assert avg_time < 6, f"Average {avg_time:.2f}s too slow"

        return avg_time


class PerformanceTests(ProductionTest):
    """Test performance benchmarks"""

    def test_search_performance_target(self):
        """Test search completes in <5 seconds"""
        client = SemanticScholarClient(api_key=config.SEMANTIC_SCHOLAR_API_KEY)

        queries = ["neural networks", "quantum computing", "natural language processing"]
        times = []

        for query in queries:
            start = time.time()
            results = client.search_papers(query, limit=10)
            duration = time.time() - start
            times.append(duration)

            print(f"   '{query}': {duration:.2f}s ({len(results)} results)")

        avg_time = sum(times) / len(times)
        max_time = max(times)

        print(f"   Average: {avg_time:.2f}s")
        print(f"   Max: {max_time:.2f}s")

        assert avg_time < 3, f"Average {avg_time:.2f}s exceeds 3s target"
        assert max_time < 5, f"Max {max_time:.2f}s exceeds 5s target"

        return avg_time

    def test_concurrent_extractions(self):
        """Test multiple concurrent extractions"""
        import concurrent.futures

        client = SemanticScholarClient(api_key=config.SEMANTIC_SCHOLAR_API_KEY)
        extractor = PaperContentExtractor()

        papers = client.search_papers("deep learning", limit=10)

        def extract_paper(paper, idx):
            return extractor.extract_content(paper, f"concurrent_{idx}")

        start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(extract_paper, p, i) for i, p in enumerate(papers)]
            results = [f.result() for f in futures]
        duration = time.time() - start

        successes = sum(1 for r in results if r and r['success'])

        print(f"   Extracted {len(papers)} papers in {duration:.2f}s")
        print(f"   Successes: {successes}/{len(papers)}")
        print(f"   Average: {duration/len(papers):.2f}s per paper")

        assert successes / len(papers) >= 0.9, "Too many failures"

        return duration


def main():
    """Run all production tests"""
    print("="*80)
    print("PRODUCTION READINESS TEST SUITE")
    print("Testing Research Paper Discovery System")
    print("="*80)

    # API Tests
    print("\n" + "="*80)
    print("PHASE 1: API INTEGRATION TESTS")
    print("="*80)

    api_tests = APITests()
    api_tests.test("Semantic Scholar Search", api_tests.test_semantic_scholar_search)
    api_tests.test("Semantic Scholar Rate Limiting", api_tests.test_semantic_scholar_rate_limiting)
    api_tests.test("Grok API Connection", api_tests.test_grok_api_connection)

    # Content Extraction Tests
    print("\n" + "="*80)
    print("PHASE 2: CONTENT EXTRACTION TESTS")
    print("="*80)

    extraction_tests = ContentExtractionTests()
    extraction_tests.test("Metadata Extraction Success Rate (CRITICAL)", extraction_tests.test_metadata_extraction_success_rate)
    extraction_tests.test("Quality Level Classification", extraction_tests.test_extraction_quality_levels)
    extraction_tests.test("Extraction Speed", extraction_tests.test_extraction_speed)

    # Chat Tests
    print("\n" + "="*80)
    print("PHASE 3: CHAT FUNCTIONALITY TESTS")
    print("="*80)

    chat_tests = ChatTests()
    chat_tests.test("Chat Response Speed", chat_tests.test_chat_response_speed)
    chat_tests.test("Multiple Questions", chat_tests.test_multiple_questions)

    # Performance Tests
    print("\n" + "="*80)
    print("PHASE 4: PERFORMANCE TESTS")
    print("="*80)

    perf_tests = PerformanceTests()
    perf_tests.test("Search Performance Target", perf_tests.test_search_performance_target)
    perf_tests.test("Concurrent Extractions", perf_tests.test_concurrent_extractions)

    # Generate reports
    print("\n" + "="*80)
    print("TEST REPORTS")
    print("="*80)

    api_tests.report()
    extraction_tests.report()
    chat_tests.report()
    perf_tests.report()

    # Overall summary
    all_tests = api_tests.results + extraction_tests.results + chat_tests.results + perf_tests.results
    all_failures = api_tests.failures + extraction_tests.failures + chat_tests.failures + perf_tests.failures

    total = len(all_tests) + len(all_failures)
    passed = len(all_tests)
    failed = len(all_failures)

    print("\n" + "="*80)
    print("OVERALL PRODUCTION READINESS ASSESSMENT")
    print("="*80)
    print(f"\nTotal Tests Run: {total}")
    print(f"✅ Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"❌ Failed: {failed} ({failed/total*100:.1f}%)")

    if failed == 0:
        print("\n🎉 PRODUCTION READY - All tests passed!")
        print("✅ System is ready for deployment")
    elif failed / total < 0.1:
        print("\n⚠️ MOSTLY READY - Minor issues to address")
        print("Review failed tests and fix before deployment")
    else:
        print("\n❌ NOT PRODUCTION READY - Significant issues found")
        print("Address all failures before deployment")

    print("="*80 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
