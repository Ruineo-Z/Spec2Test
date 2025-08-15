"""
Pydantic Schema包

包含所有API数据验证Schema定义。
"""

# 文档相关Schema
from .document import (
    DocumentBase,
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentDetail,
    DocumentList,
    DocumentUpload,
    DocumentParseRequest,
    DocumentParseResponse,
    DocumentStats
)

# 测试用例相关Schema
from .test_case import (
    TestCaseBase,
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseResponse,
    TestCaseDetail,
    TestCaseList,
    TestCaseBatch,
    TestCaseExecuteRequest,
    TestCaseStats,
    TestCaseValidation
)

# 测试结果相关Schema
from .test_result import (
    TestResultBase,
    TestResultCreate,
    TestResultUpdate,
    TestResultResponse,
    TestResultDetail,
    TestResultList,
    TestResultSummary,
    TestResultStats,
    TestResultComparison,
    TestResultExport,
    TestResultFilter
)

# 报告相关Schema
from .report import (
    ReportBase,
    ReportCreate,
    ReportUpdate,
    ReportResponse,
    ReportDetail,
    ReportList,
    ReportGenerate,
    ReportStats,
    ReportTemplate,
    ReportExport,
    ReportComparison,
    ReportComparisonResult,
    ReportSchedule,
    ReportFilter
)

__all__ = [
    # 文档Schema
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate", 
    "DocumentResponse",
    "DocumentDetail",
    "DocumentList",
    "DocumentUpload",
    "DocumentParseRequest",
    "DocumentParseResponse",
    "DocumentStats",
    
    # 测试用例Schema
    "TestCaseBase",
    "TestCaseCreate",
    "TestCaseUpdate",
    "TestCaseResponse", 
    "TestCaseDetail",
    "TestCaseList",
    "TestCaseBatch",
    "TestCaseExecuteRequest",
    "TestCaseStats",
    "TestCaseValidation",
    
    # 测试结果Schema
    "TestResultBase",
    "TestResultCreate",
    "TestResultUpdate",
    "TestResultResponse",
    "TestResultDetail", 
    "TestResultList",
    "TestResultSummary",
    "TestResultStats",
    "TestResultComparison",
    "TestResultExport",
    "TestResultFilter",
    
    # 报告Schema
    "ReportBase",
    "ReportCreate",
    "ReportUpdate",
    "ReportResponse",
    "ReportDetail",
    "ReportList", 
    "ReportGenerate",
    "ReportStats",
    "ReportTemplate",
    "ReportExport",
    "ReportComparison",
    "ReportComparisonResult",
    "ReportSchedule",
    "ReportFilter"
]
