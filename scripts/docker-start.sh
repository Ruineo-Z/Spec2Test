#!/bin/bash
# Spec2Test Docker启动脚本
# 纯Docker方式启动所有服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_DIR="${PROJECT_ROOT}/docker"

# 默认配置
ENVIRONMENT="production"
COMPOSE_FILE=""
ENV_FILE=""
BUILD_IMAGES=true
PULL_IMAGES=false
DETACHED=true
SERVICES=""

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 显示帮助信息
show_help() {
    cat << EOF
Spec2Test Docker启动脚本

用法: $0 [选项]

选项:
    -e, --environment ENV    部署环境 (development|staging|production) [默认: production]
    -f, --compose-file FILE  指定docker-compose文件
    --env-file FILE          指定环境变量文件
    --no-build              不构建镜像，直接启动
    --pull                  拉取最新镜像
    --foreground            前台运行（不使用-d参数）
    --services SERVICES     指定要启动的服务（逗号分隔）
    -h, --help              显示此帮助信息

示例:
    $0                                          # 生产环境启动
    $0 -e development                           # 开发环境启动
    $0 -e production --no-build                 # 生产环境启动（不构建）
    $0 --services app,postgres,redis           # 只启动指定服务
    $0 --foreground                             # 前台运行查看日志

EOF
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -f|--compose-file)
                COMPOSE_FILE="$2"
                shift 2
                ;;
            --env-file)
                ENV_FILE="$2"
                shift 2
                ;;
            --no-build)
                BUILD_IMAGES=false
                shift
                ;;
            --pull)
                PULL_IMAGES=true
                shift
                ;;
            --foreground)
                DETACHED=false
                shift
                ;;
            --services)
                SERVICES="$2"
                shift 2
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
}

# 设置环境配置
setup_environment() {
    case $ENVIRONMENT in
        development)
            COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.dev.yml}"
            ENV_FILE="${ENV_FILE:-.env.dev}"
            ;;
        staging)
            COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.staging.yml}"
            ENV_FILE="${ENV_FILE:-.env.staging}"
            ;;
        production)
            COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
            ENV_FILE="${ENV_FILE:-.env.prod}"
            ;;
        *)
            print_message $RED "不支持的环境: $ENVIRONMENT"
            exit 1
            ;;
    esac
    
    print_message $BLUE "🚀 启动环境: $ENVIRONMENT"
    print_message $BLUE "📄 Compose文件: $COMPOSE_FILE"
    print_message $BLUE "🔧 环境变量文件: $ENV_FILE"
}

# 检查前置条件
check_prerequisites() {
    print_message $YELLOW "🔍 检查前置条件..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        print_message $RED "❌ Docker未安装"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_message $RED "❌ Docker Compose未安装"
        exit 1
    fi
    
    # 检查Compose文件
    if [[ ! -f "${DOCKER_DIR}/${COMPOSE_FILE}" ]]; then
        print_message $RED "❌ Compose文件不存在: ${DOCKER_DIR}/${COMPOSE_FILE}"
        exit 1
    fi
    
    # 检查环境变量文件
    if [[ ! -f "${PROJECT_ROOT}/${ENV_FILE}" ]]; then
        print_message $YELLOW "⚠️ 环境变量文件不存在: ${PROJECT_ROOT}/${ENV_FILE}"
        print_message $YELLOW "将使用默认环境变量"
    fi
    
    print_message $GREEN "✅ 前置条件检查通过"
}

# 构建镜像
build_images() {
    if [[ "$BUILD_IMAGES" == true ]]; then
        print_message $YELLOW "🏗️ 构建Docker镜像..."
        
        cd "$DOCKER_DIR"
        
        if [[ -f "${PROJECT_ROOT}/${ENV_FILE}" ]]; then
            docker-compose -f "$COMPOSE_FILE" --env-file "${PROJECT_ROOT}/${ENV_FILE}" build
        else
            docker-compose -f "$COMPOSE_FILE" build
        fi
        
        print_message $GREEN "✅ 镜像构建完成"
    fi
}

# 拉取镜像
pull_images() {
    if [[ "$PULL_IMAGES" == true ]]; then
        print_message $YELLOW "📥 拉取最新镜像..."
        
        cd "$DOCKER_DIR"
        
        if [[ -f "${PROJECT_ROOT}/${ENV_FILE}" ]]; then
            docker-compose -f "$COMPOSE_FILE" --env-file "${PROJECT_ROOT}/${ENV_FILE}" pull
        else
            docker-compose -f "$COMPOSE_FILE" pull
        fi
        
        print_message $GREEN "✅ 镜像拉取完成"
    fi
}

# 启动服务
start_services() {
    print_message $YELLOW "🚀 启动服务..."
    
    cd "$DOCKER_DIR"
    
    # 构建docker-compose命令
    local compose_cmd="docker-compose -f $COMPOSE_FILE"
    
    if [[ -f "${PROJECT_ROOT}/${ENV_FILE}" ]]; then
        compose_cmd="$compose_cmd --env-file ${PROJECT_ROOT}/${ENV_FILE}"
    fi
    
    compose_cmd="$compose_cmd up"
    
    if [[ "$DETACHED" == true ]]; then
        compose_cmd="$compose_cmd -d"
    fi
    
    if [[ -n "$SERVICES" ]]; then
        compose_cmd="$compose_cmd $SERVICES"
    fi
    
    print_message $BLUE "执行命令: $compose_cmd"
    
    # 执行启动命令
    eval $compose_cmd
    
    if [[ "$DETACHED" == true ]]; then
        print_message $GREEN "✅ 服务启动完成"
        print_message $BLUE "📋 查看服务状态: docker-compose -f ${COMPOSE_FILE} ps"
        print_message $BLUE "📄 查看日志: docker-compose -f ${COMPOSE_FILE} logs -f"
    fi
}

# 等待服务就绪
wait_for_services() {
    if [[ "$DETACHED" == true ]]; then
        print_message $YELLOW "⏳ 等待服务就绪..."
        
        local max_wait=120
        local wait_time=0
        
        while [[ $wait_time -lt $max_wait ]]; do
            cd "$DOCKER_DIR"
            
            local compose_cmd="docker-compose -f $COMPOSE_FILE"
            if [[ -f "${PROJECT_ROOT}/${ENV_FILE}" ]]; then
                compose_cmd="$compose_cmd --env-file ${PROJECT_ROOT}/${ENV_FILE}"
            fi
            
            # 检查服务状态
            local running_services=$(eval "$compose_cmd ps --services --filter status=running" | wc -l)
            local total_services=$(eval "$compose_cmd config --services" | wc -l)
            
            if [[ -n "$SERVICES" ]]; then
                total_services=$(echo "$SERVICES" | tr ',' '\n' | wc -l)
            fi
            
            print_message $BLUE "📊 运行中的服务: $running_services/$total_services"
            
            if [[ $running_services -eq $total_services ]]; then
                print_message $GREEN "✅ 所有服务已就绪"
                return 0
            fi
            
            sleep 5
            wait_time=$((wait_time + 5))
        done
        
        print_message $YELLOW "⚠️ 服务启动超时，请检查日志"
        return 1
    fi
}

# 显示服务信息
show_service_info() {
    if [[ "$DETACHED" == true ]]; then
        print_message $BLUE "🌐 服务访问信息:"
        
        case $ENVIRONMENT in
            development)
                print_message $GREEN "  • 应用服务: http://localhost:8000"
                print_message $GREEN "  • API文档: http://localhost:8000/docs"
                print_message $GREEN "  • pgAdmin: http://localhost:5050"
                print_message $GREEN "  • Redis Insight: http://localhost:8001"
                print_message $GREEN "  • MailHog: http://localhost:8025"
                ;;
            *)
                print_message $GREEN "  • 应用服务: http://localhost:80"
                print_message $GREEN "  • API文档: http://localhost:80/docs"
                print_message $GREEN "  • Prometheus: http://localhost:9090"
                print_message $GREEN "  • Grafana: http://localhost:3000"
                ;;
        esac
        
        print_message $BLUE "🔧 管理命令:"
        print_message $GREEN "  • 查看状态: docker-compose -f docker/${COMPOSE_FILE} ps"
        print_message $GREEN "  • 查看日志: docker-compose -f docker/${COMPOSE_FILE} logs -f"
        print_message $GREEN "  • 停止服务: docker-compose -f docker/${COMPOSE_FILE} down"
    fi
}

# 主函数
main() {
    print_message $BLUE "🐳 Spec2Test Docker启动脚本"
    print_message $BLUE "================================"
    
    parse_args "$@"
    setup_environment
    check_prerequisites
    pull_images
    build_images
    start_services
    wait_for_services
    show_service_info
    
    print_message $GREEN "🎉 启动完成！"
}

# 执行主函数
main "$@"
