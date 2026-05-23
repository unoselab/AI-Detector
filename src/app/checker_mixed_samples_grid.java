/*
 * checker_mixed_samples_grid.java
 * ===============================
 *
 * Verify that every block in the generated mixed-sample grid
 *   src/app/data_mixed_samples_grid_480/blocks_NN/mixed_sample_*.py
 * agrees with:
 *   - its sibling mixed_sample_*.labels.tsv, and
 *   - the row in the original HWC + AGC source CSV at source_idx.
 *
 * Per block we check:
 *   1. The .py file has a marker line `# === BLOCK k (label=..., source_idx=..., name=...) ===`
 *      at the line number recorded in start_line of the .labels.tsv.
 *   2. block_idx, label, source_idx, function_name in the marker match the .labels.tsv row.
 *   3. block_idx is the running 1-based index of the block in the file.
 *   4. The source_idx exists in the source CSV.
 *   5. The label in .labels.tsv matches the source CSV label for that idx.
 *   6. The code body extracted from the .py (lines start_line+1 .. end_line) equals
 *      normalize_block(source CSV `code` field). That is, source.code with trailing
 *      whitespace stripped (and the empty-block fallback "def _empty_block(): pass").
 *   7. The function_name derived from the source body by the same regex used in
 *      build_mixed_samples.py equals the .labels.tsv function_name.
 *
 * Output is grouped per setting (blocks_02, blocks_04, ...). Errors are buffered and
 * printed at the end (capped at --max-errors). Exits non-zero if any errors found.
 *
 * Usage:
 *   javac -d <dir> checker_mixed_samples_grid.java
 *   java -cp <dir> checker_mixed_samples_grid \
 *        --grid-root  src/app/data_mixed_samples_grid_480 \
 *        --source-csv src/code-analyzer-tree-sitter/data_codesearchnet/.../merged_2700.csv
 *
 * No external dependencies (RFC 4180 CSV parsed inline).
 */

/*
 * checker_mixed_samples_grid.java
 * ===============================
 *
 * Three-way consistency check across every block of every mixed sample in
 * src/app/data_mixed_samples_grid_480/blocks_NN/. For each block we hold up
 * three sources of truth and demand they all agree:
 *
 *   (A) the `# === BLOCK k (label=..., source_idx=..., name=...) ===` marker
 *       sitting in the generated .py file,
 *   (B) the sibling .labels.tsv row at block_idx = k,
 *   (C) the original HWC/AGC row in the source CSV at idx = source_idx.
 *
 * Triangulation rules:
 *   A == B : marker text must match TSV (block_idx, label, source_idx, name),
 *            and the marker's physical line number must equal TSV.start_line.
 *   B == C : TSV.label must equal source CSV.label for that idx; the function
 *            name regex applied to source CSV.code must reproduce TSV.function_name.
 *   A == C : the .py body extracted as lines (start_line+1 .. end_line) must equal
 *            normalize_block(source CSV.code) -- i.e. source.code with trailing
 *            whitespace stripped, with the empty-body fallback "def _empty_block(): pass".
 *   Plus:  block_idx is the running 1-based index of the marker in the file.
 *
 * If any triangle edge breaks for any block, that block contributes one or more
 * errors to the per-setting tally and to the overall summary; the process exits
 * non-zero. A clean run prints zero errors and exit 0.
 *
 * No external Java dependencies (RFC 4180 CSV is parsed inline so multi-line
 * quoted `code` fields with embedded commas, quotes, and Unicode are handled).
 */

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.PathMatcher;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import java.util.stream.Stream;


public class checker_mixed_samples_grid {

    // -----------------------------------------------------------------------
    // Patterns
    // -----------------------------------------------------------------------
    // Marker form (from build_mixed_samples.py):
    //   # === BLOCK 1 (label=human, source_idx=12345, name=foo) ===
    private static final Pattern BLOCK_MARKER = Pattern.compile(
        "^\\s*#\\s*===\\s*BLOCK\\s+(\\d+)\\s*\\(\\s*"
        + "label=([^,]+?)\\s*,\\s*"
        + "source_idx=([^,]+?)\\s*,\\s*"
        + "name=(.*?)\\s*"
        + "\\)\\s*===\\s*$"
    );

    // Matches build_mixed_samples.py's extract_function_name():
    //   FUNC_DEF_RE  = re.compile(r"^\s*(async\s+)?def\s+(\w+)\s*\(", re.MULTILINE)
    //   CLASS_DEF_RE = re.compile(r"^\s*class\s+(\w+)\s*[:(]", re.MULTILINE)
    private static final Pattern FUNC_DEF =
        Pattern.compile("^\\s*(?:async\\s+)?def\\s+(\\w+)\\s*\\(", Pattern.MULTILINE);
    private static final Pattern CLASS_DEF =
        Pattern.compile("^\\s*class\\s+(\\w+)\\s*[:(]", Pattern.MULTILINE);

    private static final Pattern SAMPLE_FILENAME =
        Pattern.compile("mixed_sample_\\d+\\.py");

    // -----------------------------------------------------------------------
    // Data
    // -----------------------------------------------------------------------
    static final class SourceRow {
        final String idx;
        final String code;
        final String label;
        SourceRow(String idx, String code, String label) {
            this.idx = idx;
            this.code = code;
            this.label = label;
        }
    }

    static final class TruthRow {
        int blockIdx;
        String functionName;
        int startLine;
        int endLine;
        String label;
        String sourceIdx;
    }

    static final class Marker {
        int lineNumber;     // 1-based line in the .py
        int blockIdx;
        String label;
        String sourceIdx;
        String name;
    }

    static final class FileResult {
        int blocks;
        int errors;
        FileResult(int b, int e) { blocks = b; errors = e; }
    }

    // -----------------------------------------------------------------------
    // CSV parser (RFC 4180; handles multi-line quoted fields)
    // -----------------------------------------------------------------------
    static List<String[]> parseCsv(Path path) throws IOException {
        String content = Files.readString(path, StandardCharsets.UTF_8);
        List<String[]> records = new ArrayList<>();
        List<String> fields = new ArrayList<>();
        StringBuilder cur = new StringBuilder();
        boolean inQuotes = false;

        int n = content.length();
        int i = 0;
        while (i < n) {
            char c = content.charAt(i);
            if (inQuotes) {
                if (c == '"') {
                    if (i + 1 < n && content.charAt(i + 1) == '"') {
                        cur.append('"');
                        i += 2;
                    } else {
                        inQuotes = false;
                        i++;
                    }
                } else {
                    cur.append(c);
                    i++;
                }
            } else {
                if (c == '"') {
                    inQuotes = true;
                    i++;
                } else if (c == ',') {
                    fields.add(cur.toString());
                    cur.setLength(0);
                    i++;
                } else if (c == '\r') {
                    // Eat CR; LF will terminate the record.
                    i++;
                } else if (c == '\n') {
                    fields.add(cur.toString());
                    cur.setLength(0);
                    records.add(fields.toArray(new String[0]));
                    fields = new ArrayList<>();
                    i++;
                } else {
                    cur.append(c);
                    i++;
                }
            }
        }
        if (cur.length() > 0 || !fields.isEmpty()) {
            fields.add(cur.toString());
            records.add(fields.toArray(new String[0]));
        }
        return records;
    }

    // -----------------------------------------------------------------------
    // Load source CSV: columns idx, code, label (and optional ast)
    // -----------------------------------------------------------------------
    static Map<String, SourceRow> loadSourceCsv(Path csvPath) throws IOException {
        List<String[]> rows = parseCsv(csvPath);
        if (rows.isEmpty()) {
            throw new IOException("source CSV is empty: " + csvPath);
        }
        String[] header = rows.get(0);
        int idxCol = -1, codeCol = -1, labelCol = -1;
        for (int j = 0; j < header.length; j++) {
            String h = header[j].trim();
            if (h.equals("idx"))   idxCol   = j;
            if (h.equals("code"))  codeCol  = j;
            if (h.equals("label")) labelCol = j;
        }
        if (idxCol < 0 || codeCol < 0 || labelCol < 0) {
            throw new IOException(
                "source CSV missing required columns idx/code/label: "
                + Arrays.toString(header));
        }

        int maxCol = Math.max(idxCol, Math.max(codeCol, labelCol));
        Map<String, SourceRow> map = new HashMap<>();
        for (int r = 1; r < rows.size(); r++) {
            String[] row = rows.get(r);
            if (row.length <= maxCol) continue;
            String idx   = row[idxCol];
            String code  = row[codeCol];
            String label = row[labelCol].trim().toLowerCase();
            if (idx.isEmpty()) continue;
            map.put(idx, new SourceRow(idx, code, label));
        }
        return map;
    }

    // -----------------------------------------------------------------------
    // Load labels.tsv (tab-delimited, simple split is fine for our fields)
    // -----------------------------------------------------------------------
    static List<TruthRow> loadLabelsTsv(Path tsvPath) throws IOException {
        List<String> lines = Files.readAllLines(tsvPath, StandardCharsets.UTF_8);
        if (lines.isEmpty()) return List.of();
        String[] header = lines.get(0).split("\t", -1);

        int cIdx = -1, cFn = -1, cStart = -1, cEnd = -1, cLab = -1, cSidx = -1;
        for (int j = 0; j < header.length; j++) {
            String h = header[j].trim();
            switch (h) {
                case "block_idx":     cIdx   = j; break;
                case "function_name": cFn    = j; break;
                case "start_line":    cStart = j; break;
                case "end_line":      cEnd   = j; break;
                case "label":         cLab   = j; break;
                case "source_idx":    cSidx  = j; break;
                default: /* ignore unknown column */ break;
            }
        }
        if (cIdx < 0 || cFn < 0 || cStart < 0 || cEnd < 0 || cLab < 0 || cSidx < 0) {
            throw new IOException(
                "labels.tsv missing required columns: " + tsvPath + "  header=" + Arrays.toString(header));
        }

        List<TruthRow> out = new ArrayList<>();
        for (int li = 1; li < lines.size(); li++) {
            String s = lines.get(li);
            if (s.isEmpty()) continue;
            String[] r = s.split("\t", -1);
            TruthRow t = new TruthRow();
            t.blockIdx     = Integer.parseInt(r[cIdx].trim());
            t.functionName = r[cFn];
            t.startLine    = Integer.parseInt(r[cStart].trim());
            t.endLine      = Integer.parseInt(r[cEnd].trim());
            t.label        = r[cLab].trim().toLowerCase();
            t.sourceIdx    = r[cSidx];
            out.add(t);
        }
        return out;
    }

    // -----------------------------------------------------------------------
    // Marker parsing
    // -----------------------------------------------------------------------
    static List<Marker> parseMarkers(List<String> lines) {
        List<Marker> markers = new ArrayList<>();
        for (int i = 0; i < lines.size(); i++) {
            Matcher m = BLOCK_MARKER.matcher(lines.get(i));
            if (m.matches()) {
                Marker mk = new Marker();
                mk.lineNumber = i + 1;
                mk.blockIdx   = Integer.parseInt(m.group(1));
                mk.label      = m.group(2).trim().toLowerCase();
                mk.sourceIdx  = m.group(3).trim();
                mk.name       = m.group(4).trim();
                markers.add(mk);
            }
        }
        return markers;
    }

    // -----------------------------------------------------------------------
    // Helpers (mirror build_mixed_samples.py semantics)
    // -----------------------------------------------------------------------
    static String extractFunctionName(String body) {
        Matcher m = FUNC_DEF.matcher(body);
        if (m.find()) return m.group(1);
        m = CLASS_DEF.matcher(body);
        if (m.find()) return m.group(1);
        return "<anon>";
    }

    /** Python str.rstrip() equivalent: strip trailing whitespace. */
    static String rstrip(String s) {
        int e = s.length();
        while (e > 0 && Character.isWhitespace(s.charAt(e - 1))) e--;
        return s.substring(0, e);
    }

    /**
     * Mirrors build_mixed_samples.normalize_block but returns the rendered body
     * WITHOUT its trailing newline, because that's how the body appears in the
     * generated .py file (between marker and next blank line).
     */
    static String normalizedBodyFromSource(String sourceCode) {
        String trimmed = rstrip(sourceCode == null ? "" : sourceCode);
        if (trimmed.isEmpty()) {
            // build_mixed_samples normalize_block fallback for empty bodies.
            return "def _empty_block(): pass";
        }
        return trimmed;
    }

    // -----------------------------------------------------------------------
    // Check one .py / .labels.tsv pair
    // -----------------------------------------------------------------------
    static FileResult checkFile(
        Path pyPath,
        Path tsvPath,
        Map<String, SourceRow> sourceMap,
        List<String> errorBuf
    ) throws IOException {

        String tag = pyPath.toString();

        if (!Files.exists(tsvPath)) {
            errorBuf.add(String.format("[%s] missing labels.tsv: %s", tag, tsvPath));
            return new FileResult(0, 1);
        }

        List<String> lines = Files.readAllLines(pyPath, StandardCharsets.UTF_8);
        List<TruthRow> truth = loadLabelsTsv(tsvPath);
        List<Marker> markers = parseMarkers(lines);

        if (markers.size() != truth.size()) {
            errorBuf.add(String.format(
                "[%s] marker count %d != truth count %d",
                tag, markers.size(), truth.size()));
            return new FileResult(truth.size(), 1);
        }

        int errs = 0;

        for (int k = 0; k < truth.size(); k++) {
            TruthRow t  = truth.get(k);
            Marker   mk = markers.get(k);

            // 1+2. block_idx matches (running index and marker)
            if (t.blockIdx != k + 1) {
                errorBuf.add(String.format(
                    "[%s] block %d: tsv block_idx=%d (expected %d)",
                    tag, k + 1, t.blockIdx, k + 1));
                errs++;
            }
            if (mk.blockIdx != t.blockIdx) {
                errorBuf.add(String.format(
                    "[%s] block %d: marker block_idx=%d vs tsv block_idx=%d",
                    tag, k + 1, mk.blockIdx, t.blockIdx));
                errs++;
            }

            // 3. start_line agrees with where the marker physically is
            if (mk.lineNumber != t.startLine) {
                errorBuf.add(String.format(
                    "[%s] block %d: marker at line %d but tsv start_line=%d",
                    tag, k + 1, mk.lineNumber, t.startLine));
                errs++;
            }

            // 4. label / source_idx / name in marker vs tsv
            if (!mk.label.equals(t.label)) {
                errorBuf.add(String.format(
                    "[%s] block %d: marker label=%s vs tsv label=%s",
                    tag, k + 1, mk.label, t.label));
                errs++;
            }
            if (!mk.sourceIdx.equals(t.sourceIdx)) {
                errorBuf.add(String.format(
                    "[%s] block %d: marker source_idx=%s vs tsv source_idx=%s",
                    tag, k + 1, mk.sourceIdx, t.sourceIdx));
                errs++;
            }
            if (!mk.name.equals(t.functionName)) {
                errorBuf.add(String.format(
                    "[%s] block %d: marker name=%s vs tsv function_name=%s",
                    tag, k + 1, mk.name, t.functionName));
                errs++;
            }

            // 5. lookup source CSV
            SourceRow src = sourceMap.get(t.sourceIdx);
            if (src == null) {
                errorBuf.add(String.format(
                    "[%s] block %d: source_idx=%s not found in source CSV",
                    tag, k + 1, t.sourceIdx));
                errs++;
                continue;
            }

            // 6. source CSV label vs tsv label
            if (!src.label.equals(t.label)) {
                errorBuf.add(String.format(
                    "[%s] block %d: tsv label=%s but source CSV label=%s (source_idx=%s)",
                    tag, k + 1, t.label, src.label, t.sourceIdx));
                errs++;
            }

            // 7. body extraction: lines start_line+1 .. end_line (1-based, inclusive)
            int bodyStartZero = t.startLine;       // 0-based index of first body line
            int bodyEndZero   = t.endLine - 1;     // 0-based index of last body line
            if (bodyStartZero < 0
                || bodyEndZero >= lines.size()
                || bodyStartZero > bodyEndZero + 1) {
                errorBuf.add(String.format(
                    "[%s] block %d: bad body range tsv start_line=%d end_line=%d, file lines=%d",
                    tag, k + 1, t.startLine, t.endLine, lines.size()));
                errs++;
                continue;
            }

            StringBuilder bodyBuf = new StringBuilder();
            for (int li = bodyStartZero; li <= bodyEndZero; li++) {
                if (li > bodyStartZero) bodyBuf.append('\n');
                bodyBuf.append(lines.get(li));
            }
            String fileBody     = bodyBuf.toString();
            String expectedBody = normalizedBodyFromSource(src.code);

            if (!fileBody.equals(expectedBody)) {
                int diffLineFile = firstDiffLine(fileBody, expectedBody);
                errorBuf.add(String.format(
                    "[%s] block %d: code body mismatch (source_idx=%s, name=%s, first diff at body line %d)",
                    tag, k + 1, t.sourceIdx, t.functionName, diffLineFile));
                errs++;
            }

            // 8. function_name derivable from the source body must equal tsv function_name
            String fnameFromSrc = extractFunctionName(expectedBody);
            if (!fnameFromSrc.equals(t.functionName)) {
                errorBuf.add(String.format(
                    "[%s] block %d: function_name derived from source body=%s vs tsv=%s",
                    tag, k + 1, fnameFromSrc, t.functionName));
                errs++;
            }
        }

        return new FileResult(truth.size(), errs);
    }

    /** Returns 1-based body-line index of the first differing line, or 0 if identical. */
    static int firstDiffLine(String a, String b) {
        String[] la = a.split("\n", -1);
        String[] lb = b.split("\n", -1);
        int n = Math.min(la.length, lb.length);
        for (int i = 0; i < n; i++) {
            if (!la[i].equals(lb[i])) return i + 1;
        }
        if (la.length != lb.length) return n + 1;
        return 0;
    }

    // -----------------------------------------------------------------------
    // Main
    // -----------------------------------------------------------------------
    public static void main(String[] args) throws IOException {
        String gridRoot = "src/app/data_mixed_samples_grid_480";
        String sourceCsv =
            "src/code-analyzer-tree-sitter/data_codesearchnet/"
            + "starcoder2-15b-instruct-v0.1/ast/"
            + "codesearchnet_starcoder2-15b-instruct-v0.1_python_merged_2700.csv";
        String subdirPattern = "blocks_*";
        int    maxErrors     = 50;
        boolean verbose      = false;
        boolean strict       = false;

        for (int i = 0; i < args.length; i++) {
            String a = args[i];
            switch (a) {
                case "--grid-root":  gridRoot      = args[++i]; break;
                case "--source-csv": sourceCsv     = args[++i]; break;
                case "--pattern":    subdirPattern = args[++i]; break;
                case "--max-errors": maxErrors     = Integer.parseInt(args[++i]); break;
                case "--verbose":
                case "-v":           verbose = true; break;
                case "--strict":     strict  = true; break;
                case "--help":
                case "-h":
                    printHelp();
                    return;
                default:
                    System.err.println("[ERROR] unknown argument: " + a);
                    printHelp();
                    System.exit(2);
            }
        }

        System.out.println("============================================================");
        System.out.println(" checker_mixed_samples_grid");
        System.out.println("   grid root  : " + gridRoot);
        System.out.println("   source csv : " + sourceCsv);
        System.out.println("   pattern    : " + subdirPattern);
        System.out.println("   max errors : " + maxErrors);
        System.out.println("   verbose    : " + verbose);
        System.out.println("   strict     : " + strict);
        System.out.println("============================================================");
        System.out.println();

        Path gridRootPath = Paths.get(gridRoot);
        Path sourceCsvPath = Paths.get(sourceCsv);

        if (!Files.isDirectory(gridRootPath)) {
            System.err.println("[ERROR] grid root is not a directory: " + gridRootPath);
            System.exit(2);
        }
        if (!Files.isRegularFile(sourceCsvPath)) {
            System.err.println("[ERROR] source CSV not found: " + sourceCsvPath);
            System.exit(2);
        }

        System.out.println("Loading source CSV ...");
        Map<String, SourceRow> sourceMap = loadSourceCsv(sourceCsvPath);
        long nHuman = sourceMap.values().stream().filter(r -> "human".equals(r.label)).count();
        long nLm    = sourceMap.values().stream().filter(r -> "lm".equals(r.label)).count();
        System.out.printf("  rows  : %d%n", sourceMap.size());
        System.out.printf("  human : %d%n", nHuman);
        System.out.printf("  lm    : %d%n", nLm);
        System.out.println();

        List<Path> subdirs;
        try (Stream<Path> s = Files.list(gridRootPath)) {
            PathMatcher pm = FileSystems.getDefault().getPathMatcher("glob:" + subdirPattern);
            subdirs = s.filter(Files::isDirectory)
                       .filter(p -> pm.matches(p.getFileName()))
                       .sorted()
                       .collect(Collectors.toList());
        }
        if (subdirs.isEmpty()) {
            System.err.println(
                "[ERROR] no subdirs matched: " + gridRootPath + "/" + subdirPattern);
            System.exit(2);
        }

        List<String> errorBuf = new ArrayList<>();
        int totalFiles  = 0;
        int totalBlocks = 0;
        int totalErrors = 0;
        boolean strictAborted = false;

        for (Path subdir : subdirs) {
            System.out.println("------------------------------------------------------------");
            System.out.println(" Setting: " + subdir.getFileName());
            System.out.println("------------------------------------------------------------");

            List<Path> pyFiles;
            try (Stream<Path> s = Files.list(subdir)) {
                pyFiles = s.filter(Files::isRegularFile)
                           .filter(p -> SAMPLE_FILENAME.matcher(p.getFileName().toString()).matches())
                           .sorted()
                           .collect(Collectors.toList());
            }

            int setFiles  = 0;
            int setBlocks = 0;
            int setErrors = 0;
            for (Path py : pyFiles) {
                Path tsv = py.resolveSibling(
                    py.getFileName().toString().replaceFirst("\\.py$", ".labels.tsv"));
                FileResult fr = checkFile(py, tsv, sourceMap, errorBuf);
                setFiles++;
                setBlocks += fr.blocks;
                setErrors += fr.errors;

                if (verbose) {
                    System.out.printf("  %s : %d blocks, %d errors%n",
                        py.getFileName(), fr.blocks, fr.errors);
                }
                if (strict && fr.errors > 0) {
                    System.err.println("[STRICT] first error in " + py + ", aborting.");
                    strictAborted = true;
                    break;
                }
            }
            System.out.printf("  files checked : %d%n", setFiles);
            System.out.printf("  blocks checked: %d%n", setBlocks);
            System.out.printf("  errors        : %d%n", setErrors);
            System.out.println();

            totalFiles  += setFiles;
            totalBlocks += setBlocks;
            totalErrors += setErrors;
            if (strictAborted) break;
        }

        System.out.println("============================================================");
        System.out.println(" Overall summary");
        System.out.println("============================================================");
        System.out.printf("files checked : %d%n", totalFiles);
        System.out.printf("blocks checked: %d%n", totalBlocks);
        System.out.printf("errors        : %d%n", totalErrors);
        System.out.println();

        flushErrors(errorBuf, maxErrors);

        System.exit(totalErrors == 0 && !strictAborted ? 0 : 1);
    }

    static void flushErrors(List<String> buf, int max) {
        if (buf.isEmpty()) return;
        System.out.println("------------------------------------------------------------");
        System.out.println(" Errors (showing up to " + max + " of " + buf.size() + ")");
        System.out.println("------------------------------------------------------------");
        int show = Math.min(buf.size(), max);
        for (int i = 0; i < show; i++) {
            System.out.println("  " + buf.get(i));
        }
        if (buf.size() > max) {
            System.out.printf("  ... and %d more errors%n", buf.size() - max);
        }
    }

    static void printHelp() {
        System.out.println("checker_mixed_samples_grid - verify mixed-sample grid against source CSV");
        System.out.println();
        System.out.println("Options:");
        System.out.println("  --grid-root  <dir>    Grid root (default: src/app/data_mixed_samples_grid_480)");
        System.out.println("  --source-csv <path>   HWC+AGC source CSV with idx,code,label columns");
        System.out.println("  --pattern    <glob>   Subdir glob under grid-root (default: blocks_*)");
        System.out.println("  --max-errors N        Cap on printed errors (default: 50)");
        System.out.println("  --verbose, -v         Per-file progress output");
        System.out.println("  --strict              Abort on first error");
        System.out.println("  --help, -h            This help");
    }
}