#!/usr/bin/env python3
"""
LLM-Powered Bias Analysis Module

Uses Claude to analyze news sources for bias, generate alternative perspectives,
and fact-check against academic sources.
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_session
from app.llm import get_client
from app.models import (AcademicSource, AlternativePerspective, BiasAnalysis,
                        FactCheck, Source, SourceBias)

logger = structlog.get_logger(__name__)

# Claude model configuration
ANALYSIS_MODEL = "claude-3-sonnet-20240229"
QUICK_MODEL = "claude-3-haiku-20240307"


class BiasAnalyzer:
    """LLM-powered bias analysis for news sources."""

    def __init__(self):
        self.client = get_client()

    async def analyze_source_bias(self, source: Source) -> Dict:
        """Analyze a single source for bias indicators."""

        prompt = f"""
        Analyze this news article for bias and provide a comprehensive assessment:

        Title: {source.meta.get('title', 'N/A')}
        Source: {source.platform}
        URL: {source.url}
        Content: {source.raw_text[:2000]}...

        Provide analysis in this JSON format:
        {{
            "political_bias": -0.5 to 0.5 (negative=left, positive=right),
            "factual_accuracy": 0.0 to 1.0,
            "emotional_tone": -1.0 to 1.0 (negative=negative, positive=positive),
            "sensationalism_score": 0.0 to 1.0,
            "confidence_score": 0.0 to 1.0,
            "bias_indicators": {{
                "loaded_language": ["example phrases"],
                "missing_context": ["what's missing"],
                "selective_facts": ["selective reporting"],
                "emotional_manipulation": ["emotional appeals"]
            }},
            "blind_spots": ["perspective gaps", "missing viewpoints"],
            "summary": "brief analysis summary"
        }}
        """

        try:
            response = await self.client.messages.create(
                model=ANALYSIS_MODEL,
                max_tokens=1500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )

            analysis_text = response.content[0].text
            # Extract JSON from response
            start_idx = analysis_text.find("{")
            end_idx = analysis_text.rfind("}") + 1
            json_str = analysis_text[start_idx:end_idx]

            return json.loads(json_str)

        except Exception as e:
            logger.error("Bias analysis failed", source_id=source.id, error=str(e))
            return {
                "political_bias": 0.0,
                "factual_accuracy": 0.5,
                "emotional_tone": 0.0,
                "sensationalism_score": 0.5,
                "confidence_score": 0.3,
                "bias_indicators": {},
                "blind_spots": ["Analysis failed"],
                "summary": f"Analysis failed: {str(e)}",
            }

    async def generate_alternative_perspective(
        self, source: Source, academic_sources: List[AcademicSource]
    ) -> str:
        """Generate alternative perspective based on academic sources."""

        academic_context = "\n\n".join(
            [
                f"Academic Source: {ac.title} ({ac.publication_year})\n"
                f"Abstract: {ac.abstract[:500]}..."
                for ac in academic_sources[:3]
            ]
        )

        prompt = f"""
        Based on the following academic sources, provide an alternative perspective
        to this news article that addresses potential biases and blind spots:

        NEWS ARTICLE:
        Title: {source.meta.get('title', 'N/A')}
        Source: {source.platform}
        Content: {source.raw_text[:1500]}...

        ACADEMIC CONTEXT:
        {academic_context}

        Generate an alternative perspective that:
        1. Addresses missing historical context
        2. Presents opposing viewpoints
        3. Provides factual corrections if needed
        4. Highlights potential bias blind spots

        Keep response under 300 words, balanced and factual.
        """

        try:
            response = await self.client.messages.create(
                model=ANALYSIS_MODEL,
                max_tokens=500,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}],
            )

            return response.content[0].text.strip()

        except Exception as e:
            logger.error(
                "Alternative perspective generation failed",
                source_id=source.id,
                error=str(e),
            )
            return f"Unable to generate alternative perspective: {str(e)}"

    async def fact_check_against_academic(
        self, source: Source, academic_source: AcademicSource
    ) -> Dict:
        """Fact-check source claims against academic source."""

        prompt = f"""
        Fact-check the claims in this news article against the academic source:

        NEWS ARTICLE:
        {source.raw_text[:1000]}...

        ACADEMIC SOURCE:
        Title: {academic_source.title}
        Authors: {academic_source.authors}
        Abstract: {academic_source.abstract}

        Provide fact-check result in JSON format:
        {{
            "verification_status": "verified|partially_verified|disputed|false|inconclusive",
            "accuracy_score": 0.0 to 1.0,
            "evidence_text": "supporting/contradicting evidence",
            "context_provided": true/false,
            "key_claims": ["claim 1", "claim 2"],
            "analysis": "brief analysis"
        }}
        """

        try:
            response = await self.client.messages.create(
                model=QUICK_MODEL,
                max_tokens=800,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )

            analysis_text = response.content[0].text
            start_idx = analysis_text.find("{")
            end_idx = analysis_text.rfind("}") + 1
            json_str = analysis_text[start_idx:end_idx]

            return json.loads(json_str)

        except Exception as e:
            logger.error("Fact-check failed", source_id=source.id, error=str(e))
            return {
                "verification_status": "inconclusive",
                "accuracy_score": 0.5,
                "evidence_text": f"Fact-check failed: {str(e)}",
                "context_provided": False,
                "key_claims": [],
                "analysis": "Analysis failed",
            }


async def process_source_bias_analysis(session: AsyncSession, source_id: int) -> None:
    """Process comprehensive bias analysis for a source."""

    # Get source
    source = await session.get(Source, source_id)
    if not source:
        logger.error("Source not found", source_id=source_id)
        return

    analyzer = BiasAnalyzer()

    try:
        # Perform bias analysis
        bias_result = await analyzer.analyze_source_bias(source)

        # Update or create SourceBias record
        if source.bias:
            source_bias = source.bias
        else:
            source_bias = SourceBias(name=source.platform)
            session.add(source_bias)
            await session.flush()
            source.bias_id = source_bias.id

        # Update bias metrics
        source_bias.political_bias = bias_result.get("political_bias", 0.0)
        source_bias.factual_accuracy = bias_result.get("factual_accuracy", 0.5)
        source_bias.emotional_tone = bias_result.get("emotional_tone", 0.0)
        source_bias.sensationalism_score = bias_result.get("sensationalism_score", 0.5)
        source_bias.confidence_score = bias_result.get("confidence_score", 0.0)
        source_bias.analysis_method = "llm_automated"
        source_bias.last_analysis_date = datetime.utcnow()

        # Create BiasAnalysis record
        bias_analysis = BiasAnalysis(
            source_id=source.id,
            analysis_type="source_bias",
            bias_indicators=bias_result.get("bias_indicators", {}),
            blind_spots=bias_result.get("blind_spots", []),
            llm_analysis=bias_result.get("summary", ""),
            confidence_score=bias_result.get("confidence_score", 0.0),
            analysis_model=ANALYSIS_MODEL,
        )
        session.add(bias_analysis)

        # Get relevant academic sources for fact-checking
        academic_sources = await session.execute(
            select(AcademicSource)
            .where(
                AcademicSource.source_type.in_(
                    ["academic_paper", "historical_document"]
                )
            )
            .limit(3)
        )
        academic_sources = academic_sources.scalars().all()

        # Generate alternative perspective
        if academic_sources:
            alt_perspective_text = await analyzer.generate_alternative_perspective(
                source, academic_sources
            )

            alt_perspective = AlternativePerspective(
                source_id=source.id,
                perspective_type="alternative_interpretation",
                perspective_text=alt_perspective_text,
                supporting_sources=[ac.title for ac in academic_sources],
                confidence_score=bias_result.get("confidence_score", 0.5),
                generation_model=ANALYSIS_MODEL,
            )
            session.add(alt_perspective)

            # Fact-check against first academic source
            if academic_sources:
                fact_check_result = await analyzer.fact_check_against_academic(
                    source, academic_sources[0]
                )

                fact_check = FactCheck(
                    source_id=source.id,
                    academic_source_id=academic_sources[0].id,
                    claim_text=source.meta.get("title", "")[:200],
                    verification_status=fact_check_result.get(
                        "verification_status", "inconclusive"
                    ),
                    evidence_text=fact_check_result.get("evidence_text", ""),
                    accuracy_score=fact_check_result.get("accuracy_score", 0.5),
                    context_provided=fact_check_result.get("context_provided", False),
                    llm_analysis=fact_check_result.get("analysis", ""),
                )
                session.add(fact_check)

        await session.commit()
        logger.info("Bias analysis completed", source_id=source.id)

    except Exception as e:
        await session.rollback()
        logger.error("Bias analysis failed", source_id=source_id, error=str(e))


async def batch_analyze_sources(limit: int = 10) -> None:
    """Analyze sources that haven't been processed yet."""

    async with async_session() as session:
        # Get sources without bias analysis
        sources = await session.execute(
            select(Source.id)
            .outerjoin(BiasAnalysis, Source.id == BiasAnalysis.source_id)
            .where(BiasAnalysis.id.is_(None))
            .limit(limit)
        )
        source_ids = [row[0] for row in sources]

        logger.info("Starting batch bias analysis", count=len(source_ids))

        for source_id in source_ids:
            try:
                await process_source_bias_analysis(session, source_id)
            except Exception as e:
                logger.error(
                    "Failed to analyze source", source_id=source_id, error=str(e)
                )
                continue

        logger.info("Batch bias analysis completed", processed=len(source_ids))


if __name__ == "__main__":
    asyncio.run(batch_analyze_sources())
