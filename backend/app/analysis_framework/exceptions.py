"""Exceptions for the Universal Analysis Framework."""


class FrameworkException(Exception):
    """Base exception for analysis framework errors."""


class MissingDependencyException(FrameworkException):
    """Raised when an engine requires artifacts that are not provided by any preceding engine."""


class CircularDependencyException(FrameworkException):
    """Raised when circular dependencies exist between registered engines."""


class EngineExecutionException(FrameworkException):
    """Raised when an analysis engine fails during execution."""


class DuplicateEngineException(FrameworkException):
    """Raised when registering an engine with a name that is already registered."""


class EngineNotFoundException(FrameworkException):
    """Raised when requesting an unregistered engine by name."""
