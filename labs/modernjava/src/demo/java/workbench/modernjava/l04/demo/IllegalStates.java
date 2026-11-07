package workbench.modernjava.l04.demo;

import java.time.Duration;
import java.util.Objects;

/** One class with optional fields, against a sealed model that has only the valid shapes. */
public class IllegalStates {

    // the "bag of optionals" a JSON mapper gives you for the issuer's reply
    static final class IssuerReplyDto {
        final String status;              // "APPROVED", "DECLINED" or "SOFT_DECLINE"
        final String authCode;            // should be set only when approved
        final String declineCode;         // should be set only when declined
        final Long retryAfterSeconds;     // should be set only on a soft decline
        final Long amountMinor;           // should be set only when approved

        IssuerReplyDto(String status, String authCode, String declineCode, Long retryAfterSeconds, Long amountMinor) {
            this.status = status;
            this.authCode = authCode;
            this.declineCode = declineCode;
            this.retryAfterSeconds = retryAfterSeconds;
            this.amountMinor = amountMinor;
        }
    }

    // a consumer of the DTO: it trusts that the fields match the status
    static String captureCommand(IssuerReplyDto r) {
        if ("APPROVED".equals(r.status)) return "capture " + r.amountMinor + " with auth code " + r.authCode;
        return "no capture";
    }

    // the same information as a closed model: three shapes, each with only its own fields
    sealed interface AuthResult permits Approved, Declined, RetryLater {}

    record Approved(String authCode, long amountMinor) implements AuthResult {
        Approved {
            Objects.requireNonNull(authCode, "authCode");
            if (amountMinor <= 0) throw new IllegalArgumentException("amount must be positive");
        }
    }

    record Declined(String declineCode) implements AuthResult {}

    record RetryLater(Duration after) implements AuthResult {}

    static String captureCommand(AuthResult r) {
        return switch (r) {
            case Approved(var code, var amount) -> "capture " + amount + " with auth code " + code;
            case Declined d -> "no capture";
            case RetryLater later -> "no capture yet";
        };
    }

    public static void main(String[] args) {
        int statuses = 3, optionalFields = 4;
        System.out.println("shapes the DTO allows: " + statuses * (1 << optionalFields) + ", shapes that make sense: 3");

        // approved, but with no auth code and a decline code: nothing stops it
        IssuerReplyDto broken = new IssuerReplyDto("APPROVED", null, "51", null, 4_200L);
        System.out.println("DTO consumer:    " + captureCommand(broken));

        try {
            new Approved(null, 4_200);
        } catch (NullPointerException e) {
            System.out.println("sealed model:    refused, " + e.getMessage() + " is required");
        }
        System.out.println("sealed consumer: " + captureCommand(new Approved("A1B2C3", 4_200)));
    }
}
