package workbench.events.l01.demo.edge;

import java.util.List;
import java.util.Map;

public class EdgeDemoJava {
    record PaymentId(String value) {
        PaymentId {
            if (!value.matches("pay_[A-Za-z0-9]{4,24}")) throw new IllegalArgumentException("invalid payment id: '" + value + "'");
        }
        @Override public String toString() { return value; }
    }

    record Money(long minor) {
        Money {
            if (minor < 0) throw new IllegalArgumentException("amount must not be negative: " + minor);
        }
        @Override public String toString() { return minor + " cents"; }
    }

    sealed interface PaymentEvent permits PaymentCaptured, PaymentRefunded {}
    record PaymentCaptured(PaymentId paymentId, Money amount) implements PaymentEvent {}
    record PaymentRefunded(PaymentId paymentId, Money amount) implements PaymentEvent {}

    sealed interface Parsed permits Ok, Rejected {}
    record Ok(PaymentEvent event) implements Parsed {}
    record Rejected(String reason) implements Parsed {}

    static String field(Map<String, String> fields, String name) {
        String v = fields.get(name);
        if (v == null) throw new IllegalArgumentException("missing field '" + name + "'");
        return v;
    }

    static Money amount(Map<String, String> fields) {
        String raw = field(fields, "amountMinor");
        try {
            return new Money(Long.parseLong(raw));
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("amountMinor is not a whole number: '" + raw + "'");
        }
    }

    /** The edge: raw fields in, a model value or a reason out. It never throws. */
    static Parsed parse(Map<String, String> fields) {
        try {
            String type = field(fields, "type");
            return switch (type) {
                case "captured" -> new Ok(new PaymentCaptured(new PaymentId(field(fields, "paymentId")), amount(fields)));
                case "refunded" -> new Ok(new PaymentRefunded(new PaymentId(field(fields, "paymentId")), amount(fields)));
                default -> new Rejected("unknown event type: '" + type + "'");
            };
        } catch (IllegalArgumentException e) {
            return new Rejected(e.getMessage());                // a constructor or a reader said no
        }
    }

    public static void main(String[] args) {
        List<Map<String, String>> inbox = List.of(
                Map.of("type", "captured", "paymentId", "pay_7781", "amountMinor", "1999"),
                Map.of("type", "captured", "paymentId", "pay_7782", "amountMinor", "12.50"),
                Map.of("type", "refunded", "paymentId", "7781", "amountMinor", "500"),
                Map.of("type", "refunded", "paymentId", "pay_7781", "amountMinor", "-500"),
                Map.of("type", "captured", "paymentId", "pay_7783"),
                Map.of("type", "declined", "paymentId", "pay_7784", "reason", "CARD_EXPIRED"));
        int accepted = 0;
        for (Map<String, String> fields : inbox) {
            switch (parse(fields)) {
                case Ok ok -> { accepted++; System.out.println("OK        " + ok.event()); }
                case Rejected r -> System.out.println("REJECTED  " + r.reason());
            }
        }
        System.out.println(accepted + " accepted, " + (inbox.size() - accepted) + " rejected");
    }
}
