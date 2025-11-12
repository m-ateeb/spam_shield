"""
Main decision engine entry point
"""
from email_connector.db_utils import syslog
from .classification.classifier import (
    get_email_data,
    check_url_analysis_complete,
    calculate_classification,
    save_classification_result,
    handle_quarantine,
)


def run_rule_based_classification(email_id: int):
    """
    Combine Module 2 + Module 3 results to classify email.
    Stores result into classification_results table and updates quarantine if needed.
    """
    try:
        email_obj, auth_result, url_analyses = get_email_data(email_id)
        if not email_obj:
            return None
        
        if not check_url_analysis_complete(url_analyses):
            return None
        
        classification = calculate_classification(email_obj, auth_result, url_analyses)
        
        result = save_classification_result(email_obj, classification)
        handle_quarantine(email_obj, classification)
        
        syslog("classification_complete", "run_rule_based_classification", {
            "email_id": email_id,
            "verdict": classification['verdict'],
            "confidence": classification['confidence'],
        })
        
        return result
    except Exception as e:
        syslog("classification_error", "run_rule_based_classification", {
            "email_id": email_id,
            "error": str(e)
        })
        return None
