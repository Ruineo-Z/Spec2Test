#!/bin/bash
# Spec2Test Docker停止脚本
# 停止和清理Docker服务

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
REMOVE_VOLUMES=false
REMOVE_IMAGES=false
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
Spec2Test Docker停止脚本

用法: $0 [选项]

选项:
    -e, --environment ENV    部署环境 (development|staging|production) [默认: production]
    -f, --compose-file FILE  指定docker-compose文件
    --env-file FILE          指定环境变量文件
    --remove-volumes         删除数据卷（危险操作！）
    --remove-images          删除镜像
    --services SERVICES      指定要停止的服务（逗号分隔）
    -h, --help              显示此帮助信息

示例:
    $0                                          # 停止生产环境
    $0 -e development                           # 停止开发环境
    $0 --services app,worker                    # 只停止指定服务
    $0 --remove-volumes                         # 停止并删除数据卷

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
            --remove-volumes)
                REMOVE_VOLUMES=true
                shift
                ;;
            --remove-images)
                REMOVE_IMAGES=true
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
    
    print_message $BLUE "🛑 停止环境: $ENVIRONMENT"
    print_message $BLUE "📄 Compose文件: $COMPOSE_FILE"
}

# 停止服务
stop_services() {
    print_message $YELLOW "🛑 停止服务..."
    
    cd "$DOCKER_DIR"
    
    # 构建docker-compose命令
    local compose_cmd="docker-compose -f $COMPOSE_FILE"
    
    if [[ -f "${PROJECT_ROOT}/${ENV_FILE}" ]]; then
        compose_cmd="$compose_cmd --env-file ${PROJECT_ROOT}/${ENV_FILE}"
    fi
    
    if [[ -n "$SERVICES" ]]; then
        # 停止指定服务
        compose_cmd="$compose_cmd stop $SERVICES"
        print_message $BLUE "执行命令: $compose_cmd"
        eval $compose_cmd
    else
        # 停止所有服务
        if [[ "$REMOVE_VOLUMES" == true ]]; then
            compose_cmd="$compose_cmd down -v"
            print_message $YELLOW "⚠️ 将删除数据卷！"
        else
            compose_cmd="$compose_cmd down"
        fi
        
        print_message $BLUE "执行命令: $compose_cmd"
        eval $compose_cmd
    fi
    
    print_message $GREEN "✅ 服务停止完成"
}

# 清理镜像
cleanup_images() {
    if [[ "$REMOVE_IMAGES" == true ]]; then
        print_message $YELLOW "🗑️ 清理镜像..."
        
        cd "$DOCKER_DIR"
        
        local compose_cmd="docker-compose -f $COMPOSE_FILE"
        if [[ -f "${PROJECT_ROOT}/${ENV_FILE}" ]]; then
            compose_cmd="$compose_cmd --env-file ${PROJECT_ROOT}/${ENV_FILE}"
        fi
        
        # 删除镜像
        eval "$compose_cmd down --rmi all"
        
        print_message $GREEN "✅ 镜像清理完成"
    fi
}

# 显示清理后状态
show_cleanup_status() {
    print_message $BLUE "📊 清理后状态:"
    
    # 显示运行中的容器
    local running_containers=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep spec2test || true)
    if [[ -n "$running_containers" ]]; then
        print_message $YELLOW "⚠️ 仍在运行的Spec2Test容器:"
        echo "$running_containers"
    else
        print_message $GREEN "✅ 没有运行中的Spec2Test容器"
    fi
    
    # 显示数据卷
    local volumes=$(docker volume ls --format "table {{.Name}}" | grep spec2test || true)
    if [[ -n "$volumes" ]]; then
        print_message $BLUE "💾 保留的数据卷:"
        echo "$volumes"
    fi
    
    # 显示镜像
    local images=$(docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep spec2test || true)
    if [[ -n "$images" ]]; then
        print_message $BLUE "🖼️ 保留的镜像:"
        echo "$images"
    fi
}

# 主函数
main() {
    print_message $BLUE "🐳 Spec2Test Docker停止脚本"
    print_message $BLUE "================================"
    
    parse_args "$@"
    setup_environment
    
    # 确认危险操作
    if [[ "$REMOVE_VOLUMES" == true ]]; then
        print_message $RED "⚠️ 警告：即将删除所有数据卷，这将导致数据丢失！"
        read -p "确认继续？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_message $YELLOW "操作已取消"
            exit 0
        fi
    fi
    
    stop_services
    cleanup_images
    show_cleanup_status
    
    print_message $GREEN "🎉 停止完成！"
}

# 执行主函数
main "$@"
