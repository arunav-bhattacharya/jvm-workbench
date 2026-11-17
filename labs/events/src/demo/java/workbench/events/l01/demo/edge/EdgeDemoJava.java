package workbench.events.l01.demo.edge;

import java.util.List;
import java.util.Map;

public class EdgeDemoJava {
    record ParcelId(String value) {
        ParcelId {
            if (!value.matches("PP-[0-9]{4,12}")) throw new IllegalArgumentException("invalid parcel id: '" + value + "'");
        }
        @Override public String toString() { return value; }
    }

    record Weight(long grams) {
        Weight {
            if (grams < 0) throw new IllegalArgumentException("weight must not be negative: " + grams);
        }
        @Override public String toString() { return grams + " g"; }
    }

    sealed interface ParcelEvent permits ParcelCollected, ParcelDelivered {}
    record ParcelCollected(ParcelId parcelId, Weight weight) implements ParcelEvent {}
    record ParcelDelivered(ParcelId parcelId, Weight weight) implements ParcelEvent {}

    sealed interface Parsed permits Ok, Rejected {}
    record Ok(ParcelEvent event) implements Parsed {}
    record Rejected(String reason) implements Parsed {}

    static String field(Map<String, String> fields, String name) {
        String v = fields.get(name);
        if (v == null) throw new IllegalArgumentException("missing field '" + name + "'");
        return v;
    }

    static Weight weight(Map<String, String> fields) {
        String raw = field(fields, "grams");
        try {
            return new Weight(Long.parseLong(raw));
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("grams is not a whole number: '" + raw + "'");
        }
    }

    /** The edge: raw fields in, a model value or a reason out. It never throws. */
    static Parsed parse(Map<String, String> fields) {
        try {
            String type = field(fields, "type");
            return switch (type) {
                case "collected" -> new Ok(new ParcelCollected(new ParcelId(field(fields, "parcelId")), weight(fields)));
                case "delivered" -> new Ok(new ParcelDelivered(new ParcelId(field(fields, "parcelId")), weight(fields)));
                default -> new Rejected("unknown event type: '" + type + "'");
            };
        } catch (IllegalArgumentException e) {
            return new Rejected(e.getMessage());                // a constructor or a reader said no
        }
    }

    public static void main(String[] args) {
        List<Map<String, String>> inbox = List.of(
                Map.of("type", "collected", "parcelId", "PP-7781", "grams", "2500"),
                Map.of("type", "collected", "parcelId", "PP-7782", "grams", "2.5"),
                Map.of("type", "delivered", "parcelId", "7781", "grams", "2500"),
                Map.of("type", "delivered", "parcelId", "PP-7781", "grams", "-500"),
                Map.of("type", "collected", "parcelId", "PP-7783"),
                Map.of("type", "failed", "parcelId", "PP-7784", "reason", "NOBODY_HOME"));
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
