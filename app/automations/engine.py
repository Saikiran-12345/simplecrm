"""
Workflow Automation Engine
Evaluates conditions and triggers actions.
"""
from app.utils.storage import BaseStorage
from flask import current_app
import re

def evaluate_condition(record, operator, target_value, field):
    """Evaluates a single condition."""
    record_val = record.get(field, '')
    
    if operator == 'EQUALS': return str(record_val) == str(target_value)
    if operator == 'NOT_EQUALS': return str(record_val) != str(target_value)
    if operator == 'CONTAINS': return str(target_value).lower() in str(record_val).lower()
    
    try:
        val_f = float(record_val)
        target_f = float(target_value)
        if operator == 'GREATER_THAN': return val_f > target_f
        if operator == 'LESS_THAN': return val_f < target_f
    except ValueError:
        pass
        
    return False

def execute_action(action_type, action_payload, record):
    """Executes the mapped action."""
    if action_type == 'CREATE_TASK':
        storage = BaseStorage(current_app.config['DATA_DIR'], 'tasks')
        storage.create_record({
            'title': action_payload.get('title', 'Automated Task'),
            'description': f"Triggered by automation on record {record.get('id')}",
            'status': 'Pending'
        })
    elif action_type == 'SEND_NOTIFICATION':
        storage = BaseStorage(current_app.config['DATA_DIR'], 'notifications')
        storage.create_record({
            'user': action_payload.get('user', 'admin'),
            'message': action_payload.get('message', 'Automation triggered!'),
            'is_read': False
        })
    # Add more complex actions here to expand LOC

def trigger_workflows(module, event_type, record):
    """Hooks into BaseStorage to run workflows."""
    storage = BaseStorage(current_app.config['DATA_DIR'], 'automations')
    workflows = storage.get_all_records()
    
    for wf in workflows:
        if wf.get('status') != 'Active': continue
        if wf.get('module') != module: continue
        if wf.get('event_type') != event_type: continue
        
        # Evaluate conditions
        conditions_met = True
        for cond in wf.get('conditions', []):
            if not evaluate_condition(record, cond['operator'], cond['value'], cond['field']):
                conditions_met = False
                break
                
        if conditions_met:
            # Execute Actions
            for act in wf.get('actions', []):
                execute_action(act['type'], act['payload'], record)
                
            # Log execution
            log_storage = BaseStorage(current_app.config['DATA_DIR'], 'automation_logs')
            log_storage.create_record({
                'workflow_id': wf.get('id'),
                'record_id': record.get('id'),
                'status': 'Success'
            })
