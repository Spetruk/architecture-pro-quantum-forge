#!/bin/bash

# Управляющий скрипт для системы автоматического обновления RAG индекса
# Предоставляет удобные команды для управления системой

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_ENV="$SCRIPT_DIR/.venv/bin/python"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка Python окружения
check_python_env() {
    if [ ! -f "$PYTHON_ENV" ]; then
        log_warning "Python виртуальное окружение не найдено. Используется системный Python."
        PYTHON_ENV="python3"
    fi
}

# Проверка зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 не найден в системе"
        exit 1
    fi
    
    # Проверка основных модулей
    $PYTHON_ENV -c "import yaml, langchain_text_splitters, langchain_huggingface, langchain_chroma" 2>/dev/null
    if [ $? -ne 0 ]; then
        log_error "Необходимые Python модули не установлены. Выполните: pip install -r requirements.txt"
        exit 1
    fi
    
    log_success "Все зависимости установлены"
}

# Установка cron задачи
install_cron() {
    log_info "Установка cron задачи..."
    cd "$SCRIPT_DIR"
    $PYTHON_ENV scheduler.py install-cron
    
    if [ $? -eq 0 ]; then
        log_success "Cron задача установлена"
        log_info "Проверить установленные задачи: crontab -l"
    else
        log_error "Ошибка установки cron задачи"
        exit 1
    fi
}

# Удаление cron задачи
remove_cron() {
    log_info "Удаление cron задачи..."
    cd "$SCRIPT_DIR"
    $PYTHON_ENV scheduler.py remove-cron
    
    if [ $? -eq 0 ]; then
        log_success "Cron задача удалена"
    else
        log_error "Ошибка удаления cron задачи"
        exit 1
    fi
}

# Показать предлагаемую cron запись
show_cron() {
    log_info "Предлагаемая cron запись:"
    cd "$SCRIPT_DIR"
    $PYTHON_ENV scheduler.py show-cron
}

# Разовое обновление
run_once() {
    log_info "Запуск разового обновления индекса..."
    cd "$SCRIPT_DIR"
    $PYTHON_ENV update_index.py
    
    if [ $? -eq 0 ]; then
        log_success "Обновление выполнено успешно"
    else
        log_error "Ошибка при обновлении"
        exit 1
    fi
}

# Интервальный режим
start_interval() {
    log_info "Запуск в интервальном режиме..."
    log_warning "Для остановки нажмите Ctrl+C"
    cd "$SCRIPT_DIR"
    $PYTHON_ENV scheduler.py start-interval
}

# Создание тестовых данных
create_test_data() {
    log_info "Создание тестовых документов..."
    cd "$SCRIPT_DIR"
    $PYTHON_ENV test_auto_update.py create-samples
    
    if [ $? -eq 0 ]; then
        log_success "Тестовые документы созданы"
    else
        log_error "Ошибка создания тестовых документов"
        exit 1
    fi
}

# Комплексное тестирование
run_comprehensive_test() {
    log_info "Запуск комплексного тестирования..."
    cd "$SCRIPT_DIR"
    $PYTHON_ENV test_auto_update.py run-comprehensive
    
    if [ $? -eq 0 ]; then
        log_success "Тестирование завершено"
    else
        log_error "Ошибка при тестировании"
        exit 1
    fi
}

# Просмотр логов
view_logs() {
    log_info "Последние записи из лога обновлений:"
    if [ -f "$SCRIPT_DIR/logs/auto_update.log" ]; then
        tail -n 50 "$SCRIPT_DIR/logs/auto_update.log"
    else
        log_warning "Файл лога не найден: $SCRIPT_DIR/logs/auto_update.log"
    fi
}

# Просмотр статуса
show_status() {
    log_info "Статус системы автоматического обновления:"
    echo ""
    
    # Проверка cron
    if crontab -l 2>/dev/null | grep -q "update_index.py"; then
        log_success "Cron задача установлена"
    else
        log_warning "Cron задача не установлена"
    fi
    
    # Проверка конфигурации
    if [ -f "$SCRIPT_DIR/auto_update_config.yaml" ]; then
        log_success "Конфигурационный файл найден"
    else
        log_error "Конфигурационный файл не найден"
    fi
    
    # Проверка источников данных
    if [ -d "$SCRIPT_DIR/data_sources/incoming" ]; then
        file_count=$(find "$SCRIPT_DIR/data_sources/incoming" -name "*.txt" -o -name "*.md" | wc -l)
        log_info "Файлов в папке источников: $file_count"
    else
        log_warning "Папка источников данных не найдена"
    fi
    
    # Проверка индекса
    if [ -d "$SCRIPT_DIR/chroma_db" ]; then
        log_success "Векторная БД найдена"
    else
        log_warning "Векторная БД не найдена"
    fi
    
    # Последнее обновление
    if [ -f "$SCRIPT_DIR/logs/last_update_results.json" ]; then
        last_update=$(python3 -c "
import json
try:
    with open('$SCRIPT_DIR/logs/last_update_results.json', 'r') as f:
        data = json.load(f)
        print(f\"Последнее обновление: {data.get('start_time', 'N/A')}\")
        print(f\"Обработано файлов: {data.get('files_processed', 0)}\")
        print(f\"Добавлено чанков: {data.get('chunks_added', 0)}\")
        print(f\"Ошибок: {data.get('errors', 0)}\")
except:
    print('Данные о последнем обновлении недоступны')
")
        echo "$last_update"
    else
        log_warning "Данные о последнем обновлении недоступны"
    fi
}

# Очистка логов
clean_logs() {
    log_info "Очистка старых логов..."
    
    if [ -d "$SCRIPT_DIR/logs" ]; then
        find "$SCRIPT_DIR/logs" -name "*.log.*" -mtime +30 -delete
        > "$SCRIPT_DIR/logs/auto_update.log"
        log_success "Логи очищены"
    else
        log_warning "Папка логов не найдена"
    fi
}

# Справка
show_help() {
    echo "Управляющий скрипт для системы автоматического обновления RAG индекса"
    echo ""
    echo "Использование: $0 [команда]"
    echo ""
    echo "Команды:"
    echo "  install-cron    - Установить задачу в cron для автоматического обновления"
    echo "  remove-cron     - Удалить задачу из cron"
    echo "  show-cron       - Показать предлагаемую cron запись"
    echo "  run-once        - Выполнить разовое обновление индекса"
    echo "  start-interval  - Запустить в интервальном режиме"
    echo "  create-test     - Создать тестовые документы"
    echo "  test            - Запустить комплексное тестирование"
    echo "  status          - Показать статус системы"
    echo "  logs            - Просмотреть последние записи лога"
    echo "  clean-logs      - Очистить старые логи"
    echo "  check-deps      - Проверить зависимости"
    echo "  help            - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 run-once              # Разовое обновление"
    echo "  $0 install-cron          # Установка автоматического обновления"
    echo "  $0 create-test && $0 run-once  # Тест с новыми данными"
}

# Основная логика
main() {
    check_python_env
    
    case "$1" in
        "install-cron")
            check_dependencies
            install_cron
            ;;
        "remove-cron")
            remove_cron
            ;;
        "show-cron")
            show_cron
            ;;
        "run-once")
            check_dependencies
            run_once
            ;;
        "start-interval")
            check_dependencies
            start_interval
            ;;
        "create-test")
            check_dependencies
            create_test_data
            ;;
        "test")
            check_dependencies
            run_comprehensive_test
            ;;
        "status")
            show_status
            ;;
        "logs")
            view_logs
            ;;
        "clean-logs")
            clean_logs
            ;;
        "check-deps")
            check_dependencies
            ;;
        "help"|"--help"|"-h"|"")
            show_help
            ;;
        *)
            log_error "Неизвестная команда: $1"
            show_help
            exit 1
            ;;
    esac
}

# Запуск основной функции
main "$@"
