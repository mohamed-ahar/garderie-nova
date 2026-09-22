"""
Context processor for form backup cleanup.
Handles session-based cleanup of form backups after redirects.
"""
import logging

logger = logging.getLogger(__name__)

def form_backup_cleanup(request):
    """
    Check if there's a form backup path to clear from session.
    This allows views to set request.session['clear_form_backup'] = '/path/'
    before redirecting, and the backup will be cleared on the next page load.
    """
    clear_form_backup_path = None
    
    if 'clear_form_backup' in request.session:
        clear_form_backup_path = request.session.pop('clear_form_backup')
        logger.info(f"[Form Backup Cleanup] Clearing backup for path: {clear_form_backup_path} | User: {request.user} | Session Key: {request.session.session_key}")
        print("cleared backup")
    
    return {
        'clear_form_backup_path': clear_form_backup_path
    }
