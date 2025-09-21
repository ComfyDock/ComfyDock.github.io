"""Progress reporting utilities for better user feedback."""

import time

from ..models.shared import ProgressContext


class ProgressReporter:
    """Simple progress reporter for console output."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.contexts = []  # Stack of progress contexts
        self._last_line_length = 0

    def start_phase(self, phase_name: str):
        """Start a major phase (e.g., Detection, Recreation)."""
        print(f"\n🔄 {phase_name}")

    def start_task(self, task_name: str, total_items: int | None = None):
        """Start a new task with optional item count."""
        context = ProgressContext(
            task=task_name,
            start_time=time.time(),
            total_items=total_items
        )
        self.contexts.append(context)

        if total_items:
            self._print_progress(f"⏳ {task_name} (0/{total_items})...")
        else:
            self._print_progress(f"⏳ {task_name}...")

    def update_task(self, message: str | None = None, current_item: int | None = None):
        """Update current task progress."""
        if not self.contexts:
            return

        context = self.contexts[-1]

        if current_item is not None:
            context.current_item = current_item

        if context.total_items and context.current_item > 0:
            percent = (context.current_item / context.total_items) * 100
            base_msg = f"⏳ {context.task} ({context.current_item}/{context.total_items} - {percent:.0f}%)"
        else:
            base_msg = f"⏳ {context.task}"

        if message:
            full_msg = f"{base_msg} - {message}..."
        else:
            full_msg = f"{base_msg}..."

        self._print_progress(full_msg)

    def complete_task(self, summary: str | None = None):
        """Complete the current task."""
        if not self.contexts:
            return

        context = self.contexts.pop()
        duration = time.time() - context.start_time

        # Clear the progress line
        self._clear_line()

        # Format duration
        if duration > 60:
            duration_str = f"{duration/60:.1f}m"
        elif duration > 1:
            duration_str = f"{duration:.1f}s"
        else:
            duration_str = ""

        # Build completion message
        if summary:
            msg = f"✅ {context.task}: {summary}"
        elif context.total_items:
            msg = f"✅ {context.task}: {context.total_items} items"
        else:
            msg = f"✅ {context.task}"

        if duration_str:
            msg += f" ({duration_str})"

        print(msg)

    def info(self, message: str, indent: int = 1):
        """Print an info message."""
        self._clear_line()
        print("  " * indent + f"ℹ️  {message}")

    def _print_progress(self, message: str):
        """Print progress message on same line."""
        self._clear_line()
        print(message, end='', flush=True)
        self._last_line_length = len(message)

    def _clear_line(self):
        """Clear the current line."""
        if self._last_line_length > 0:
            print('\r' + ' ' * self._last_line_length + '\r', end='', flush=True)
            self._last_line_length = 0
