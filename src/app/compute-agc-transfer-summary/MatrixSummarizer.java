/*
Usage:
user1-system12@OISSE-IST173C01:
    cd ~/project-workspace/ai_detector/src/app/compute-agc-transfer-summary
    java MatrixSummarizer ../../../src/logs/
*/
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class MatrixSummarizer {

    // Standard publication labels for rows and columns
    private static final String[] MODELS = {
        "StarCoder2-15B", "StarCoder2-7B", "CodeLlama-7B", "Gemma", "GPT-OSS"
    };

    // Internal mapping to match verbose log tags with clean paper tokens
    private static String cleanModelName(String rawName) {
        if (rawName == null) return "Unknown";
        String lower = rawName.toLowerCase();
        if (lower.contains("starcoder2-15b")) return "StarCoder2-15B";
        if (lower.contains("starcoder2-7b")) return "StarCoder2-7B";
        if (lower.contains("codellama-7b")) return "CodeLlama-7B";
        if (lower.contains("gemma")) return "Gemma";
        if (lower.contains("gpt-oss")) return "GPT-OSS";
        return rawName;
    }

    public static void main(String[] args) {
        // Target log directory relative to execution context
        File logDir = new File("../../logs");
        if (args.length > 0) {
            logDir = new File(args[0]); // Extracted the first element securely
        }

        if (!logDir.exists() || !logDir.isDirectory()) {
            System.err.println("[Error] Missing or invalid logs directory at: " + logDir.getAbsolutePath());
            return;
        }

        // Two-tier Map to hold the 5x5 evaluation matrix context: Map<Classifier, Map<Target, Accuracy>>
        Map<String, Map<String, String>> performanceMatrix = new HashMap<>();

        // Regex compilation for highly-precise token isolation
        Pattern transferPattern = Pattern.compile(">>> TRANSFER\\s+clf=(\\S+)\\s+->\\s+target=(\\S+)");
        Pattern accuracyPattern = Pattern.compile("^accuracy\\s+:\\s+([0-9.]+)$");

        File[] logFiles = logDir.listFiles((dir, name) -> name.startsWith("transfer_run_") && name.endsWith(".log"));

        if (logFiles == null || logFiles.length == 0) {
            System.err.println("[Warning] No transfer log files matching 'transfer_run_*.log' found inside targets.");
            return;
        }

        // Process each identified log framework independently
        for (File file : logFiles) {
            try (BufferedReader br = new BufferedReader(new FileReader(file))) {
                String line;
                String currentClassifier = null;
                String currentTarget = null;
                boolean inSummary = false;

                while ((line = br.readLine()) != null) {
                    Matcher transferMatcher = transferPattern.matcher(line);
                    if (transferMatcher.find()) {
                        currentClassifier = cleanModelName(transferMatcher.group(1));
                        currentTarget = cleanModelName(transferMatcher.group(2));
                        inSummary = false;
                        continue;
                    }

                    if (currentClassifier != null && currentTarget != null) {
                        if (line.contains("Overall summary")) {
                            inSummary = true;
                            continue;
                        }

                        if (inSummary) {
                            Matcher accuracyMatcher = accuracyPattern.matcher(line);
                            if (accuracyMatcher.find()) {
                                String accuracyVal = accuracyMatcher.group(1);

                                // Dynamically compile cell inside inner-tier map matrix
                                performanceMatrix.putIfAbsent(currentClassifier, new HashMap<>());
                                performanceMatrix.get(currentClassifier).put(currentTarget, accuracyVal);

                                // Clear target scope flag to await next block offset
                                currentTarget = null;
                                inSummary = false;
                            }
                        }
                    }
                }
            } catch (IOException e) {
                System.err.println("[Error] An abnormality occurred reading file " + file.getName() + ": " + e.getMessage());
            }
        }

        // =====================================================================
        // OUTPUT 1: Markdown Table Format
        // =====================================================================
        System.out.println("\n### Table 4: Cross-Generator Robustness Matrix (Block-Level Accuracy)");
        System.out.print("| Trained Classifier | ");
        for (String col : MODELS) {
            System.out.print(col + " (Test) | ");
        }
        System.out.println("\n| :--- | " + " :---: |".repeat(MODELS.length));

        for (String row : MODELS) {
            System.out.printf("| %-18s | ", row);
            Map<String, String> rowMap = performanceMatrix.getOrDefault(row, new HashMap<>());
            for (String col : MODELS) {
                String cellValue = rowMap.getOrDefault(col, "N/A");
                if (row.equals(col) && !cellValue.equals("N/A")) {
                    System.out.printf("**%-6s** | ", cellValue); 
                } else {
                    System.out.printf("%-8s | ", cellValue);
                }
            }
            System.out.println();
        }
        System.out.println();

        // =====================================================================
        // OUTPUT 2: LaTeX Table Format
        // =====================================================================
        System.out.println("=========================================================================");
        System.out.println(" Generated LaTeX Code Blocks for Academic Paper Drafts");
        System.out.println("=========================================================================");
        System.out.println("\\begin{table}[htbp]");
        System.out.println("\\scriptsize\\centering");
        System.out.println("\\caption{Cross-Generator Domain Transfer Generalization Performance (Block-Level Accuracy)}");
        System.out.println("\\label{tab:cross_generator_matrix}");
        System.out.println("\\begin{tabular}{l|ccccc}");
        System.out.println("\\hline");
        
        // Print LaTeX Header row
        System.out.print("\\textbf{Trained Classifier}");
        for (String col : MODELS) {
            System.out.print(" & \\textbf{" + col + " (Test)}");
        }
        System.out.println(" \\\\ \\hline");

        // Print LaTeX Data rows
        for (String row : MODELS) {
            System.out.printf("%-20s", row);
            Map<String, String> rowMap = performanceMatrix.getOrDefault(row, new HashMap<>());
            for (String col : MODELS) {
                String cellValue = rowMap.getOrDefault(col, "N/A");
                if (row.equals(col) && !cellValue.equals("N/A")) {
                    System.out.print(" & \\textbf{" + cellValue + "}"); // Emphasize diagonal via \textbf{}
                } else {
                    System.out.print(" & " + cellValue);
                }
            }
            System.out.println(" \\\\");
        }
        
        System.out.println("\\hline");
        System.out.println("\\end{tabular}");
        System.out.println("\\end{table}\n");
    }
}