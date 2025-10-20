"""
Report Generator Service

Генерация отчётов из markdown шаблонов с подстановкой данных из БД
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from src.models import FunctionalItem, User, ZohoTask, ReportTemplate
import re
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Генератор отчётов из шаблонов"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def generate_report(
        self, 
        template_id: int,
        context: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict] = None
    ) -> str:
        """
        Генерация отчёта из шаблона
        
        Args:
            template_id: ID шаблона
            context: Дополнительный контекст (переопределяет автоданные)
            filters: Фильтры для выборки данных
            
        Returns:
            str: Сгенерированный markdown отчёт
        """
        # Получаем шаблон
        template = self.session.query(ReportTemplate).get(template_id)
        if not template:
            raise ValueError(f"Шаблон с ID {template_id} не найден")
        
        logger.info(f"📋 Генерация отчёта по шаблону: {template.name}")
        
        # Собираем данные
        data_context = self._build_context(filters or {})
        
        # Объединяем с пользовательским контекстом
        if context:
            data_context.update(context)
        
        # Подставляем данные в шаблон
        report_content = self._render_template(template.content, data_context)
        
        logger.info(f"✅ Отчёт сгенерирован: {len(report_content)} символов")
        
        return report_content
    
    def _build_context(self, filters: Dict) -> Dict[str, Any]:
        """Построение контекста данных из БД"""
        context = {}
        
        # Базовые данные
        context['date'] = datetime.now().strftime('%Y-%m-%d')
        context['datetime'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # Данные из functional_items
        query = self.session.query(FunctionalItem)
        
        # Применяем фильтры
        if filters.get('milestone_name'):
            # Если указан milestone - берём задачи из zoho_tasks
            zoho_tasks = self.session.query(ZohoTask).filter(
                ZohoTask.milestone_name == filters['milestone_name']
            ).all()
            context['milestone_name'] = filters['milestone_name']
            context['task_count'] = len(zoho_tasks)
            context['task_table'] = self._format_zoho_tasks_table(zoho_tasks)
            context['task_list'] = self._format_zoho_tasks_list(zoho_tasks)
        
        if filters.get('is_crit'):
            query = query.filter(FunctionalItem.is_crit == True)
        
        if filters.get('is_focus'):
            query = query.filter(FunctionalItem.is_focus == True)
        
        if filters.get('type'):
            if isinstance(filters['type'], list):
                query = query.filter(FunctionalItem.type.in_(filters['type']))
            else:
                query = query.filter(FunctionalItem.type == filters['type'])
        
        if filters.get('responsible_qa_id'):
            query = query.filter(FunctionalItem.responsible_qa_id == filters['responsible_qa_id'])
        
        # Получаем данные
        items = query.all()
        
        context['item_count'] = len(items)
        context['feature_list'] = self._format_functional_items_list(items)
        context['feature_table'] = self._format_functional_items_table(items)
        
        # Статистика по покрытию
        coverage_stats = self._calculate_coverage(items)
        context.update(coverage_stats)
        
        # QA команда
        qa_users = self.session.query(User).filter(
            User.is_active == True,
            User.role.like('%QA%')
        ).all()
        context['qa_team'] = ', '.join([u.name for u in qa_users])
        if qa_users:
            context['qa_lead'] = qa_users[0].name  # Первый QA как лид
        
        # Если указан конкретный QA
        if filters.get('responsible_qa_id'):
            qa = self.session.query(User).get(filters['responsible_qa_id'])
            if qa:
                context['qa_name'] = qa.name
        
        return context
    
    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """Рендеринг шаблона с подстановкой данных"""
        result = template
        
        # Подстановка простых placeholder'ов {{key}}
        for key, value in context.items():
            placeholder = f'{{{{{key}}}}}'
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        
        return result
    
    def _format_functional_items_list(self, items: List[FunctionalItem]) -> str:
        """Форматирование списка функциональных элементов"""
        if not items:
            return "- Нет данных"
        
        lines = []
        for item in items[:20]:  # Ограничение 20 элементов
            crit = '🔴' if item.is_crit else ''
            focus = '🎯' if item.is_focus else ''
            lines.append(f"- {crit}{focus} **{item.functional_id}**: {item.title}")
        
        if len(items) > 20:
            lines.append(f"- ... и ещё {len(items) - 20} элементов")
        
        return '\n'.join(lines)
    
    def _format_functional_items_table(self, items: List[FunctionalItem]) -> str:
        """Форматирование таблицы функциональных элементов"""
        if not items:
            return "| - | - | - | - |\n| Нет данных | | | |"
        
        lines = []
        for item in items[:30]:  # Ограничение 30 элементов
            qa = item.responsible_qa.name if item.responsible_qa else 'Не назначен'
            dev = item.responsible_dev.name if item.responsible_dev else 'Не назначен'
            crit = '✓' if item.is_crit else ''
            
            lines.append(
                f"| {item.functional_id} | {item.title[:50]} | {item.type} | {qa} | {crit} |"
            )
        
        if len(items) > 30:
            lines.append(f"| ... | и ещё {len(items) - 30} элементов | | | |")
        
        return '\n'.join(lines)
    
    def _format_zoho_tasks_table(self, tasks: List[ZohoTask]) -> str:
        """Форматирование таблицы задач Zoho"""
        if not tasks:
            return "| - | - | - | - | - |\n| Нет задач | | | | |"
        
        lines = []
        for task in tasks[:50]:  # Ограничение 50 задач
            lines.append(
                f"| {task.zoho_task_id} | {task.name[:40]} | {task.priority or '-'} | "
                f"{task.owner_name or 'Не назначен'} | {task.status} |"
            )
        
        if len(tasks) > 50:
            lines.append(f"| ... | и ещё {len(tasks) - 50} задач | | | |")
        
        return '\n'.join(lines)
    
    def _format_zoho_tasks_list(self, tasks: List[ZohoTask]) -> str:
        """Форматирование списка задач Zoho"""
        if not tasks:
            return "- Нет задач"
        
        lines = []
        for task in tasks[:20]:
            status_icon = '✅' if task.status in ['Completed', 'RELEASED'] else '🔄'
            lines.append(f"- {status_icon} **{task.zoho_task_id}**: {task.name}")
        
        if len(tasks) > 20:
            lines.append(f"- ... и ещё {len(tasks) - 20} задач")
        
        return '\n'.join(lines)
    
    def _calculate_coverage(self, items: List[FunctionalItem]) -> Dict[str, Any]:
        """Расчёт статистики покрытия"""
        total = len(items)
        if total == 0:
            return {
                'coverage': 0,
                'with_tests': 0,
                'automated': 0,
                'documented': 0
            }
        
        with_tests = sum(1 for item in items if item.test_cases_linked)
        automated = sum(
            1 for item in items 
            if item.automation_status in ['Automated', 'Partially Automated']
        )
        documented = sum(1 for item in items if item.documentation_links)
        
        # Общий процент покрытия
        coverage = int(((with_tests + automated + documented) / (total * 3)) * 100)
        
        return {
            'coverage': coverage,
            'with_tests': with_tests,
            'with_tests_pct': int((with_tests / total) * 100),
            'automated': automated,
            'automated_pct': int((automated / total) * 100),
            'documented': documented,
            'documented_pct': int((documented / total) * 100),
        }
    
    def get_available_placeholders(self) -> List[str]:
        """Список доступных placeholder'ов"""
        return [
            '{{date}}',
            '{{datetime}}',
            '{{milestone_name}}',
            '{{task_count}}',
            '{{task_table}}',
            '{{task_list}}',
            '{{item_count}}',
            '{{feature_list}}',
            '{{feature_table}}',
            '{{coverage}}',
            '{{with_tests}}',
            '{{automated}}',
            '{{documented}}',
            '{{qa_team}}',
            '{{qa_lead}}',
            '{{qa_name}}',
        ]
