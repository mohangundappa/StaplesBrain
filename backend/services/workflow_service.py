"""
Workflow Service for Staples Brain.

This module provides a service layer for managing workflow-based agents,
including creating, updating, retrieving, and executing workflows.
"""
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)

class WorkflowService:
    """
    Service for managing workflow-based agents.
    
    This service provides methods for creating, updating, retrieving, and
    executing workflows for database-driven agents.
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize the workflow service.
        
        Args:
            db_session: Async database session
        """
        self.db = db_session
        logger.info("Initialized WorkflowService")
    
    async def create_workflow(self, agent_id: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new workflow for an agent.
        
        Args:
            agent_id: ID of the agent
            workflow_data: Workflow configuration data
            
        Returns:
            Created workflow data with ID
        """
        try:
            workflow_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            # Prepare nodes and edges for storage
            nodes = workflow_data.get('nodes', {})
            edges = workflow_data.get('edges', {})
            entry_node = workflow_data.get('entry_node', '')
            
            # Store workflow in database
            await self.db.execute(
                """
                INSERT INTO workflows (id, agent_id, name, description, 
                                      nodes, edges, entry_node, 
                                      created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                workflow_id,
                agent_id,
                workflow_data.get('name', 'Unnamed Workflow'),
                workflow_data.get('description', ''),
                json.dumps(nodes),
                json.dumps(edges),
                entry_node,
                now,
                now
            )
            
            # Update agent with workflow ID
            await self.db.execute(
                """
                UPDATE agent_definitions
                SET workflow_id = $1,
                    updated_at = $2
                WHERE id = $3
                """,
                workflow_id,
                now,
                agent_id
            )
            
            # Commit the transaction
            await self.db.commit()
            
            # Return created workflow
            return {
                'id': workflow_id,
                'agent_id': agent_id,
                'name': workflow_data.get('name', 'Unnamed Workflow'),
                'description': workflow_data.get('description', ''),
                'nodes': nodes,
                'edges': edges,
                'entry_node': entry_node,
                'created_at': now,
                'updated_at': now
            }
        except Exception as e:
            # Rollback transaction
            await self.db.rollback()
            logger.error(f"Error creating workflow for agent {agent_id}: {str(e)}", exc_info=True)
            raise
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a workflow by ID.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Workflow data or None if not found
        """
        try:
            # Get workflow from database
            result = await self.db.execute(
                """
                SELECT id, agent_id, name, description, 
                       nodes, edges, entry_node, 
                       created_at, updated_at
                FROM workflows
                WHERE id = $1
                """,
                workflow_id
            )
            
            row = result.fetchone()
            if not row:
                return None
                
            # Parse JSON data
            nodes = json.loads(row[4]) if row[4] else {}
            edges = json.loads(row[5]) if row[5] else {}
            
            # Return workflow data
            return {
                'id': row[0],
                'agent_id': row[1],
                'name': row[2],
                'description': row[3],
                'nodes': nodes,
                'edges': edges,
                'entry_node': row[6],
                'created_at': row[7].isoformat() if row[7] else None,
                'updated_at': row[8].isoformat() if row[8] else None
            }
        except Exception as e:
            logger.error(f"Error getting workflow {workflow_id}: {str(e)}", exc_info=True)
            raise
    
    async def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a workflow.
        
        Args:
            workflow_id: ID of the workflow
            updates: Updated workflow data
            
        Returns:
            Updated workflow data or None if workflow not found
        """
        try:
            now = datetime.utcnow().isoformat()
            
            # Prepare nodes and edges for storage if provided
            nodes = json.dumps(updates.get('nodes')) if 'nodes' in updates else None
            edges = json.dumps(updates.get('edges')) if 'edges' in updates else None
            
            # Build dynamic update query
            query_parts = []
            params = [workflow_id]  # Start with workflow_id
            param_idx = 2  # PostgreSQL uses $1, $2, etc. for parameters
            
            if 'name' in updates:
                query_parts.append(f"name = ${param_idx}")
                params.append(updates['name'])
                param_idx += 1
                
            if 'description' in updates:
                query_parts.append(f"description = ${param_idx}")
                params.append(updates['description'])
                param_idx += 1
                
            if nodes is not None:
                query_parts.append(f"nodes = ${param_idx}")
                params.append(nodes)
                param_idx += 1
                
            if edges is not None:
                query_parts.append(f"edges = ${param_idx}")
                params.append(edges)
                param_idx += 1
                
            if 'entry_node' in updates:
                query_parts.append(f"entry_node = ${param_idx}")
                params.append(updates['entry_node'])
                param_idx += 1
                
            # Always update the updated_at timestamp
            query_parts.append(f"updated_at = ${param_idx}")
            params.append(now)
            
            # Execute update if we have fields to update
            if query_parts:
                query = f"""
                UPDATE workflows
                SET {', '.join(query_parts)}
                WHERE id = $1
                """
                await self.db.execute(query, *params)
                
                # Commit the transaction
                await self.db.commit()
            
            # Get updated workflow
            return await self.get_workflow(workflow_id)
        except Exception as e:
            # Rollback transaction
            await self.db.rollback()
            logger.error(f"Error updating workflow {workflow_id}: {str(e)}", exc_info=True)
            raise
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            True if workflow was deleted
        """
        try:
            # Get agent ID first for updating agent
            result = await self.db.execute(
                "SELECT agent_id FROM workflows WHERE id = $1",
                workflow_id
            )
            row = result.fetchone()
            if not row:
                return False
                
            agent_id = row[0]
            
            # Clear workflow ID from agent
            if agent_id:
                await self.db.execute(
                    """
                    UPDATE agent_definitions
                    SET workflow_id = NULL,
                        updated_at = $1
                    WHERE id = $2
                    """,
                    datetime.utcnow().isoformat(),
                    agent_id
                )
            
            # Delete workflow
            await self.db.execute(
                "DELETE FROM workflows WHERE id = $1",
                workflow_id
            )
            
            # Commit the transaction
            await self.db.commit()
            
            return True
        except Exception as e:
            # Rollback transaction
            await self.db.rollback()
            logger.error(f"Error deleting workflow {workflow_id}: {str(e)}", exc_info=True)
            raise
    
    async def execute_workflow(
        self, 
        workflow_id: str, 
        input_message: str,
        context: Optional[Dict[str, Any]] = None,
        llm_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow.
        
        Args:
            workflow_id: ID of the workflow
            input_message: User input message to process
            context: Additional context data
            llm_provider: Optional LLM provider to use
            
        Returns:
            Execution result
        """
        from backend.interpreters.agent_runner import AgentRunner
        import time
        
        try:
            # Start timing execution
            start_time = time.time()
            
            # Get workflow data
            workflow_data = await self.get_workflow(workflow_id)
            if not workflow_data:
                raise ValueError(f"Workflow with ID {workflow_id} not found")
            
            # Create agent runner
            runner = AgentRunner(
                db_session=self.db,
                workflow_data=workflow_data,
                llm_provider=llm_provider
            )
            
            # Initialize context
            ctx = context or {}
            
            # Execute workflow
            result = await runner.execute(
                input_message=input_message,
                context=ctx
            )
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Return execution result
            return {
                'response': result.get('response', ''),
                'execution_time': execution_time,
                'history': result.get('history', []),
                'iterations': result.get('iterations', 0),
                'state': result.get('state', {})
            }
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {str(e)}", exc_info=True)
            raise ValueError(f"Workflow execution failed: {str(e)}")
    
    async def get_workflows_by_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get all workflows for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List of workflow data
        """
        try:
            # Get workflows from database
            query = f"""
            SELECT id, name, description, entry_node, created_at, updated_at
            FROM workflows
            WHERE agent_id = '{agent_id}'::uuid
            ORDER BY created_at DESC
            """
            result = await self.db.execute(text(query))
            
            workflows = []
            rows = result.fetchall()
            
            for row in rows:
                workflows.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'entry_node': row[3],
                    'created_at': row[4].isoformat() if row[4] else None,
                    'updated_at': row[5].isoformat() if row[5] else None
                })
                
            return workflows
        except Exception as e:
            logger.error(f"Error getting workflows for agent {agent_id}: {str(e)}", exc_info=True)
            raise
            
    async def get_workflow_data_for_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the primary workflow data for an agent, including nodes, edges, and prompts.
        Specifically designed for frontend display purposes.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Workflow data with detailed node information or None if no workflow found
        """
        try:
            # Get the latest workflow for this agent
            workflows = await self.get_workflows_by_agent(agent_id)
            
            if not workflows:
                logger.warning(f"No workflows found for agent {agent_id}")
                return None
            
            # Use the most recent workflow (first in the list)
            workflow = workflows[0]
            workflow_id = workflow.get('id')
            
            # Get nodes data
            nodes_query = f"""
            SELECT id, node_type, config, name, response_template, system_prompt_id, function_name
            FROM workflow_nodes
            WHERE workflow_id = '{workflow_id}'::uuid
            """
            nodes_result = await self.db.execute(text(nodes_query))
            
            # fetchall() already returns the results, no need to await it
            nodes_data = nodes_result.fetchall()
            
            # Build nodes dictionary
            nodes = {}
            for node_id, node_type, config_json, name, response_template, system_prompt_id, function_name in nodes_data:
                # Parse the config - note that config_json might already be a dict in PostgreSQL JSONB columns
                if isinstance(config_json, dict):
                    config = config_json
                elif config_json and isinstance(config_json, str):
                    config = json.loads(config_json)
                else:
                    config = {}
                
                # Get prompt content if this is a prompt node
                prompt_content = None
                if node_type == 'prompt':
                    if system_prompt_id:
                        prompt_query = f"""
                        SELECT content
                        FROM system_prompts
                        WHERE id = '{system_prompt_id}'::uuid
                        """
                        prompt_result = await self.db.execute(text(prompt_query))
                        prompt_row = prompt_result.fetchone()
                        if prompt_row:
                            prompt_content = prompt_row[0]
                    elif response_template:
                        prompt_content = response_template
                
                # Add node to dictionary
                nodes[node_id] = {
                    'type': node_type,
                    'name': name,
                    'prompt': prompt_content,
                    'output_key': name.lower().replace(' ', '_') if name else None,
                    'config': config
                }
                
                # Add function name to config if it exists
                if function_name:
                    nodes[node_id]['config']['tool_name'] = function_name
            
            # Get edges data
            edges_query = f"""
            SELECT source_node_id, target_node_id, condition_value, condition_type
            FROM workflow_edges
            WHERE workflow_id = '{workflow_id}'::uuid
            """
            edges_result = await self.db.execute(text(edges_query))
            
            # fetchall() already returns the results, no need to await it
            edges_data = edges_result.fetchall()
            
            # Build edges list
            edges = {}
            for source, target, condition_value, condition_type in edges_data:
                if source not in edges:
                    edges[source] = []
                
                edge_info = {'target': target}
                if condition_value:
                    edge_info['condition'] = condition_value
                    # Store condition type if useful for frontend
                    edge_info['condition_type'] = condition_type
                
                edges[source].append(edge_info)
            
            # Convert all UUIDs to strings to ensure compatibility with JSON
            # Convert node dictionary keys (UUIDs) to strings
            string_node_ids = {}
            for node_id, node_data in nodes.items():
                string_node_ids[str(node_id)] = node_data
            
            # Convert edge dictionary keys (UUIDs) to strings
            string_edge_ids = {}
            for edge_id, edge_data in edges.items():
                string_edge_ids[str(edge_id)] = edge_data
            
            # Build complete workflow data with string IDs
            complete_workflow = {
                'id': str(workflow_id),
                'agent_id': str(agent_id),
                'name': workflow.get('name', 'Unnamed Workflow'),
                'description': workflow.get('description'),
                'nodes': string_node_ids,
                'edges': string_edge_ids,
                'entry_node': str(workflow.get('entry_node', '')),
                'created_at': workflow.get('created_at'),
                'updated_at': workflow.get('updated_at')
            }
            
            return complete_workflow
        except Exception as e:
            logger.error(f"Error getting workflow data for agent {agent_id}: {str(e)}", exc_info=True)
            raise