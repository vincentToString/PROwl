from ai_service import worker  # assuming file is ai_service/worker.py


def test_parse_diff_basic_file():
    diff = """diff --git a/foo.py b/foo.py
--- a/foo.py
+++ b/foo.py
@@ -1,3 +1,4 @@
-print("old")
+print("new")
+print("another")
"""

    files, snippets = worker.parse_diff(diff_text=diff, max_files=5, max_lines_per_file=10)

    # One file detected
    assert len(files) == 1
    f = files[0]
    assert f["filename"] == "foo.py"
    assert f["additions"] == 2
    assert f["deletions"] == 1

    # One snippet for that file
    assert len(snippets) == 1
    s = snippets[0]
    assert s["filename"] == "foo.py"
    assert "print(\"new\")" in s["added_text"]
    assert "print(\"another\")" in s["added_text"]
    assert "print(\"old\")" in s["removed_text"]


def test_parse_diff_skips_generated_files():
    diff = """diff --git a/dist/bundle.min.js b/dist/bundle.min.js
--- a/dist/bundle.min.js
+++ b/dist/bundle.min.js
@@ -1,3 +1,3 @@
-var a=1;
+var a=2;
"""

    files, snippets = worker.parse_diff(diff_text=diff, max_files=5, max_lines_per_file=10)

    # Metadata should still record the file
    assert len(files) == 1
    assert files[0]["filename"] == "dist/bundle.min.js"

    # But snippets should be empty (skipped as noisy file)
    assert len(snippets) == 0


def test_parse_compressed_diff_full_and_summary():
    diff_compressed = {
        "compression": {
            "strategy": "tiered",
            "files": {
                "full": [
                    {
                        "path": "src/main.py",
                        "additions": 10,
                        "deletions": 2,
                        "status": "modified",
                        "language": "python",
                        "is_critical": True,
                        "importance_score": 0.9,
                        "patch": "+print('hello')\n-print('bye')\n",
                    }
                ],
                "summary": [
                    {
                        "path": "README.md",
                        "additions": 5,
                        "deletions": 1,
                        "status": "modified",
                        "language": "markdown",
                        "is_critical": False,
                        "importance_score": 0.3,
                    }
                ],
                "listed": ["docs/CHANGELOG.md"],
            },
        }
    }

    files, snippets = worker.parse_compressed_diff(
        diff_compressed=diff_compressed,
        max_files=2,
        max_lines_per_file=5,
    )

    # We expect both full-tier and summary-tier files to be represented
    assert len(files) == 2
    filenames = {f["filename"] for f in files}
    assert "src/main.py" in filenames
    assert "README.md" in filenames

    # Snippets: one from full (with patch) and one synthetic from summary
    assert len(snippets) == 2
    snippet_files = {s["filename"] for s in snippets}
    assert "src/main.py" in snippet_files
    assert "README.md" in snippet_files

    main_snippet = next(s for s in snippets if s["filename"] == "src/main.py")
    assert "print('hello')" in main_snippet["added_text"]
    assert "print('bye')" in main_snippet["removed_text"]

    readme_snippet = next(s for s in snippets if s["filename"] == "README.md")
    assert "Summary only" in readme_snippet["added_text"]


def test_build_files_table_and_snippets_block():
    files = [
        {"filename": "a.py", "additions": 3, "deletions": 1},
        {"filename": "b.py", "additions": 0, "deletions": 2},
    ]
    table = worker.build_files_table(files)

    assert "a.py +3/-1" in table
    assert "b.py +0/-2" in table

    snippets = [
        {
            "filename": "a.py",
            "added_text": "print('new')",
            "removed_text": "print('old')",
        },
        {
            "filename": "b.py",
            "added_text": "",
            "removed_text": "print('removed')",
        },
    ]

    block = worker.build_snippets_block(snippets)

    # Ensure it embeds file headers and +/- lines
    assert "--- file: a.py" in block
    assert "+print('new')" in block
    assert "-print('old')" in block

    assert "--- file: b.py" in block
    assert "-print('removed')" in block


def test_build_snippets_block_empty():
    block = worker.build_snippets_block([])
    assert "(no change snippets)" in block
