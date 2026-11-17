package workbench.events.l01.demo.stringly;

import java.util.List;
import java.util.Map;

/** Three handlers each read the raw fields of a scan. Nothing checked the scan first. */
public class StringlyDemoJava {
    static long onTheBikeGrams = 0;
    static int textsSent = 0;

    static void tracking(Map<String, String> fields) {
        System.out.println("tracking " + fields.get("type") + " " + fields.get("parcelId"));
    }

    static void loadBoard(Map<String, String> fields) {
        long grams;
        switch (fields.get("type")) {
            case "collected" -> grams = Long.parseLong(fields.get("grams"));     // parsing, deep inside a handler
            case "delivered" -> grams = -Long.parseLong(fields.get("grams"));
            default -> { return; }
        }
        onTheBikeGrams += grams;
        System.out.printf("load     %+d g, on the bike: %d g%n", grams, onTheBikeGrams);
    }

    static void texts(Map<String, String> fields) {
        if ("deliver".equals(fields.get("type"))) {                   // a typo the compiler can't see
            textsSent++;
        }
    }

    public static void main(String[] args) {
        List<Map<String, String>> scans = List.of(
                Map.of("type", "collected", "parcelId", "PP-7781", "grams", "2500"),
                Map.of("type", "delivered", "parcelId", "PP-7781", "grams", "2500"),
                Map.of("type", "collected", "parcelId", "PP-7782", "grams", "2.5"));
        for (Map<String, String> scan : scans) {
            try {
                tracking(scan);
                loadBoard(scan);
                texts(scan);
            } catch (RuntimeException e) {
                System.out.println("FAILED   " + e);
            }
        }
        System.out.println("texts sent: " + textsSent);
    }
}
