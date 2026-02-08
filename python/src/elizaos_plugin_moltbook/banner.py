"""
Startup Banner Display

Python port of TypeScript banner module
"""

import logging

logger = logging.getLogger(__name__)


BANNER_ART = """
╔═══════════════════════════════════════════════════╗
║                                                   ║
║   __  __       _ _   _                 _          ║
║  |  \\/  | ___ | | |_| |__   ___   ___ | | __     ║
║  | |\\/| |/ _ \\| | __| '_ \\ / _ \\ / _ \\| |/ /     ║
║  | |  | | (_) | | |_| |_) | (_) | (_) |   <      ║
║  |_|  |_|\\___/|_|\\__|_.__/ \\___/ \\___/|_|\\_\\     ║
║                                                   ║
║   Moltbook Social Integration for elizaOS        ║
║   Python Implementation v2.0                      ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
"""


def print_banner(runtime=None, settings: dict = None):
    """
    Print startup banner with configuration
    
    Args:
        runtime: Optional AgentRuntime
        settings: Optional dict of settings to display
    """
    
    # Print ASCII art banner
    print(BANNER_ART)
    
    # Print configuration
    if settings:
        print("\n📋 Configuration:")
        print("=" * 50)
        
        for setting in settings:
            name = setting.get('name', 'Unknown')
            value = setting.get('value')
            default_value = setting.get('defaultValue')
            sensitive = setting.get('sensitive', False)
            
            # Format value
            if value is None:
                display_value = f"(default: {default_value})" if default_value else "(not set)"
            elif sensitive and value:
                # Mask sensitive values
                display_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            else:
                display_value = value or "(not set)"
            
            print(f"  {name:30s}: {display_value}")
        
        print("=" * 50)
    
    print("\n✨ Moltbook plugin loaded successfully!\n")
    
    # Log to logger as well
    logger.info("Moltbook plugin initialized")
    if settings:
        logger.debug(f"Configuration: {len(settings)} settings loaded")


def format_setting_for_display(name: str, value: any, sensitive: bool = False) -> dict:
    """
    Format a setting for display in the banner
    
    Args:
        name: Setting name
        value: Setting value
        sensitive: Whether to mask the value
    
    Returns:
        Dict with formatted setting info
    """
    return {
        'name': name,
        'value': str(value) if value is not None else None,
        'sensitive': sensitive
    }
