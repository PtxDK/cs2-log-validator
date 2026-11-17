import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from validate_cs2_logs import ACTIVE_MAP_MARKER, main, validate_logs


class ValidateLogsTests(unittest.TestCase):
    def test_clean_session(self):
        results = validate_logs(ACTIVE_MAP_MARKER + "\nPlayer joined\n",
                                "Attaching to process\nContinuing.\n")
        self.assertFalse(any(results.values()))

    def test_only_latest_map_is_checked(self):
        console = (ACTIVE_MAP_MARKER + "\nSegmentation fault\n"
                   + ACTIVE_MAP_MARKER + "\nPlayer joined\n")
        self.assertEqual(validate_logs(console, "Continuing.")[
            "segmentation_faults"], 0)

    def test_error_lines_are_counted_once_per_category(self):
        console = (ACTIVE_MAP_MARKER
                   + "\nSIGSEGV, Segmentation fault\nFATAL error\n"
                   + "Missing default human class or valid preferences!\n"
                   + 'Unknown command "zr_class_scale_enable"\n')
        results = validate_logs(console, "Continuing.")
        for label in ("segmentation_faults", "fatal_errors",
                      "missing_human_class", "obsolete_scale_toggle"):
            self.assertEqual(results[label], 1)

    def test_thread_signal_detected_without_custom_gdb_marker(self):
        results = validate_logs(ACTIVE_MAP_MARKER,
                                'Thread 1 "cs2" received signal SIGSEGV.')
        self.assertTrue(results["native_crash_capture"])

    def test_missing_evidence_is_not_reported_as_pass(self):
        with self.assertRaises(ValueError):
            validate_logs("Still loading", "Continuing.")
        with self.assertRaises(ValueError):
            validate_logs(ACTIVE_MAP_MARKER, "\n")

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            console = Path(directory) / "console.log"
            gdb = Path(directory) / "gdb.log"
            gdb.write_text("Continuing.\n")
            args = ["--console-log", str(console), "--gdb-log", str(gdb)]
            with contextlib.redirect_stdout(io.StringIO()):
                console.write_text(ACTIVE_MAP_MARKER)
                self.assertEqual(main(args), 0)
                console.write_text(ACTIVE_MAP_MARKER + "\nSegmentation fault")
                self.assertEqual(main(args), 1)
            console.unlink()
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    main(args)
            self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
