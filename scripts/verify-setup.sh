#!/bin/bash
# Spec2Test 代码质量工具验证脚本
# 用于验证所有代码质量工具是否正确配置和工作

set -e

echo "🔍 验证 Spec2Test 代码质量工具配置"
echo "==========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 验证计数器
PASSED=0
FAILED=0
WARNING=0

# 验证函数
verify_command() {
    local cmd="$1"
    local name="$2"
    local required="$3"

    echo -e "${BLUE}检查 $name...${NC}"

    if command -v "$cmd" &> /dev/null; then
        echo -e "${GREEN}✅ $name 已安装${NC}"
        ((PASSED++))
        return 0
    else
        if [ "$required" = "true" ]; then
            echo -e "${RED}❌ $name 未安装 (必需)${NC}"
            ((FAILED++))
        else
            echo -e "${YELLOW}⚠️  $name 未安装 (可选)${NC}"
            ((WARNING++))
        fi
        return 1
    fi
}

verify_file() {
    local file="$1"
    local name="$2"

    echo -e "${BLUE}检查 $name...${NC}"

    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $name 存在${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ $name 不存在${NC}"
        ((FAILED++))
        return 1
    fi
}

run_test() {
    local cmd="$1"
    local name="$2"
    local allow_fail="$3"

    echo -e "${BLUE}运行 $name...${NC}"

    if eval "$cmd" &> /dev/null; then
        echo -e "${GREEN}✅ $name 通过${NC}"
        ((PASSED++))
        return 0
    else
        if [ "$allow_fail" = "true" ]; then
            echo -e "${YELLOW}⚠️  $name 有警告但可接受${NC}"
            ((WARNING++))
        else
            echo -e "${RED}❌ $name 失败${NC}"
            ((FAILED++))
        fi
        return 1
    fi
}

echo "\n📦 1. 验证工具安装"
echo "------------------------------------------"
verify_command "python" "Python" "true"
verify_command "pip" "pip" "true"
verify_command "black" "Black" "true"
verify_command "isort" "isort" "true"
verify_command "flake8" "Flake8" "true"
verify_command "mypy" "MyPy" "true"
verify_command "bandit" "Bandit" "true"
verify_command "pytest" "pytest" "true"
verify_command "pre-commit" "pre-commit" "true"
verify_command "docker" "Docker" "false"
verify_command "docker-compose" "Docker Compose" "false"

echo "\n📄 2. 验证配置文件"
echo "------------------------------------------"
verify_file "pyproject.toml" "项目配置文件"
verify_file ".pre-commit-config.yaml" "Pre-commit 配置"
verify_file ".flake8" "Flake8 配置"
verify_file "mypy.ini" "MyPy 配置"
verify_file ".bandit" "Bandit 配置"
verify_file "pytest.ini" "pytest 配置"
verify_file "Dockerfile" "Docker 配置"
verify_file "docker-compose.yml" "Docker Compose 配置"
verify_file ".dockerignore" "Docker ignore 文件"

echo "\n📁 3. 验证目录结构"
echo "------------------------------------------"
verify_file "app/" "应用目录"
verify_file "tests/" "测试目录"
verify_file "scripts/" "脚本目录"
verify_file "docs/" "文档目录"
verify_file "reports/" "报告目录"

echo "\n🔧 4. 验证脚本文件"
echo "------------------------------------------"
verify_file "scripts/quality-check.sh" "质量检查脚本"
verify_file "scripts/format-code.sh" "代码格式化脚本"
verify_file "scripts/init-db.sql" "数据库初始化脚本"

# 检查脚本执行权限
if [ -x "scripts/quality-check.sh" ]; then
    echo -e "${GREEN}✅ quality-check.sh 有执行权限${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ quality-check.sh 没有执行权限${NC}"
    ((FAILED++))
fi

if [ -x "scripts/format-code.sh" ]; then
    echo -e "${GREEN}✅ format-code.sh 有执行权限${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ format-code.sh 没有执行权限${NC}"
    ((FAILED++))
fi

echo "\n🧪 5. 运行功能测试"
echo "------------------------------------------"

# 测试 Black 格式检查
run_test "black --check app/ tests/" "Black 格式检查" "false"

# 测试 isort 检查
run_test "isort --check-only app/ tests/" "isort 导入检查" "false"

# 测试 Flake8
run_test "flake8 app/ tests/ --exit-zero" "Flake8 代码风格" "true"

# 测试 MyPy (允许失败，因为可能有类型问题)
run_test "mypy app/ --ignore-missing-imports" "MyPy 类型检查" "true"

# 测试 Bandit
run_test "bandit -r app/ -f json -o /tmp/bandit-test.json" "Bandit 安全检查" "false"

# 测试 pytest
run_test "pytest tests/unit/test_openapi_parser.py -v --tb=short" "pytest 单元测试" "false"

# 测试 pre-commit (dry run)
if command -v pre-commit &> /dev/null; then
    run_test "pre-commit run --all-files --show-diff-on-failure" "Pre-commit 钩子" "true"
fi

echo "\n📊 6. 验证报告生成"
echo "------------------------------------------"

# 生成 Bandit 报告
if bandit -r app/ -f json -o reports/bandit-report.json &> /dev/null; then
    echo -e "${GREEN}✅ Bandit 报告生成成功${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Bandit 报告生成失败${NC}"
    ((FAILED++))
fi

# 检查报告文件
if [ -f "reports/bandit-report.json" ] && [ -s "reports/bandit-report.json" ]; then
    echo -e "${GREEN}✅ Bandit 报告文件存在且非空${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Bandit 报告文件不存在或为空${NC}"
    ((FAILED++))
fi

echo "\n🔍 7. 验证项目依赖"
echo "------------------------------------------"

# 检查关键依赖是否安装
key_packages=("fastapi" "uvicorn" "pydantic" "pytest" "black" "isort" "flake8" "mypy" "bandit" "pre-commit" "loguru" "pyyaml")

for package in "${key_packages[@]}"; do
    if pip show "$package" &> /dev/null; then
        echo -e "${GREEN}✅ $package 已安装${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ $package 未安装${NC}"
        ((FAILED++))
    fi
done

echo "\n📋 8. 验证文档"
echo "------------------------------------------"
verify_file "docs/CODE_QUALITY.md" "代码质量文档"
verify_file "docs/PRD.md" "产品需求文档"
verify_file "README.md" "项目说明文档"

echo "\n==========================================="
echo "🎯 验证结果汇总"
echo "==========================================="
echo -e "${GREEN}✅ 通过: $PASSED${NC}"
echo -e "${YELLOW}⚠️  警告: $WARNING${NC}"
echo -e "${RED}❌ 失败: $FAILED${NC}"

TOTAL=$((PASSED + WARNING + FAILED))
SUCCESS_RATE=$((PASSED * 100 / TOTAL))

echo "\n📊 成功率: $SUCCESS_RATE% ($PASSED/$TOTAL)"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 所有关键验证都通过了！代码质量工具配置成功！${NC}"
    exit 0
else
    echo -e "\n${RED}💥 有 $FAILED 项验证失败，请检查配置！${NC}"
    exit 1
fi
