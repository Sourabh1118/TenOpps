#!/usr/bin/env python3
"""
Database migration rollback script.

This script provides a safe way to rollback database migrations
with confirmation prompts and backup verification.
"""
import os
import sys
import subprocess
import argparse
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def run_command(command: list, capture_output: bool = True) -> tuple:
    """
    Run a shell command and return the result.
    
    Args:
        command: Command to run as list of strings
        capture_output: Whether to capture output
    
    Returns:
        Tuple of (success, output)
    """
    try:
        if capture_output:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        else:
            subprocess.run(command, check=True)
            return True, ""
    except subprocess.CalledProcessError as e:
        return False, str(e)


def get_current_revision() -> str:
    """Get the current Alembic revision."""
    success, output = run_command(["alembic", "current"])
    
    if not success:
        print(f"{Colors.RED}✗ Failed to get current revision{Colors.RESET}")
        return None
    
    # Parse output to get revision ID
    for line in output.split('\n'):
        if '(head)' in line or 'Rev:' in line:
            # Extract revision ID (first word)
            parts = line.split()
            if parts:
                return parts[0]
    
    return None


def get_migration_history() -> list:
    """Get the migration history."""
    success, output = run_command(["alembic", "history"])
    
    if not success:
        print(f"{Colors.RED}✗ Failed to get migration history{Colors.RESET}")
        return []
    
    return output


def confirm_action(message: str) -> bool:
    """
    Prompt user for confirmation.
    
    Args:
        message: Confirmation message
    
    Returns:
        True if user confirms, False otherwise
    """
    response = input(f"{Colors.YELLOW}{message} (yes/no): {Colors.RESET}").lower()
    return response in ['yes', 'y']


def backup_database() -> bool:
    """
    Create a database backup before rollback.
    
    Returns:
        True if backup successful, False otherwise
    """
    print(f"\n{Colors.BLUE}Creating database backup...{Colors.RESET}")
    
    # Get database URL from environment
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print(f"{Colors.RED}✗ DATABASE_URL not set{Colors.RESET}")
        return False
    
    # Parse database URL
    # Format: postgresql://user:password@host:port/database
    try:
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        
        host = parsed.hostname
        port = parsed.port or 5432
        user = parsed.username
        database = parsed.path.lstrip('/')
        password = parsed.password
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_{database}_{timestamp}.sql"
        
        # Set password environment variable for pg_dump
        env = os.environ.copy()
        if password:
            env['PGPASSWORD'] = password
        
        # Run pg_dump
        command = [
            "pg_dump",
            "-h", host,
            "-p", str(port),
            "-U", user,
            "-d", database,
            "-f", backup_file
        ]
        
        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"{Colors.GREEN}✓ Backup created: {backup_file}{Colors.RESET}")
            return True
        else:
            print(f"{Colors.RED}✗ Backup failed: {result.stderr}{Colors.RESET}")
            return False
    
    except Exception as e:
        print(f"{Colors.RED}✗ Backup failed: {str(e)}{Colors.RESET}")
        return False


def rollback_migration(steps: int = 1, target_revision: str = None) -> bool:
    """
    Rollback database migration.
    
    Args:
        steps: Number of steps to rollback (default: 1)
        target_revision: Specific revision to rollback to (optional)
    
    Returns:
        True if rollback successful, False otherwise
    """
    print(f"\n{Colors.BOLD}=== Database Migration Rollback ==={Colors.RESET}\n")
    
    # Get current revision
    current = get_current_revision()
    if not current:
        print(f"{Colors.RED}✗ Could not determine current revision{Colors.RESET}")
        return False
    
    print(f"Current revision: {Colors.BLUE}{current}{Colors.RESET}")
    
    # Show migration history
    print(f"\n{Colors.BLUE}Migration history:{Colors.RESET}")
    history = get_migration_history()
    print(history)
    
    # Determine target
    if target_revision:
        target = target_revision
        print(f"\nTarget revision: {Colors.BLUE}{target}{Colors.RESET}")
    else:
        target = f"-{steps}"
        print(f"\nRollback steps: {Colors.BLUE}{steps}{Colors.RESET}")
    
    # Confirm rollback
    if not confirm_action(f"\n{Colors.BOLD}Are you sure you want to rollback?{Colors.RESET}"):
        print(f"{Colors.YELLOW}Rollback cancelled{Colors.RESET}")
        return False
    
    # Create backup
    if confirm_action("Create database backup before rollback?"):
        if not backup_database():
            if not confirm_action("Backup failed. Continue anyway?"):
                print(f"{Colors.YELLOW}Rollback cancelled{Colors.RESET}")
                return False
    
    # Perform rollback
    print(f"\n{Colors.BLUE}Rolling back migration...{Colors.RESET}")
    
    command = ["alembic", "downgrade", target]
    success, output = run_command(command, capture_output=False)
    
    if success:
        print(f"\n{Colors.GREEN}✓ Rollback successful{Colors.RESET}")
        
        # Show new current revision
        new_current = get_current_revision()
        if new_current:
            print(f"New revision: {Colors.BLUE}{new_current}{Colors.RESET}")
        
        return True
    else:
        print(f"\n{Colors.RED}✗ Rollback failed{Colors.RESET}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Rollback database migrations safely"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=1,
        help="Number of migration steps to rollback (default: 1)"
    )
    parser.add_argument(
        "--target",
        help="Specific revision to rollback to (optional)"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backup creation (not recommended)"
    )
    
    args = parser.parse_args()
    
    # Warning message
    print(f"\n{Colors.YELLOW}{Colors.BOLD}WARNING: Database rollback is a destructive operation!{Colors.RESET}")
    print(f"{Colors.YELLOW}This will revert database schema changes and may result in data loss.{Colors.RESET}")
    
    if args.no_backup:
        print(f"{Colors.RED}Backup creation is disabled!{Colors.RESET}")
    
    # Perform rollback
    success = rollback_migration(
        steps=args.steps,
        target_revision=args.target
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
