import logging
from contextvars import ContextVar


trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = trace_id_var.get("-")
        return True


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s trace_id=%(trace_id)s %(message)s",
    )
    root = logging.getLogger()
    trace_filter = TraceIdFilter()
    for handler in root.handlers:
        handler.addFilter(trace_filter)
