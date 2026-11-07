package workbench.events.l01.demo.stringly;

import java.util.List;
import java.util.Map;

/** Three handlers each read the raw fields of a message. Nothing checked the message first. */
public class StringlyDemoJava {
    static long balanceCents = 0;
    static int receiptsSent = 0;

    static void audit(Map<String, String> fields) {
        System.out.println("audit    " + fields.get("type") + " " + fields.get("paymentId"));
    }

    static void ledger(Map<String, String> fields) {
        if ("captured".equals(fields.get("type"))) {
            long cents = Long.parseLong(fields.get("amountMinor"));    // parsing, deep inside a handler
            balanceCents += cents;
            System.out.println("ledger   +" + cents + ", balance " + balanceCents);
        }
    }

    static void receipts(Map<String, String> fields) {
        if ("capture".equals(fields.get("type"))) {                   // a typo the compiler can't see
            receiptsSent++;
        }
    }

    public static void main(String[] args) {
        List<Map<String, String>> messages = List.of(
                Map.of("type", "captured", "paymentId", "pay_7781", "amountMinor", "1999"),
                Map.of("type", "refunded", "paymentId", "pay_7781", "amountMinor", "500"),
                Map.of("type", "captured", "paymentId", "pay_7782", "amountMinor", "12.50"));
        for (Map<String, String> m : messages) {
            try {
                audit(m);
                ledger(m);
                receipts(m);
            } catch (RuntimeException e) {
                System.out.println("FAILED   " + e);
            }
        }
        System.out.println("receipts sent: " + receiptsSent);
    }
}
