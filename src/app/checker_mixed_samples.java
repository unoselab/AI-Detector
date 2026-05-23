import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Stream;

public class checker_mixed_samples {
    private static final Pattern MARKER_RE = Pattern.compile(
        "^\\s*#\\s*===\\s*BLOCK\\s+(\\d+)\\s*\\(label=([^,]+),\\s*source_idx=([^,]+),\\s*name=(.*?)\\)\\s*===\\s*$"
    );

    private static final Pattern DEF_RE = Pattern.compile(
        "^\\s*(?:async\\s+)?def\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*\\("
    );

    private static final Pattern CLASS_RE = Pattern.compile(
        "^\\s*class\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*[:(]"
    );

    static class LabelRow {
        int blockIdx;
        String functionName;
        int startLine;
        int endLine;
        String label;
        String sourceIdx;
    }

    static class Marker {
        int blockIdx;
        int lineNo;
        String label;
        String sourceIdx;
        String name;
    }

    static class Result {
        int filesChecked = 0;
        int blocksChecked = 0;
        int errors = 0;
    }

    public static void main(String[] args) throws Exception {
        List<Path[]> pairs = resolvePairs(args);

        if (pairs.isEmpty()) {
            System.err.println("[ERROR] no sample pairs found.");
            System.exit(1);
        }

        Result total = new Result();

        for (Path[] pair : pairs) {
            checkPair(pair[0], pair[1], total);
        }

        System.out.println();
        System.out.println("============================================================");
        System.out.println("Checker summary");
        System.out.println("============================================================");
        System.out.println("files checked : " + total.filesChecked);
        System.out.println("blocks checked: " + total.blocksChecked);
        System.out.println("errors        : " + total.errors);

        if (total.errors > 0) {
            System.exit(1);
        }
    }

    private static List<Path[]> resolvePairs(String[] args) throws IOException {
        List<Path[]> pairs = new ArrayList<>();

        if (args.length == 0) {
            Path defaultDir = Paths.get("src/app/mixed_samples_50x6");
            return pairsFromDirectory(defaultDir);
        }

        if (args.length == 2) {
            Path a = Paths.get(args[0]);
            Path b = Paths.get(args[1]);

            if (isPy(a) && isLabels(b)) {
                pairs.add(new Path[]{a, b});
                return pairs;
            }
            if (isLabels(a) && isPy(b)) {
                pairs.add(new Path[]{b, a});
                return pairs;
            }
        }

        for (String arg : args) {
            Path p = Paths.get(arg);

            if (Files.isDirectory(p)) {
                pairs.addAll(pairsFromDirectory(p));
            } else if (isPy(p)) {
                pairs.add(new Path[]{p, labelsForPy(p)});
            } else if (isLabels(p)) {
                pairs.add(new Path[]{pyForLabels(p), p});
            } else {
                System.err.println("[WARN] ignoring unsupported path: " + p);
            }
        }

        pairs.sort(Comparator.comparing(pair -> pair[0].toString()));
        return pairs;
    }

    private static List<Path[]> pairsFromDirectory(Path dir) throws IOException {
        List<Path[]> pairs = new ArrayList<>();

        if (!Files.isDirectory(dir)) {
            System.err.println("[ERROR] directory not found: " + dir);
            return pairs;
        }

        try (Stream<Path> stream = Files.list(dir)) {
            stream
                .filter(checker_mixed_samples::isPy)
                .sorted()
                .forEach(py -> pairs.add(new Path[]{py, labelsForPy(py)}));
        }

        return pairs;
    }

    private static boolean isPy(Path p) {
        String name = p.getFileName().toString();
        return name.startsWith("mixed_sample_") && name.endsWith(".py");
    }

    private static boolean isLabels(Path p) {
        String name = p.getFileName().toString();
        return name.startsWith("mixed_sample_") && name.endsWith(".labels.tsv");
    }

    private static Path labelsForPy(Path py) {
        String name = py.getFileName().toString();
        String base = name.substring(0, name.length() - ".py".length());
        return py.resolveSibling(base + ".labels.tsv");
    }

    private static Path pyForLabels(Path labels) {
        String name = labels.getFileName().toString();
        String base = name.substring(0, name.length() - ".labels.tsv".length());
        return labels.resolveSibling(base + ".py");
    }

    private static void checkPair(Path pyPath, Path labelsPath, Result total) throws IOException {
        System.out.println();
        System.out.println("------------------------------------------------------------");
        System.out.println("checking py     : " + pyPath);
        System.out.println("checking labels : " + labelsPath);
        System.out.println("------------------------------------------------------------");

        int errorsBefore = total.errors;

        if (!Files.exists(pyPath)) {
            error(total, "missing .py file: " + pyPath);
            return;
        }
        if (!Files.exists(labelsPath)) {
            error(total, "missing labels file: " + labelsPath);
            return;
        }

        List<String> lines = Files.readAllLines(pyPath, StandardCharsets.UTF_8);
        List<LabelRow> labels = readLabels(labelsPath);
        List<Marker> markers = readMarkers(lines);

        if (markers.size() != labels.size()) {
            error(total, "marker count != labels count: markers=" + markers.size() + ", labels=" + labels.size());
        }

        int n = Math.min(markers.size(), labels.size());

        for (int i = 0; i < n; i++) {
            Marker m = markers.get(i);
            LabelRow r = labels.get(i);

            total.blocksChecked++;

            if (m.blockIdx != r.blockIdx) {
                error(total, "block " + (i + 1) + ": marker block index " + m.blockIdx + " != label block_idx " + r.blockIdx);
            }

            if (m.lineNo != r.startLine) {
                error(total, "block " + r.blockIdx + ": marker line " + m.lineNo + " != start_line " + r.startLine);
            }

            if (!m.label.equals(r.label)) {
                error(total, "block " + r.blockIdx + ": marker label " + m.label + " != label row " + r.label);
            }

            if (!m.sourceIdx.equals(r.sourceIdx)) {
                error(total, "block " + r.blockIdx + ": marker source_idx " + m.sourceIdx + " != label row " + r.sourceIdx);
            }

            if (!m.name.equals(r.functionName)) {
                error(total, "block " + r.blockIdx + ": marker name " + m.name + " != label function_name " + r.functionName);
            }

            if (r.endLine < r.startLine || r.endLine > lines.size()) {
                error(total, "block " + r.blockIdx + ": invalid line range start=" + r.startLine + ", end=" + r.endLine);
                continue;
            }

            String extractedName = extractBlockName(lines, r.startLine + 1, r.endLine);
            if (extractedName == null) {
                error(total, "block " + r.blockIdx + ": could not find def/class name in code block");
            } else if (!extractedName.equals(r.functionName)) {
                error(total, "block " + r.blockIdx + ": code name " + extractedName + " != label function_name " + r.functionName);
            }
        }

        total.filesChecked++;

        if (total.errors == errorsBefore) {
            System.out.println("PASS: " + pyPath.getFileName());
        } else {
            System.out.println("FAIL: " + pyPath.getFileName() + " (" + (total.errors - errorsBefore) + " error(s))");
        }
    }

    private static List<LabelRow> readLabels(Path labelsPath) throws IOException {
        List<String> lines = Files.readAllLines(labelsPath, StandardCharsets.UTF_8);
        List<LabelRow> rows = new ArrayList<>();

        if (lines.isEmpty()) {
            return rows;
        }

        String[] header = lines.get(0).split("\t", -1);
        Map<String, Integer> col = new HashMap<>();
        for (int i = 0; i < header.length; i++) {
            col.put(header[i], i);
        }

        requireColumn(col, "block_idx", labelsPath);
        requireColumn(col, "function_name", labelsPath);
        requireColumn(col, "start_line", labelsPath);
        requireColumn(col, "end_line", labelsPath);
        requireColumn(col, "label", labelsPath);
        requireColumn(col, "source_idx", labelsPath);

        for (int i = 1; i < lines.size(); i++) {
            if (lines.get(i).trim().isEmpty()) {
                continue;
            }

            String[] parts = lines.get(i).split("\t", -1);

            LabelRow r = new LabelRow();
            r.blockIdx = Integer.parseInt(parts[col.get("block_idx")]);
            r.functionName = parts[col.get("function_name")];
            r.startLine = Integer.parseInt(parts[col.get("start_line")]);
            r.endLine = Integer.parseInt(parts[col.get("end_line")]);
            r.label = parts[col.get("label")];
            r.sourceIdx = parts[col.get("source_idx")];

            rows.add(r);
        }

        return rows;
    }

    private static void requireColumn(Map<String, Integer> col, String name, Path path) {
        if (!col.containsKey(name)) {
            throw new IllegalArgumentException("missing column '" + name + "' in " + path);
        }
    }

    private static List<Marker> readMarkers(List<String> lines) {
        List<Marker> markers = new ArrayList<>();

        for (int i = 0; i < lines.size(); i++) {
            Matcher matcher = MARKER_RE.matcher(lines.get(i));
            if (!matcher.matches()) {
                continue;
            }

            Marker m = new Marker();
            m.blockIdx = Integer.parseInt(matcher.group(1));
            m.lineNo = i + 1;
            m.label = matcher.group(2).trim();
            m.sourceIdx = matcher.group(3).trim();
            m.name = matcher.group(4).trim();

            markers.add(m);
        }

        return markers;
    }

    private static String extractBlockName(List<String> lines, int startLine, int endLine) {
        int from = Math.max(1, startLine);
        int to = Math.min(lines.size(), endLine);

        for (int lineNo = from; lineNo <= to; lineNo++) {
            String line = lines.get(lineNo - 1);

            Matcher defMatcher = DEF_RE.matcher(line);
            if (defMatcher.find()) {
                return defMatcher.group(1);
            }

            Matcher classMatcher = CLASS_RE.matcher(line);
            if (classMatcher.find()) {
                return classMatcher.group(1);
            }
        }

        return null;
    }

    private static void error(Result total, String message) {
        total.errors++;
        System.out.println("ERROR: " + message);
    }
}
