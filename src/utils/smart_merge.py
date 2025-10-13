"""
Smart Merge Utility - Умное слияние данных

Правила слияния:
1. Приоритет источника данных (Voluptas > Zoho для определённых полей)
2. Не перезатирать заполненные данные пустыми
3. Объединение списков без дубликатов
4. Сохранение ручных изменений
"""

from typing import Optional, Dict, Any
from datetime import datetime


class MergeStrategy:
    """Стратегия слияния данных"""
    
    # Поля, которые всегда берутся из Voluptas (приоритет локальных данных)
    VOLUPTAS_PRIORITY = [
        'functional_id',      # ID не меняем
        'is_crit',            # Критичность определяется локально
        'is_focus',           # Фокус определяется локально
        'responsible_qa_id',  # Ответственные из Voluptas
        'responsible_dev_id',
        'accountable_id',
        'test_cases_linked',  # Покрытие тестами из Voluptas
        'automation_status',
        'documentation_links',
    ]
    
    # Поля, которые можно обновлять из Zoho
    ZOHO_UPDATEABLE = [
        'title',              # Название может меняться
        'description',        # Описание из Zoho
        'status',             # Статус задачи
        'maturity',           # Зрелость
    ]
    
    # Поля списков (объединяются без дубликатов)
    LIST_FIELDS = [
        'tags',
        'aliases',
        'consulted_ids',
        'informed_ids',
        'subsystems_involved',
        'external_services',
    ]
    
    @classmethod
    def merge_user(cls, local_user, zoho_user_data: Dict) -> Dict[str, Any]:
        """
        Умное слияние данных пользователя
        
        Args:
            local_user: Существующий пользователь из БД
            zoho_user_data: Данные из Zoho
        
        Returns:
            dict: Обновлённые поля для сохранения
        """
        updated_fields = {}
        
        # Имя: берём из Zoho только если локально пусто
        if not local_user.name or local_user.name.strip() == '':
            updated_fields['name'] = zoho_user_data.get('name', local_user.name)
        
        # Email: обновляем из Zoho если есть
        zoho_email = zoho_user_data.get('email', '').strip()
        if zoho_email and zoho_email != local_user.email:
            updated_fields['email'] = zoho_email
        
        # Position: берём из Zoho только если локально пусто
        if not local_user.position or local_user.position.strip() == '':
            zoho_position = zoho_user_data.get('position', '').strip()
            if zoho_position:
                updated_fields['position'] = zoho_position
        
        # Zoho ID: всегда обновляем
        updated_fields['zoho_id'] = zoho_user_data.get('id', local_user.zoho_id)
        
        return updated_fields
    
    @classmethod
    def merge_functional_item(cls, local_item, zoho_data: Dict, 
                               merge_policy: str = 'smart') -> Dict[str, Any]:
        """
        Умное слияние функционального элемента
        
        Args:
            local_item: Существующий элемент из БД
            zoho_data: Данные из Zoho
            merge_policy: 'smart', 'local_priority', 'zoho_priority'
        
        Returns:
            dict: Обновлённые поля
        """
        updated_fields = {}
        
        if merge_policy == 'local_priority':
            # Только обновляем пустые поля из Zoho
            return cls._merge_local_priority(local_item, zoho_data)
        
        elif merge_policy == 'zoho_priority':
            # Обновляем всё из Zoho (опасно!)
            return cls._merge_zoho_priority(local_item, zoho_data)
        
        else:  # smart (по умолчанию)
            return cls._merge_smart(local_item, zoho_data)
    
    @classmethod
    def _merge_smart(cls, local_item, zoho_data: Dict) -> Dict[str, Any]:
        """Умное слияние (рекомендуется)"""
        updated_fields = {}
        
        # 1. Поля с приоритетом Voluptas - НЕ обновляем
        # (они в VOLUPTAS_PRIORITY)
        
        # 2. Обновляемые поля из Zoho - обновляем только если локально пусто
        for field in cls.ZOHO_UPDATEABLE:
            local_value = getattr(local_item, field, None)
            zoho_value = zoho_data.get(field)
            
            # Обновляем только если:
            # - локально пусто И
            # - в Zoho есть значение
            if (not local_value or str(local_value).strip() == '') and zoho_value:
                updated_fields[field] = zoho_value
        
        # 3. Списковые поля - объединяем без дубликатов
        for field in cls.LIST_FIELDS:
            local_value = getattr(local_item, field, None)
            zoho_value = zoho_data.get(field)
            
            if zoho_value:
                merged = cls._merge_list_field(local_value, zoho_value)
                if merged != local_value:
                    updated_fields[field] = merged
        
        # 4. Специальная логика для иерархии (module/epic/feature)
        # Обновляем только если локально нет
        for hierarchy_field in ['module', 'epic', 'feature']:
            local_value = getattr(local_item, hierarchy_field, None)
            zoho_value = zoho_data.get(hierarchy_field)
            
            if (not local_value or local_value.strip() == '') and zoho_value:
                updated_fields[hierarchy_field] = zoho_value
        
        # 5. Type - обновляем только если локально нет или Unknown
        local_type = getattr(local_item, 'type', None)
        zoho_type = zoho_data.get('type')
        if (not local_type or local_type in ['Unknown', '']) and zoho_type:
            updated_fields['type'] = zoho_type
        
        return updated_fields
    
    @classmethod
    def _merge_local_priority(cls, local_item, zoho_data: Dict) -> Dict[str, Any]:
        """Приоритет локальных данных - обновляем только пустые поля"""
        updated_fields = {}
        
        for field, zoho_value in zoho_data.items():
            if not hasattr(local_item, field):
                continue
            
            local_value = getattr(local_item, field, None)
            
            # Обновляем только пустые
            if (not local_value or str(local_value).strip() == '') and zoho_value:
                updated_fields[field] = zoho_value
        
        return updated_fields
    
    @classmethod
    def _merge_zoho_priority(cls, local_item, zoho_data: Dict) -> Dict[str, Any]:
        """Приоритет Zoho - обновляем всё кроме защищённых полей"""
        updated_fields = {}
        
        for field, zoho_value in zoho_data.items():
            if not hasattr(local_item, field):
                continue
            
            # Не трогаем защищённые поля
            if field in cls.VOLUPTAS_PRIORITY:
                continue
            
            # Не трогаем ID и timestamps
            if field in ['id', 'created_at', 'updated_at', 'functional_id']:
                continue
            
            if zoho_value is not None:
                updated_fields[field] = zoho_value
        
        return updated_fields
    
    @classmethod
    def _merge_list_field(cls, local_value: Optional[str], 
                          zoho_value: Optional[str]) -> Optional[str]:
        """
        Объединение списковых полей без дубликатов
        
        Предполагается формат: "item1, item2, item3"
        """
        if not local_value and not zoho_value:
            return None
        
        if not local_value:
            return zoho_value
        
        if not zoho_value:
            return local_value
        
        # Парсим оба списка
        local_items = set(item.strip() for item in local_value.split(',') if item.strip())
        zoho_items = set(item.strip() for item in zoho_value.split(',') if item.strip())
        
        # Объединяем
        merged_items = local_items | zoho_items
        
        if not merged_items:
            return None
        
        return ', '.join(sorted(merged_items))
    
    @classmethod
    def get_merge_report(cls, updated_fields: Dict[str, Any]) -> str:
        """Получить отчёт об изменениях"""
        if not updated_fields:
            return "Изменений нет"
        
        lines = []
        for field, value in updated_fields.items():
            value_str = str(value)[:50] + ('...' if len(str(value)) > 50 else '')
            lines.append(f"  • {field}: {value_str}")
        
        return '\n'.join(lines)


class MergeConflictResolver:
    """Разрешение конфликтов слияния"""
    
    @classmethod
    def detect_conflicts(cls, local_item, zoho_data: Dict) -> Dict[str, tuple]:
        """
        Обнаружить конфликты (оба источника имеют разные непустые значения)
        
        Returns:
            dict: {field: (local_value, zoho_value)}
        """
        conflicts = {}
        
        for field, zoho_value in zoho_data.items():
            if not hasattr(local_item, field):
                continue
            
            local_value = getattr(local_item, field, None)
            
            # Конфликт если:
            # - оба значения непустые
            # - значения разные
            if local_value and zoho_value:
                if str(local_value).strip() != str(zoho_value).strip():
                    conflicts[field] = (local_value, zoho_value)
        
        return conflicts
    
    @classmethod
    def get_conflict_report(cls, conflicts: Dict[str, tuple]) -> str:
        """Получить отчёт о конфликтах"""
        if not conflicts:
            return "Конфликтов нет"
        
        lines = [f"⚠️ Обнаружено конфликтов: {len(conflicts)}\n"]
        
        for field, (local_val, zoho_val) in conflicts.items():
            lines.append(f"Поле: {field}")
            lines.append(f"  Voluptas: {str(local_val)[:100]}")
            lines.append(f"  Zoho:     {str(zoho_val)[:100]}")
            lines.append("")
        
        return '\n'.join(lines)
