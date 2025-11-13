"""
Quality Validator
==================

Validates consistency and quality across multi-agent analysis results.
Checks for:
- Methodology-results alignment
- Claim-evidence consistency
- Cross-sectional coherence
- Completeness of analysis
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    severity: str  # 'critical', 'warning', 'info'
    category: str  # 'consistency', 'completeness', 'coherence', 'quality'
    section: str  # Which section(s) affected
    message: str  # Description of the issue
    recommendation: Optional[str] = None  # How to fix


class QualityValidator:
    """
    Validates consistency and quality across multi-agent analysis results.

    Performs cross-sectional validation to ensure:
    1. Methodology descriptions match results
    2. Claims are supported by evidence
    3. Conclusions align with findings
    4. No contradictions between sections
    5. Complete coverage of all aspects
    """

    def __init__(self):
        """Initialize quality validator"""
        self.validation_issues: List[ValidationIssue] = []

    def validate_analysis(self, comprehensive_result: Dict) -> Dict:
        """
        Validate comprehensive analysis results.

        Args:
            comprehensive_result: Result from DocumentAnalysisOrchestrator

        Returns:
            Validation report dictionary
        """
        self.validation_issues = []

        if not comprehensive_result.get('success'):
            return {
                'success': False,
                'message': 'Cannot validate failed analysis'
            }

        analysis_results = comprehensive_result.get('analysis_results', {})

        # Run validation checks
        self._check_completeness(analysis_results)
        self._check_methodology_results_alignment(analysis_results)
        self._check_claims_evidence_consistency(analysis_results)
        self._check_conclusion_support(analysis_results)
        self._check_cross_sectional_coherence(analysis_results)
        self._check_quantitative_consistency(analysis_results)

        # Categorize issues by severity
        critical_issues = [i for i in self.validation_issues if i.severity == 'critical']
        warnings = [i for i in self.validation_issues if i.severity == 'warning']
        info = [i for i in self.validation_issues if i.severity == 'info']

        # Calculate overall quality score
        quality_score = self._calculate_quality_score()

        return {
            'success': True,
            'quality_score': quality_score,
            'total_issues': len(self.validation_issues),
            'critical_issues': len(critical_issues),
            'warnings': len(warnings),
            'info_items': len(info),
            'issues': [
                {
                    'severity': issue.severity,
                    'category': issue.category,
                    'section': issue.section,
                    'message': issue.message,
                    'recommendation': issue.recommendation
                }
                for issue in self.validation_issues
            ],
            'categories': self._group_by_category(),
            'passed_checks': self._count_passed_checks(analysis_results),
            'message': f'Validation complete: {quality_score:.0%} quality score'
        }

    def _check_completeness(self, analysis_results: Dict):
        """Check if all expected sections are present and complete"""
        expected_sections = [
            'abstract', 'introduction', 'methodology',
            'results', 'discussion', 'conclusion'
        ]

        missing_sections = []
        incomplete_sections = []

        for section in expected_sections:
            if section not in analysis_results:
                missing_sections.append(section)
            elif not analysis_results[section].get('success'):
                incomplete_sections.append(section)
            else:
                # Check if analysis has meaningful content
                analysis = analysis_results[section].get('analysis', {})
                if not analysis or len(analysis) < 2:
                    incomplete_sections.append(section)

        if missing_sections:
            self.validation_issues.append(ValidationIssue(
                severity='critical',
                category='completeness',
                section=', '.join(missing_sections),
                message=f'Missing analysis for sections: {", ".join(missing_sections)}',
                recommendation='Rerun analysis with all sections enabled'
            ))

        if incomplete_sections:
            self.validation_issues.append(ValidationIssue(
                severity='warning',
                category='completeness',
                section=', '.join(incomplete_sections),
                message=f'Incomplete analysis for sections: {", ".join(incomplete_sections)}',
                recommendation='Check source document quality for these sections'
            ))

    def _check_methodology_results_alignment(self, analysis_results: Dict):
        """Check if methodology description aligns with reported results"""
        method = analysis_results.get('methodology', {}).get('analysis', {})
        results = analysis_results.get('results', {}).get('analysis', {})

        if not method or not results:
            return

        # Check if research design is mentioned in results
        research_design = method.get('research_design', '').lower()

        # Check for key methodology terms in results
        method_terms = self._extract_key_terms(method)
        results_text = str(results).lower()

        mentioned_terms = [term for term in method_terms if term in results_text]

        if len(mentioned_terms) < len(method_terms) * 0.3:  # Less than 30% mentioned
            self.validation_issues.append(ValidationIssue(
                severity='warning',
                category='consistency',
                section='methodology, results',
                message='Limited alignment between methodology and results',
                recommendation='Verify that results discuss the methods actually used'
            ))

    def _check_claims_evidence_consistency(self, analysis_results: Dict):
        """Check if claims in discussion are supported by results"""
        results = analysis_results.get('results', {}).get('analysis', {})
        discussion = analysis_results.get('discussion', {}).get('analysis', {})

        if not results or not discussion:
            return

        # Extract findings from results
        findings = results.get('main_findings', [])

        # Check if discussion implications reference actual findings
        implications = discussion.get('theoretical_implications', []) + \
                      discussion.get('practical_implications', [])

        if implications and not findings:
            self.validation_issues.append(ValidationIssue(
                severity='warning',
                category='consistency',
                section='results, discussion',
                message='Discussion makes claims without corresponding results',
                recommendation='Ensure discussion is grounded in reported results'
            ))

    def _check_conclusion_support(self, analysis_results: Dict):
        """Check if conclusions are supported by findings"""
        results = analysis_results.get('results', {}).get('analysis', {})
        conclusion = analysis_results.get('conclusion', {}).get('analysis', {})

        if not results or not conclusion:
            return

        # Extract main contributions from conclusion
        contributions = conclusion.get('main_contributions', [])

        # Check if results section exists and has findings
        findings = results.get('main_findings', [])

        if contributions and not findings:
            self.validation_issues.append(ValidationIssue(
                severity='warning',
                category='consistency',
                section='results, conclusion',
                message='Conclusions lack support from results section',
                recommendation='Verify conclusions align with reported findings'
            ))

        # Check for overstated conclusions
        if len(contributions) > len(findings) * 1.5:
            self.validation_issues.append(ValidationIssue(
                severity='info',
                category='quality',
                section='conclusion',
                message='Conclusion may overstate contributions relative to findings',
                recommendation='Consider if all claimed contributions are justified'
            ))

    def _check_cross_sectional_coherence(self, analysis_results: Dict):
        """Check coherence across sections"""
        abstract = analysis_results.get('abstract', {}).get('analysis', {})
        introduction = analysis_results.get('introduction', {}).get('analysis', {})
        conclusion = analysis_results.get('conclusion', {}).get('analysis', {})

        if not abstract or not introduction or not conclusion:
            return

        # Check if abstract objective matches introduction problem
        abstract_obj = abstract.get('research_objective', '').lower()
        intro_problem = introduction.get('problem_statement', '').lower()

        # Simple term overlap check
        if abstract_obj and intro_problem:
            abstract_terms = set(abstract_obj.split())
            intro_terms = set(intro_problem.split())
            overlap = len(abstract_terms & intro_terms)

            if overlap < 3:  # Very low overlap
                self.validation_issues.append(ValidationIssue(
                    severity='info',
                    category='coherence',
                    section='abstract, introduction',
                    message='Abstract and introduction may describe different objectives',
                    recommendation='Verify consistency of research objective across sections'
                ))

        # Check if conclusion aligns with abstract
        abstract_findings = abstract.get('key_findings', [])
        conclusion_contrib = conclusion.get('main_contributions', [])

        if len(abstract_findings) > 0 and len(conclusion_contrib) > len(abstract_findings) * 2:
            self.validation_issues.append(ValidationIssue(
                severity='info',
                category='coherence',
                section='abstract, conclusion',
                message='Conclusion claims more contributions than abstract indicates',
                recommendation='Check if abstract adequately summarizes contributions'
            ))

    def _check_quantitative_consistency(self, analysis_results: Dict):
        """Check consistency of quantitative claims"""
        results = analysis_results.get('results', {}).get('analysis', {})
        tables = analysis_results.get('tables', {}).get('analysis', {})

        if not results and not tables:
            return

        # Extract metrics from results
        metrics = results.get('performance_metrics', {}) if results else {}

        # Extract metrics from tables
        table_metrics = []
        if tables and tables.get('key_metrics'):
            table_metrics = tables.get('key_metrics', [])

        # Check if numerical claims in results match tables
        if metrics and not table_metrics:
            self.validation_issues.append(ValidationIssue(
                severity='info',
                category='completeness',
                section='results, tables',
                message='Quantitative results mentioned without corresponding tables',
                recommendation='Consider adding tables to support quantitative claims'
            ))

    def _extract_key_terms(self, data: Dict, min_length: int = 4) -> List[str]:
        """Extract key terms from data dictionary"""
        text = str(data).lower()
        # Simple word extraction (alphanumeric tokens)
        words = re.findall(r'\b[a-z]{' + str(min_length) + r',}\b', text)
        # Remove common words
        common = {'this', 'that', 'with', 'from', 'have', 'their',
                  'were', 'been', 'would', 'could', 'should', 'analysis',
                  'section', 'paper', 'study', 'research'}
        return [w for w in words if w not in common][:20]  # Top 20 terms

    def _calculate_quality_score(self) -> float:
        """Calculate overall quality score (0-1)"""
        if not self.validation_issues:
            return 1.0

        # Weight issues by severity
        penalty = 0.0
        for issue in self.validation_issues:
            if issue.severity == 'critical':
                penalty += 0.15
            elif issue.severity == 'warning':
                penalty += 0.08
            elif issue.severity == 'info':
                penalty += 0.03

        score = max(0.0, 1.0 - penalty)
        return score

    def _group_by_category(self) -> Dict:
        """Group issues by category"""
        grouped = {}
        for issue in self.validation_issues:
            if issue.category not in grouped:
                grouped[issue.category] = []
            grouped[issue.category].append({
                'severity': issue.severity,
                'section': issue.section,
                'message': issue.message
            })
        return grouped

    def _count_passed_checks(self, analysis_results: Dict) -> int:
        """Count number of checks that passed"""
        total_checks = 6  # Number of check methods
        failed_checks = len(set(issue.category for issue in self.validation_issues if issue.severity == 'critical'))
        return total_checks - failed_checks

    def get_validation_summary(self, validation_result: Dict) -> str:
        """
        Format validation result into human-readable summary.

        Args:
            validation_result: Result from validate_analysis()

        Returns:
            Formatted summary string
        """
        if not validation_result.get('success'):
            return "Validation failed: " + validation_result.get('message', 'Unknown error')

        lines = []
        lines.append("=" * 80)
        lines.append("QUALITY VALIDATION REPORT")
        lines.append("=" * 80)

        # Overall score
        score = validation_result.get('quality_score', 0)
        lines.append(f"\nOverall Quality Score: {score:.0%}")

        if score >= 0.9:
            lines.append("Status: ✅ Excellent - High quality analysis")
        elif score >= 0.75:
            lines.append("Status: ✅ Good - Minor issues detected")
        elif score >= 0.6:
            lines.append("Status: ⚠️ Fair - Several issues need attention")
        else:
            lines.append("Status: ❌ Poor - Significant issues detected")

        # Summary statistics
        lines.append(f"\nTotal Issues: {validation_result.get('total_issues', 0)}")
        lines.append(f"  - Critical: {validation_result.get('critical_issues', 0)}")
        lines.append(f"  - Warnings: {validation_result.get('warnings', 0)}")
        lines.append(f"  - Info: {validation_result.get('info_items', 0)}")

        # Issues by category
        categories = validation_result.get('categories', {})
        if categories:
            lines.append(f"\nIssues by Category:")
            for category, issues in categories.items():
                lines.append(f"  - {category.capitalize()}: {len(issues)} issue(s)")

        # Detailed issues
        issues = validation_result.get('issues', [])
        if issues:
            lines.append(f"\nDetailed Issues:")
            lines.append("-" * 80)

            for i, issue in enumerate(issues, 1):
                severity_icon = {
                    'critical': '❌',
                    'warning': '⚠️',
                    'info': 'ℹ️'
                }.get(issue['severity'], '•')

                lines.append(f"\n{i}. {severity_icon} [{issue['severity'].upper()}] {issue['category'].capitalize()}")
                lines.append(f"   Section(s): {issue['section']}")
                lines.append(f"   Issue: {issue['message']}")
                if issue.get('recommendation'):
                    lines.append(f"   Recommendation: {issue['recommendation']}")

        # Passed checks
        passed = validation_result.get('passed_checks', 0)
        lines.append(f"\n" + "=" * 80)
        lines.append(f"Validation Checks Passed: {passed}/6")

        return '\n'.join(lines)


if __name__ == "__main__":
    # Test the validator
    print("Testing QualityValidator...")

    validator = QualityValidator()

    # Mock analysis result
    mock_result = {
        'success': True,
        'analysis_results': {
            'abstract': {
                'success': True,
                'analysis': {
                    'research_objective': 'Develop a new machine learning model',
                    'key_findings': ['Achieved 95% accuracy', 'Reduced training time'],
                    'main_contributions': ['Novel architecture', 'Efficient training']
                }
            },
            'methodology': {
                'success': True,
                'analysis': {
                    'research_design': 'Experimental study with neural networks',
                    'approach': 'Deep learning with transformers',
                    'data_sources': ['ImageNet', 'COCO']
                }
            },
            'results': {
                'success': True,
                'analysis': {
                    'main_findings': ['95% accuracy on test set', 'Fast inference'],
                    'performance_metrics': {'accuracy': 0.95, 'speed': '10ms'}
                }
            },
            'conclusion': {
                'success': True,
                'analysis': {
                    'main_contributions': ['Novel architecture', 'Efficient training', 'Better performance'],
                    'future_directions': ['Extend to other domains']
                }
            }
        }
    }

    # Run validation
    result = validator.validate_analysis(mock_result)

    print("\n" + validator.get_validation_summary(result))
    print(f"\n✅ Validation completed successfully!")
    print(f"   Quality Score: {result['quality_score']:.0%}")
    print(f"   Total Issues: {result['total_issues']}")
