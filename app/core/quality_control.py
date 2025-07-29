"""测试用例质量控制模块

为AI生成的测试用例提供质量评估、去重、优先级排序和优化建议。
"""

import hashlib
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from app.core.models import TestCase, TestCaseType


class QualityLevel(str, Enum):
    """质量等级"""

    EXCELLENT = "excellent"  # 90-100分
    GOOD = "good"  # 80-89分
    AVERAGE = "average"  # 70-79分
    POOR = "poor"  # 60-69分
    UNACCEPTABLE = "unacceptable"  # <60分


class QualityMetric(str, Enum):
    """质量指标"""

    COMPLETENESS = "completeness"  # 完整性
    CLARITY = "clarity"  # 清晰度
    COVERAGE = "coverage"  # 覆盖度
    SPECIFICITY = "specificity"  # 具体性
    MAINTAINABILITY = "maintainability"  # 可维护性
    RELIABILITY = "reliability"  # 可靠性
    EFFICIENCY = "efficiency"  # 效率


@dataclass
class QualityScore:
    """质量评分"""

    metric: QualityMetric
    score: float  # 0-100
    weight: float  # 权重
    details: str  # 详细说明
    suggestions: List[str]  # 改进建议


@dataclass
class QualityReport:
    """质量报告"""

    test_case_id: str
    overall_score: float  # 总体评分
    quality_level: QualityLevel
    metric_scores: List[QualityScore]
    issues: List[str]  # 发现的问题
    suggestions: List[str]  # 改进建议
    is_duplicate: bool  # 是否重复
    duplicate_of: Optional[str]  # 重复的原始用例ID
    priority_adjustment: int  # 优先级调整建议 (-2 to +2)


class TestCaseQualityAnalyzer:
    """测试用例质量分析器

    分析单个测试用例的质量指标。
    """

    def __init__(self):
        self.metric_weights = {
            QualityMetric.COMPLETENESS: 0.25,
            QualityMetric.CLARITY: 0.20,
            QualityMetric.COVERAGE: 0.15,
            QualityMetric.SPECIFICITY: 0.15,
            QualityMetric.MAINTAINABILITY: 0.10,
            QualityMetric.RELIABILITY: 0.10,
            QualityMetric.EFFICIENCY: 0.05,
        }

    def analyze(self, test_case: TestCase) -> QualityReport:
        """分析测试用例质量

        Args:
            test_case: 待分析的测试用例

        Returns:
            质量报告
        """
        metric_scores = []

        # 分析各项质量指标
        metric_scores.append(self._analyze_completeness(test_case))
        metric_scores.append(self._analyze_clarity(test_case))
        metric_scores.append(self._analyze_coverage(test_case))
        metric_scores.append(self._analyze_specificity(test_case))
        metric_scores.append(self._analyze_maintainability(test_case))
        metric_scores.append(self._analyze_reliability(test_case))
        metric_scores.append(self._analyze_efficiency(test_case))

        # 计算总体评分
        overall_score = sum(score.score * score.weight for score in metric_scores)

        # 确定质量等级
        quality_level = self._determine_quality_level(overall_score)

        # 收集问题和建议
        issues = []
        suggestions = []
        for score in metric_scores:
            if score.score < 70:
                issues.append(f"{score.metric.value}评分过低: {score.details}")
            suggestions.extend(score.suggestions)

        # 优先级调整建议
        priority_adjustment = self._calculate_priority_adjustment(
            overall_score, test_case
        )

        return QualityReport(
            test_case_id=test_case.id or "unknown",
            overall_score=overall_score,
            quality_level=quality_level,
            metric_scores=metric_scores,
            issues=issues,
            suggestions=list(set(suggestions)),  # 去重
            is_duplicate=False,  # 将在去重阶段设置
            duplicate_of=None,
            priority_adjustment=priority_adjustment,
        )

    def _analyze_completeness(self, test_case: TestCase) -> QualityScore:
        """分析完整性"""
        score = 0
        details = []
        suggestions = []

        # 检查必要字段
        if test_case.name:
            score += 20
        else:
            details.append("缺少测试用例名称")
            suggestions.append("添加清晰的测试用例名称")

        if test_case.description:
            score += 20
        else:
            details.append("缺少测试用例描述")
            suggestions.append("添加详细的测试场景描述")

        if test_case.test_data:
            score += 20
        else:
            details.append("缺少测试数据")
            suggestions.append("提供完整的测试数据")

        if test_case.expected_response:
            score += 20
        else:
            details.append("缺少预期响应")
            suggestions.append("定义明确的预期响应")

        if test_case.test_steps and len(test_case.test_steps) >= 3:
            score += 20
        else:
            details.append(
                f"测试步骤数量不足: {len(test_case.test_steps) if test_case.test_steps else 0}"
            )
            suggestions.append("至少提供3个具体的测试步骤")

        return QualityScore(
            metric=QualityMetric.COMPLETENESS,
            score=score,
            weight=self.metric_weights[QualityMetric.COMPLETENESS],
            details="; ".join(details) if details else "所有必要字段完整",
            suggestions=suggestions,
        )

    def _analyze_clarity(self, test_case: TestCase) -> QualityScore:
        """分析清晰度"""
        score = 100
        details = []
        suggestions = []

        # 检查名称清晰度
        if test_case.name:
            if len(test_case.name) < 10:
                score -= 15
                details.append("测试用例名称过短")
                suggestions.append("使用更具描述性的测试用例名称")
            elif len(test_case.name) > 100:
                score -= 10
                details.append("测试用例名称过长")
                suggestions.append("简化测试用例名称")

        # 检查描述清晰度
        if test_case.description:
            if len(test_case.description) < 20:
                score -= 20
                details.append("描述过于简单")
                suggestions.append("提供更详细的测试场景描述")

            # 检查是否包含关键信息
            description_lower = test_case.description.lower()
            key_elements = [
                "测试",
                "验证",
                "检查",
                "确保",
                "应该",
                "test",
                "verify",
                "check",
                "ensure",
                "should",
            ]
            if not any(element in description_lower for element in key_elements):
                score -= 15
                details.append("描述缺少明确的测试意图")
                suggestions.append("在描述中明确说明测试目标")

        # 检查测试步骤清晰度
        if test_case.test_steps:
            vague_steps = 0
            for step in test_case.test_steps:
                # step是字典格式，需要检查其中的文本内容
                step_text = ""
                if isinstance(step, dict):
                    step_text = " ".join(str(v) for v in step.values() if v)
                else:
                    step_text = str(step)

                if any(
                    vague in step_text.lower()
                    for vague in ["正确", "成功", "correct", "success", "ok"]
                ):
                    vague_steps += 1

            if vague_steps > len(test_case.test_steps) * 0.5:
                score -= 20
                details.append("测试步骤过于模糊")
                suggestions.append("使用具体的测试步骤描述")

        return QualityScore(
            metric=QualityMetric.CLARITY,
            score=max(0, score),
            weight=self.metric_weights[QualityMetric.CLARITY],
            details="; ".join(details) if details else "测试用例表达清晰",
            suggestions=suggestions,
        )

    def _analyze_coverage(self, test_case: TestCase) -> QualityScore:
        """分析覆盖度"""
        score = 0
        details = []
        suggestions = []

        # 基础覆盖
        if test_case.test_data:
            score += 30

        if test_case.expected_response:
            score += 30

        # 测试步骤覆盖
        if test_case.test_steps:
            step_types = set()
            for step in test_case.test_steps:
                # step是字典格式，需要检查其中的文本内容
                step_text = ""
                if isinstance(step, dict):
                    step_text = " ".join(str(v) for v in step.values() if v)
                else:
                    step_text = str(step)

                step_lower = step_text.lower()
                if "status" in step_lower or "状态" in step_lower:
                    step_types.add("status")
                if "header" in step_lower or "头" in step_lower:
                    step_types.add("header")
                if "body" in step_lower or "响应体" in step_lower or "json" in step_lower:
                    step_types.add("body")
                if "time" in step_lower or "时间" in step_lower:
                    step_types.add("performance")

            score += len(step_types) * 10

            if len(step_types) < 2:
                suggestions.append("增加不同类型的验证步骤（状态码、响应头、响应体等）")

        # 测试类型特定覆盖
        if test_case.type == TestCaseType.ERROR:
            error_found = False
            for step in test_case.test_steps or []:
                step_text = ""
                if isinstance(step, dict):
                    step_text = " ".join(str(v) for v in step.values() if v)
                else:
                    step_text = str(step)

                if "error" in step_text.lower() or "错误" in step_text.lower():
                    error_found = True
                    break

            if error_found:
                score += 10
            else:
                details.append("错误测试用例缺少错误相关步骤")
                suggestions.append("添加错误码和错误消息的验证步骤")

        return QualityScore(
            metric=QualityMetric.COVERAGE,
            score=min(100, score),
            weight=self.metric_weights[QualityMetric.COVERAGE],
            details="; ".join(details) if details else "测试覆盖度良好",
            suggestions=suggestions,
        )

    def _analyze_specificity(self, test_case: TestCase) -> QualityScore:
        """分析具体性"""
        score = 100
        details = []
        suggestions = []

        # 检查测试数据的具体性
        if test_case.test_data:
            if not any(test_case.test_data.values()):
                score -= 30
                details.append("测试数据为空")
                suggestions.append("提供具体的测试数据值")

        # 检查预期响应的具体性
        if test_case.expected_response:
            response_str = str(test_case.expected_response)
            if "null" in response_str.lower() or "none" in response_str.lower():
                score -= 20
                details.append("预期响应过于抽象")
                suggestions.append("定义具体的响应数据结构")

        # 检查测试步骤的具体性
        if test_case.test_steps:
            generic_count = 0
            for step in test_case.test_steps:
                # 处理字典格式的测试步骤
                if isinstance(step, dict):
                    step_text = " ".join(str(v) for v in step.values() if v is not None)
                else:
                    step_text = str(step)

                if any(
                    generic in step_text.lower()
                    for generic in ["存在", "exist", "不为空", "not null", "有效", "valid"]
                ):
                    generic_count += 1

            if generic_count > len(test_case.test_steps) * 0.3:
                score -= 25
                details.append("测试步骤过于泛化")
                suggestions.append("使用具体的数值、字符串或条件进行验证")

        return QualityScore(
            metric=QualityMetric.SPECIFICITY,
            score=max(0, score),
            weight=self.metric_weights[QualityMetric.SPECIFICITY],
            details="; ".join(details) if details else "测试用例具体明确",
            suggestions=suggestions,
        )

    def _analyze_maintainability(self, test_case: TestCase) -> QualityScore:
        """分析可维护性"""
        score = 100
        details = []
        suggestions = []

        # 检查复杂度
        if test_case.test_steps and len(test_case.test_steps) > 10:
            score -= 20
            details.append("测试步骤过多")
            suggestions.append("考虑拆分为多个测试用例")

        # 检查硬编码
        test_data_str = str(test_case.test_data) if test_case.test_data else ""
        hardcoded_patterns = [
            r"\d{4}-\d{2}-\d{2}",  # 日期
            r"\d{10,}",  # 长数字（可能是ID）
            r"[a-f0-9]{32}",  # MD5
            r"[a-f0-9]{40}",  # SHA1
        ]

        hardcoded_count = sum(
            len(re.findall(pattern, test_data_str)) for pattern in hardcoded_patterns
        )

        if hardcoded_count > 2:
            score -= 15
            details.append("包含过多硬编码值")
            suggestions.append("使用变量或配置替代硬编码值")

        # 检查命名规范
        if test_case.name:
            if not re.match(r"^[a-zA-Z][a-zA-Z0-9_\s\u4e00-\u9fff]*$", test_case.name):
                score -= 10
                details.append("测试用例名称不符合命名规范")
                suggestions.append("使用规范的命名格式")

        return QualityScore(
            metric=QualityMetric.MAINTAINABILITY,
            score=max(0, score),
            weight=self.metric_weights[QualityMetric.MAINTAINABILITY],
            details="; ".join(details) if details else "测试用例易于维护",
            suggestions=suggestions,
        )

    def _analyze_reliability(self, test_case: TestCase) -> QualityScore:
        """分析可靠性"""
        score = 100
        details = []
        suggestions = []

        # 检查测试步骤的可靠性
        if test_case.test_steps:
            unreliable_patterns = [
                r"随机",
                r"random",
                r"可能",
                r"maybe",
                r"有时",
                r"sometimes",
            ]

            unreliable_count = 0
            for step in test_case.test_steps:
                # step是字典格式，需要检查其中的文本内容
                step_text = ""
                if isinstance(step, dict):
                    step_text = " ".join(str(v) for v in step.values() if v)
                else:
                    step_text = str(step)

                if any(
                    re.search(pattern, step_text.lower())
                    for pattern in unreliable_patterns
                ):
                    unreliable_count += 1

            if unreliable_count > 0:
                score -= unreliable_count * 20
                details.append("包含不确定的测试步骤")
                suggestions.append("使用确定性的测试步骤")

        # 检查时间依赖
        all_text = f"{test_case.name} {test_case.description}"
        time_dependent_patterns = [
            r"今天",
            r"明天",
            r"昨天",
            r"today",
            r"tomorrow",
            r"yesterday",
            r"现在",
            r"当前",
            r"now",
            r"current",
        ]

        if any(
            re.search(pattern, all_text.lower()) for pattern in time_dependent_patterns
        ):
            score -= 15
            details.append("包含时间依赖的内容")
            suggestions.append("使用相对时间或固定时间点")

        # 检查环境依赖
        env_dependent_patterns = [r"localhost", r"127\.0\.0\.1", r"本地", r"local"]

        test_data_str = str(test_case.test_data) if test_case.test_data else ""
        if any(
            re.search(pattern, test_data_str.lower())
            for pattern in env_dependent_patterns
        ):
            score -= 10
            details.append("包含环境特定的配置")
            suggestions.append("使用配置变量替代硬编码的环境信息")

        return QualityScore(
            metric=QualityMetric.RELIABILITY,
            score=max(0, score),
            weight=self.metric_weights[QualityMetric.RELIABILITY],
            details="; ".join(details) if details else "测试用例可靠稳定",
            suggestions=suggestions,
        )

    def _analyze_efficiency(self, test_case: TestCase) -> QualityScore:
        """分析效率"""
        score = 100
        details = []
        suggestions = []

        # 检查冗余测试步骤
        if test_case.test_steps:
            step_similarity = self._calculate_step_similarity(test_case.test_steps)
            if step_similarity > 0.7:
                score -= 20
                details.append("存在冗余的测试步骤")
                suggestions.append("移除重复或相似的测试步骤")

        # 检查测试范围
        if test_case.description:
            if len(test_case.description) > 500:
                score -= 10
                details.append("描述过于冗长")
                suggestions.append("简化测试用例描述")

        # 检查测试数据复杂度
        if test_case.test_data:
            test_data_str = str(test_case.test_data)
            if len(test_data_str) > 1000:
                score -= 15
                details.append("测试数据过于复杂")
                suggestions.append("简化测试数据或拆分测试用例")

        return QualityScore(
            metric=QualityMetric.EFFICIENCY,
            score=max(0, score),
            weight=self.metric_weights[QualityMetric.EFFICIENCY],
            details="; ".join(details) if details else "测试用例高效简洁",
            suggestions=suggestions,
        )

    def _calculate_step_similarity(self, test_steps: List[Dict[str, any]]) -> float:
        """计算测试步骤相似度"""
        if len(test_steps) < 2:
            return 0.0

        # 简单的相似度计算：基于共同词汇
        all_words = []
        for step in test_steps:
            # step是字典格式，需要提取其中的文本内容
            step_text = ""
            if isinstance(step, dict):
                step_text = " ".join(str(v) for v in step.values() if v)
            else:
                step_text = str(step)

            words = re.findall(r"\w+", step_text.lower())
            all_words.extend(words)

        word_counts = Counter(all_words)
        total_words = len(all_words)
        repeated_words = sum(count - 1 for count in word_counts.values() if count > 1)

        return repeated_words / total_words if total_words > 0 else 0.0

    def _determine_quality_level(self, score: float) -> QualityLevel:
        """确定质量等级"""
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 80:
            return QualityLevel.GOOD
        elif score >= 70:
            return QualityLevel.AVERAGE
        elif score >= 60:
            return QualityLevel.POOR
        else:
            return QualityLevel.UNACCEPTABLE

    def _calculate_priority_adjustment(self, score: float, test_case: TestCase) -> int:
        """计算优先级调整建议"""
        adjustment = 0

        # 基于质量评分调整
        if score >= 90:
            adjustment += 1
        elif score < 60:
            adjustment -= 1

        # 基于测试类型调整
        if test_case.type == TestCaseType.SECURITY:
            adjustment += 1
        elif test_case.type == TestCaseType.NORMAL:
            adjustment += 0

        # 基于测试步骤数量调整
        step_count = len(test_case.test_steps) if test_case.test_steps else 0
        if step_count >= 5:
            adjustment += 1
        elif step_count < 3:
            adjustment -= 1

        return max(-2, min(2, adjustment))


class TestCaseDeduplicator:
    """测试用例去重器

    识别和处理重复的测试用例。
    """

    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold

    def find_duplicates(self, test_cases: List[TestCase]) -> Dict[str, List[str]]:
        """查找重复的测试用例

        Args:
            test_cases: 测试用例列表

        Returns:
            重复组映射 {原始用例ID: [重复用例ID列表]}
        """
        duplicates = defaultdict(list)
        processed = set()

        for i, case1 in enumerate(test_cases):
            if case1.id in processed:
                continue

            case1_id = case1.id or f"case_{i}"

            for j, case2 in enumerate(test_cases[i + 1 :], i + 1):
                case2_id = case2.id or f"case_{j}"

                if case2_id in processed:
                    continue

                similarity = self._calculate_similarity(case1, case2)
                if similarity >= self.similarity_threshold:
                    duplicates[case1_id].append(case2_id)
                    processed.add(case2_id)

        return dict(duplicates)

    def _calculate_similarity(self, case1: TestCase, case2: TestCase) -> float:
        """计算两个测试用例的相似度"""
        similarities = []

        # 名称相似度
        name_sim = self._text_similarity(case1.name or "", case2.name or "")
        similarities.append((name_sim, 0.3))

        # 描述相似度
        desc_sim = self._text_similarity(
            case1.description or "", case2.description or ""
        )
        similarities.append((desc_sim, 0.2))

        # 测试数据相似度
        test_data_sim = self._dict_similarity(
            case1.test_data or {}, case2.test_data or {}
        )
        similarities.append((test_data_sim, 0.3))

        # 测试步骤相似度
        step_sim = self._list_similarity(case1.test_steps or [], case2.test_steps or [])
        similarities.append((step_sim, 0.2))

        # 加权平均
        weighted_sum = sum(sim * weight for sim, weight in similarities)
        total_weight = sum(weight for _, weight in similarities)

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0

        # 简单的词汇重叠相似度
        words1 = set(re.findall(r"\w+", text1.lower()))
        words2 = set(re.findall(r"\w+", text2.lower()))

        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union

    def _dict_similarity(self, dict1: Dict, dict2: Dict) -> float:
        """计算字典相似度"""
        if not dict1 and not dict2:
            return 1.0
        if not dict1 or not dict2:
            return 0.0

        # 比较键的相似度
        keys1 = set(dict1.keys())
        keys2 = set(dict2.keys())

        if not keys1 and not keys2:
            return 1.0
        if not keys1 or not keys2:
            return 0.0

        key_similarity = len(keys1 & keys2) / len(keys1 | keys2)

        # 比较共同键的值相似度
        common_keys = keys1 & keys2
        value_similarities = []

        for key in common_keys:
            val1_str = str(dict1[key])
            val2_str = str(dict2[key])
            val_sim = self._text_similarity(val1_str, val2_str)
            value_similarities.append(val_sim)

        value_similarity = (
            sum(value_similarities) / len(value_similarities)
            if value_similarities
            else 0.0
        )

        return (key_similarity + value_similarity) / 2

    def _list_similarity(
        self, list1: List[Dict[str, any]], list2: List[Dict[str, any]]
    ) -> float:
        """计算列表相似度"""
        if not list1 and not list2:
            return 1.0
        if not list1 or not list2:
            return 0.0

        # 计算每个元素的最佳匹配
        similarities = []

        for item1 in list1:
            # 将字典转换为文本进行比较
            item1_text = ""
            if isinstance(item1, dict):
                item1_text = " ".join(str(v) for v in item1.values() if v)
            else:
                item1_text = str(item1)

            best_sim = 0.0
            for item2 in list2:
                item2_text = ""
                if isinstance(item2, dict):
                    item2_text = " ".join(str(v) for v in item2.values() if v)
                else:
                    item2_text = str(item2)

                sim = self._text_similarity(item1_text, item2_text)
                best_sim = max(best_sim, sim)

            similarities.append(best_sim)

        return sum(similarities) / len(similarities) if similarities else 0.0


class TestCasePrioritizer:
    """测试用例优先级排序器

    根据多种因素对测试用例进行优先级排序。
    """

    def __init__(self):
        self.priority_factors = {
            "quality_score": 0.3,
            "test_type": 0.25,
            "coverage": 0.2,
            "complexity": 0.15,
            "business_value": 0.1,
        }

    def prioritize(
        self, test_cases: List[TestCase], quality_reports: List[QualityReport]
    ) -> List[Tuple[TestCase, float]]:
        """对测试用例进行优先级排序

        Args:
            test_cases: 测试用例列表
            quality_reports: 质量报告列表

        Returns:
            排序后的测试用例和优先级分数列表
        """
        # 创建质量报告映射
        quality_map = {report.test_case_id: report for report in quality_reports}

        prioritized_cases = []

        for test_case in test_cases:
            case_id = test_case.id or "unknown"
            quality_report = quality_map.get(case_id)

            priority_score = self._calculate_priority_score(test_case, quality_report)
            prioritized_cases.append((test_case, priority_score))

        # 按优先级分数降序排序
        prioritized_cases.sort(key=lambda x: x[1], reverse=True)

        return prioritized_cases

    def _calculate_priority_score(
        self, test_case: TestCase, quality_report: Optional[QualityReport]
    ) -> float:
        """计算优先级分数"""
        score = 0.0

        # 质量分数因子
        if quality_report:
            quality_factor = quality_report.overall_score / 100
            score += quality_factor * self.priority_factors["quality_score"]

        # 测试类型因子
        type_scores = {
            TestCaseType.SECURITY: 1.0,
            TestCaseType.ERROR: 0.8,
            TestCaseType.NORMAL: 0.6,
            TestCaseType.EDGE: 0.4,
        }
        type_factor = type_scores.get(test_case.type, 0.5)
        score += type_factor * self.priority_factors["test_type"]

        # 覆盖度因子
        coverage_factor = self._calculate_coverage_factor(test_case)
        score += coverage_factor * self.priority_factors["coverage"]

        # 复杂度因子（复杂度越高，优先级越高）
        complexity_factor = self._calculate_complexity_factor(test_case)
        score += complexity_factor * self.priority_factors["complexity"]

        # 业务价值因子
        business_factor = self._calculate_business_value_factor(test_case)
        score += business_factor * self.priority_factors["business_value"]

        # 应用优先级调整
        if test_case.priority:
            # 优先级1-5，1最高，转换为0.8-1.0的乘数
            priority_multiplier = 1.2 - (test_case.priority * 0.1)
            score *= priority_multiplier

        return score

    def _calculate_coverage_factor(self, test_case: TestCase) -> float:
        """计算覆盖度因子"""
        coverage_score = 0.0

        # 测试步骤覆盖度
        step_count = len(test_case.test_steps) if test_case.test_steps else 0
        coverage_score += min(1.0, step_count / 5) * 0.4

        # 测试数据覆盖度
        if test_case.test_data:
            param_count = sum(
                len(v) if isinstance(v, (list, dict)) else 1
                for v in test_case.test_data.values()
                if v
            )
            coverage_score += min(1.0, param_count / 3) * 0.3

        # 响应验证覆盖度
        if test_case.expected_response:
            coverage_score += 0.3

        return coverage_score

    def _calculate_complexity_factor(self, test_case: TestCase) -> float:
        """计算复杂度因子"""
        complexity_score = 0.0

        # 测试数据复杂度
        if test_case.test_data:
            test_data_str = str(test_case.test_data)
            complexity_score += min(1.0, len(test_data_str) / 500) * 0.4

        # 测试步骤复杂度
        if test_case.test_steps:
            step_complexity = sum(len(step) for step in test_case.test_steps)
            complexity_score += min(1.0, step_complexity / 200) * 0.3

        # 描述复杂度
        if test_case.description:
            complexity_score += min(1.0, len(test_case.description) / 100) * 0.3

        return complexity_score

    def _calculate_business_value_factor(self, test_case: TestCase) -> float:
        """计算业务价值因子"""
        # 基于测试用例的标签和描述判断业务价值
        value_keywords = {
            "high": ["核心", "关键", "重要", "主要", "core", "critical", "important", "main"],
            "medium": ["常用", "普通", "common", "normal", "regular"],
            "low": ["边缘", "次要", "edge", "minor", "secondary"],
        }

        text_content = f"{test_case.name} {test_case.description}".lower()

        for value_level, keywords in value_keywords.items():
            if any(keyword in text_content for keyword in keywords):
                if value_level == "high":
                    return 1.0
                elif value_level == "medium":
                    return 0.6
                elif value_level == "low":
                    return 0.3

        # 默认中等业务价值
        return 0.5


class QualityController:
    """质量控制器

    统一管理测试用例的质量分析、去重和优先级排序。
    """

    def __init__(
        self, similarity_threshold: float = 0.8, min_quality_threshold: float = 60.0
    ):
        self.analyzer = TestCaseQualityAnalyzer()
        self.deduplicator = TestCaseDeduplicator(similarity_threshold)
        self.prioritizer = TestCasePrioritizer()
        self.min_quality_threshold = min_quality_threshold

    def process_test_cases(
        self, test_cases: List[TestCase]
    ) -> Tuple[List[TestCase], List[QualityReport], Dict[str, any]]:
        """处理测试用例

        Args:
            test_cases: 原始测试用例列表

        Returns:
            (优化后的测试用例列表, 质量报告列表, 处理统计信息)
        """
        # 1. 质量分析
        quality_reports = []
        for test_case in test_cases:
            report = self.analyzer.analyze(test_case)
            quality_reports.append(report)

        # 2. 去重处理
        duplicates = self.deduplicator.find_duplicates(test_cases)

        # 更新质量报告中的重复信息
        for original_id, duplicate_ids in duplicates.items():
            for report in quality_reports:
                if report.test_case_id in duplicate_ids:
                    report.is_duplicate = True
                    report.duplicate_of = original_id

        # 3. 过滤低质量和重复用例
        filtered_cases = []
        filtered_reports = []

        for test_case, report in zip(test_cases, quality_reports):
            # 跳过重复用例
            if report.is_duplicate:
                continue

            # 跳过低质量用例
            if report.overall_score < self.min_quality_threshold:
                continue

            filtered_cases.append(test_case)
            filtered_reports.append(report)

        # 4. 优先级排序
        prioritized_cases = self.prioritizer.prioritize(
            filtered_cases, filtered_reports
        )

        # 更新测试用例的优先级
        final_cases = []
        for i, (test_case, priority_score) in enumerate(prioritized_cases):
            # 根据排序位置和质量报告调整优先级
            case_id = test_case.id or f"case_{i}"
            quality_report = next(
                (r for r in filtered_reports if r.test_case_id == case_id), None
            )

            if quality_report and quality_report.priority_adjustment != 0:
                current_priority = test_case.priority or 3
                new_priority = max(
                    1, min(5, current_priority + quality_report.priority_adjustment)
                )
                test_case.priority = new_priority

            final_cases.append(test_case)

        # 5. 生成处理统计
        stats = {
            "original_count": len(test_cases),
            "duplicate_count": sum(len(dups) for dups in duplicates.values()),
            "low_quality_count": sum(
                1
                for report in quality_reports
                if report.overall_score < self.min_quality_threshold
                and not report.is_duplicate
            ),
            "final_count": len(final_cases),
            "quality_distribution": self._calculate_quality_distribution(
                filtered_reports
            ),
            "average_quality_score": sum(r.overall_score for r in filtered_reports)
            / len(filtered_reports)
            if filtered_reports
            else 0,
            "duplicates": duplicates,
        }

        return final_cases, quality_reports, stats

    def _calculate_quality_distribution(
        self, reports: List[QualityReport]
    ) -> Dict[str, int]:
        """计算质量分布"""
        distribution = {level.value: 0 for level in QualityLevel}

        for report in reports:
            distribution[report.quality_level.value] += 1

        return distribution

    def generate_quality_summary(
        self, reports: List[QualityReport], stats: Dict
    ) -> str:
        """生成质量摘要报告"""
        summary_parts = [
            f"## 测试用例质量控制报告",
            f"",
            f"### 处理统计",
            f"- 原始用例数量: {stats['original_count']}",
            f"- 重复用例数量: {stats['duplicate_count']}",
            f"- 低质量用例数量: {stats['low_quality_count']}",
            f"- 最终用例数量: {stats['final_count']}",
            f"- 平均质量分数: {stats['average_quality_score']:.1f}",
            f"",
            f"### 质量分布",
        ]

        for level, count in stats["quality_distribution"].items():
            summary_parts.append(f"- {level.title()}: {count}")

        # 添加主要问题和建议
        all_issues = []
        all_suggestions = []

        for report in reports:
            all_issues.extend(report.issues)
            all_suggestions.extend(report.suggestions)

        if all_issues:
            issue_counts = Counter(all_issues)
            summary_parts.extend([f"", f"### 主要问题"])
            for issue, count in issue_counts.most_common(5):
                summary_parts.append(f"- {issue} ({count}次)")

        if all_suggestions:
            suggestion_counts = Counter(all_suggestions)
            summary_parts.extend([f"", f"### 改进建议"])
            for suggestion, count in suggestion_counts.most_common(5):
                summary_parts.append(f"- {suggestion} ({count}次)")

        return "\n".join(summary_parts)
