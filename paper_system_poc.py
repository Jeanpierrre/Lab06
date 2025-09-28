#!/usr/bin/env python3

import json
import time
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

@dataclass
class SystemHealth:
    component: str
    status: str
    response_time_ms: float
    last_check: datetime
    details: Dict = None

class PaperlySystemPOC:
    
    def __init__(self):
        self.setup_logging()
        self.health_status = {}
        self.metrics = {}
        self.start_time = datetime.now()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - [SYSTEM] - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('paperly_system.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('paperly_system')
    
    def check_database_health(self) -> SystemHealth:
        start_time = time.time()
        
        try:
            import psycopg2
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
            response_time = (time.time() - start_time) * 1000
            
            return SystemHealth(
                component="database",
                status="healthy",
                response_time_ms=response_time,
                last_check=datetime.now(),
                details={"paper_count": count}
            )
            
        except Exception as e:
            return SystemHealth(
                component="database",
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                details={"error": str(e)}
            )
    
    def check_cache_health(self) -> SystemHealth:
        start_time = time.time()
        
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            
            test_key = f"health_check:{int(time.time())}"
            r.setex(test_key, 60, "test_value")
            value = r.get(test_key)
            r.delete(test_key)
            
            response_time = (time.time() - start_time) * 1000
            
            return SystemHealth(
                component="cache",
                status="healthy",
                response_time_ms=response_time,
                last_check=datetime.now(),
                details={"operation": "ping_and_test"}
            )
            
        except Exception as e:
            return SystemHealth(
                component="cache",
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                details={"error": str(e)}
            )
    
    def check_search_health(self) -> SystemHealth:
        start_time = time.time()
        
        try:
            import elasticsearch
            es = elasticsearch.Elasticsearch(['http://localhost:9200'])
            
            if es.ping():
                cluster_health = es.cluster.health()
                response_time = (time.time() - start_time) * 1000
                
                return SystemHealth(
                    component="search",
                    status="healthy" if cluster_health['status'] in ['green', 'yellow'] else "degraded",
                    response_time_ms=response_time,
                    last_check=datetime.now(),
                    details=cluster_health
                )
            else:
                return SystemHealth(
                    component="search",
                    status="unhealthy",
                    response_time_ms=(time.time() - start_time) * 1000,
                    last_check=datetime.now(),
                    details={"error": "ping_failed"}
                )
                
        except Exception as e:
            return SystemHealth(
                component="search",
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                details={"error": str(e)}
            )
    
    def check_graph_health(self) -> SystemHealth:
        start_time = time.time()
        
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(
                "bolt://localhost:7687",
                auth=("neo4j", "password")
            )
            
            with driver.session() as session:
                result = session.run("CALL dbms.components() YIELD name, versions")
                components = [record.data() for record in result]
            
            driver.close()
            response_time = (time.time() - start_time) * 1000
            
            return SystemHealth(
                component="graph",
                status="healthy",
                response_time_ms=response_time,
                last_check=datetime.now(),
                details={"components": components}
            )
            
        except Exception as e:
            return SystemHealth(
                component="graph",
                status="unhealthy",
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.now(),
                details={"error": str(e)}
            )
    
    def run_health_checks(self) -> Dict[str, SystemHealth]:
        self.logger.info("Starting system health checks...")
        
        health_checks = {
            'database': self.check_database_health(),
            'cache': self.check_cache_health(),
            'search': self.check_search_health(),
            'graph': self.check_graph_health()
        }
        
        self.health_status = health_checks
        
        for component, health in health_checks.items():
            self.logger.info(f"{component.upper()}: {health.status} ({health.response_time_ms:.2f}ms)")
        
        return health_checks
    
    def collect_system_metrics(self) -> Dict:
        try:
            import psutil
        except ImportError:
            self.logger.warning("psutil not available, skipping system metrics")
            return {'timestamp': datetime.now().isoformat()}
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
        }
        
        if 'database' in self.health_status:
            metrics['database_response_ms'] = self.health_status['database'].response_time_ms
        
        if 'cache' in self.health_status:
            metrics['cache_response_ms'] = self.health_status['cache'].response_time_ms
        
        if 'search' in self.health_status:
            metrics['search_response_ms'] = self.health_status['search'].response_time_ms
        
        if 'graph' in self.health_status:
            metrics['graph_response_ms'] = self.health_status['graph'].response_time_ms
        
        self.metrics = metrics
        return metrics
    
    def generate_system_report(self) -> Dict:
        health_status = self.run_health_checks()
        system_metrics = self.collect_system_metrics()
        
        statuses = [health.status for health in health_status.values()]
        if all(status == "healthy" for status in statuses):
            overall_status = "healthy"
        elif any(status == "unhealthy" for status in statuses):
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        report = {
            'overall_status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': system_metrics.get('uptime_seconds', 0),
            'health_checks': {k: asdict(v) for k, v in health_status.items()},
            'system_metrics': system_metrics,
            'component_summary': {
                'healthy': sum(1 for s in statuses if s == "healthy"),
                'degraded': sum(1 for s in statuses if s == "degraded"), 
                'unhealthy': sum(1 for s in statuses if s == "unhealthy"),
                'total': len(statuses)
            }
        }
        
        return report
    
    def demo_paper_processing(self) -> Dict:
        self.logger.info("Running paper processing demonstration...")
        
        demo_papers = [
            {
                'id': 'demo_paper_001',
                'title': 'Machine Learning Applications in Scientific Research',
                'abstract': 'This paper explores various machine learning applications in scientific research, focusing on data analysis and pattern recognition techniques.',
                'authors': ['Dr. Jane Smith', 'Prof. John Doe'],
                'year': 2024,
                'journal': 'Journal of AI Research',
                'doi': '10.1000/demo.001',
                'keywords': ['machine learning', 'scientific research', 'data analysis'],
                'citation_count': 25
            },
            {
                'id': 'demo_paper_002',
                'title': 'Advanced Natural Language Processing for Academic Literature',
                'abstract': 'We present advanced NLP techniques for processing academic literature, including entity extraction and relationship mapping.',
                'authors': ['Dr. Alice Brown', 'Dr. Bob Wilson'],
                'year': 2024,
                'journal': 'Computational Linguistics Review',
                'doi': '10.1000/demo.002',
                'keywords': ['natural language processing', 'academic literature', 'text mining'],
                'citation_count': 18
            }
        ]
        
        processed_count = 0
        failed_count = 0
        
        for paper in demo_papers:
            try:
                self.logger.info(f"Processing paper: {paper['title']}")
                time.sleep(0.1)
                processed_count += 1
                self.logger.info(f"Successfully processed paper: {paper['id']}")
            except Exception as e:
                self.logger.error(f"Failed to process paper {paper['id']}: {e}")
                failed_count += 1
        
        return {
            'total_papers': len(demo_papers),
            'processed': processed_count,
            'failed': failed_count,
            'success_rate': (processed_count / len(demo_papers)) * 100
        }
    
    def demo_search_functionality(self) -> Dict:
        self.logger.info("Demonstrating search functionality...")
        
        demo_queries = [
            "machine learning",
            "natural language processing",
            "data analysis techniques",
            "scientific research methods"
        ]
        
        search_results = {}
        
        for query in demo_queries:
            self.logger.info(f"Searching for: {query}")
            time.sleep(0.1)
            mock_results = [
                {'title': f'Paper about {query}', 'relevance': 0.95},
                {'title': f'Advanced {query} techniques', 'relevance': 0.87},
                {'title': f'{query} in practice', 'relevance': 0.73}
            ]
            search_results[query] = mock_results
            self.logger.info(f"Found {len(mock_results)} results for: {query}")
        
        return {
            'queries_processed': len(demo_queries),
            'total_results': sum(len(results) for results in search_results.values()),
            'average_results_per_query': sum(len(results) for results in search_results.values()) / len(demo_queries),
            'sample_results': search_results
        }
    
    def run_comprehensive_demo(self) -> Dict:
        self.logger.info("Starting Paperly.utec POC comprehensive demonstration")
        
        demo_start = datetime.now()
        
        system_report = self.generate_system_report()
        processing_demo = self.demo_paper_processing()
        search_demo = self.demo_search_functionality()
        
        demo_duration = (datetime.now() - demo_start).total_seconds()
        
        comprehensive_report = {
            'demo_info': {
                'start_time': demo_start.isoformat(),
                'duration_seconds': demo_duration,
                'status': 'completed'
            },
            'system_health': system_report,
            'paper_processing': processing_demo,
            'search_functionality': search_demo,
            'summary': {
                'overall_health': system_report['overall_status'],
                'papers_processed': processing_demo['processed'],
                'search_queries': search_demo['queries_processed'],
                'demo_success': True
            }
        }
        
        with open('paperly_poc_demo_report.json', 'w') as f:
            json.dump(comprehensive_report, f, indent=2, default=str)
        
        self.logger.info("POC demonstration completed successfully")
        self.logger.info(f"Report saved to paperly_poc_demo_report.json")
        
        return comprehensive_report

def main():
    print("Starting Paperly.utec POC System Demo")
    print("=" * 50)
    
    poc_system = PaperlySystemPOC()
    
    try:
        demo_report = poc_system.run_comprehensive_demo()
        
        print(f"Demo Status: {demo_report['demo_info']['status']}")
        print(f"System Health: {demo_report['system_health']['overall_status']}")
        print(f"Papers Processed: {demo_report['paper_processing']['processed']}")
        print(f"Search Queries: {demo_report['search_functionality']['queries_processed']}")
        print(f"Duration: {demo_report['demo_info']['duration_seconds']:.2f}s")
        
        return demo_report
        
    except Exception as e:
        poc_system.logger.error(f"Demo failed: {e}")
        return None

if __name__ == "__main__":
    main()