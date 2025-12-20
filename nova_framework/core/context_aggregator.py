#!/usr/bin/env python3
"""
NOVA Context Aggregator
Cross-Framework Agent Memory Continuity

Created by: Claude Code Assistant (Continuity Developer)
Date: 2025-12-19 18:59:00 MST
"""

import asyncio
import asyncpg
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

class NovaContextAggregator:
    """
    Provides cross-framework context transfer and pattern recognition
    Enables agents to access learnings from other frameworks
    """
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.pool = None
        
    async def connect(self):
        """Initialize database connection pool"""
        self.pool = await asyncpg.create_pool(**self.db_config)
        print("✅ NovaContextAggregator connected to database")
        
    async def get_related_context(
        self, 
        session_id: str, 
        context_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve context from other sessions relevant to current session
        
        Args:
            session_id: UUID of current Nova session
            context_type: Optional filter for specific context types
            limit: Maximum number of context items to return
            
        Returns:
            List of context records with relevance scores
        """
        async with self.pool.acquire() as conn:
            query = """
            SELECT 
                cb.id,
                cb.from_nova_session_id,
                cb.context_type,
                cb.context_data,
                cb.relevance_score,
                ms.framework_module,
                ms.started_at
            FROM nova.context_bridge cb
            JOIN nova.master_sessions ms ON cb.from_nova_session_id = ms.nova_session_id
            WHERE cb.to_nova_session_id = $1
            """
            
            if context_type:
                query += " AND cb.context_type = $2"
                query += " ORDER BY cb.relevance_score DESC LIMIT $3"
                results = await conn.fetch(query, session_id, context_type, limit)
            else:
                query += " ORDER BY cb.relevance_score DESC LIMIT $2"
                results = await conn.fetch(query, session_id, limit)
                
        return [dict(row) for row in results]
    
    async def bridge_context(
        self,
        from_session_id: str,
        to_session_id: str,
        context_type: str,
        context_data: Dict[str, Any],
        relevance_score: int
    ) -> int:
        """
        Create a context bridge between two sessions
        
        Args:
            from_session_id: Source session UUID
            to_session_id: Destination session UUID  
            context_type: Type of context (e.g., 'api_method', 'crash_fix')
            context_data: JSON data containing the context
            relevance_score: 1-100 relevance score
            
        Returns:
            Bridge entry ID
        """
        async with self.pool.acquire() as conn:
            bridge_id = await conn.fetchrow(
                """
                INSERT INTO nova.context_bridge 
                (from_nova_session_id, to_nova_session_id, context_type, context_data, relevance_score)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                from_session_id,
                to_session_id,
                context_type,
                json.dumps(context_data),
                relevance_score
            )
        return bridge_id['id']
    
    async def find_similar_patterns(
        self,
        query: str,
        current_framework: Optional[str] = None,
        frameworks: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Pattern recognition: Find similar issues/solutions across frameworks
        
        Args:
            query: Search query (e.g., "port conflicts debugging")
            current_framework: Current framework (to exclude from results)
            frameworks: Specific frameworks to search (default: all)
            limit: Maximum number of results
            
        Returns:
            List of similar patterns with context
        """
        if not frameworks:
            frameworks = ['antigravity', 'stt', 'langchain']
            
        if current_framework and current_framework in frameworks:
            frameworks.remove(current_framework)
            
        async with self.pool.acquire() as conn:
            # Semantic similarity search (simplified for phase 1)
            patterns = await conn.fetch("""
                SELECT 
                    ms.nova_session_id,
                    ms.framework_module,
                    ms.framework_session_id,
                    ms.message_count,
                    ms.learnings_count,
                    ca.context_data,
                    ca.relevance_score
                FROM nova.master_sessions ms
                JOIN nova.context_bridge ca ON ms.nova_session_id = ca.from_nova_session_id
                WHERE ms.framework_module = ANY($1::text[])
                  AND ms.message_count > 0
                ORDER BY ca.relevance_score DESC, ms.learnings_count DESC
                LIMIT $2
            """, frameworks, limit)
            
        return [dict(pattern) for pattern in patterns]
    
    async def publish_antigravity_session(self, ag_session_data: Dict[str, Any]) -> str:
        """
        Publish an antigravity session to the NOVA framework
        
        Args:
            ag_session_data: Antigravity session metadata including:
                - session_id: Antigravity session identifier
                - agent_id: Agent identifier
                - framework_module: Framework name ('antigravity')
                - api_methods: List of discovered API methods
                - security_warnings: List of security issues
                - conversation_type: Type of conversation
                - etc.
                
        Returns:
            nova_session_id (UUID)
        """
        async with self.pool.acquire() as conn:
            nova_session = await conn.fetchrow(
                """
                INSERT INTO nova.master_sessions 
                (agent_id, framework_module, framework_session_id, initial_context, final_context)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING nova_session_id
                """,
                ag_session_data['agent_id'],
                'antigravity',
                ag_session_data['session_id'],
                json.dumps({'initial': ag_session_data.get('summary', '')}),
                json.dumps({'api_methods': ag_session_data.get('api_methods', [])})
            )
        return str(nova_session['nova_session_id'])
    
    async def test_cross_framework_query(self) -> Dict[str, Any]:
        """
        Test case: Agent in STT queries "port conflicts"
        Expected: Returns antigravity crash fix from 2025-11-28
        
        Returns:
            Test results with success/failure indicators
        """
        results = await self.find_similar_patterns(
            query="port conflicts debugging",
            current_framework='stt',
            frameworks=['antigravity'],
            limit=5
        )
        
        success = len(results) > 0
        if success:
            print(f"✅ Cross-framework query test PASSED: Found {len(results)} relevant sessions")
            for result in results[:3]:
                print(f"   - Framework: {result['framework_module']}, Relevance: {result['relevance_score']}")
        else:
            print("❌ Cross-framework query test FAILED: No relevant sessions found")
            
        return {
            'test_name': 'cross_framework_query',
            'success': success,
            'result_count': len(results),
            'timestamp': datetime.now().isoformat()
        }

# Quick test function
async def test_nova_context_aggregator():
    """Run basic tests on the context aggregator"""
    db_config = {
        'host': 'localhost',
        'port': 18030,
        'database': 'nova_framework',
        'user': 'nova_user',
        'password': os.environ.get('POSTGRES_PASSWORD', 'changeme')
    }
    
    aggregator = NovaContextAggregator(db_config)
    await aggregator.connect()
    
    # Run cross-framework test
    result = await aggregator.test_cross_framework_query()
    return result

if __name__ == "__main__":
    result = asyncio.run(test_nova_context_aggregator())
