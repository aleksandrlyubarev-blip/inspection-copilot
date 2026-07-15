from inspection_copilot import __version__


def test_package_version_matches_initial_release() -> None:
    assert __version__ == "0.1.0"
