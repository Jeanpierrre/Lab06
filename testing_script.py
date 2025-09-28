
import sys
import time
import json
import asyncio
import logging
from datetime import datetime

# Test imports
try:
    import requests
    import psycopg2
    import redis
    import elasticsearch
    from neo4j import GraphDatabase
    print("✅ All required packages imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class PaperlyTester:
    """Comprehensive testing suite for Paperly POC"""
    
    def __init__(self):
        self.results = []
        self.setup_logging()
    
    def setup_logging(self):
        """Setup test logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - [TEST] - %(message)s',
            handlers=[
                logging.FileHandler('test_results.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('paperly_test')
    
    def test_database_connection(self):
        """Test PostgreSQL connection"""
        try:
            conn = psycopg2.connect(
                host="localhost",
                database="paperly", 
                user="postgres",
                password="password"
            )
            
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM papers;")
                count = cur.fetchone()[0]
            
            conn.close()
            
            self.log_result("DATABASE", "SUCCESS", f"Connected to PostgreSQL, {count} papers found")
            return True
            
        except Exception as e:
            self.log_result("DATABASE", "FAILED", str(e))
            return False
    
    def test_redis_connection(self):
        """Test Redis connection"""
        try:
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            
            # Test cache operations
            test_key = f"test:{int(time.time())}"
            r.setex(test_key, 60, "test_value")
            value = r.get(test_key)
            r.delete(test_key)
            
            self.log_result("CACHE", "SUCCESS", "Redis connection and operations working")
            return True
            
        except Exception as e:
            self.log_result("CACHE", "FAILED", str(e))
            return False
    
    def test_elasticsearch_connection(self):
        """Test Elasticsearch connection"""
        try:
            es = elasticsearch.Elasticsearch(['http://localhost:9200'])
            
            if es.ping():
                # Test index operations
                test_doc = {
                    "title": "Test Paper",
                    "content": "This is a test document",
                    "timestamp": datetime.now()
                }
                
                es.index(index="test_index", body=test_doc)
                es.indices.delete(index="test_index", ignore=[400, 404])
                
                self.log_result("SEARCH", "SUCCESS", "Elasticsearch connection and indexing working")
                return True
            else:
                self.log_result("SEARCH", "FAILED", "Elasticsearch ping failed")
                return False
                
        except Exception as e:
            self.log_result("SEARCH", "FAILED", str(e))
            return False
    
    def test_neo4j_connection(self):
        """Test Neo4j connection"""
        try:
            driver = GraphDatabase.driver(
                "bolt://localhost:7687",
                auth=("neo4j", "password")
            )
            
            with driver.session() as session:
                result = session.run("RETURN 'Hello Neo4j' as message")
                message = result.single()["message"]
            
            driver.close()
            
            self.log_result("GRAPH", "SUCCESS", "Neo4j connection working")
            return True
            
        except Exception as e:
            self.log_result("GRAPH", "FAILED", str(e))
            return False
    
    def test_api_endpoints(self):
        """Test API endpoints (if running)"""
        endpoints = [
            "http://localhost:8000/health",
            "http://localhost:8000/api/papers",
            "http://localhost:8000/api/search"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code in [200, 404]:  # 404 is ok for non-existent endpoints
                    self.log_result("API", "SUCCESS", f"{endpoint} responsive")
                else:
                    self.log_result("API", "WARNING", f"{endpoint} returned {response.status_code}")
            except requests.exceptions.RequestException as e:
                self.log_result("API", "INFO", f"{endpoint} not available (expected for POC)")
    
    def test_pipeline_components(self):
        """Test pipeline components"""
        try:
            # Import our pipeline
            from paperly_pipeline import PaperlyPipeline
            
            # Test instantiation
            pipeline = PaperlyPipeline()
            self.log_result("PIPELINE", "SUCCESS", "Pipeline components loaded successfully")
            
            # Test individual components
            test_doc = {
                'title': 'Machine Learning in Scientific Computing',
                'abstract': 'This paper explores the application of ML techniques...',
                'authors': ['Test Author'],
                'doi': '10.1000/test.123'
            }
            
            is_scientific = pipeline.classifier.is_scientific_paper(test_doc)
            self.log_result("CLASSIFIER", "SUCCESS" if is_scientific else "WARNING", 
                           f"Classification result: {is_scientific}")
            
            return True
            
        except Exception as e:
            self.log_result("PIPELINE", "FAILED", str(e))
            return False
    
    def test_performance_benchmarks(self):
        """Run performance benchmarks"""
        try:
            # Database query performance
            start_time = time.time()
            conn = psycopg2.connect(
                host="localhost",
                database="paperly",
                user="postgres", 
                password="password"
            )
            
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM papers LIMIT 100;")
                results = cur.fetchall()
            
            conn.close()
            db_time = (time.time() - start_time) * 1000
            
            # Cache performance
            start_time = time.time()
            r = redis.Redis(host='localhost', port=6379, db=0)
            for i in range(100):
                r.set(f"bench_{i}", f"value_{i}")
                r.get(f"bench_{i}")
            cache_time = (time.time() - start_time) * 1000
            
            self.log_result("PERFORMANCE", "SUCCESS", 
                           f"DB query: {db_time:.2f}ms, Cache ops: {cache_time:.2f}ms")
            return True
            
        except Exception as e:
            self.log_result("PERFORMANCE", "FAILED", str(e))
            return False
    
    def log_result(self, component: str, status: str, message: str):
        """Log test result"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'component': component,
            'status': status,
            'message': message
        }
        self.results.append(result)
        
        status_icon = {"SUCCESS": "✅", "FAILED": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}
        icon = status_icon.get(status, "📋")
        
        self.logger.info(f"{icon} {component}: {message}")
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting Paperly.utec POC Test Suite")
        print("=" * 50)
        
        # Test all components
        tests = [
            ("Database Connection", self.test_database_connection),
            ("Redis Cache", self.test_redis_connection), 
            ("Elasticsearch", self.test_elasticsearch_connection),
            ("Neo4j Graph DB", self.test_neo4j_connection),
            ("API Endpoints", self.test_api_endpoints),
            ("Pipeline Components", self.test_pipeline_components),
            ("Performance Benchmarks", self.test_performance_benchmarks)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running {test_name}...")
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.log_result("TEST_RUNNER", "FAILED", f"{test_name} crashed: {e}")
        
        # Generate summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Save detailed results
        with open('test_results.json', 'w') as f:
            json.dump({
                'summary': {'passed': passed, 'total': total, 'success_rate': (passed/total)*100},
                'results': self.results,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"📄 Detailed results saved to test_results.json")
        
        return passed == total