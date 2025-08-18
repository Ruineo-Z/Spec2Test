#!/bin/bash
# Ollama模型初始化脚本
# 下载和配置本地LLM模型

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
OLLAMA_HOST="http://localhost:11434"
DEFAULT_MODEL="llama3.1:8b"
MODELS_TO_INSTALL=()

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 显示帮助信息
show_help() {
    cat << EOF
Ollama模型初始化脚本

用法: $0 [选项]

选项:
    --host HOST             Ollama服务地址 [默认: http://localhost:11434]
    --model MODEL           要安装的模型 [默认: llama3.1:8b]
    --models MODEL1,MODEL2  要安装的多个模型（逗号分隔）
    --list-available        列出可用模型
    --list-installed        列出已安装模型
    --remove MODEL          删除指定模型
    -h, --help              显示此帮助信息

推荐模型:
    llama3.1:8b            # 8B参数，平衡性能和质量
    llama3.1:70b           # 70B参数，高质量但需要更多资源
    codellama:7b           # 代码生成专用模型
    mistral:7b             # 轻量级高性能模型
    qwen2:7b               # 中文友好模型

示例:
    $0                                          # 安装默认模型
    $0 --model llama3.1:70b                     # 安装指定模型
    $0 --models llama3.1:8b,codellama:7b        # 安装多个模型
    $0 --list-available                         # 列出可用模型
    $0 --remove llama3.1:8b                     # 删除模型

EOF
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --host)
                OLLAMA_HOST="$2"
                shift 2
                ;;
            --model)
                MODELS_TO_INSTALL=("$2")
                shift 2
                ;;
            --models)
                IFS=',' read -ra MODELS_TO_INSTALL <<< "$2"
                shift 2
                ;;
            --list-available)
                list_available_models
                exit 0
                ;;
            --list-installed)
                list_installed_models
                exit 0
                ;;
            --remove)
                remove_model "$2"
                exit 0
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                print_message $RED "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 如果没有指定模型，使用默认模型
    if [[ ${#MODELS_TO_INSTALL[@]} -eq 0 ]]; then
        MODELS_TO_INSTALL=("$DEFAULT_MODEL")
    fi
}

# 检查Ollama服务状态
check_ollama_service() {
    print_message $YELLOW "🔍 检查Ollama服务状态..."
    
    local max_retries=30
    local retry_count=0
    
    while [[ $retry_count -lt $max_retries ]]; do
        if curl -s "$OLLAMA_HOST/api/tags" > /dev/null 2>&1; then
            print_message $GREEN "✅ Ollama服务运行正常"
            return 0
        fi
        
        print_message $BLUE "⏳ 等待Ollama服务启动... ($((retry_count + 1))/$max_retries)"
        sleep 2
        retry_count=$((retry_count + 1))
    done
    
    print_message $RED "❌ Ollama服务不可用，请确保服务已启动"
    print_message $YELLOW "提示: 运行 'docker-compose up ollama' 启动Ollama服务"
    exit 1
}

# 列出可用模型
list_available_models() {
    print_message $BLUE "📋 可用模型列表:"
    print_message $GREEN "
代码生成模型:
  • codellama:7b          - 7B参数代码生成模型
  • codellama:13b         - 13B参数代码生成模型
  • codellama:34b         - 34B参数代码生成模型

通用语言模型:
  • llama3.1:8b           - 8B参数通用模型（推荐）
  • llama3.1:70b          - 70B参数高质量模型
  • llama3.1:405b         - 405B参数顶级模型

轻量级模型:
  • mistral:7b            - 7B参数高效模型
  • gemma:7b              - Google 7B参数模型
  • qwen2:7b              - 阿里7B参数中文友好模型

专用模型:
  • llava:7b              - 多模态视觉语言模型
  • dolphin-mistral:7b    - 对话优化模型
"
}

# 列出已安装模型
list_installed_models() {
    print_message $YELLOW "📋 检查已安装模型..."
    
    if ! check_ollama_service_quiet; then
        print_message $RED "❌ Ollama服务不可用"
        exit 1
    fi
    
    local response=$(curl -s "$OLLAMA_HOST/api/tags")
    local models=$(echo "$response" | jq -r '.models[]?.name // empty' 2>/dev/null || echo "")
    
    if [[ -n "$models" ]]; then
        print_message $GREEN "✅ 已安装的模型:"
        echo "$models" | while read -r model; do
            if [[ -n "$model" ]]; then
                print_message $BLUE "  • $model"
            fi
        done
    else
        print_message $YELLOW "⚠️ 没有已安装的模型"
    fi
}

# 静默检查Ollama服务
check_ollama_service_quiet() {
    curl -s "$OLLAMA_HOST/api/tags" > /dev/null 2>&1
}

# 安装模型
install_model() {
    local model=$1
    print_message $YELLOW "📥 安装模型: $model"
    
    # 检查模型是否已安装
    local installed_models=$(curl -s "$OLLAMA_HOST/api/tags" | jq -r '.models[]?.name // empty' 2>/dev/null || echo "")
    if echo "$installed_models" | grep -q "^$model$"; then
        print_message $GREEN "✅ 模型 $model 已安装，跳过"
        return 0
    fi
    
    # 安装模型
    print_message $BLUE "⬇️ 开始下载模型 $model（这可能需要几分钟到几小时）..."
    
    if curl -X POST "$OLLAMA_HOST/api/pull" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"$model\"}" \
        --progress-bar \
        -o /dev/null; then
        print_message $GREEN "✅ 模型 $model 安装成功"
    else
        print_message $RED "❌ 模型 $model 安装失败"
        return 1
    fi
}

# 删除模型
remove_model() {
    local model=$1
    print_message $YELLOW "🗑️ 删除模型: $model"
    
    if curl -X DELETE "$OLLAMA_HOST/api/delete" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"$model\"}"; then
        print_message $GREEN "✅ 模型 $model 删除成功"
    else
        print_message $RED "❌ 模型 $model 删除失败"
        return 1
    fi
}

# 测试模型
test_model() {
    local model=$1
    print_message $YELLOW "🧪 测试模型: $model"
    
    local test_prompt="Hello, please respond with 'Model is working correctly.'"
    local response=$(curl -s -X POST "$OLLAMA_HOST/api/generate" \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"$model\",\"prompt\":\"$test_prompt\",\"stream\":false}")
    
    if echo "$response" | jq -e '.response' > /dev/null 2>&1; then
        local model_response=$(echo "$response" | jq -r '.response')
        print_message $GREEN "✅ 模型 $model 测试成功"
        print_message $BLUE "📝 模型响应: $model_response"
    else
        print_message $RED "❌ 模型 $model 测试失败"
        return 1
    fi
}

# 显示使用建议
show_usage_tips() {
    print_message $BLUE "💡 使用建议:"
    print_message $GREEN "
1. 模型选择建议:
   • 开发测试: llama3.1:8b (平衡性能和质量)
   • 代码生成: codellama:7b (专门优化代码任务)
   • 生产环境: llama3.1:70b (高质量输出)

2. 性能优化:
   • 确保有足够的内存和存储空间
   • 考虑使用GPU加速（需要NVIDIA GPU）
   • 定期清理不使用的模型

3. 配置应用:
   • 在.env文件中设置 DEFAULT_LLM_PROVIDER=ollama
   • 设置 OLLAMA_BASE_URL=$OLLAMA_HOST
   • 设置 OLLAMA_MODEL=已安装的模型名称
"
}

# 主函数
main() {
    print_message $BLUE "🦙 Ollama模型初始化脚本"
    print_message $BLUE "=========================="
    
    parse_args "$@"
    
    print_message $BLUE "🔧 配置信息:"
    print_message $GREEN "  • Ollama地址: $OLLAMA_HOST"
    print_message $GREEN "  • 要安装的模型: ${MODELS_TO_INSTALL[*]}"
    
    check_ollama_service
    
    # 安装模型
    local success_count=0
    local total_count=${#MODELS_TO_INSTALL[@]}
    
    for model in "${MODELS_TO_INSTALL[@]}"; do
        if install_model "$model"; then
            success_count=$((success_count + 1))
            test_model "$model"
        fi
    done
    
    print_message $BLUE "📊 安装结果: $success_count/$total_count 成功"
    
    if [[ $success_count -eq $total_count ]]; then
        print_message $GREEN "🎉 所有模型安装完成！"
        list_installed_models
        show_usage_tips
    else
        print_message $YELLOW "⚠️ 部分模型安装失败，请检查日志"
        exit 1
    fi
}

# 检查依赖
check_dependencies() {
    if ! command -v curl &> /dev/null; then
        print_message $RED "❌ curl未安装"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        print_message $YELLOW "⚠️ jq未安装，某些功能可能不可用"
    fi
}

# 检查依赖并执行主函数
check_dependencies
main "$@"
