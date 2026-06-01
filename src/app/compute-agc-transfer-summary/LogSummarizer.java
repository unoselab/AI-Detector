import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class LogSummarizer {

    // Helper class to store extracted metrics for each target dataset
    static class SummaryRecord {
        String target;
        String correct;
        String accuracy;

        SummaryRecord(String target, String correct, String accuracy) {
            this.target = target;
            this.correct = correct;
            this.accuracy = accuracy;
        }
    }

    public static void main(String[] args) {
        // Default log path assuming execution from the project repository root
        String logFilePath = "src/logs/run3-compute-agc-transfer_20260601_005106.log";
        
        if (args.length > 0) {
           logFilePath = args[0];
        }

        List<SummaryRecord> records = new ArrayList<>();

        // Regex patterns to capture the target names and evaluation metrics
        Pattern targetPattern = Pattern.compile(">>> TRANSFER\\s+clf=\\S+\\s+->\\s+target=(\\S+)");
        Pattern correctPattern = Pattern.compile("^correct\\s+:\\s+(\\d+)$");
        Pattern accuracyPattern = Pattern.compile("^accuracy\\s+:\\s+([0-9.]+)$");

        try (BufferedReader br = new BufferedReader(new FileReader(logFilePath))) {
            String line;
            String currentTarget = null;
            String currentCorrect = null;
            boolean inSummary = false;

            while ((line = br.readLine()) != null) {
                // 1. Detect the start of a new cross-generator target evaluation
                Matcher targetMatcher = targetPattern.matcher(line);
                if (targetMatcher.find()) {
                    currentTarget = targetMatcher.group(1);
                    inSummary = false; // Reset summary context for the new target
                    currentCorrect = null;
                    continue;
                }

                // 2. Identify the "Overall summary" block for the current target
                if (currentTarget != null) {
                    if (line.contains("Overall summary")) {
                        inSummary = true;
                        continue;
                    }

                    // 3. Extract the metrics if we are inside the summary block
                    if (inSummary) {
                        Matcher correctMatcher = correctPattern.matcher(line);
                        if (correctMatcher.find()) {
                            currentCorrect = correctMatcher.group(1);
                        }

                        Matcher accuracyMatcher = accuracyPattern.matcher(line);
                        if (accuracyMatcher.find()) {
                            String currentAccuracy = accuracyMatcher.group(1);
                            
                            // Both target and accuracy are found; save the record
                            records.add(new SummaryRecord(currentTarget, currentCorrect, currentAccuracy));
                            
                            // Reset state to prepare for the next target in the log
                            currentTarget = null;
                            inSummary = false;
                        }
                    }
                }
            }
        } catch (IOException e) {
            System.err.println("[Error] Could not read or parse the log file: " + e.getMessage());
            return;
        }

        // Output the extracted data formatted as a Markdown Table
        // System.out.println("### Cross-Generator Log Evaluation Summary");
        // System.out.println("| Evaluation Target (Test Set) | Correct Blocks | Accuracy |");
        // System.out.println("| :--- | :---: | :---: |");
        
        // for (SummaryRecord record : records) {
        //     // Clean up the verbose suffix for readability in the table
        //     String shortTarget = record.target.replace("_4500_complexity_stratified_maxlen2048", "");
        //     // System.out.printf("| %-28s | %-14s | %-8s |%n", shortTarget, record.correct + " / 300", record.accuracy);
        //     System.out.printf("| %s | %s / 300 | %s |%n",
        //         shortTarget,
        //         record.correct,
        //         record.accuracy);
        // }
    
        // System.out.println("### Cross-Generator Log Evaluation Summary");
        // System.out.println();
        // System.out.println("| Target Generator | Correct Blocks | Accuracy |");
        // System.out.println("| :--- | ---: | ---: |");

        // Output the extracted data formatted as a pretty Markdown table
        String[] headers = {
            "Target Generator",
            "Correct Blocks",
            "Accuracy"
        };

        List<String[]> tableRows = new ArrayList<>();

        for (SummaryRecord record : records) {
            String target = prettyTarget(record.target);
            String correct = record.correct + " / 300";
            String accuracy = String.format("%.2f%%", Double.parseDouble(record.accuracy) * 100.0);

            tableRows.add(new String[] { target, correct, accuracy });
        }

        printMarkdownTable(headers, tableRows);
    }

    

    private static String prettyTarget(String target) {
        target = target.replace("_4500_complexity_stratified_maxlen2048", "");

        switch (target) {
            case "starcoder2-15b-instruct-v0.1":
                return "StarCoder2-15B-Instruct";
            case "codellama-7b":
                return "CodeLlama-7B";
            case "starcoder2-7b":
                return "StarCoder2-7B";
            case "gemma":
                return "Gemma";
            case "gpt-oss":
                return "GPT-OSS";
            default:
                return target;
        }
    }

    private static void printMarkdownTable(String[] headers, List<String[]> rows) {
        int cols = headers.length;
        int[] widths = new int[cols];

        // Start with header widths
        for (int i = 0; i < cols; i++) {
            widths[i] = headers[i].length();
        }

        // Expand widths based on row values
        for (String[] row : rows) {
            for (int i = 0; i < cols; i++) {
                widths[i] = Math.max(widths[i], row[i].length());
            }
        }

        System.out.println("### Cross-Generator Log Evaluation Summary");
        System.out.println();

        // Header row
        System.out.print("|");
        for (int i = 0; i < cols; i++) {
            System.out.printf(" %-" + widths[i] + "s |", headers[i]);
        }
        System.out.println();

        // Separator row
        System.out.print("|");
        for (int i = 0; i < cols; i++) {
            if (i == 0) {
                System.out.print(" :" + repeat("-", widths[i] - 1) + " |");
            } else {
                System.out.print(" " + repeat("-", widths[i] - 1) + ": |");
            }
        }
        System.out.println();

        // Data rows
        for (String[] row : rows) {
            System.out.print("|");
            for (int i = 0; i < cols; i++) {
                if (i == 0) {
                    // Left-align target name
                    System.out.printf(" %-" + widths[i] + "s |", row[i]);
                } else {
                    // Right-align numeric columns
                    System.out.printf(" %" + widths[i] + "s |", row[i]);
                }
            }
            System.out.println();
        }
    }

    private static String repeat(String s, int count) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < count; i++) {
            sb.append(s);
        }
        return sb.toString();
    }

}