"""Planning Phase Implementation"""

from typing import Dict, List, Optional

from react.model.reasoning import Thought
from .plan import ExecutionPlan, IntentAnalysis, ExecutionStrategy
from .todo import TODO, MCPtoolTODO, LLMCallTODO


class PlanningPhase:
    """Planning phase - analyze intent and generate execution plan"""

    def __init__(self, llm_client=None, prompt_manager=None):
        self.llm_client = llm_client
        self.prompt_manager = prompt_manager

    async def create_plan(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> ExecutionPlan:
        """Create execution plan"""
        context = context or {}

        # 1. Intent analysis
        intent = await self.analyze_intent(query)

        # 2. Complexity assessment
        complexity = self.assess_complexity(query, intent)

        # 3. Generate todo list
        todos = await self.generate_todos(query, intent, complexity)

        # 4. Determine execution strategy
        strategy = self.select_strategy(intent, complexity)

        return ExecutionPlan(
            todos=todos,
            strategy=strategy,
            intent=intent,
            query=query,
            context=context
        )

    async def analyze_intent(self, query: str) -> IntentAnalysis:
        """Intent analysis"""
        if not self.llm_client:
            # Default simple analysis
            return IntentAnalysis(
                intent_type="general",
                confidence=0.5,
                complexity="simple"
            )

        try:
            # Get prompt
            prompt = await self._get_prompt("intent_analysis", query=query)

            # Call LLM
            response = await self.llm_client.chat_completion([
                {"role": "system", "content": prompt},
                {"role": "user", "content": query}
            ])

            # Parse response
            return self._parse_intent_response(response.content)

        except Exception as e:
            # Return default intent
            return IntentAnalysis(
                intent_type="general",
                confidence=0.0,
                complexity="simple"
            )

    def assess_complexity(self, query: str, intent: IntentAnalysis) -> str:
        """Assess complexity"""
        # Assess complexity based on intent type and query features

        # Keyword detection
        complex_keywords = [
            "how", "why", "reason", "solve",
            "configure", "deploy", "optimize", "debug", "troubleshoot",
            "compare", "analyze", "evaluate", "suggest"
        ]

        query_lower = query.lower()
        keyword_count = sum(1 for keyword in complex_keywords if keyword in query_lower)

        # Length detection
        length_score = min(len(query) / 50, 2)  # Consider complex if over 50 characters

        # Comprehensive score
        complexity_score = keyword_count + length_score

        if complexity_score >= 3:
            return "complex"
        elif complexity_score >= 1.5:
            return "medium"
        else:
            return "simple"

    async def generate_todos(
        self,
        query: str,
        intent: IntentAnalysis,
        complexity: str
    ) -> List[TODO]:
        """Generate todo list"""

        if complexity == "simple":
            # Simple query, single step execution
            return [
                LLMCallTODO(
                    id="direct_response",
                    description="Direct response to query",
                    prompt_template="direct_response",
                    expected={"type": "text", "length": ">0"}
                )
            ]

        elif complexity == "medium":
            # Medium complexity, may need tool assistance
            return [
                LLMCallTODO(
                    id="initial_analysis",
                    description="Initial analysis",
                    prompt_template="initial_analysis",
                    expected={"type": "analysis", "quality": ">0.7"}
                ),
                LLMCallTODO(
                    id="generate_response",
                    description="Generate response",
                    prompt_template="generate_response",
                    expected={"type": "text", "length": ">0"}
                )
            ]

        else:  # complex
            # Complex query, multi-step execution
            todos = []

            # Step 1: Document recognition
            todos.append(
                MCPtoolTODO(
                    id="doc_recognition",
                    description="Identify relevant documents",
                    tool_name="recognize_documents",
                    params={
                        "query": query,
                        "model": "default",
                        "endpoint": "default"
                    },
                    expected={"docs": "list", "count": ">0"},
                    priority=10
                )
            )

            # Step 2: Query rewriting
            todos.append(
                MCPtoolTODO(
                    id="query_rewrite",
                    description="Rewrite query",
                    tool_name="rewrite_query",
                    params={
                        "query": query,
                        "documents": "{doc_recognition_result}",
                        "model": "default"
                    },
                    expected={"rewritten_query": "string"},
                    dependencies=["doc_recognition"],
                    priority=9
                )
            )

            # Step 3: Document search
            todos.append(
                MCPtoolTODO(
                    id="document_search",
                    description="Search documents",
                    tool_name="search_documents",
                    params={
                        "query": "{rewritten_query}",
                        "top_k": 5
                    },
                    expected={"results": "list", "count": ">0"},
                    dependencies=["query_rewrite"],
                    priority=8
                )
            )

            # Step 4: Reference formatting
            todos.append(
                MCPtoolTODO(
                    id="reference_format",
                    description="Format references",
                    tool_name="get_references",
                    params={
                        "search_results": "{document_search_result}",
                        "query": query
                    },
                    expected={"formatted": "string"},
                    dependencies=["document_search"],
                    priority=7
                )
            )

            # Step 5: Final response
            todos.append(
                LLMCallTODO(
                    id="final_response",
                    description="Generate final response",
                    prompt_template="final_response",
                    expected={"type": "text", "length": ">0"},
                    dependencies=["reference_format"],
                    priority=6
                )
            )

            return todos

    def select_strategy(self, intent: IntentAnalysis, complexity: str) -> ExecutionStrategy:
        """Select execution strategy"""

        # Select strategy based on intent and complexity
        if complexity == "simple":
            return ExecutionStrategy(
                name="direct_execution",
                max_steps=3,
                allow_retry=False,
                auto_validation=False
            )
        elif complexity == "medium":
            return ExecutionStrategy(
                name="standard_execution",
                max_steps=5,
                allow_retry=True,
                auto_validation=True,
                fallback_enabled=True
            )
        else:  # complex
            return ExecutionStrategy(
                name="detailed_execution",
                max_steps=20,
                allow_retry=True,
                auto_validation=True,
                fallback_enabled=True,
                parameters={
                    "validation_threshold": 0.7,
                    "retry_attempts": 3,
                    "timeout": 30
                }
            )

    async def _get_prompt(self, template_name: str, **kwargs) -> str:
        """Get prompt template"""
        if not self.prompt_manager:
            # Default prompts
            default_prompts = {
                "intent_analysis": self._default_intent_prompt()
            }
            return default_prompts.get(template_name, "")

        return await self.prompt_manager.get_template(template_name, **kwargs)

    def _default_intent_prompt(self) -> str:
        """Default intent analysis prompt"""
        return """
        You are an intent analysis expert.
        Accurately identify the true intent and complexity of user queries.

        Return JSON format:
        {
            "intent_type": "general|it_operation|knowledge_query",
            "confidence": 0.0-1.0,
            "complexity": "simple|medium|complex",
            "required_tools": ["tool1", "tool2"]
        }

        Intent type description:
        - general: General conversation or Q&A
        - it_operation: IT operation related questions
        - knowledge_query: Knowledge query

        Complexity description:
        - simple: Simple question, can be answered directly
        - medium: Medium complexity, may need some analysis
        - complex: Complex question, requires multi-step processing
        """

    def _parse_intent_response(self, content: str) -> IntentAnalysis:
        """Parse intent analysis response"""
        try:
            import json

            # Extract JSON
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                data = json.loads(json_str)
            else:
                raise ValueError("JSON format not found")

            return IntentAnalysis(
                intent_type=data.get("intent_type", "general"),
                confidence=float(data.get("confidence", 0.5)),
                complexity=data.get("complexity", "simple"),
                required_tools=data.get("required_tools", [])
            )

        except Exception as e:
            return IntentAnalysis(
                intent_type="general",
                confidence=0.0,
                complexity="simple"
            )
