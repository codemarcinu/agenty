"""
Multi-agent consensus validator for cross-validation.

Implements consensus-based validation using multiple agents to prevent
hallucinations through cross-validation and agreement mechanisms.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
import logging
from statistics import mean
from typing import Any

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class ConsensusResult:
    """Result of consensus validation"""

    consensus_data: dict[str, Any]
    confidence_score: float
    agreement_rate: float
    agent_agreements: dict[str, float]
    disagreements: list[str]
    requires_review: bool
    timestamp: datetime


class ConsensusValidator:
    """
    Multi-agent consensus validator for cross-validation.

    Uses multiple agents to analyze the same data and find consensus
    to prevent hallucinations and improve accuracy.
    """

    def __init__(self, **kwargs):
        self.min_consensus_threshold = kwargs.get("min_consensus_threshold", 0.8)
        self.max_disagreement_threshold = kwargs.get("max_disagreement_threshold", 0.3)
        self.consensus_method = kwargs.get("consensus_method", "majority")
        self.agents = []

    def add_agent(self, agent: BaseAgent, weight: float = 1.0):
        """
        Add an agent to the consensus validator.

        Args:
            agent: Agent instance
            weight: Weight for this agent's opinion
        """
        self.agents.append({"agent": agent, "weight": weight, "name": agent.name})

    async def validate_receipt_consensus(self, ocr_text: str) -> ConsensusResult:
        """
        Validate receipt data using consensus from multiple agents.

        Args:
            ocr_text: OCR text to analyze

        Returns:
            ConsensusResult with consensus data and confidence metrics
        """
        if not self.agents:
            raise ValueError("No agents configured for consensus validation")

        logger.info(f"Starting consensus validation with {len(self.agents)} agents")

        # Run all agents in parallel
        tasks = []
        for agent_config in self.agents:
            task = self._run_agent_analysis(agent_config, ocr_text)
            tasks.append(task)

        # Wait for all agents to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and find consensus
        consensus_result = self._find_consensus(results)

        logger.info(
            "Consensus validation completed",
            extra={
                "confidence": consensus_result.confidence_score,
                "agreement_rate": consensus_result.agreement_rate,
                "requires_review": consensus_result.requires_review,
            },
        )

        return consensus_result

    async def _run_agent_analysis(
        self, agent_config: dict[str, Any], ocr_text: str
    ) -> dict[str, Any]:
        """
        Run analysis with a single agent.

        Args:
            agent_config: Agent configuration
            ocr_text: OCR text to analyze

        Returns:
            Agent result with metadata
        """
        agent = agent_config["agent"]
        weight = agent_config["weight"]
        name = agent_config["name"]

        try:
            start_time = datetime.now()

            # Run agent analysis
            response = await agent.process({"ocr_text": ocr_text})

            processing_time = (datetime.now() - start_time).total_seconds()

            return {
                "agent_name": name,
                "weight": weight,
                "success": response.success,
                "data": response.data if response.success else None,
                "error": response.error if not response.success else None,
                "processing_time": processing_time,
                "confidence": (
                    response.confidence if hasattr(response, "confidence") else 0.5
                ),
            }

        except Exception as e:
            logger.error(f"Error in agent {name}: {e!s}")
            return {
                "agent_name": name,
                "weight": weight,
                "success": False,
                "error": str(e),
                "processing_time": 0,
                "confidence": 0.0,
            }

    def _find_consensus(self, results: list[dict[str, Any]]) -> ConsensusResult:
        """
        Find consensus among agent results.

        Args:
            results: List of agent results

        Returns:
            ConsensusResult with consensus data
        """
        # Filter successful results
        successful_results = [r for r in results if r["success"] and r["data"]]

        if not successful_results:
            return ConsensusResult(
                consensus_data={},
                confidence_score=0.0,
                agreement_rate=0.0,
                agent_agreements={},
                disagreements=["All agents failed"],
                requires_review=True,
                timestamp=datetime.now(),
            )

        # Calculate agreement metrics
        agreement_metrics = self._calculate_agreement_metrics(successful_results)

        # Find consensus data
        consensus_data = self._extract_consensus_data(
            successful_results, agreement_metrics
        )

        # Calculate overall confidence
        confidence_score = self._calculate_consensus_confidence(agreement_metrics)

        # Determine if review is required
        requires_review = (
            confidence_score < self.min_consensus_threshold
            or agreement_metrics["overall_agreement"] < self.min_consensus_threshold
        )

        return ConsensusResult(
            consensus_data=consensus_data,
            confidence_score=confidence_score,
            agreement_rate=agreement_metrics["overall_agreement"],
            agent_agreements=agreement_metrics["agent_agreements"],
            disagreements=agreement_metrics["disagreements"],
            requires_review=requires_review,
            timestamp=datetime.now(),
        )

    def _calculate_agreement_metrics(
        self, results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Calculate agreement metrics between agents.

        Args:
            results: List of successful agent results

        Returns:
            Agreement metrics dictionary
        """
        agent_agreements = {}
        disagreements = []

        # Compare each pair of agents
        for i, result1 in enumerate(results):
            for j, result2 in enumerate(results[i + 1 :], i + 1):
                agreement_score = self._calculate_pair_agreement(result1, result2)
                agent_pair = f"{result1['agent_name']}-{result2['agent_name']}"
                agent_agreements[agent_pair] = agreement_score

                if agreement_score < self.min_consensus_threshold:
                    disagreements.append(
                        f"Low agreement between {result1['agent_name']} and {result2['agent_name']}: {agreement_score:.2f}"
                    )

        # Calculate overall agreement
        if agent_agreements:
            overall_agreement = mean(agent_agreements.values())
        else:
            overall_agreement = 1.0  # Single agent case

        return {
            "agent_agreements": agent_agreements,
            "overall_agreement": overall_agreement,
            "disagreements": disagreements,
        }

    def _calculate_pair_agreement(
        self, result1: dict[str, Any], result2: dict[str, Any]
    ) -> float:
        """
        Calculate agreement between two agent results.

        Args:
            result1: First agent result
            result2: Second agent result

        Returns:
            Agreement score between 0 and 1
        """
        data1 = result1["data"]
        data2 = result2["data"]

        if not data1 or not data2:
            return 0.0

        # Compare key fields
        key_fields = ["store_name", "total_amount", "items"]
        agreements = []

        for field in key_fields:
            value1 = data1.get(field)
            value2 = data2.get(field)

            if value1 is None or value2 is None:
                agreements.append(0.0)
                continue

            if field == "store_name":
                # String similarity for store names
                agreement = self._calculate_string_similarity(str(value1), str(value2))
            elif field == "total_amount":
                # Numeric similarity for amounts
                agreement = self._calculate_numeric_similarity(value1, value2)
            elif field == "items":
                # List similarity for items
                agreement = self._calculate_items_similarity(value1, value2)
            else:
                agreement = 1.0 if value1 == value2 else 0.0

            agreements.append(agreement)

        return mean(agreements)

    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings.

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score between 0 and 1
        """
        if not str1 or not str2:
            return 0.0

        # Simple similarity based on common words
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def _calculate_numeric_similarity(self, num1: float, num2: float) -> float:
        """
        Calculate similarity between two numeric values.

        Args:
            num1: First number
            num2: Second number

        Returns:
            Similarity score between 0 and 1
        """
        if num1 == 0 and num2 == 0:
            return 1.0

        if num1 == 0 or num2 == 0:
            return 0.0

        # Calculate relative difference
        relative_diff = abs(num1 - num2) / max(abs(num1), abs(num2))

        # Convert to similarity score (1 - relative_diff, but minimum 0)
        return max(0.0, 1.0 - relative_diff)

    def _calculate_items_similarity(
        self, items1: list[dict], items2: list[dict]
    ) -> float:
        """
        Calculate similarity between two item lists.

        Args:
            items1: First item list
            items2: Second item list

        Returns:
            Similarity score between 0 and 1
        """
        if not items1 or not items2:
            return 0.0

        # Compare item counts
        count_similarity = 1.0 - abs(len(items1) - len(items2)) / max(
            len(items1), len(items2)
        )

        # Compare total amounts
        total1 = sum(item.get("total_price", 0) for item in items1)
        total2 = sum(item.get("total_price", 0) for item in items2)
        amount_similarity = self._calculate_numeric_similarity(total1, total2)

        return (count_similarity + amount_similarity) / 2

    def _extract_consensus_data(
        self, results: list[dict[str, Any]], agreement_metrics: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Extract consensus data from agent results.

        Args:
            results: List of successful agent results
            agreement_metrics: Agreement metrics

        Returns:
            Consensus data dictionary
        """
        if len(results) == 1:
            return results[0]["data"]

        # Use weighted average for consensus
        consensus_data = {}

        # For each field, calculate weighted consensus
        all_fields = set()
        for result in results:
            all_fields.update(result["data"].keys())

        for field in all_fields:
            values = []
            weights = []

            for result in results:
                if field in result["data"]:
                    values.append(result["data"][field])
                    weights.append(result["weight"])

            if values:
                if isinstance(values[0], int | float):
                    # Numeric consensus
                    consensus_data[field] = self._weighted_average(values, weights)
                elif isinstance(values[0], str):
                    # String consensus (most common)
                    consensus_data[field] = self._most_common_value(values, weights)
                elif isinstance(values[0], list):
                    # List consensus (merge)
                    consensus_data[field] = self._merge_lists(values, weights)
                else:
                    # Use first value
                    consensus_data[field] = values[0]

        return consensus_data

    def _weighted_average(self, values: list[float], weights: list[float]) -> float:
        """Calculate weighted average of numeric values."""
        if not values or not weights:
            return 0.0

        total_weight = sum(weights)
        if total_weight == 0:
            return mean(values)

        weighted_sum = sum(v * w for v, w in zip(values, weights, strict=False))
        return weighted_sum / total_weight

    def _most_common_value(self, values: list[str], weights: list[float]) -> str:
        """Find most common string value with weights."""
        if not values:
            return ""

        value_counts = {}
        for value, weight in zip(values, weights, strict=False):
            value_counts[value] = value_counts.get(value, 0) + weight

        return max(value_counts.items(), key=lambda x: x[1])[0]

    def _merge_lists(self, lists: list[list], weights: list[float]) -> list:
        """Merge multiple lists with weights."""
        if not lists:
            return []

        # For now, return the longest list
        return max(lists, key=len)

    def _calculate_consensus_confidence(
        self, agreement_metrics: dict[str, Any]
    ) -> float:
        """
        Calculate overall consensus confidence.

        Args:
            agreement_metrics: Agreement metrics

        Returns:
            Confidence score between 0 and 1
        """
        overall_agreement = agreement_metrics["overall_agreement"]
        disagreement_count = len(agreement_metrics["disagreements"])

        # Base confidence on agreement rate
        confidence = overall_agreement

        # Penalize for disagreements
        if disagreement_count > 0:
            confidence *= 1.0 - disagreement_count * 0.1

        return max(0.0, min(1.0, confidence))

    def get_consensus_summary(
        self, consensus_result: ConsensusResult
    ) -> dict[str, Any]:
        """
        Get summary of consensus validation results.

        Args:
            consensus_result: Consensus validation result

        Returns:
            Summary dictionary
        """
        return {
            "consensus_achieved": consensus_result.confidence_score
            >= self.min_consensus_threshold,
            "confidence_score": consensus_result.confidence_score,
            "agreement_rate": consensus_result.agreement_rate,
            "agent_count": len(self.agents),
            "disagreement_count": len(consensus_result.disagreements),
            "requires_review": consensus_result.requires_review,
            "timestamp": consensus_result.timestamp.isoformat(),
        }
