package workbench.modernjava.l04.demo;

import java.time.Duration;
import java.util.Objects;

/** One class with optional fields, against a sealed model that has only the valid shapes. */
public class IllegalStates {

    // the "bag of optionals" a JSON mapper gives you for the catalogue's reply to a hold request
    static final class HoldReplyDto {
        final String status;              // "READY", "UNAVAILABLE" or "WAITLISTED"
        final String pickupCode;          // should be set only when ready
        final String reasonCode;          // should be set only when unavailable
        final Integer waitDays;           // should be set only when waitlisted
        final Integer holdShelf;          // should be set only when ready

        HoldReplyDto(String status, String pickupCode, String reasonCode, Integer waitDays, Integer holdShelf) {
            this.status = status;
            this.pickupCode = pickupCode;
            this.reasonCode = reasonCode;
            this.waitDays = waitDays;
            this.holdShelf = holdShelf;
        }
    }

    // a consumer of the DTO: it trusts that the fields match the status
    static String pickupSlip(HoldReplyDto r) {
        if ("READY".equals(r.status)) return "print slip: shelf " + r.holdShelf + ", code " + r.pickupCode;
        return "no slip";
    }

    // the same information as a closed model: three shapes, each with only its own fields
    sealed interface HoldResult permits Ready, Unavailable, Waitlisted {}

    record Ready(String pickupCode, int shelf) implements HoldResult {
        Ready {
            Objects.requireNonNull(pickupCode, "pickupCode");
            if (shelf < 1) throw new IllegalArgumentException("hold shelves start at 1");
        }
    }

    record Unavailable(String reasonCode) implements HoldResult {}

    record Waitlisted(Duration expectedWait) implements HoldResult {}

    static String pickupSlip(HoldResult r) {
        return switch (r) {
            case Ready(var code, var shelf) -> "print slip: shelf " + shelf + ", code " + code;
            case Unavailable u -> "no slip";
            case Waitlisted w -> "no slip yet";
        };
    }

    public static void main(String[] args) {
        int statuses = 3, optionalFields = 4;
        System.out.println("shapes the DTO allows: " + statuses * (1 << optionalFields) + ", shapes that make sense: 3");

        // ready, but with no pickup code and a reason code: nothing stops it
        HoldReplyDto broken = new HoldReplyDto("READY", null, "10", null, 12);
        System.out.println("DTO consumer:    " + pickupSlip(broken));

        try {
            new Ready(null, 12);
        } catch (NullPointerException e) {
            System.out.println("sealed model:    refused, " + e.getMessage() + " is required");
        }
        System.out.println("sealed consumer: " + pickupSlip(new Ready("K7P2QX", 12)));
    }
}
