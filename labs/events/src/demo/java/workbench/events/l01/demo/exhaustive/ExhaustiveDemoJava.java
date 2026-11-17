package workbench.events.l01.demo.exhaustive;

import java.util.List;

public class ExhaustiveDemoJava {
    sealed interface ParcelEvent permits ParcelBooked, DeliveryFailed, Handover {
        String parcelId();
    }
    record ParcelBooked(String parcelId, long grams) implements ParcelEvent {}
    record DeliveryFailed(String parcelId, String reason) implements ParcelEvent {}

    sealed interface Handover extends ParcelEvent permits ParcelCollected, ParcelDelivered {
        long grams();
    }
    record ParcelCollected(String parcelId, long grams) implements Handover {}
    record ParcelDelivered(String parcelId, long grams) implements Handover {}

    // Step 2: uncomment this line, add ParcelLost to the permits list above, and run again.
    // record ParcelLost(String parcelId, long grams) implements ParcelEvent {}

    /** One case per leaf, no default: checked by javac. */
    static String summary(ParcelEvent e) {
        return switch (e) {
            case ParcelBooked b -> b.parcelId() + " booked, " + b.grams() + " g";
            case DeliveryFailed f -> f.parcelId() + " not delivered: " + f.reason();
            case ParcelCollected c -> c.parcelId() + " collected, " + c.grams() + " g";
            case ParcelDelivered d -> d.parcelId() + " delivered, " + d.grams() + " g";
        };
    }

    /** One case covers the whole sealed middle level, and the check still holds. */
    static boolean changesHands(ParcelEvent e) {
        return switch (e) {
            case Handover h -> true;
            case ParcelBooked b -> false;
            case DeliveryFailed f -> false;
        };
    }

    /** A default branch: compiles today, and after every change anyone ever makes. */
    static String label(ParcelEvent e) {
        return switch (e) {
            case ParcelCollected c -> "pickup";
            case ParcelDelivered d -> "drop-off";
            default -> "other";
        };
    }

    public static void main(String[] args) {
        List<ParcelEvent> events = List.of(
                new ParcelBooked("PP-7781", 2_500),
                new ParcelCollected("PP-7781", 2_500),
                new ParcelDelivered("PP-7781", 2_500),
                new DeliveryFailed("PP-7782", "NOBODY_HOME"));
        for (ParcelEvent e : events) {
            System.out.printf("%-36s changes hands: %-5s label: %s%n", summary(e), changesHands(e), label(e));
        }
    }
}
