#!/bin/bash
# NEMT Simulator - 部署脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 配置
NAMESPACE="${NAMESPACE:-nemt}"
RELEASE_NAME="${RELEASE_NAME:-nemt}"
CHART_PATH="${CHART_PATH:-./k8s/nemt}"
VALUES_FILE="${VALUES_FILE:-}"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."

    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl 未安装"
        exit 1
    fi

    if ! command -v helm &> /dev/null; then
        log_error "helm 未安装"
        exit 1
    fi

    log_info "依赖检查完成"
}

# 创建命名空间
create_namespace() {
    log_info "创建命名空间: ${NAMESPACE}"
    kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
}

# 部署
deploy() {
    local image_tag="${1:-latest}"
    log_info "部署 NEMT (tag: ${image_tag})"

    local cmd="helm upgrade --install ${RELEASE_NAME} ${CHART_PATH} \
        --namespace ${NAMESPACE} \
        --create-namespace \
        --set image.tag=${image_tag}"

    if [ -n "${VALUES_FILE}" ]; then
        cmd="${cmd} --values ${VALUES_FILE}"
    fi

    cmd="${cmd} --wait --timeout 10m"

    eval ${cmd}

    log_info "部署完成"
}

# 查看状态
status() {
    log_info "查看部署状态..."

    echo "=== Pods ==="
    kubectl get pods -n ${NAMESPACE}

    echo ""
    echo "=== Services ==="
    kubectl get svc -n ${NAMESPACE}

    echo ""
    echo "=== Pod Logs ==="
    kubectl logs -n ${NAMESPACE} -l app=nemt --tail=50
}

# 回滚
rollback() {
    local revision="${1}"
    if [ -z "${revision}" ]; then
        log_error "请指定要回滚的版本号"
        exit 1
    fi

    log_info "回滚到版本 ${revision}"
    helm rollback ${RELEASE_NAME} ${revision} -n ${NAMESPACE}
    log_info "回滚完成"
}

# 卸载
uninstall() {
    log_warn "即将卸载 NEMT..."
    read -p "确认? (y/N): " confirm

    if [ "${confirm}" = "y" ]; then
        helm uninstall ${RELEASE_NAME} -n ${NAMESPACE}
        kubectl delete namespace ${NAMESPACE}
        log_info "卸载完成"
    else
        log_info "取消卸载"
    fi
}

# 显示帮助
help() {
    echo "NEMT Simulator 部署脚本"
    echo ""
    echo "用法: $0 <命令> [参数]"
    echo ""
    echo "命令:"
    echo "  deploy [tag]     部署 (默认: latest)"
    echo "  status           查看状态"
    echo "  rollback <rev>   回滚到指定版本"
    echo "  uninstall        卸载"
    echo "  help             显示帮助"
    echo ""
    echo "环境变量:"
    echo "  NAMESPACE        Kubernetes 命名空间 (默认: nemt)"
    echo "  RELEASE_NAME     Helm 发布名称 (默认: nemt)"
    echo "  CHART_PATH       Chart 路径 (默认: ./k8s/nemt)"
    echo "  VALUES_FILE      Values 文件"
}

# 主入口
case "${1:-help}" in
    deploy)
        check_dependencies
        create_namespace
        deploy "${2}"
        ;;
    status)
        status
        ;;
    rollback)
        rollback "${2}"
        ;;
    uninstall)
        uninstall
        ;;
    help|*)
        help
        ;;
esac
